"""JWT authentication dependency.

Usage in any router:

    from app.middlewares.auth import CurrentUser

    @router.get("/cases")
    def list_cases(user: CurrentUser, db: Session = Depends(get_db)):
        ...
"""

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.cookies import ACCESS_COOKIE
from app.core.exceptions import NotAuthenticated
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Pull the access token from the httpOnly cookie first, falling back
    to the Authorization: Bearer header. Cookie-based auth is the canonical
    transport; the header path keeps Postman/curl + legacy clients working."""
    cookie_token = request.cookies.get(ACCESS_COOKIE)
    if cookie_token:
        return cookie_token
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    token = _extract_token(request, credentials)
    if not token:
        raise NotAuthenticated("Missing access token.")

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise NotAuthenticated("Token has expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise NotAuthenticated("Invalid token.")

    if payload.get("kind") != "access":
        raise NotAuthenticated("Wrong token type — access token required.")

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise NotAuthenticated("Token missing subject.")

    try:
        user_id = uuid.UUID(user_id_raw)
    except ValueError:
        raise NotAuthenticated("Token subject is not a valid UUID.")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise NotAuthenticated("Account not found or inactive.")

    # Stash request metadata for downstream audit logging
    request.state.user_id = user.id
    request.state.user_role = user.role

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
