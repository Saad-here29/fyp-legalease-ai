"""A dropped database connection gets one retry, then a clear 503 instead
of a raw 500. In the Oct 2026 audit transient Supabase SSL drops surfaced
as 500 Internal Server Error."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import DatabaseUnavailable
from app.db import session as db_session_module
from app.db.session import get_db, is_connection_error, open_session
from app.main import app


def _dropped():
    return OperationalError("SELECT 1", {}, Exception("SSL SYSCALL error: EOF detected"))


class FakeSession:
    def __init__(self, fail):
        self.fail, self.closed = fail, False

    def connection(self):
        if self.fail:
            raise _dropped()

    def close(self):
        self.closed = True


@pytest.fixture
def sessions(monkeypatch):
    """Sessions handed out by SessionLocal; set `plan` to which ones fail."""
    made, plan = [], []

    def factory():
        s = FakeSession(fail=plan[len(made)] if len(made) < len(plan) else False)
        made.append(s)
        return s

    monkeypatch.setattr(db_session_module, "SessionLocal", factory)
    monkeypatch.setattr(db_session_module, "RETRY_DELAY_SECONDS", 0)
    return made, plan


def test_connection_failure_is_retried_once(sessions):
    made, plan = sessions
    plan[:] = [True, False]
    db = open_session()
    assert len(made) == 2
    assert db is made[1]
    assert made[0].closed and not made[1].closed


def test_two_failures_raise_database_unavailable(sessions):
    made, plan = sessions
    plan[:] = [True, True]
    with pytest.raises(DatabaseUnavailable) as exc:
        open_session()
    assert exc.value.status_code == 503
    assert len(made) == 2 and all(s.closed for s in made)


def test_healthy_connection_is_not_retried(sessions):
    made, _ = sessions
    open_session()
    assert len(made) == 1


def test_only_connection_errors_count():
    assert is_connection_error(_dropped())
    assert not is_connection_error(IntegrityError("INSERT", {}, Exception("duplicate key")))


def _client_with_get_db(gen):
    app.dependency_overrides[get_db] = gen
    return TestClient(app, raise_server_exceptions=False)


def test_unreachable_database_returns_clear_503(sessions):
    _, plan = sessions
    plan[:] = [True, True]
    with TestClient(app) as c:  # real get_db, failing connections
        r = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer x"})
    assert r.status_code == 503
    assert r.json() == {"error": {"code": "db_unavailable",
                                  "message": "The database is temporarily unreachable.",
                                  "hint": "Please try again in a few seconds."}}


def test_connection_dropped_mid_request_returns_503():
    def dropped_mid_request():
        raise _dropped()
        yield  # pragma: no cover

    try:
        with _client_with_get_db(dropped_mid_request) as c:
            r = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer x"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "db_unavailable"


def test_other_database_errors_stay_500():
    def constraint_violation():
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))
        yield  # pragma: no cover

    try:
        with _client_with_get_db(constraint_violation) as c:
            r = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer x"})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 500
