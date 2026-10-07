"""AI Legal Chat router — /chat/* endpoints.

Implements UC-04 (Ask Legal Question via AI Chat). Backed by RAG over the
Pakistani legal corpus (FAISS + sentence-transformers + OpenAI).

Primary endpoint per Task 3 spec: POST /chat/message
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.schemas.chat import ChatMessageRead, ChatSessionRead
from app.services.legal_chat_service import LegalChatService

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    # The page's "Family law" switch: "auto" searches the family-law index
    # first for family questions; "off" never does.
    family: Literal["auto", "off"] = "auto"


class CitationRef(BaseModel):
    # Knowledge-base v2 passages add section, heading, source_url and doc_id;
    # they're passed through only when present, so v1 citations are unchanged.
    model_config = ConfigDict(extra="allow")

    n: int                      # matches the [n] marker in the answer
    source: str
    excerpt: str | None = None


class ChatMessageResponse(BaseModel):
    # With JUDGMENTS_V2 on, also "case_law": the judgment paragraphs given to
    # the model (doc_id, court, year, case_number, paragraph, excerpt,
    # relevance). Off: exactly as before.
    model_config = ConfigDict(extra="allow")

    response: str
    sources: list[str]          # distinct statute names, in citation order
    session_id: str
    citations: list[CitationRef] = []
    response_time_ms: int | None = None
    confidence: Literal["low", "normal"] | None = None   # None for refusals
    family_scope: bool = False   # passages came from the family-law index


class ChatOptions(BaseModel):
    family_index: bool          # the page shows its "Family law" switch only when on


@router.get("/options", response_model=ChatOptions, summary="Chat features switched on")
def chat_options(_user: CurrentUser):
    return ChatOptions(family_index=settings.FAMILY_INDEX)


@router.get(
    "/sessions",
    response_model=list[ChatSessionRead],
    summary="List my chat sessions",
)
def list_sessions(user: CurrentUser, db: Session = Depends(get_db)):
    return LegalChatService(db).list_sessions(user)


@router.get(
    "/sessions/{session_id}/history",
    response_model=list[ChatMessageRead],
    summary="Full message history for a chat session",
)
def session_history(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return LegalChatService(db).get_history(session_id, user)


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Ask the AI legal assistant (UC-04) — RAG-grounded, "
    "Pakistani-law-only scope",
)
def send_message(
    payload: ChatMessageRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return LegalChatService(db).send(
        user=user,
        message=payload.message,
        session_id=payload.session_id,
        case_id=payload.case_id,
        family=payload.family,
    )

