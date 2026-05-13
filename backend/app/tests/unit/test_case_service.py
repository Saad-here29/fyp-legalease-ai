"""Unit tests for CaseService — covers UT-CASE-001..004 from Final Report
§ 4.3 Table 4.3. Exercises the case lifecycle state machine, RBAC, and
client-by-email assignment."""

import pytest

from app.core.exceptions import IllegalStateTransition, NotAuthorized
from app.core.security import hash_password
from app.models.enums import CaseStatus, CaseType, UserRole
from app.models.user import User
from app.schemas.cases import CaseCreate
from app.services.case_service import CaseService


@pytest.fixture
def lawyer(db_session):
    u = User(
        email="counsel@gmail.com",
        password_hash=hash_password("x"),
        full_name="Adv. Counsel",
        role=UserRole.LAWYER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def client_user(db_session):
    u = User(
        email="client@gmail.com",
        password_hash=hash_password("x"),
        full_name="Client Person",
        role=UserRole.CLIENT,
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


# ============================================================
# UT-CASE-001: lawyer can create a case
# ============================================================
def test_lawyer_creates_case_in_created_state(db_session, lawyer):
    svc = CaseService(db_session)
    case = svc.create(
        CaseCreate(
            title="Khan v. Khan — Custody",
            case_type=CaseType.CUSTODY,
            description="Test matter",
        ),
        lawyer,
    )

    assert case.title == "Khan v. Khan — Custody"
    assert case.assigned_lawyer_id == lawyer.id
    assert case.client_id is None
    # No client supplied → CREATED. With client → ASSIGNED.
    assert case.status == CaseStatus.CREATED


# ============================================================
# UT-CASE-002: lawyer creating case WITH client_email auto-promotes to ASSIGNED
# ============================================================
def test_create_with_client_email_auto_assigns(db_session, lawyer, client_user):
    svc = CaseService(db_session)
    case = svc.create(
        CaseCreate(
            title="Property Dispute",
            case_type=CaseType.INHERITANCE,
            client_email=client_user.email,
        ),
        lawyer,
    )

    assert case.client_id == client_user.id
    assert case.status == CaseStatus.ASSIGNED


# ============================================================
# UT-CASE-003: state machine enforces allowed transitions only
# ============================================================
def test_status_transitions_follow_state_machine(db_session, lawyer, client_user):
    svc = CaseService(db_session)
    case = svc.create(
        CaseCreate(
            title="Custody",
            case_type=CaseType.CUSTODY,
            client_email=client_user.email,
        ),
        lawyer,
    )

    # ASSIGNED → IN_PROGRESS allowed
    case = svc.update_status(case.id, CaseStatus.IN_PROGRESS, lawyer)
    assert case.status == CaseStatus.IN_PROGRESS

    # IN_PROGRESS → HEARING_SCHEDULED allowed
    case = svc.update_status(case.id, CaseStatus.HEARING_SCHEDULED, lawyer)
    assert case.status == CaseStatus.HEARING_SCHEDULED

    # HEARING_SCHEDULED → CLOSED allowed
    case = svc.update_status(case.id, CaseStatus.CLOSED, lawyer)
    assert case.status == CaseStatus.CLOSED

    # CLOSED is terminal — any further transition raises
    with pytest.raises(IllegalStateTransition):
        svc.update_status(case.id, CaseStatus.IN_PROGRESS, lawyer)


# ============================================================
# UT-CASE-004: RBAC — client cannot create cases
# ============================================================
def test_client_cannot_create_case(db_session, client_user):
    svc = CaseService(db_session)
    with pytest.raises(NotAuthorized):
        svc.create(
            CaseCreate(title="Self-filed", case_type=CaseType.DIVORCE),
            client_user,
        )


# ============================================================
# Client list_for_user only sees their own cases
# ============================================================
def test_client_only_sees_own_cases(db_session, lawyer, client_user):
    svc = CaseService(db_session)
    svc.create(
        CaseCreate(
            title="Their case",
            case_type=CaseType.MAINTENANCE,
            client_email=client_user.email,
        ),
        lawyer,
    )
    # A case for some OTHER client should not appear in this client's list
    other = User(
        email="other@gmail.com",
        password_hash=hash_password("x"),
        full_name="Other",
        role=UserRole.CLIENT,
        is_active=True,
        is_verified=True,
    )
    db_session.add(other)
    db_session.commit()
    svc.create(
        CaseCreate(
            title="Other client's case",
            case_type=CaseType.DIVORCE,
            client_email=other.email,
        ),
        lawyer,
    )

    cases = svc.list_for_user(client_user)
    assert len(cases) == 1
    assert cases[0].title == "Their case"
