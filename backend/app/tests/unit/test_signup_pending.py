"""Re-registering an unverified email only resends the code. In the Oct
2026 quality pass a second signup for a pending email replaced its
password, name and role (a pending lawyer became a client named "Someone
Else"); if the owner then verified with the code they received, the account
carried the second person's password (R3)."""

import pytest

from app.core.exceptions import InvalidCredentials
from app.core.security import verify_password
from app.models.enums import UserRole
from app.models.lawyer import Lawyer
from app.models.user import User
from app.schemas.auth import SignupRequest
from app.services.auth_service import AuthService

EMAIL = "pending.owner@gmail.com"  # gmail.com: the domain check's offline fast path


def _signup(db, **over):
    payload = {"email": EMAIL, "password": "OwnerPass123", "full_name": "Real Owner", "role": UserRole.LAWYER,
               "bar_license_no": "PB-PEND-1", "specialization": "Family Law", "bar_year": 2016}
    payload.update(over)
    return AuthService(db).signup(SignupRequest(**payload))


def _user(db):
    db.expire_all()
    return db.query(User).filter(User.email == EMAIL).one()


def test_second_signup_keeps_password_name_role_and_profile(db_session):
    _signup(db_session)
    first_otp = _user(db_session).otp

    result = _signup(db_session, password="AttackerPass999", full_name="Someone Else", role=UserRole.CLIENT,
                     bar_license_no=None, cnic="35202-0000000-1")

    user = _user(db_session)
    assert user.role == UserRole.LAWYER
    assert user.full_name == "Real Owner"
    assert verify_password("OwnerPass123", user.password_hash)
    assert not verify_password("AttackerPass999", user.password_hash)
    assert db_session.query(Lawyer).filter(Lawyer.user_id == user.id).one().bar_license_no == "PB-PEND-1"
    # it only re-sent a code, with the same response as a first signup
    assert user.otp and user.otp != first_otp
    assert result == {"email": EMAIL, "message": "Verification code sent. Check your inbox."}


def test_owner_verifying_after_a_second_signup_keeps_their_own_password(db_session):
    _signup(db_session)
    _signup(db_session, password="AttackerPass999", full_name="Someone Else", role=UserRole.CLIENT)
    service = AuthService(db_session)
    service.verify_otp(EMAIL, _user(db_session).otp)

    assert service.login(email=EMAIL, password="OwnerPass123").user.email == EMAIL
    with pytest.raises(InvalidCredentials):
        AuthService(db_session).login(email=EMAIL, password="AttackerPass999")
