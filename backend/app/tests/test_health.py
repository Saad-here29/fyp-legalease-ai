"""Smoke test — proves the FastAPI app starts and the /health route works."""

import numpy as np
import pytest

from app.core.config import settings
from app.main import _faiss_ntotal


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    # which search mode is running (docs/DEMO_RUNBOOK.md)
    assert set(body) == {"status", "kb_v2", "v1_index_chunks", "v2_index_chunks", "threshold",
                         "judgments_v2", "judgment_chunks", "judgments",
                         "scraped_v2", "scraped_chunks", "scraped_judgment_chunks", "reasoning_v2"}
    assert body["judgments_v2"] is settings.JUDGMENTS_V2
    assert body["kb_v2"] is settings.KB_V2


def test_health_reports_kb_v2_mode_and_chunk_counts(client, tmp_path, monkeypatch):
    faiss = pytest.importorskip("faiss")
    for name, n in (("v1.faiss", 7), ("v2.faiss", 3)):
        index = faiss.IndexFlatIP(4)
        index.add(np.eye(4, dtype=np.float32)[np.arange(n) % 4])
        faiss.write_index(index, str(tmp_path / name))
    monkeypatch.setattr(settings, "FAISS_INDEX_PATH", str(tmp_path / "v1.faiss"))
    monkeypatch.setattr(settings, "KB_V2_INDEX_PATH", str(tmp_path / "v2.faiss"))
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "KB_V2_THRESHOLD", 0.62)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", False)
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    monkeypatch.setattr(settings, "REASONING_V2", False)
    body = client.get("/health").json()
    assert body =={"status": "ok", "kb_v2": True, "v1_index_chunks": 7, "v2_index_chunks": 3, "threshold": 0.62,
                    "judgments_v2": False, "judgment_chunks": None, "judgments": None,
                    "scraped_v2": False, "scraped_chunks": None, "scraped_judgment_chunks": None,
                    "reasoning_v2": False}
    monkeypatch.setattr(settings, "KB_V2", False)
    body = client.get("/health").json()
    assert body["kb_v2"] is False and body["v2_index_chunks"] is None
    assert body["threshold"] == settings.RAG_SIMILARITY_THRESHOLD


def test_faiss_ntotal_missing_or_not_faiss(tmp_path):
    assert _faiss_ntotal(str(tmp_path / "nope.faiss")) is None
    (tmp_path / "x.faiss").write_bytes(b"not a faiss index at all")
    assert _faiss_ntotal(str(tmp_path / "x.faiss")) is None


def test_root_returns_app_info(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert "name" in body
    assert "version" in body
