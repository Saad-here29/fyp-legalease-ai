"""Authentication request/response schemas."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import APIModel


# ===== Requests =====

class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SignupRequest(APIModel):
    """Signup collects exactly: full name, email, phone, password, role.

    Role-specific fields below (bar license, CNIC, university ID, ...) are
    kept optional — no verification system exists for them yet, so the
    frontend no longer collects them and no role requires them at signup.
    They stay available for a future verification flow or direct API use.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=20)
    role: UserRole

    # Lawyer fields (optional — unverified)
    bar_license_no: str | None = Field(default=None, max_length=50)
    specialization: str | None = Field(default=None, max_length=120)
    bar_year: int | None = Field(default=None, ge=1950, le=2100)
    bar_council: str | None = Field(default=None, max_length=120)

    # Client fields
    address: str | None = Field(default=None, max_length=500)
    cnic: str | None = Field(default=None, max_length=20)

    # Student fields (optional — unverified)
    university_id: str | None = Field(default=None, max_length=50)
    university_name: str | None = Field(default=None, max_length=150)
    current_year: int | None = Field(default=None, ge=1, le=7)


class RefreshRequest(APIModel):
    refresh_token: str | None = None  # optional — refresh cookie is preferred


class ForgotPasswordRequest(APIModel):
    email: EmailStr


class ResetPasswordRequest(APIModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=8, max_length=128)


class ResendOtpRequest(APIModel):
    email: EmailStr


class VerifyOtpRequest(APIModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=8)


class SignupAcceptedResponse(APIModel):
    email: EmailStr
    message: str


# ===== Responses =====

class TokenPair(APIModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_minutes: int


class UserRead(APIModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class LoginResponse(APIModel):
    user: UserRead
    tokens: TokenPair


class MessageResponse(APIModel):
    message: str
