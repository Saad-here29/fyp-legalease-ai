"""Password hashing (bcrypt) and JWT signing/verification."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


# ===== Passwords =====

def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ===== JWT =====

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str | int, role: str, token_version: int = 0, extra: dict[str, Any] | None = None
) -> str:
    payload = {
        "sub": str(subject),
        "role": role,
        "kind": "access",
        "tv": token_version,
        "iat": _now_utc(),
        "exp": _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | int, token_version: int = 0) -> str:
    payload = {
        "sub": str(subject),
        "kind": "refresh",
        "tv": token_version,
        "iat": _now_utc(),
        "exp": _now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def token_is_current(payload: dict[str, Any], current_version: int) -> bool:
    """False once the user has signed out since this token was issued.
    Tokens from before versioning carry no "tv" and count as version 0."""
    return payload.get("tv", 0) == current_version
