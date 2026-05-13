"""Authentication service.

Implements:
  - signup(payload)            — validate MX + create inactive User + send OTP
  - resend_otp(email)          — regenerate code and re-send the email
  - verify_otp(email, otp)     — activate account, return user + tokens
  - login(email, password)     — Algorithm 1; account lockout after 5 fails
  - refresh(refresh_token)     — rotates access + refresh
  - forgot_password(email)     — generate + send reset OTP (silent if unknown)
  - reset_password(email, otp, new_password) — verify code + set new hash

Account lockout: after 5 consecutive failed attempts the user account
goes inactive (UC-01 alternative flow 2b → HTTP 423).
"""

import random
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.exc import IntegrityError, PendingRollbackError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    AccountLocked,
    InvalidCredentials,
    NotAuthenticated,
    NotFound,
    ValidationFailed,
)
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.client import Client
from app.models.enums import UserRole
from app.models.lawyer import Lawyer
from app.models.student import Student
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginResponse,
    SignupRequest,
    TokenPair,
    UserRead,
)
from app.services.base import BaseService
from app.utils.email import send_otp_email, send_password_reset_email
from app.utils.email_validator import EmailValidationError, validate_email_domain

MAX_FAILED_ATTEMPTS = 5
OTP_TTL_MINUTES = 10


def _new_otp() -> str:
    return f"{random.randint(100000, 999999)}"


class AuthService(BaseService):
    def __init__(self, db: Session, request=None):
        super().__init__(db, request)
        self.users = UserRepository(db)

    # ===== SIGNUP =====
    def signup(self, payload: SignupRequest) -> dict:
        """Validate email + create an INACTIVE user + send OTP.

        Returns {"email": ..., "message": ...} — the frontend then takes
        the user to the OTP page. Tokens are NOT issued here; they come
        from verify_otp once the email is proven.
        """
        email = payload.email.lower()

        # 1) Validate format and MX record before we touch the DB
        try:
            validate_email_domain(email)
        except EmailValidationError as e:
            raise ValidationFailed(
                message=str(e),
                hint="Use an email at a real domain such as gmail.com.",
            )

        # 2) Reject if there's already a *verified* user with this email.
        # If an unverified row exists, regenerate the OTP and update fields
        # rather than erroring — covers the "I closed the tab" case.
        existing = self.users.get_by_email(email)
        if existing and existing.is_verified:
            raise ValidationFailed(
                message="An account with this email already exists.",
                hint="Try signing in or use a different email.",
            )

        otp = _new_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)

        if existing is None:
            user = User(
                email=email,
                password_hash=hash_password(payload.password),
                full_name=payload.full_name,
                phone=payload.phone,
                role=payload.role,
                is_active=False,
                is_verified=False,
                otp=otp,
                otp_expires_at=expires_at,
                failed_login_count=0,
            )
            self.users.add(user)
            self.db.flush()  # need user.id for the role profile FK
            self._add_role_profile(user, payload)
        else:
            # Refresh fields on the unverified row (allows password fix /
            # name correction before verification)
            existing.password_hash = hash_password(payload.password)
            existing.full_name = payload.full_name
            existing.phone = payload.phone
            existing.role = payload.role
            existing.otp = otp
            existing.otp_expires_at = expires_at
            user = existing
            self._update_role_profile(user, payload)

        self.audit(
            "SIGNUP_OTP_SENT",
            user_id=user.id,
            entity_type="User",
            entity_id=user.id,
            new_values={"email": user.email, "role": user.role.value},
        )
        try:
            self.commit()
        except (IntegrityError, PendingRollbackError, SQLAlchemyError) as e:
            self.db.rollback()
            raise self._friendly_integrity_error(e, payload)
        self.db.refresh(user)

        send_otp_email(user.email, otp, recipient_name=user.full_name)

        return {
            "email": user.email,
            "message": "Verification code sent. Check your inbox.",
        }

    # ===== RESEND OTP =====
    def resend_otp(self, email: str) -> dict:
        user = self.users.get_by_email(email.lower())
        if user is None:
            # Don't reveal whether the email exists
            return {"email": email, "message": "If that email is registered, a new code has been sent."}
        if user.is_verified:
            return {"email": email, "message": "This account is already verified — please sign in."}

        otp = _new_otp()
        user.otp = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
        self.audit("OTP_RESENT", user_id=user.id)
        self.commit()
        send_otp_email(user.email, otp, recipient_name=user.full_name)
        return {"email": user.email, "message": "New verification code sent."}

    # ===== VERIFY OTP — activates the account but does NOT auto-login =====
    def verify_otp(self, email: str, otp: str) -> dict:
        """Confirm OTP and activate the account. Returns the verified email
        so the frontend can pre-fill the login form. Does NOT issue tokens
        — the user is sent back to /login and must enter their password."""
        user = self.users.get_by_email(email.lower())
        if user is None:
            raise NotFound("Account not found.")
        if user.is_verified:
            # Idempotent — already verified, just confirm
            return {
                "email": user.email,
                "message": "Already verified. Please sign in.",
            }

        if not user.otp or user.otp != otp:
            self.audit("OTP_VERIFY_FAILED_BAD_CODE", user_id=user.id)
            raise ValidationFailed(
                message="Invalid verification code.",
                hint="Check the code and try again, or request a new one.",
            )

        expires_at = user.otp_expires_at
        if expires_at is not None:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                self.audit("OTP_VERIFY_FAILED_EXPIRED", user_id=user.id)
                raise ValidationFailed(
                    message="Verification code has expired.",
                    hint="Click \"Resend code\" to get a new one.",
                )

        user.is_verified = True
        user.is_active = True
        user.otp = None
        user.otp_expires_at = None
        self.audit("OTP_VERIFY_OK", user_id=user.id)
        self.commit()
        self.db.refresh(user)

        return {
            "email": user.email,
            "message": "Email verified. Please sign in to continue.",
        }

    # ===== LOGIN =====
    def login(self, *, email: str, password: str) -> LoginResponse:
        user = self.users.get_by_email(email.lower())
        if user is None:
            self.audit("LOGIN_FAILED_NO_USER", user_id=None, new_values={"email": email})
            raise InvalidCredentials()

        if not user.is_verified:
            self.audit("LOGIN_BLOCKED_UNVERIFIED", user_id=user.id)
            raise AccountLocked(
                message="Please verify your email before signing in.",
                hint="We've sent you a 6-digit code. Use the resend option if it expired.",
            )

        if not user.is_active:
            self.audit("LOGIN_BLOCKED_INACTIVE", user_id=user.id)
            raise AccountLocked(
                message="Your account has been locked.",
                hint="Reset your password to regain access.",
            )

        if not verify_password(password, user.password_hash):
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
                user.is_active = False
                self.audit(
                    "ACCOUNT_LOCKED",
                    user_id=user.id,
                    new_values={"failed_attempts": user.failed_login_count},
                )
                self.commit()
                raise AccountLocked()
            self.commit()
            self.audit(
                "LOGIN_FAILED_BAD_PASSWORD",
                user_id=user.id,
                new_values={"failed_attempts": user.failed_login_count},
            )
            raise InvalidCredentials()

        # Success — reset counter, issue tokens, audit
        user.failed_login_count = 0
        tokens = self._issue_tokens(user)
        self.audit("LOGIN_OK", user_id=user.id)
        self.commit()

        return LoginResponse(user=UserRead.model_validate(user), tokens=tokens)

    # ===== REFRESH =====
    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            raise NotAuthenticated("Refresh token has expired. Please sign in again.")
        except jwt.InvalidTokenError:
            raise NotAuthenticated("Invalid refresh token.")

        if payload.get("kind") != "refresh":
            raise NotAuthenticated("Wrong token type — refresh token required.")

        user_id_raw = payload.get("sub")
        try:
            user_id = uuid.UUID(user_id_raw) if user_id_raw else None
        except (ValueError, TypeError):
            raise NotAuthenticated("Refresh token subject is not a valid UUID.")

        user = self.users.get(user_id) if user_id else None
        if user is None or not user.is_active:
            raise NotAuthenticated("Account not found or inactive.")

        return self._issue_tokens(user)

    # ===== FORGOT PASSWORD =====
    def forgot_password(self, email: str) -> dict:
        user = self.users.get_by_email(email.lower())
        # Always respond OK to avoid leaking which emails are registered
        if user is None or not user.is_verified:
            return {"message": "If that email is registered, a reset code has been sent."}
        otp = _new_otp()
        user.otp = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
        self.audit("PASSWORD_RESET_REQUESTED", user_id=user.id)
        self.commit()
        send_password_reset_email(user.email, otp)
        return {"message": "If that email is registered, a reset code has been sent."}

    # ===== RESET PASSWORD =====
    def reset_password(self, email: str, otp: str, new_password: str) -> dict:
        user = self.users.get_by_email(email.lower())
        if user is None or not user.is_verified:
            raise ValidationFailed(
                message="We could not reset that password.",
                hint="Request a new reset code and try again.",
            )

        if not user.otp or user.otp != otp:
            self.audit("PASSWORD_RESET_FAILED_BAD_CODE", user_id=user.id)
            raise ValidationFailed(
                message="Invalid or expired reset code.",
                hint="Request a new one and try again.",
            )

        expires_at = user.otp_expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at is None or expires_at < datetime.now(timezone.utc):
            raise ValidationFailed(
                message="Reset code has expired.",
                hint="Request a new one.",
            )

        user.password_hash = hash_password(new_password)
        user.otp = None
        user.otp_expires_at = None
        user.failed_login_count = 0
        user.is_active = True  # Recover from lockout via password reset
        self.audit("PASSWORD_RESET_OK", user_id=user.id)
        self.commit()
        return {"message": "Password reset. Please sign in with your new password."}

    # ===== HELPERS =====

    def _add_role_profile(self, user: User, payload: SignupRequest) -> None:
        if payload.role == UserRole.LAWYER:
            self.db.add(
                Lawyer(
                    user_id=user.id,
                    bar_license_no=payload.bar_license_no,
                    specialization=payload.specialization,
                    bar_year=payload.bar_year,
                    bar_council=payload.bar_council,
                )
            )
        elif payload.role == UserRole.CLIENT:
            self.db.add(
                Client(
                    user_id=user.id,
                    address=payload.address,
                    cnic=payload.cnic,
                )
            )
        elif payload.role == UserRole.STUDENT:
            self.db.add(
                Student(
                    user_id=user.id,
                    university_id=payload.university_id,
                    university_name=payload.university_name,
                    current_year=payload.current_year,
                )
            )

    def _update_role_profile(self, user: User, payload: SignupRequest) -> None:
        """When an unverified user retries signup, update their role profile
        in place rather than inserting a new row (avoids unique violations
        on bar_license_no / cnic / university_id)."""
        if payload.role == UserRole.LAWYER:
            row = self.db.query(Lawyer).filter(Lawyer.user_id == user.id).first()
            if row is None:
                self._add_role_profile(user, payload)
                return
            row.bar_license_no = payload.bar_license_no
            row.specialization = payload.specialization
            row.bar_year = payload.bar_year
            row.bar_council = payload.bar_council
        elif payload.role == UserRole.CLIENT:
            row = self.db.query(Client).filter(Client.user_id == user.id).first()
            if row is None:
                self._add_role_profile(user, payload)
                return
            row.address = payload.address
            row.cnic = payload.cnic
        elif payload.role == UserRole.STUDENT:
            row = self.db.query(Student).filter(Student.user_id == user.id).first()
            if row is None:
                self._add_role_profile(user, payload)
                return
            row.university_id = payload.university_id
            row.university_name = payload.university_name
            row.current_year = payload.current_year

    @staticmethod
    def _friendly_integrity_error(e: IntegrityError, payload: SignupRequest) -> ValidationFailed:
        """Map Postgres unique-constraint names to user-facing messages so the
        frontend can show 'X already registered' instead of a generic 500."""
        text = str(getattr(e, "orig", e)).lower()
        if "lawyers_bar_license_no" in text:
            return ValidationFailed(
                message=f"Bar license '{payload.bar_license_no}' is already registered.",
                hint="If this is your license, use Sign in instead.",
            )
        if "clients_cnic" in text:
            return ValidationFailed(
                message=f"CNIC '{payload.cnic}' is already registered.",
                hint="If this is your CNIC, use Sign in instead.",
            )
        if "students_university_id" in text:
            return ValidationFailed(
                message=f"University ID '{payload.university_id}' is already registered.",
                hint="If this is your ID, use Sign in instead.",
            )
        if "users_email" in text or "ix_users_email" in text:
            return ValidationFailed(
                message="An account with this email already exists.",
                hint="Try signing in instead.",
            )
        return ValidationFailed(
            message="Could not create the account — a unique field is already in use.",
            hint="Check your email, license number, CNIC, or university ID.",
        )

    def _issue_tokens(self, user: User) -> TokenPair:
        access = create_access_token(subject=user.id, role=user.role.value)
        refresh = create_refresh_token(subject=user.id)
        logger.debug(f"Issued token pair for {user.email}")
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
