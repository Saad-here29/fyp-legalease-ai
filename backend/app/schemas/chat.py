"""AI Chat Assistant request/response schemas."""

import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import SenderType
from app.schemas.common import APIModel


class Citation(APIModel):
    source: str
    title: str
    excerpt: str | None = None


class ChatAskRequest(APIModel):
    """Single ask — creates a session if session_id is omitted."""

    session_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=4000)
    language_hint: str | None = Field(default=None, max_length=10)


class ChatMessageRead(APIModel):
    id: uuid.UUID
    sender_type: SenderType
    content: str
    citations: list[dict] | None
    response_time_ms: int | None = None
    created_at: datetime


class ChatAskResponse(APIModel):
    session_id: uuid.UUID
    user_message: ChatMessageRead
    ai_message: ChatMessageRead
    citations: list[Citation]


class ChatSessionRead(APIModel):
    id: uuid.UUID
    title: str | None
    summary: str | None
    total_messages: int
    started_at: datetime
    updated_at: datetime
