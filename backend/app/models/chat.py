"""Chat session + message tables for the AI Legal Chat Assistant.

Reconstructed from services/legal_chat_service.py, services/chat_service.py
(dead code, but shares these tables) and schemas/chat.py.

Deliberately does NOT use TimestampMixin: `ChatSessionRead.started_at` and
`docs/database-schema.md` both name the session's creation-time column
`started_at` (with a paired `ended_at`, unused by any code path today), which
diverges from the generic `created_at` convention used elsewhere. ChatMessage
rows are immutable (never updated after creation), so it only gets
`created_at`, no `updated_at` — same reasoning as ActivityLog.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSONBType, UUIDType
from app.models.enums import SenderType, values_callable


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("cases.id"), nullable=True
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Declared in ChatSessionRead but never written by any service today —
    # kept nullable with no writer until a session-summarisation feature exists.
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_hint: Mapped[str | None] = mapped_column(String(10), nullable=True)
    total_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # In docs/database-schema.md but no "end session" flow exists in code yet.
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("chat_sessions.id"), nullable=False
    )
    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType, name="sender_type", values_callable=values_callable), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Shape varies by call site ({source,title,excerpt} vs {source,kind,excerpt,
    # relevance}) — kept as a generic nullable JSON blob, not a fixed schema.
    citations: Mapped[list | None] = mapped_column(JSONBType, nullable=True)
    # Only ever set on AI-authored messages (including 0 for refusals); never
    # set on user messages.
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
