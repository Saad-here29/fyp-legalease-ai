"""General case types and the case fields added in migration e7b3c9d14a02:
case number, petitioner, respondent, next hearing date (plus the existing
court and summary). Role rules and the timeline entries for edits."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.core.exceptions import IllegalStateTransition, NotAuthorized, ValidationFailed
from app.core.security import hash_password
from app.models.audit import ActivityLog
from app.models.enums import CaseStatus, CaseType, UserRole
from app.models.user import User
from app.schemas.cases import CaseCreate, CaseDetailsUpdate, CaseRead
from app.services.case_service import CaseService


def _user(db, email, role):
    u = User(email=email, password_hash=hash_password("x"), full_name=email.split("@")[0],
             role=role, is_active=True, is_verified=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def people(db_session):
    return {
        "lawyer": _user(db_session, "counsel@gmail.com", UserRole.LAWYER),
        "other": _user(db_session, "other@gmail.com", UserRole.LAWYER),
        "client": _user(db_session, "client@gmail.com", UserRole.CLIENT),
    }


def _case(db, lawyer, **kw):
    data = {"title": "State v. Khan", "case_type": CaseType.CRIMINAL, **kw}
    return CaseService(db).create(CaseCreate(**data), lawyer)


def test_case_types_cover_family_and_general():
    assert {t.value for t in CaseType} == {
        "custody", "inheritance", "divorce", "maintenance",
        "civil", "criminal", "commercial", "property", "service"}


@pytest.mark.parametrize("ctype", ["civil", "criminal", "commercial", "property", "service", "divorce"])
def test_create_with_each_type(db_session, people, ctype):
    case = _case(db_session, people["lawyer"], case_type=CaseType(ctype))
    assert case.case_type.value == ctype


def test_create_with_all_fields(db_session, people):
    hearing = date.today() + timedelta(days=10)
    case = _case(db_session, people["lawyer"], case_number="Crl.P. 187-P/2026", court_code="Supreme Court",
                 petitioner="Nadar Khan", respondent="The State", next_hearing_date=hearing,
                 description="Bail on medical grounds")
    read = CaseRead.model_validate(case)
    assert (read.case_number, read.petitioner, read.respondent, read.next_hearing_date) == (
        "Crl.P. 187-P/2026", "Nadar Khan", "The State", hearing)
    tl = CaseService(db_session).timeline(case.id, people["lawyer"])
    assert any(e.kind == "HEARING" and str(hearing) in e.title for e in tl)


def test_fields_are_optional(db_session, people):
    case = _case(db_session, people["lawyer"])
    assert case.case_number is None and case.next_hearing_date is None
    assert not [e for e in CaseService(db_session).timeline(case.id, people["lawyer"]) if e.kind == "HEARING"]


def test_hearing_change_is_on_the_timeline(db_session, people):
    svc = CaseService(db_session)
    case = _case(db_session, people["lawyer"])
    d1, d2 = date.today() + timedelta(days=3), date.today() + timedelta(days=30)
    svc.update_details(case.id, CaseDetailsUpdate(next_hearing_date=d1), people["lawyer"])
    svc.update_details(case.id, CaseDetailsUpdate(next_hearing_date=d2), people["lawyer"])
    hearings = [e for e in svc.timeline(case.id, people["lawyer"]) if e.kind == "HEARING"]
    assert [e.title for e in hearings] == [f"Next hearing: {d1}", f"Next hearing: {d2}"]
    assert hearings[1].description == f"Was {d1}"


def test_other_details_logged_once(db_session, people):
    svc = CaseService(db_session)
    case = _case(db_session, people["lawyer"])
    svc.update_details(case.id, CaseDetailsUpdate(case_number="W.P. 12/2026", court_code="Lahore High Court"),
                       people["lawyer"])
    svc.update_details(case.id, CaseDetailsUpdate(case_number="W.P. 12/2026"), people["lawyer"])  # no change
    logs = db_session.query(ActivityLog).filter(ActivityLog.action == "CASE_DETAILS_UPDATED").all()
    assert len(logs) == 1 and logs[0].new_values == {"court_code": "Lahore High Court", "case_number": "W.P. 12/2026"}
    details = [e for e in svc.timeline(case.id, people["lawyer"]) if e.kind == "DETAILS"]
    assert details and "court" in details[0].description and "case number" in details[0].description


def test_null_clears_a_field(db_session, people):
    svc = CaseService(db_session)
    case = _case(db_session, people["lawyer"], petitioner="A")
    svc.update_details(case.id, CaseDetailsUpdate(petitioner=None), people["lawyer"])
    assert case.petitioner is None


def test_title_cannot_be_cleared(db_session, people):
    case = _case(db_session, people["lawyer"])
    with pytest.raises(ValidationFailed):
        CaseService(db_session).update_details(case.id, CaseDetailsUpdate(title=None), people["lawyer"])
    with pytest.raises(ValidationError):
        CaseDetailsUpdate(title="ab")


def test_client_and_other_lawyer_cannot_edit(db_session, people):
    svc = CaseService(db_session)
    case = _case(db_session, people["lawyer"], client_email="client@gmail.com")
    with pytest.raises(NotAuthorized):
        svc.update_details(case.id, CaseDetailsUpdate(case_number="X"), people["client"])
    with pytest.raises(NotAuthorized):
        svc.update_details(case.id, CaseDetailsUpdate(case_number="X"), people["other"])
    # The client still reads every field.
    assert CaseRead.model_validate(svc.get(case.id, people["client"])).case_number is None


def test_closed_case_cannot_be_edited(db_session, people):
    svc = CaseService(db_session)
    case = _case(db_session, people["lawyer"])
    svc.update_status(case.id, CaseStatus.CLOSED, people["lawyer"])
    with pytest.raises(IllegalStateTransition):
        svc.update_details(case.id, CaseDetailsUpdate(case_number="X"), people["lawyer"])


def test_stats_list_upcoming_hearings(db_session, people):
    svc = CaseService(db_session)
    soon, later, past = (date.today() + timedelta(days=2), date.today() + timedelta(days=20),
                         date.today() - timedelta(days=1))
    _case(db_session, people["lawyer"], title="Later case", next_hearing_date=later)
    _case(db_session, people["lawyer"], title="Soon case", next_hearing_date=soon, case_number="C-1")
    _case(db_session, people["lawyer"], title="Past case", next_hearing_date=past)
    hearings = svc.stats_for_user(people["lawyer"])["upcoming_hearings"]
    assert [h["title"] for h in hearings] == ["Soon case", "Later case"]
    assert hearings[0]["case_number"] == "C-1"


def test_patch_over_http(client, db_session, people):
    from app.core.security import create_access_token
    case = _case(db_session, people["lawyer"])
    tok = create_access_token(people["lawyer"].id, "lawyer", people["lawyer"].token_version)
    r = client.patch(f"/api/v1/cases/{case.id}", json={"next_hearing_date": "2026-12-01", "respondent": "The State"},
                     headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200, r.text
    assert r.json()["next_hearing_date"] == "2026-12-01" and r.json()["respondent"] == "The State"
    ctok = create_access_token(people["client"].id, "client", people["client"].token_version)
    r = client.patch(f"/api/v1/cases/{case.id}", json={"respondent": "X"}, headers={"Authorization": f"Bearer {ctok}"})
    assert r.status_code in (403, 404)


def test_detail_includes_every_case_field(db_session, people):
    """Regression: detail() listed fields by hand and dropped the new ones."""
    from app.schemas.cases import CaseRead as _Read
    case = _case(db_session, people["lawyer"], case_number="C.S. 41/2026", petitioner="A", respondent="B",
                 next_hearing_date=date.today() + timedelta(days=5), client_email="client@gmail.com")
    for viewer in (people["lawyer"], people["client"]):
        d = CaseService(db_session).detail(case.id, viewer).model_dump()
        assert all(d[f] == getattr(_Read.model_validate(case), f) for f in _Read.model_fields)
        assert d["case_number"] == "C.S. 41/2026" and d["client_email"] == "client@gmail.com"
