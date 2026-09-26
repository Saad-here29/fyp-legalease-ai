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

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import embeddings, section_lookup
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
    "topics. Answer in the same language the user writes in (English or "
    "Urdu)."
)

OUT_OF_SCOPE_REFUSAL = (
    "I can only answer questions about Pakistani law and legal matters. "
    "This question appears to be outside my scope. Please ask about "
    "Pakistani statutes, court procedures, or legal matters."
)


def _ms_since(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


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
    ) -> dict:
        """Send a message and get the AI reply.

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
            history = self._recent_history(session.id, limit=10)
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

        lang = session.language_hint or _detect_language(message)
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
            return self._reply(
                sid, lang,
                "The legal knowledge base is still being built. Please try again in a few minutes.",
            )

        search_query = rewrite_for_search(message)
        retrieved = embeddings.search(search_query, top_k=settings.RAG_TOP_K)
        passages = [
            r for r in retrieved
            if r.get("relevance", 0) >= settings.RAG_SIMILARITY_THRESHOLD
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

        # Out-of-scope refusal — no LLM call, no hallucination risk
        if not passages:
            logger.info(
                f"Chat refusal — no chunks above {settings.RAG_SIMILARITY_THRESHOLD} threshold"
            )
            return self._reply(sid, lang, OUT_OF_SCOPE_REFUSAL,
                               response_time_ms=_ms_since(t0))

        context_block = "\n\n".join(
            f"[{i + 1}] Source: {embeddings.record_source(p)}\n"
            f"{embeddings.record_text(p)}"
            for i, p in enumerate(passages)
        )
        history.append({"role": "user", "content": message})
        system = (
            f"{SYSTEM_PROMPT}\n\n"
            "--- Relevant Pakistani legal authorities (cite by [n]) ---\n"
            f"{context_block}\n"
            "--- End authorities ---"
        )

        # AIServiceUnavailable propagates -> router returns 503; the user
        # message stays saved without a reply.
        raw_text = self.ai.chat(history, system=system)

        # Every section cited must appear in the retrieved passages; case
        # law (which the statute-only corpus never contains) is removed.
        checked = check_citations(
            raw_text,
            [{"source": embeddings.record_source(p), "text": embeddings.record_text(p)}
             for p in passages],
            lang=lang,
        )
        logger.info(f"Citation check: {checked.summary()}")

        citations_payload = [
            {
                "source": embeddings.record_source(p),
                "kind": embeddings.record_kind(p),
                "excerpt": embeddings.record_text(p)[:240],
                "relevance": round(p.get("relevance", 0), 4),
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
