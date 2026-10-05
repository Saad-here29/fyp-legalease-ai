"""Unfilled placeholders in contract drafts. The Oct 2026 audit found
"[address]" and "[date]" left in generated drafts while the compliance
check passed them. Deterministic — no model calls."""

import pytest

from app.core.security import hash_password
from app.models.contract import Contract, ContractVersion
from app.models.enums import ContractType, UserRole
from app.models.user import User
from app.services.contract_service import ContractService
from app.utils.placeholders import find_unfilled_placeholders


@pytest.mark.parametrize("text, expected", [
    ("The Employee resides at [address] and signs on [date].", ["[address]", "[date]"]),
    ("Signed by [Name of Employer] at [address], again at [address].", ["[Name of Employer]", "[address]"]),
    ("Fee: PKR [ ] payable within [____] days, see [●].", ["[ ]", "[____]", "[●]"]),
    ("Dear {{client_name}}, the term is <<duration>>.", ["{{client_name}}", "<<duration>>"]),
])
def test_placeholders_are_found(text, expected):
    assert find_unfilled_placeholders(text) == expected


@pytest.mark.parametrize("text", [
    "See the [Contract Act](https://example.org/contract-act) for details.",
    "As held in the authorities [1] and [12], and under sub-clause [a] and [ii].",
    "Signature: ______________________   Date: ____________",
    "A complete clause with no brackets at all.",
])
def test_legitimate_text_is_not_flagged(text):
    assert find_unfilled_placeholders(text) == []


@pytest.fixture
def contract(db_session):
    lawyer = User(email="drafter@gmail.com", password_hash=hash_password("x"), full_name="Drafter",
                  role=UserRole.LAWYER, is_active=True, is_verified=True)
    db_session.add(lawyer)
    db_session.flush()
    c = Contract(created_by_id=lawyer.id, contract_type=ContractType.NDA, title="NDA", fields={})
    db_session.add(c)
    db_session.flush()
    db_session.add(ContractVersion(contract_id=c.id, version_number=1, content=""))
    db_session.commit()
    return lawyer, c


def _check(db_session, contract, text):
    lawyer, c = contract
    version = db_session.query(ContractVersion).filter_by(contract_id=c.id).one()
    version.content = text
    db_session.commit()
    return ContractService(db_session).check_compliance(c.id, lawyer).compliance_result


def _all_clauses_text():
    from app.ai.contract_templates import get_template
    return " ".join(cl["keywords"][0] for cl in get_template(ContractType.NDA)["required_clauses"])


def test_compliance_flags_placeholders_and_fails(db_session, contract):
    result = _check(db_session, contract, _all_clauses_text() + " Address: [address]. Dated [date].")
    assert all(r["passed"] for r in result["results"])  # every clause is there…
    assert result["unfilled_placeholders"] == ["[address]", "[date]"]
    assert result["all_passed"] is False  # …but the draft is not finished


def test_compliance_passes_a_filled_draft(db_session, contract):
    result = _check(db_session, contract, _all_clauses_text() + " Address: 12 Mall Road, Lahore.")
    assert result["unfilled_placeholders"] == []
    assert result["all_passed"] is True


# The compliance endpoint's body is optional: none means the latest version.
# (It used to default to a request model built once at import time, B008.)
@pytest.mark.parametrize("body", [None, {}, {"version_number": 1}])
def test_compliance_endpoint_body_is_optional(client, db_session, contract, body):
    lawyer, c = contract
    r = client.post("/api/v1/auth/login", json={"email": lawyer.email, "password": "x"})
    headers = {"Authorization": "Bearer " + r.json()["tokens"]["access_token"]}
    kwargs = {} if body is None else {"json": body}
    r = client.post(f"/api/v1/contracts/{c.id}/check-compliance", headers=headers, **kwargs)
    assert r.status_code == 200, r.text
    assert r.json()["version_number"] == 1
