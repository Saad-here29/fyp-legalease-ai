"""Case management router — /cases/* endpoints.

Implements UC-02 (Create New Case), UC-03 (Assign Client to Case), the
case lifecycle state machine from FR-CM06, the case timeline view, and
research-result-to-case attachment.
"""

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.models.document import Document
from app.schemas.cases import (
    CaseAssignClientByEmail,
    CaseCreate,
    CaseDetail,
    CaseRead,
    CaseStatusUpdate,
    CaseTimelineEntry,
)
from app.schemas.documents import DocumentRead
from app.services.case_service import CaseService

router = APIRouter()


class AssignClientByIdRequest(BaseModel):
    client_id: uuid.UUID


class SaveResearchRequest(BaseModel):
    title: str
    citation: str | None = None
    excerpt: str | None = None
    source_id: str | None = None


@router.get("", response_model=list[CaseRead], summary="List cases visible to me")
def list_cases(user: CurrentUser, db: Session = Depends(get_db)):
    return CaseService(db).list_for_user(user)


@router.get("/stats", summary="My case stats — total / active / in-hearing / closed")
def case_stats(user: CurrentUser, db: Session = Depends(get_db)):
    return CaseService(db).stats_for_user(user)


@router.post(
    "",
    response_model=CaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new case (UC-02) — lawyers only. "
    "Provide client_email to auto-link an existing client.",
)
def create_case(
    payload: CaseCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return CaseService(db).create(payload, user)


@router.get(
    "/{case_id}",
    response_model=CaseDetail,
    summary="Fetch a single case with lawyer/client names and doc count",
)
def get_case(
    case_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return CaseService(db).detail(case_id, user)


@router.get(
    "/{case_id}/timeline",
    response_model=list[CaseTimelineEntry],
    summary="Activity timeline for a case — visible to lawyer and client",
)
def case_timeline(
    case_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return CaseService(db).timeline(case_id, user)


@router.get(
    "/{case_id}/documents",
    response_model=list[DocumentRead],
    summary="List documents attached to this case",
)
def case_documents(
    case_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    CaseService(db).get(case_id, user)  # access check
    docs = (
        db.query(Document)
        .filter(Document.case_id == case_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        DocumentRead(
            id=d.id,
            case_id=d.case_id,
            filename=d.file_name,
            document_type=d.document_type,
            file_type=d.file_type,
            size_bytes=d.file_size_bytes,
            extracted_text=d.extracted_text,
            summary=d.summary_text,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.post(
    "/{case_id}/assign-client",
    response_model=CaseRead,
    summary="Assign a registered client to a case by email (UC-03)",
)
def assign_client(
    case_id: uuid.UUID,
    payload: CaseAssignClientByEmail,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return CaseService(db).assign_client_by_email(
        case_id, payload.client_email, user
    )


@router.patch(
    "/{case_id}/status",
    response_model=CaseRead,
    summary="Transition a case to a new status (FR-CM06)",
)
def update_case_status(
    case_id: uuid.UUID,
    payload: CaseStatusUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return CaseService(db).update_status(case_id, payload.status, user)


@router.post(
    "/{case_id}/research",
    response_model=CaseTimelineEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Save a Legal Research result as a note on this case",
)
def save_research(
    case_id: uuid.UUID,
    payload: SaveResearchRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return CaseService(db).save_research_to_case(
        case_id=case_id,
        user=user,
        title=payload.title,
        citation=payload.citation,
        excerpt=payload.excerpt,
        source_id=payload.source_id,
    )
