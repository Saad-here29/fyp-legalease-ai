"""AI Legal Chat router — /chat/* endpoints.

Implements UC-04 (Ask Legal Question via AI Chat). Backed by RAG over the
Pakistani legal corpus (FAISS + sentence-transformers + OpenAI).

Primary endpoint per Task 3 spec: POST /chat/message
"""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.schemas.chat import ChatMessageRead, ChatSessionRead
from app.services.legal_chat_service import LegalChatService

router = APIRouter()


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None


class CitationRef(BaseModel):
    n: int                      # matches the [n] marker in the answer
    source: str
    excerpt: str | None = None


class ChatMessageResponse(BaseModel):
    response: str
    sources: list[str]          # distinct statute names, in citation order
    session_id: str
    citations: list[CitationRef] = []
    response_time_ms: int | None = None


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
    )


# Backward-compatible alias for the original /chat/ask endpoint
@router.post(
    "/ask",
    response_model=ChatMessageResponse,
    summary="Alias of /chat/message",
)
def ask(
    payload: ChatMessageRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return LegalChatService(db).send(
        user=user,
        message=payload.message,
        session_id=payload.session_id,
        case_id=payload.case_id,
    )
