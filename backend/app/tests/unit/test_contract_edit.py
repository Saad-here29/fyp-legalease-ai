"""Contract editing: an edit is saved as the next version (earlier versions
kept) and the compliance and placeholder checks re-run on it. Only a lawyer
who created the contract, or the assigned lawyer on its case, can edit.
Deterministic: no model calls."""

import pytest

from app.core.exceptions import NotAuthorized, ValidationFailed
from app.core.security import create_access_token, hash_password
from app.models.case import Case
from app.models.contract import Contract, ContractVersion
from app.models.enums import CaseStatus, CaseType, ContractType, UserRole
from app.models.user import User
from app.services.contract_service import ContractService

FULL = ("This Agreement protects all Confidential Information. The term of this agreement is three years. "
        "It is governed by the laws of Pakistan. The parties may seek injunctive relief.")
NO_CONFIDENTIALITY = ("The term of this agreement is three years. It is governed by the laws of Pakistan. "
                      "The parties may seek injunctive relief.")


def _user(db, email, role):
    u = User(email=email, password_hash=hash_password("x"), full_name=email.split("@")[0], role=role,
             is_active=True, is_verified=True)
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def setup(db_session):
    people = {r: _user(db_session, f"{r}@gmail.com", role) for r, role in [
        ("drafter", UserRole.LAWYER), ("assigned", UserRole.LAWYER), ("other", UserRole.LAWYER),
        ("client", UserRole.CLIENT), ("student", UserRole.STUDENT)]}
    case = Case(title="Supply dispute", case_type=CaseType.COMMERCIAL, status=CaseStatus.ASSIGNED,
                assigned_lawyer_id=people["assigned"].id, client_id=people["client"].id)
    db_session.add(case)
    db_session.flush()
    c = Contract(created_by_id=people["drafter"].id, case_id=case.id, contract_type=ContractType.NDA,
                 title="NDA", fields={})
    db_session.add(c)
    db_session.flush()
    db_session.add(ContractVersion(contract_id=c.id, version_number=1, content=FULL))
    db_session.commit()
    return people, c


def test_edit_creates_next_version_and_keeps_history(db_session, setup):
    people, c = setup
    v2 = ContractService(db_session).edit(c.id, FULL + " Notices go to Lahore.", people["drafter"])
    assert v2.version_number == 2
    versions = ContractService(db_session).list_versions(c.id, people["drafter"])
    assert [v.version_number for v in versions] == [1, 2]
    assert versions[0].content == FULL  # version 1 untouched
    assert versions[1].content.endswith("Notices go to Lahore.")


def test_checks_rerun_on_the_new_version(db_session, setup):
    """MT-CON-04: remove the confidentiality clause and the check fails it."""
    people, c = setup
    v2 = ContractService(db_session).edit(c.id, NO_CONFIDENTIALITY, people["drafter"])
    r = v2.compliance_result
    assert r is not None and r["all_passed"] is False
    failed = [x["name"] for x in r["results"] if not x["passed"]]
    assert failed == ["Confidentiality clause"]


def test_placeholders_are_flagged_on_the_edit(db_session, setup):
    people, c = setup
    v2 = ContractService(db_session).edit(c.id, FULL + " Signed at [address] on [date].", people["drafter"])
    assert v2.compliance_result["unfilled_placeholders"] == ["[address]", "[date]"]
    assert v2.compliance_result["all_passed"] is False


def test_a_complete_edit_passes(db_session, setup):
    people, c = setup
    v2 = ContractService(db_session).edit(c.id, FULL + " Each party signs below.", people["drafter"])
    assert v2.compliance_result["all_passed"] is True


def test_assigned_lawyer_on_the_case_can_edit(db_session, setup):
    people, c = setup
    assert ContractService(db_session).edit(c.id, FULL + " Amended.", people["assigned"]).version_number == 2


@pytest.mark.parametrize("who", ["client", "student", "other"])
def test_others_cannot_edit(db_session, setup, who):
    people, c = setup
    with pytest.raises(NotAuthorized):
        ContractService(db_session).edit(c.id, FULL + " X", people[who])
    assert len(ContractService(db_session).list_versions(c.id, people["drafter"])) == 1


def test_unchanged_text_is_refused(db_session, setup):
    people, c = setup
    with pytest.raises(ValidationFailed):
        ContractService(db_session).edit(c.id, "  " + FULL + "\n", people["drafter"])


def test_edit_over_http(client, db_session, setup):
    people, c = setup
    tok = create_access_token(people["drafter"].id, "lawyer", people["drafter"].token_version)
    r = client.post(f"/api/v1/contracts/{c.id}/versions", json={"content": NO_CONFIDENTIALITY},
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 201, r.text
    assert r.json()["version_number"] == 2 and r.json()["compliance_result"]["all_passed"] is False
    ctok = create_access_token(people["client"].id, "client", people["client"].token_version)
    r = client.post(f"/api/v1/contracts/{c.id}/versions", json={"content": FULL + " Y"},
                    headers={"Authorization": f"Bearer {ctok}"})
    assert r.status_code == 403
    r = client.post(f"/api/v1/contracts/{c.id}/versions", json={"content": "short"},
                    headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 422
