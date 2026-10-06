"""LegalEase AI Chat — Pakistani-law-scoped RAG assistant (Task 3 spec).

Pipeline (Final Report Algorithm 5):
    1. Embed the user query with the same multilingual model used to
       build the FAISS index.
    2. Retrieve top RAG_TOP_K=5 chunks.
    3. Filter by similarity >= RAG_SIMILARITY_THRESHOLD (0.65).
    4. If NO chunks pass the threshold, return the out-of-scope refusal
       — we do NOT let the LLM answer un-grounded questions, that's the
       whole point of a RAG system.
    5. Otherwise build a system + context + history + user prompt and
       call the LLM.
    6. Ground the answer's citations in the retrieved passages
       (app/ai/citation_check.py).
    7. Persist user + AI messages to chat_sessions / chat_messages with
       the list of source names cited.
"""

from __future__ import annotations

import time
import uuid
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import embeddings, family_index, section_lookup
from app.ai.citation_check import check_citations
from app.ai.client import get_ai_client
from app.ai.query_rewrite import rewrite_for_search
from app.core.config import settings
from app.core.exceptions import NotAuthorized, NotFound
from app.core.logging import logger
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import SenderType
from app.models.user import User

# Per Task 3 spec — strict scope filter. Outside of Pakistani law the bot
# must refuse, not hallucinate.
# The retrieval index is statute-only; this prompt must never claim judgments exist.
SYSTEM_PROMPT = (
    "You are LegalEase AI, a specialized legal assistant for Pakistani law. "
    "You ONLY answer questions about Pakistani statutes, court procedures, "
    "legal rights, and matters under Pakistani jurisdiction. "
    "Your knowledge base is LegalEase's library of Pakistani statute text "
    "(Acts, Ordinances, Codes and Orders); it contains no court judgments or "
    "case law. For each question the system retrieves the most relevant "
    "statute passages and lists them below as numbered sources; the user "
    "did not write them and cannot see them, so never call them passages "
    "the user provided. Base your answer on these passages, citing them by "
    "[n]. Cite a section number only if it appears in those passages. Never "
    "cite case names, law-report citations (PLD, SCMR, MLD, CLC, YLR or "
    "similar) or any judgment. If the passages don't cover part of the "
    "question, say that LegalEase's statute library doesn't cover it, point "
    "to the closest passage that does apply, and don't fill the gap from "
    "memory. "
    "If asked anything outside Pakistani law (cooking, sports, general "
    "knowledge, foreign law etc.), politely refuse and redirect to legal "
    "topics. "
    # The chat UI shows this opening line as a highlighted "Short answer" box.
    "Begin every substantive answer with one sentence starting with the "
    "short-answer label given in the language instruction below, stating "
    "the core point, then give the detailed breakdown. Don't add it to "
    "refusals."
)

# Step 2 of the Oct 2026 chat-quality work (settings.STRICT_GROUNDING).
# The 2026-10-05 legal review found answers that extended a widow's share
# to a separated wife "by analogy", applied an Air Force Act offence to
# advocates, and listed consequences no passage mentioned
# (docs/chat_review_family_law_2026-10-05.md, section 4).
STRICT_GROUNDING_RULES = (
    "GROUNDING RULES — these override anything above:\n"
    "1. Every statement of law, procedure, right, remedy, penalty or "
    "consequence must come from a numbered passage and carry its [n]. A "
    "sentence you cannot tie to a passage does not belong in the answer.\n"
    "2. Apply a passage only to what it covers. If it is limited to a "
    "particular person (e.g. a widow, a member of the armed forces), "
    "proceeding (e.g. probate, an inquiry) or statute, don't apply it to "
    "anyone or anything else. No reasoning by analogy.\n"
    "3. Don't add consequences, procedures, remedies, duties or examples "
    "from your own knowledge, even if you believe them to be correct.\n"
    "4. If the passages don't cover the question or part of it, say so "
    "plainly — e.g. \"The retrieved provisions don't cover who bears the "
    "burden of proof\" — and stop there for that part. If they cover none "
    "of it, say that and give no other answer.\n"
    "5. The short-answer sentence follows the same rules: state only what "
    "the passages support."
)

# Appended per question. The detected language is stated explicitly: left
# to infer it, the model once answered an English question in Urdu (Oct 2026
# audit) — the prompt's only concrete label example was the Urdu one.
# Chat history is sent verbatim, and Groq's on-demand tier caps a request
# at 8,000 tokens per minute (prompt + the 2,000-token reply reserve, plus
# ~600 for the query rewrite in the same minute). A first question is ~2,200
# prompt tokens; by the 6th turn with long answers the history alone pushed
# a request past the cap (docs/retrieval_redesign.md, section 2.3). Keep the
# newest messages up to this budget.
HISTORY_TOKEN_BUDGET = 2000


@lru_cache(maxsize=1)
def _encoder():
    """gpt-oss uses the o200k tokenizer family. tiktoken downloads the
    encoding file on first use; None if that isn't possible (offline)."""
    try:
        import tiktoken
        return tiktoken.get_encoding("o200k_base")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"o200k tokenizer unavailable, estimating history tokens: {e}")
        return None


def count_tokens(text: str) -> int:
    enc = _encoder()
    if enc is not None:
        return len(enc.encode(text))
    # Conservative fallback: English legal text is ~0.22 tokens/char and
    # Urdu runs higher, so half the character count over-estimates both.
    return len(text) // 2 + 1


def trim_history(history: list[dict], budget: int = HISTORY_TOKEN_BUDGET) -> list[dict]:
    """The most recent messages whose total fits in `budget` tokens, oldest
    first. Whole messages only, and contiguous: stops at the first message
    (going back in time) that doesn't fit rather than skipping it, so the
    model never sees a gap in the conversation."""
    kept: list[dict] = []
    used = 0
    for msg in reversed(history):
        cost = count_tokens(msg["content"])
        if used + cost > budget:
            break
        kept.append(msg)
        used += cost
    if len(kept) < len(history):
        logger.info(f"Chat history trimmed to {len(kept)} of {len(history)} messages ({used} tokens)")
    kept.reverse()
    return kept


LANGUAGE_INSTRUCTION = {
    "en": (
        "LANGUAGE: The question is in English. Answer in the language of the "
        "question — write the entire answer in English. Start it with "
        "\"Short answer:\"."
    ),
    "ur": (
        "LANGUAGE: The question is in Urdu. Answer in the language of the "
        "question — write the entire answer in Urdu (Nastaliq script). Start "
        "it with \"مختصر جواب:\"."
    ),
}


def build_system_prompt(context_block: str, lang: str, *, strict: bool | None = None) -> str:
    """The full system prompt for one question: base rules, the retrieved
    authorities, then the language instruction for this question.
    `strict` (default settings.STRICT_GROUNDING) adds STRICT_GROUNDING_RULES."""
    strict = settings.STRICT_GROUNDING if strict is None else strict
    rules = f"{SYSTEM_PROMPT}\n\n{STRICT_GROUNDING_RULES}" if strict else SYSTEM_PROMPT
    return (
        f"{rules}\n\n"
        "--- Relevant Pakistani legal authorities (cite by [n]) ---\n"
        f"{context_block}\n"
        "--- End authorities ---\n\n"
        f"{LANGUAGE_INSTRUCTION['ur' if lang == 'ur' else 'en']}"
    )

# Fixed replies sent without a model call, in the language of the question
# (an Urdu question used to get the English refusal; Oct 2026 quality pass).
OUT_OF_SCOPE_REFUSAL = {
    "en": (
        "I can only answer questions about Pakistani law and legal matters. "
        "This question appears to be outside my scope. Please ask about "
        "Pakistani statutes, court procedures, or legal matters."
    ),
    "ur": (
        "میں صرف پاکستانی قانون اور قانونی معاملات سے متعلق سوالات کے جواب دے سکتا ہوں۔ "
        "یہ سوال میرے دائرۂ کار سے باہر معلوم ہوتا ہے۔ براہِ کرم پاکستانی قوانین، "
        "عدالتی طریقۂ کار یا قانونی معاملات کے بارے میں پوچھیں۔"
    ),
}
INDEX_NOT_READY = {
    "en": "The legal knowledge base is still being built. Please try again in a few minutes.",
    "ur": "قانونی معلومات کا ذخیرہ ابھی تیار کیا جا رہا ہے۔ براہِ کرم چند منٹ بعد دوبارہ کوشش کریں۔",
}


def fixed_reply(texts: dict[str, str], lang: str) -> str:
    return texts["ur" if lang == "ur" else "en"]


def _ms_since(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def answer_flags(citations: list[dict] | None) -> dict:
    """Per-answer flags the page shows, derived from the stored citations
    so a reloaded history shows the same as the live reply:
      confidence    "low" when settings.LOW_CONFIDENCE_NOTE is on and the
                    best passage scores below LOW_CONFIDENCE_UPPER; "normal"
                    otherwise; None for replies with no passages (refusals)
      family_scope  True when the passages came from the family-law index
    """
    if not citations:
        return {"confidence": None, "family_scope": False}
    best = max(c.get("relevance") or 0 for c in citations)
    low = settings.LOW_CONFIDENCE_NOTE and best < settings.LOW_CONFIDENCE_UPPER
    return {"confidence": "low" if low else "normal",
            "family_scope": any(c.get("family") for c in citations)}


def family_scope_applies(message: str, search_query: str, family: str) -> bool:
    """family: "auto" (the default; on for questions using a family term
    of art), "on" (always) or "off" (the user switched it off). Never on
    while settings.FAMILY_INDEX is off."""
    if not settings.FAMILY_INDEX or family == "off":
        return False
    return family == "on" or family_index.is_family_question(message, search_query)


def retrieve_passages(message: str, search_query: str, *, family: str = "auto") -> list[dict]:
    """The passages the model will see: the top RAG_TOP_K for the
    (rewritten) search query that pass the threshold, with contents-list
    chunks replaced by the sections they point to. Empty means refuse.

    In family scope (see family_scope_applies) the family-law side index
    is searched first, against FAMILY_THRESHOLD; if nothing passes, the
    full index is searched as before. Family passages carry
    "family_window".

    The evaluation script (scripts/eval_chat_quality.py) replays this
    function offline, so chat and evaluation can't drift apart."""
    passages: list[dict] = []
    if family_scope_applies(message, search_query, family):
        found = family_index.search(
            search_query, settings.RAG_TOP_K,
            minority=family_index.names_community(message, search_query),
        )
        passages = [r for r in found if r["relevance"] >= settings.FAMILY_THRESHOLD]
        logger.info(f"Family scope: {len(passages)} of {len(found)} family passages pass")
    if not passages:
        retrieved = embeddings.search(search_query, top_k=settings.RAG_TOP_K)
        passages = [
            r for r in retrieved
            if r.get("relevance", 0) >= embeddings.similarity_threshold()
        ]

    # A table-of-contents chunk often outranks the section text it lists
    # (fixed-size chunks split sections). Follow it to the sections the
    # question points at; their text replaces the contents list.
    extra = section_lookup.section_passages(message, passages)
    if extra:
        logger.info(
            f"Section lookup: +{len(extra)} passages via contents list "
            f"({', '.join(sorted({e['via_toc'] for e in extra}))})"
        )
        passages = [
            p for p in passages
            if not section_lookup.is_toc(embeddings.record_text(p))
        ] + extra
    return passages


def compose_answer(ai, passages: list[dict], history: list[dict], lang: str, *,
                   strict: bool | None = None):
    """Ask the model to answer from `passages` (history ends with the
    question), then ground its citations: every section cited must appear
    in the passages, and case law (which the statute-only corpus never
    contains) is removed. Returns the CitationCheck result. Shared with
    the evaluation script so both send the same prompt."""
    context_block = "\n\n".join(
        f"[{i + 1}] Source: {embeddings.record_source(p)}\n"
        f"{embeddings.record_text(p)}"
        for i, p in enumerate(passages)
    )
    system = build_system_prompt(context_block, lang, strict=strict)
    raw_text = ai.chat(history, system=system)
    checked = check_citations(
        raw_text,
        [{"source": embeddings.record_source(p), "text": embeddings.record_text(p)}
         for p in passages],
        lang=lang,
    )
    logger.info(f"Citation check: {checked.summary()}")
    return checked


def _detect_language(text: str) -> str:
    try:
        from langdetect import detect
        return "ur" if detect(text) == "ur" else "en"
    except Exception:  # noqa: BLE001
        return "en"


class LegalChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.ai = get_ai_client()

    # ----- Sessions ------------------------------------------------------

    def list_sessions(self, user: User) -> list[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(ChatSession.updated_at.desc())
        )
        return list(self.db.scalars(stmt))

    def get_session(self, session_id: uuid.UUID, user: User) -> ChatSession:
        sess = self.db.get(ChatSession, session_id)
        if sess is None:
            raise NotFound("Chat session not found.")
        if sess.user_id != user.id:
            raise NotAuthorized("This chat session belongs to another user.")
        return sess

    def get_history(self, session_id: uuid.UUID, user: User) -> list[ChatMessage]:
        sess = self.get_session(session_id, user)
        return list(sess.messages)

    # ----- Main entry point ---------------------------------------------

    def send(
        self,
        user: User,
        message: str,
        session_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
        family: str = "auto",
    ) -> dict:
        """Send a message and get the AI reply. `family` is the page's
        family-law switch: "auto" (default) or "off".

        Returns the spec-mandated shape:
            { "response": str, "sources": list[str], "session_id": str }

        Split into three phases so no DB transaction stays open across the
        slow work (embedding-model load, query rewrite, answer generation).
        Supabase's pooler kills a connection left idle-in-transaction, which
        surfaced as a 500 on the first message after a backend restart.
        """
        # Phase 1 — short DB write: resolve / create the session, read the
        # history, persist the user message (we want a full audit of what
        # was asked, whatever the outcome), then commit.
        if session_id is not None:
            session = self.get_session(session_id, user)
            history = trim_history(self._recent_history(session.id, limit=10))
        else:
            session = ChatSession(
                user_id=user.id,
                case_id=case_id,
                title=message[:80],
                language_hint=_detect_language(message),
                total_messages=0,
            )
            self.db.add(session)
            self.db.flush()
            history = []

        # Per question, not per session: answer in the language of *this*
        # question even if the conversation started in the other language.
        lang = _detect_language(message)
        sid = session.id
        self.db.add(ChatMessage(
            session_id=sid,
            sender_type=SenderType.USER,
            content=message,
            detected_language=lang,
        ))
        session.total_messages = (session.total_messages or 0) + 1
        self.db.commit()
        # From here until phase 3, touch no ORM object: commit expired them,
        # and a lazy reload would open a new transaction.

        # Phase 2 — retrieval + LLM, no DB transaction held. Timed from
        # here: rewrite + retrieval + answer is what the user waits for.
        t0 = time.perf_counter()
        index_size = embeddings.build_or_load()
        if index_size == 0:
            logger.warning("Chat called but FAISS index is empty.")
            return self._reply(sid, lang, fixed_reply(INDEX_NOT_READY, lang))

        search_query = rewrite_for_search(message)
        passages = retrieve_passages(message, search_query, family=family)

        # Out-of-scope refusal — no LLM call, no hallucination risk
        if not passages:
            logger.info(
                f"Chat refusal — no chunks above {embeddings.similarity_threshold()} threshold"
            )
            return self._reply(sid, lang, fixed_reply(OUT_OF_SCOPE_REFUSAL, lang),
                               response_time_ms=_ms_since(t0))

        history.append({"role": "user", "content": message})
        # AIServiceUnavailable propagates -> router returns 503; the user
        # message stays saved without a reply.
        checked = compose_answer(self.ai, passages, history, lang)

        citations_payload = [
            {
                "source": embeddings.record_source(p),
                "kind": embeddings.record_kind(p),
                "excerpt": embeddings.record_text(p)[:240],
                "relevance": round(p.get("relevance", 0), 4),
                "family": p.get("family_window") is not None,
            }
            for p in passages
        ]
        # Phase 3 — short DB write: persist the reply.
        return self._reply(
            sid, lang, checked.text,
            citations=citations_payload,
            response_time_ms=_ms_since(t0),
            sources=self._unique_sources(passages),
        )

    # ----- Internal ------------------------------------------------------

    def _reply(
        self,
        session_id: uuid.UUID,
        lang: str,
        content: str,
        *,
        citations: list[dict] | None = None,
        response_time_ms: int = 0,
        sources: list[str] | None = None,
    ) -> dict:
        """Persist the AI message in its own short transaction."""
        self.db.add(ChatMessage(
            session_id=session_id,
            sender_type=SenderType.AI,
            content=content,
            citations=citations,
            response_time_ms=response_time_ms,
            detected_language=lang,
        ))
        session = self.db.get(ChatSession, session_id)
        session.total_messages = (session.total_messages or 0) + 1
        self.db.commit()
        return {
            "response": content,
            "sources": sources or [],
            "session_id": str(session_id),
            # Numbered exactly as the answer's [n] markers: passage n = item n.
            "citations": [
                {"n": i + 1, "source": c["source"], "excerpt": c.get("excerpt")}
                for i, c in enumerate(citations or [])
            ],
            "response_time_ms": response_time_ms,
            **answer_flags(citations),
        }

    def _recent_history(self, session_id: uuid.UUID, *, limit: int) -> list[dict]:
        rows = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        return [
            {
                "role": "assistant" if m.sender_type == SenderType.AI else "user",
                "content": m.content,
            }
            for m in rows
        ]

    @staticmethod
    def _unique_sources(passages: list[dict]) -> list[str]:
        seen: dict[str, None] = {}
        for p in passages:
            name = embeddings.record_source(p)
            if name and name not in seen:
                seen[name] = None
        return list(seen.keys())
