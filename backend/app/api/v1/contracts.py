"""Contract Drafting & Compliance router — /contracts/* endpoints."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.models.contract import Contract
from app.schemas.contracts import (
    ComplianceCheckResponse,
    ContractCheckComplianceRequest,
    ContractDetail,
    ContractDraftRequest,
    ContractRead,
    ContractVersionRead,
)
from app.services.contract_service import ContractService

router = APIRouter()


def _to_detail(contract: Contract) -> ContractDetail:
    latest = contract.versions[-1]
    return ContractDetail(
        id=contract.id,
        case_id=contract.case_id,
        contract_type=contract.contract_type,
        title=contract.title,
        created_by_id=contract.created_by_id,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        fields=contract.fields,
        latest_version=ContractVersionRead.model_validate(latest),
    )


@router.get("", response_model=list[ContractRead], summary="List contracts visible to me")
def list_contracts(user: CurrentUser, db: Session = Depends(get_db)):
    return ContractService(db).list_for_user(user)


@router.post(
    "/draft",
    response_model=ContractDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Draft a new contract from a template + filled fields — lawyers only",
)
def draft_contract(
    payload: ContractDraftRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    contract = ContractService(db).draft(payload, user)
    return _to_detail(contract)


@router.get(
    "/{contract_id}",
    response_model=ContractDetail,
    summary="Fetch a contract with its latest version",
)
def get_contract(
    contract_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    contract = ContractService(db).get(contract_id, user)
    return _to_detail(contract)


@router.get(
    "/{contract_id}/versions",
    response_model=list[ContractVersionRead],
    summary="Full version history for a contract",
)
def list_versions(
    contract_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    return ContractService(db).list_versions(contract_id, user)


@router.post(
    "/{contract_id}/check-compliance",
    response_model=ComplianceCheckResponse,
    summary="Run the required-clauses checklist against a version's text — deterministic, no LLM call",
)
def check_compliance(
    contract_id: uuid.UUID,
    user: CurrentUser,
    payload: ContractCheckComplianceRequest = ContractCheckComplianceRequest(),
    db: Session = Depends(get_db),
):
    version = ContractService(db).check_compliance(
        contract_id, user, payload.version_number
    )
    result = version.compliance_result
    return ComplianceCheckResponse(
        contract_id=version.contract_id,
        version_number=version.version_number,
        all_passed=result["all_passed"],
        results=result["results"],
        checked_at=result["checked_at"],
    )
