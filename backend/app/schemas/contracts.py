"""Contract Drafting & Compliance request/response schemas."""

import uuid
from datetime import datetime

from pydantic import Field

from app.models.enums import ContractType
from app.schemas.common import APIModel


class ContractDraftRequest(APIModel):
    contract_type: ContractType
    fields: dict[str, str]
    case_id: uuid.UUID | None = None
    title: str | None = Field(default=None, max_length=200)


class ContractEditRequest(APIModel):
    """Edited contract text; saved as the next version."""
    content: str = Field(min_length=20, max_length=100_000)


class ContractCheckComplianceRequest(APIModel):
    # Defaults to the latest version when omitted.
    version_number: int | None = None


class ContractVersionRead(APIModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    version_number: int
    content: str
    compliance_result: dict | None
    created_at: datetime


class ContractRead(APIModel):
    id: uuid.UUID
    case_id: uuid.UUID | None
    contract_type: ContractType
    title: str | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ContractDetail(ContractRead):
    fields: dict[str, str]
    latest_version: ContractVersionRead


class ComplianceClauseResult(APIModel):
    name: str
    passed: bool
    matched_snippet: str | None = None


class ComplianceCheckResponse(APIModel):
    contract_id: uuid.UUID
    version_number: int
    all_passed: bool
    results: list[ComplianceClauseResult]
    # None on results stored before this check existed.
    unfilled_placeholders: list[str] | None = None
    checked_at: datetime
