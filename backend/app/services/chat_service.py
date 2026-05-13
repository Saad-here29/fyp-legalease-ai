"""AI Legal Chat service — RAG over Pakistani legal corpus.

Pipeline (Final Report § 4 / Algorithm 5):
    1. Detect language of user message
    2. Embed the query, retrieve top-K relevant passages from FAISS
    3. Build a context-grounded system prompt with passages
    4. Call OpenAI Chat Completions
    5. Persist user + AI messages with citations
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.ai.client import SYSTEM_PROMPT_LEGAL_CHAT, get_ai_client
from app.core.config import settings
from app.core.exceptions import NotAuthorized, NotFound
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import SenderType
from app.models.user import User
from app.schemas.chat import Citation


def _detect_language(text: str) -> str:
    """Return 'ur' for Urdu, 'en' otherwise. Cheap and good enough for citations."""
    try:
        from langdetect import detect
        code = detect(text)
        return "ur" if code == "ur" else "en"
    except Exception:  # noqa: BLE001
        return "en"


class ChatService:
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

    # ----- Ask -----------------------------------------------------------

    def ask(
        self,
        user: User,
        message: str,
        session_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
        language_hint: str | None = None,
    ) -> tuple[ChatSession, ChatMessage, ChatMessage, list[Citation]]:
        # Resolve or create session
        if session_id is not None:
            session = self.get_session(session_id, user)
        else:
            session = ChatSession(
                user_id=user.id,
                case_id=case_id,
                title=message[:80],
                language_hint=language_hint or _detect_language(message),
                total_messages=0,
            )
            self.db.add(session)
            self.db.flush()

        lang = language_hint or session.language_hint or _detect_language(message)

        # 1. Persist user message
        user_msg = ChatMessage(
            session_id=session.id,
            sender_type=SenderType.USER,
            content=message,
            detected_language=lang,
        )
        self.db.add(user_msg)
        self.db.flush()

        # 2. Retrieve context from legal corpus
        embeddings.build_or_load(self.db)
        retrieved = embeddings.search(message, top_k=settings.RAG_TOP_K)
        passages = [
            r for r in retrieved
            if r.get("relevance", 0) >= settings.RAG_SIMILARITY_THRESHOLD
        ]
        citations = [
            Citation(
                source=p.get("section_number") or p["title"],
                title=p["title"],
                excerpt=(p.get("content") or "")[:240],
            )
            for p in passages
        ]

        # 3. Build grounded prompt
        context_block = ""
        if passages:
            ctx = "\n\n".join(
                f"[{i + 1}] {p['title']} — {p.get('section_number') or ''}\n{p['content']}"
                for i, p in enumerate(passages)
            )
            context_block = (
                "\n\n--- Relevant Pakistani legal authorities ---\n"
                f"{ctx}\n--- End authorities ---\n\n"
                "Use the authorities above where relevant and cite them inline like [1], [2]."
            )

        # 4. Build chat history (last 10 turns) + this question
        prior = (
            self.db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session.id,
                ChatMessage.id != user_msg.id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
            .all()
        )
        prior.reverse()
        history = [
            {
                "role": "assistant" if m.sender_type == SenderType.AI else "user",
                "content": m.content,
            }
            for m in prior
        ]
        history.append({"role": "user", "content": message})

        system_prompt = SYSTEM_PROMPT_LEGAL_CHAT + context_block

        # 5. Call AI
        t0 = time.perf_counter()
        ai_text = self.ai.chat(history, system=system_prompt)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        ai_msg = ChatMessage(
            session_id=session.id,
            sender_type=SenderType.AI,
            content=ai_text,
            citations=[c.model_dump() for c in citations] if citations else None,
            response_time_ms=elapsed_ms,
            detected_language=lang,
        )
        self.db.add(ai_msg)

        session.total_messages = (session.total_messages or 0) + 2
        self.db.commit()
        self.db.refresh(session)
        self.db.refresh(user_msg)
        self.db.refresh(ai_msg)
        return session, user_msg, ai_msg, citations
