"""Unit tests for AuthService — covers UT-AUTH-001..006 from Final Report § 4.3
Table 4.2 plus the iteration-2 OTP-verification flow that replaced the legacy
auto-login signup.

Test users use @gmail.com so the MX-record validator hits the ALWAYS_VALID
fast-path and these tests stay deterministic / offline.
"""

import pytest

from app.core.exceptions import AccountLocked, InvalidCredentials, ValidationFailed
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import SignupRequest
from app.services.auth_service import AuthService


@pytest.fixture
def sample_user(db_session):
    """A pre-verified lawyer ready to log in. Note `is_verified=True` and
    `is_active=True` — the OTP rewrite gates login on both flags."""
    user = User(
        email="lawyer@gmail.com",
        password_hash=hash_password("SecurePass123"),
        full_name="Test Lawyer",
        role=UserRole.LAWYER,
        is_active=True,
        is_verified=True,
        failed_login_count=0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================
# UT-AUTH-001: successful login returns user + signed token pair
# ============================================================
def test_ut_auth_001_successful_login_returns_user_and_tokens(db_session, sample_user):
    service = AuthService(db_session)

    response = service.login(email="lawyer@gmail.com", password="SecurePass123")

    assert response.user.email == "lawyer@gmail.com"
    assert response.user.role == UserRole.LAWYER
    assert response.tokens.access_token
    assert response.tokens.refresh_token
    assert response.tokens.token_type == "bearer"
    # Expiry comes from settings.ACCESS_TOKEN_EXPIRE_MINUTES (60 or 120
    # depending on env) — just check it's positive, don't pin the exact value
    assert response.tokens.expires_in_minutes > 0

    # Failed counter resets on success
    db_session.refresh(sample_user)
    assert sample_user.failed_login_count == 0


# ============================================================
# UT-AUTH-002: wrong password raises InvalidCredentials and increments counter
# ============================================================
def test_ut_auth_002_wrong_password_raises_invalid_credentials(db_session, sample_user):
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentials):
        service.login(email="lawyer@gmail.com", password="WrongPassword")

    db_session.refresh(sample_user)
    assert sample_user.failed_login_count == 1


# ============================================================
# UT-AUTH-003: non-existent user → InvalidCredentials (no info leak)
# ============================================================
def test_ut_auth_003_nonexistent_user_raises_invalid_credentials(db_session):
    service = AuthService(db_session)

    with pytest.raises(InvalidCredentials):
        service.login(email="nobody@gmail.com", password="anyPassword")


# ============================================================
# UT-AUTH-004: account lockout after 5 failed attempts
# ============================================================
def test_account_locks_after_five_failed_attempts(db_session, sample_user):
    service = AuthService(db_session)

    for _ in range(4):
        with pytest.raises(InvalidCredentials):
            service.login(email="lawyer@gmail.com", password="wrong")

    # 5th attempt flips is_active to False and raises AccountLocked
    with pytest.raises(AccountLocked):
        service.login(email="lawyer@gmail.com", password="wrong")

    db_session.refresh(sample_user)
    assert sample_user.is_active is False
    assert sample_user.failed_login_count == 5

    # Locked account stays locked even with the right password
    with pytest.raises(AccountLocked):
        service.login(email="lawyer@gmail.com", password="SecurePass123")


# ============================================================
# UT-AUTH-005: signup (post-OTP-rewrite) creates an INACTIVE user
# and returns a pending-verification dict, not tokens
# ============================================================
def test_signup_creates_inactive_lawyer_pending_otp(db_session):
    service = AuthService(db_session)
    payload = SignupRequest(
        email="new.lawyer@gmail.com",
        password="StrongPass123",
        full_name="New Lawyer",
        role=UserRole.LAWYER,
        bar_license_no="PB-UT-001",
        specialization="Family Law",
        bar_year=2018,
    )

    result = service.signup(payload)

    # Response shape changed in iteration 2 — now returns a pending dict
    assert result["email"] == "new.lawyer@gmail.com"
    assert "code" in result["message"].lower() or "verif" in result["message"].lower()

    # User is in the DB but inactive + unverified, with an OTP set
    user = (
        db_session.query(User).filter(User.email == "new.lawyer@gmail.com").first()
    )
    assert user is not None
    assert user.is_verified is False
    assert user.is_active is False
    assert user.otp and len(user.otp) == 6

    # Role profile attached in the same transaction
    from app.models.lawyer import Lawyer
    lawyer = db_session.query(Lawyer).filter(Lawyer.user_id == user.id).first()
    assert lawyer is not None
    assert lawyer.bar_license_no == "PB-UT-001"


# ============================================================
# UT-AUTH-006: verify_otp activates the account (no auto-login —
# user is bounced to /login per UX decision in iteration 2)
# ============================================================
def test_verify_otp_activates_account_without_auto_login(db_session):
    service = AuthService(db_session)
    service.signup(
        SignupRequest(
            email="otp.test@gmail.com",
            password="StrongPass123",
            full_name="OTP Tester",
            role=UserRole.CLIENT,
        )
    )

    user = db_session.query(User).filter(User.email == "otp.test@gmail.com").first()
    otp = user.otp

    result = service.verify_otp("otp.test@gmail.com", otp)

    # Iteration-2 contract: returns a confirmation dict, not tokens.
    # The user is then asked to sign in fresh.
    assert isinstance(result, dict)
    assert result["email"] == "otp.test@gmail.com"
    assert "sign in" in result["message"].lower() or "verified" in result["message"].lower()

    # Account is now active + verified, OTP cleared
    db_session.refresh(user)
    assert user.is_verified is True
    assert user.is_active is True
    assert user.otp is None

    # And login works with the same password the user just registered with
    login_resp = service.login(email="otp.test@gmail.com", password="StrongPass123")
    assert login_resp.tokens.access_token


# ============================================================
# Duplicate verified-email signup is rejected
# ============================================================
def test_signup_rejects_duplicate_verified_email(db_session, sample_user):
    service = AuthService(db_session)
    payload = SignupRequest(
        email="lawyer@gmail.com",  # already exists AND verified via fixture
        password="StrongPass123",
        full_name="Duplicate",
        role=UserRole.CLIENT,
    )

    with pytest.raises(ValidationFailed):
        service.signup(payload)


# ============================================================
# Refresh rotates the token pair
# ============================================================
def test_refresh_issues_new_token_pair(db_session, sample_user):
    service = AuthService(db_session)
    login = service.login(email="lawyer@gmail.com", password="SecurePass123")

    new_pair = service.refresh(login.tokens.refresh_token)

    assert new_pair.access_token
    assert new_pair.refresh_token
    assert new_pair.token_type == "bearer"


# ============================================================
# Unverified user cannot log in even with correct password
# ============================================================
def test_unverified_account_cannot_login(db_session):
    user = User(
        email="unverified@gmail.com",
        password_hash=hash_password("rightPassword"),
        full_name="Unverified",
        role=UserRole.CLIENT,
        is_active=False,
        is_verified=False,
        failed_login_count=0,
    )
    db_session.add(user)
    db_session.commit()

    service = AuthService(db_session)
    with pytest.raises(AccountLocked):
        service.login(email="unverified@gmail.com", password="rightPassword")
