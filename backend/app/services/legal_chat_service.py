"""LegalEase AI Chat — Pakistani-law-scoped RAG assistant (Task 3 spec).

Pipeline (Final Report Algorithm 5):
    1. Embed the user query with the same multilingual model used to
       build the FAISS index.
    2. Retrieve top RAG_TOP_K=5 chunks.
    3. Filter by similarity >= RAG_SIMILARITY_THRESHOLD=0.7.
    4. If NO chunks pass the threshold, return the out-of-scope refusal
       — we do NOT let the LLM answer un-grounded questions, that's the
       whole point of a RAG system.
    5. Otherwise build a system + context + history + user prompt and
       call OpenAI chat completions.
    6. Persist user + AI messages to chat_sessions / chat_messages with
       the list of source names cited.
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.ai.client import get_ai_client
from app.ai.query_rewrite import rewrite_for_search
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailable, NotAuthorized, NotFound
from app.core.logging import logger
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import SenderType
from app.models.user import User


# Per Task 3 spec — strict scope filter. Outside of Pakistani law the bot
# must refuse, not hallucinate.
SYSTEM_PROMPT = (
    "You are LegalEase AI, a specialized legal assistant for Pakistani law. "
    "You ONLY answer questions about Pakistani statutes, court procedures, "
    "legal rights, and matters under Pakistani jurisdiction. You have access "
    "to the Pakistan Penal Code, Code of Criminal Procedure, Family Courts "
    "Act, Muslim Family Laws Ordinance, Zainab Alert Act, and Supreme Court "
    "of Pakistan judgments. If asked anything outside Pakistani law "
    "(cooking, sports, general knowledge, foreign law etc.), politely refuse "
    "and redirect to legal topics. Always cite the specific law or case you "
    "are referencing. Answer in the same language the user writes in "
    "(English or Urdu)."
)

OUT_OF_SCOPE_REFUSAL = (
    "I can only answer questions about Pakistani law and legal matters. "
    "This question appears to be outside my scope. Please ask about "
    "Pakistani statutes, court procedures, or legal matters."
)


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
        """
        # 1) Resolve / create the session up front so we have an id for both
        #    in-scope and refusal responses.
        if session_id is not None:
            session = self.get_session(session_id, user)
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

        lang = session.language_hint or _detect_language(message)

        # Persist the user message regardless of scope outcome — we want a
        # full audit of what was asked.
        user_msg = ChatMessage(
            session_id=session.id,
            sender_type=SenderType.USER,
            content=message,
            detected_language=lang,
        )
        self.db.add(user_msg)
        self.db.flush()

        # 2) Retrieval
        index_size = embeddings.build_or_load(self.db)
        if index_size == 0:
            logger.warning("Chat called but FAISS index is empty.")
            return self._refuse(
                session,
                lang,
                "The legal knowledge base is still being built. Please try again in a few minutes.",
            )

        search_query = rewrite_for_search(message)
        retrieved = embeddings.search(search_query, top_k=settings.RAG_TOP_K)
        passages = [
            r for r in retrieved
            if r.get("relevance", 0) >= settings.RAG_SIMILARITY_THRESHOLD
        ]

        # 3) Out-of-scope refusal — no LLM call, no hallucination risk
        if not passages:
            logger.info(
                f"Chat refusal — no chunks above {settings.RAG_SIMILARITY_THRESHOLD} threshold"
            )
            return self._refuse(session, lang, OUT_OF_SCOPE_REFUSAL)

        # 4) Build the prompt: system + context + history + user
        context_block = "\n\n".join(
            f"[{i + 1}] Source: {embeddings.record_source(p)}\n"
            f"{embeddings.record_text(p)}"
            for i, p in enumerate(passages)
        )

        history = self._recent_history(session.id, exclude=user_msg.id, limit=10)
        history.append({"role": "user", "content": message})

        system = (
            f"{SYSTEM_PROMPT}\n\n"
            "--- Relevant Pakistani legal authorities (cite by [n]) ---\n"
            f"{context_block}\n"
            "--- End authorities ---"
        )

        # 5) Call OpenAI
        t0 = time.perf_counter()
        try:
            ai_text = self.ai.chat(history, system=system)
        except AIServiceUnavailable:
            # Re-raise so the router returns a 503 with the hint, no AI
            # message persisted.
            raise
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        # 6) Persist AI message with citations
        source_names = self._unique_sources(passages)
        citations_payload = [
            {
                "source": embeddings.record_source(p),
                "kind": embeddings.record_kind(p),
                "excerpt": embeddings.record_text(p)[:240],
                "relevance": round(p.get("relevance", 0), 4),
            }
            for p in passages
        ]
        ai_msg = ChatMessage(
            session_id=session.id,
            sender_type=SenderType.AI,
            content=ai_text,
            citations=citations_payload,
            response_time_ms=elapsed_ms,
            detected_language=lang,
        )
        self.db.add(ai_msg)
        session.total_messages = (session.total_messages or 0) + 2
        self.db.commit()
        self.db.refresh(session)

        return {
            "response": ai_text,
            "sources": source_names,
            "session_id": str(session.id),
        }

    # ----- Internal ------------------------------------------------------

    def _refuse(self, session: ChatSession, lang: str, message: str) -> dict:
        ai_msg = ChatMessage(
            session_id=session.id,
            sender_type=SenderType.AI,
            content=message,
            citations=None,
            response_time_ms=0,
            detected_language=lang,
        )
        self.db.add(ai_msg)
        session.total_messages = (session.total_messages or 0) + 2
        self.db.commit()
        return {
            "response": message,
            "sources": [],
            "session_id": str(session.id),
        }

    def _recent_history(
        self, session_id: uuid.UUID, *, exclude: uuid.UUID, limit: int
    ) -> list[dict]:
        rows = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id,
                ChatMessage.id != exclude,
            )
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
