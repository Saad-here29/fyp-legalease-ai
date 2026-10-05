"""Case management request/response schemas."""

import uuid
from datetime import date, datetime

from pydantic import EmailStr, Field

from app.models.enums import CaseStatus, CaseType
from app.schemas.common import APIModel


class CaseCreate(APIModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    case_type: CaseType
    court_code: str | None = Field(default=None, max_length=60)
    filing_date: date | None = None
    case_number: str | None = Field(default=None, max_length=64)
    petitioner: str | None = Field(default=None, max_length=200)
    respondent: str | None = Field(default=None, max_length=200)
    next_hearing_date: date | None = None
    # Either client_id (existing user) OR client_email (lookup by email).
    # If client_email points to a registered CLIENT, they auto-see this case.
    client_id: uuid.UUID | None = None
    client_email: EmailStr | None = None


class CaseDetailsUpdate(APIModel):
    """PATCH /cases/{id}: only the fields sent are changed; send null to clear one."""
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    court_code: str | None = Field(default=None, max_length=60)
    filing_date: date | None = None
    case_number: str | None = Field(default=None, max_length=64)
    petitioner: str | None = Field(default=None, max_length=200)
    respondent: str | None = Field(default=None, max_length=200)
    next_hearing_date: date | None = None


class CaseStatusUpdate(APIModel):
    status: CaseStatus


class CaseAssignClientByEmail(APIModel):
    client_email: EmailStr


class CaseRead(APIModel):
    id: uuid.UUID
    title: str
    description: str | None
    case_type: CaseType
    status: CaseStatus
    court_code: str | None
    filing_date: date | None
    case_number: str | None = None
    petitioner: str | None = None
    respondent: str | None = None
    next_hearing_date: date | None = None
    assigned_lawyer_id: uuid.UUID | None
    client_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CaseTimelineEntry(APIModel):
    timestamp: datetime
    kind: str  # CREATED / STATUS / CLIENT_ASSIGNED / DOCUMENT / NOTE / HEARING / DETAILS
    title: str
    description: str | None = None
    actor_name: str | None = None


class CaseDetail(CaseRead):
    """Single-case view with denormalised lawyer + client + counts."""

    lawyer_name: str | None = None
    lawyer_email: EmailStr | None = None
    client_name: str | None = None
    client_email: EmailStr | None = None
    document_count: int = 0
