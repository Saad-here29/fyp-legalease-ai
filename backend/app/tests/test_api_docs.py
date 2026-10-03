"""API docs (/docs, /redoc, /openapi.json) exist only in development. The
Oct 2026 audit found them public because they were tied to APP_DEBUG."""

import importlib

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

DOC_PATHS = ["/docs", "/redoc", "/openapi.json"]


def _app_for(env, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", env)
    monkeypatch.setattr(settings, "APP_DEBUG", True)  # must not matter
    import app.main
    return importlib.reload(app.main).app


@pytest.fixture(autouse=True)
def restore_main():
    yield
    import app.main
    importlib.reload(app.main)


@pytest.mark.parametrize("env", ["development", "dev", "local"])
def test_docs_served_in_development(env, monkeypatch):
    client = TestClient(_app_for(env, monkeypatch))
    for path in DOC_PATHS:
        assert client.get(path).status_code == 200, path


@pytest.mark.parametrize("env", ["production", "staging"])
def test_docs_hidden_outside_development(env, monkeypatch):
    client = TestClient(_app_for(env, monkeypatch))
    for path in DOC_PATHS:
        assert client.get(path).status_code == 404, path
    assert client.get("/health").status_code == 200
