"""Contract Drafting & Compliance service.

Two distinct operations, deliberately kept separate:
    - draft(): the only step that touches the LLM. Builds the full contract
      text from a template + filled fields.
    - check_compliance(): pure deterministic keyword/section-presence
      matching against already-generated text. No AI client call — a
      required clause either has one of its keywords in the text or it
      doesn't.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai.client import get_ai_client
from app.ai.contract_templates import get_template
from app.core.exceptions import NotAuthorized, NotFound, ValidationFailed
from app.models.case import Case
from app.models.contract import Contract, ContractVersion
from app.models.enums import ContractType, UserRole
from app.models.user import User
from app.schemas.contracts import ContractDraftRequest

_SNIPPET_RADIUS = 60

_SYSTEM_PROMPT = (
    "You are a legal drafting assistant. Produce a complete, professional "
    "contract in plain prose (not a fill-in-the-blank template) based on the "
    "structure and party details given. Write out every section listed in "
    "the structure in full — do not leave placeholders, do not omit any "
    "listed section, and do not add commentary before or after the contract "
    "text. Use the exact party names, dates, and terms supplied."
)


class ContractService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ----- Draft -----------------------------------------------------------

    def draft(self, payload: ContractDraftRequest, user: User) -> Contract:
        if user.role != UserRole.LAWYER:
            raise NotAuthorized("Only lawyers can draft contracts.")

        template = get_template(payload.contract_type)
        required_keys = {f["key"] for f in template["required_fields"]}
        missing = sorted(required_keys - payload.fields.keys())
        if missing:
            raise ValidationFailed(
                message=f"Missing required field(s) for {template['label']}: {', '.join(missing)}.",
                hint=f"Required fields: {', '.join(sorted(required_keys))}.",
            )

        if payload.case_id is not None:
            # Reuses CaseService's own access check rather than duplicating
            # its RBAC logic here.
            from app.services.case_service import CaseService
            CaseService(self.db).get(payload.case_id, user)

        field_lines = "\n".join(f"- {k}: {v}" for k, v in payload.fields.items())
        clause_names = ", ".join(c["name"] for c in template["required_clauses"])
        prompt = (
            f"Draft a {template['label']}.\n\n"
            f"Structure to follow:\n{template['template_structure']}\n\n"
            f"Party/term details:\n{field_lines}\n\n"
            f"This contract MUST include each of these clauses: {clause_names}."
        )

        ai = get_ai_client()
        content = ai.chat([{"role": "user", "content": prompt}], system=_SYSTEM_PROMPT)

        contract = Contract(
            case_id=payload.case_id,
            created_by_id=user.id,
            contract_type=payload.contract_type,
            title=payload.title or template["label"],
            fields=payload.fields,
        )
        self.db.add(contract)
        self.db.flush()

        version = ContractVersion(
            contract_id=contract.id,
            version_number=1,
            content=content,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    # ----- Compliance --------------------------------------------------

    def check_compliance(
        self, contract_id: uuid.UUID, user: User, version_number: int | None = None
    ) -> ContractVersion:
        contract = self._get_for_action(contract_id, user)
        version = self._get_version(contract, version_number)

        template = get_template(contract.contract_type)
        text_lower = version.content.lower()

        results = []
        for clause in template["required_clauses"]:
            match = None
            for keyword in clause["keywords"]:
                idx = text_lower.find(keyword.lower())
                if idx != -1:
                    start = max(0, idx - _SNIPPET_RADIUS)
                    end = min(len(version.content), idx + len(keyword) + _SNIPPET_RADIUS)
                    match = version.content[start:end].strip()
                    break
            results.append(
                {"name": clause["name"], "passed": match is not None, "matched_snippet": match}
            )

        version.compliance_result = {
            "all_passed": all(r["passed"] for r in results),
            "results": results,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        self.db.commit()
        self.db.refresh(version)
        return version

    # ----- Read --------------------------------------------------------

    def get(self, contract_id: uuid.UUID, user: User) -> Contract:
        contract = self.db.get(Contract, contract_id)
        if contract is None:
            raise NotFound("Contract not found.")
        self._assert_can_view(contract, user)
        return contract

    def list_versions(self, contract_id: uuid.UUID, user: User) -> list[ContractVersion]:
        contract = self.get(contract_id, user)
        return list(contract.versions)

    def list_for_user(self, user: User) -> list[Contract]:
        if user.role == UserRole.LAWYER:
            return list(
                self.db.query(Contract)
                .filter(Contract.created_by_id == user.id)
                .order_by(Contract.updated_at.desc())
                .all()
            )
        if user.role == UserRole.CLIENT:
            return list(
                self.db.query(Contract)
                .join(Case, Case.id == Contract.case_id)
                .filter(Case.client_id == user.id)
                .order_by(Contract.updated_at.desc())
                .all()
            )
        return []

    # ----- Internal ------------------------------------------------------

    def _get_version(self, contract: Contract, version_number: int | None) -> ContractVersion:
        if version_number is None:
            if not contract.versions:
                raise NotFound("This contract has no versions yet.")
            return contract.versions[-1]
        for v in contract.versions:
            if v.version_number == version_number:
                return v
        raise NotFound(f"Contract has no version {version_number}.")

    def _get_for_action(self, contract_id: uuid.UUID, user: User) -> Contract:
        """Access check for actions (check-compliance), stricter than plain
        viewing: the acting user must be a lawyer with a real stake in the
        contract (its creator, or the assigned lawyer on its linked case)."""
        contract = self.db.get(Contract, contract_id)
        if contract is None:
            raise NotFound("Contract not found.")
        if user.role != UserRole.LAWYER:
            raise NotAuthorized("Only a lawyer can run a compliance check.")
        if contract.created_by_id == user.id:
            return contract
        if contract.case_id is not None:
            case = self.db.get(Case, contract.case_id)
            if case is not None and case.assigned_lawyer_id == user.id:
                return contract
        raise NotAuthorized("You do not have access to this contract.")

    def _assert_can_view(self, contract: Contract, user: User) -> None:
        if contract.created_by_id == user.id:
            return
        if contract.case_id is not None:
            case = self.db.get(Case, contract.case_id)
            if case is not None:
                if user.role == UserRole.LAWYER and case.assigned_lawyer_id == user.id:
                    return
                if user.role == UserRole.CLIENT and case.client_id == user.id:
                    return
        raise NotAuthorized("You do not have access to this contract.")
