"""HttpOnly cookie helpers for JWT delivery.

We deliver the access + refresh tokens as Secure, HttpOnly cookies so
the frontend never touches the raw token in JavaScript. This eliminates
the XSS-exfiltration class of attack against localStorage tokens.

Names are intentionally short and prefixed so they're easy to spot in
browser dev tools.
"""

from __future__ import annotations

from fastapi import Response

from app.core.config import settings

ACCESS_COOKIE = "le_access"
REFRESH_COOKIE = "le_refresh"


def _cookie_kwargs(*, max_age: int) -> dict:
    # In dev (http://localhost) we must NOT set `secure=True` or the browser
    # silently drops the cookie. In any non-dev env we force it on.
    is_prod = settings.APP_ENV.lower() not in {"development", "dev", "local"}
    return {
        "httponly": True,
        "secure": is_prod,
        # `lax` lets the cookie travel on top-level navigations (so login
        # redirects work) but blocks third-party CSRF. `strict` would
        # break the OAuth-style return flow if we add it later.
        "samesite": "lax",
        "max_age": max_age,
        "path": "/",
    }


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        **_cookie_kwargs(max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        **_cookie_kwargs(max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600),
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")
