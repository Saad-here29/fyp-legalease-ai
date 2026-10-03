"""Signing out revokes tokens. In the Oct 2026 audit a Bearer access token
and the refresh token both kept working after logout (only the cookies were
cleared). Logout now bumps the user's token_version, which every token
carries as "tv"."""

import pytest

from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.enums import UserRole
from app.models.user import User

PASSWORD = "TestPass123"


@pytest.fixture
def user(db_session):
    u = User(
        email="signout@gmail.com",
        password_hash=hash_password(PASSWORD),
        full_name="Sign Out",
        role=UserRole.LAWYER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def _login(client):
    r = client.post("/api/v1/auth/login", json={"email": "signout@gmail.com", "password": PASSWORD})
    assert r.status_code == 200, r.text
    client.cookies.clear()  # exercise the Bearer / body paths, not the cookies
    return r.json()["tokens"]


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_tokens_work_before_logout(client, user):
    tokens = _login(client)
    assert client.get("/api/v1/auth/me", headers=_bearer(tokens["access_token"])).status_code == 200
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200


def test_access_and_refresh_tokens_return_401_after_logout(client, user):
    tokens = _login(client)
    r = client.post("/api/v1/auth/logout", headers=_bearer(tokens["access_token"]))
    assert r.status_code == 200
    client.cookies.clear()

    r = client.get("/api/v1/auth/me", headers=_bearer(tokens["access_token"]))
    assert r.status_code == 401
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_logout_revokes_tokens_from_every_session(client, user):
    first, second = _login(client), _login(client)
    client.post("/api/v1/auth/logout", headers=_bearer(first["access_token"]))
    client.cookies.clear()
    assert client.get("/api/v1/auth/me", headers=_bearer(second["access_token"])).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 401


def test_signing_in_again_after_logout_works(client, user):
    old = _login(client)
    client.post("/api/v1/auth/logout", headers=_bearer(old["access_token"]))
    new = _login(client)
    assert client.get("/api/v1/auth/me", headers=_bearer(new["access_token"])).status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": new["refresh_token"]}).status_code == 200


def test_tokens_issued_before_versioning_still_work_until_logout(client, user):
    # Pre-migration tokens have no "tv" claim; they count as version 0.
    import jwt

    from app.core.config import settings

    payload = jwt.decode(create_access_token(user.id, user.role.value), settings.SECRET_KEY,
                         algorithms=[settings.JWT_ALGORITHM])
    payload.pop("tv")
    legacy = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    assert client.get("/api/v1/auth/me", headers=_bearer(legacy)).status_code == 200

    client.post("/api/v1/auth/logout", headers=_bearer(legacy))
    client.cookies.clear()
    assert client.get("/api/v1/auth/me", headers=_bearer(legacy)).status_code == 401
    assert client.post("/api/v1/auth/refresh",
                       json={"refresh_token": create_refresh_token(user.id)}).status_code == 401
