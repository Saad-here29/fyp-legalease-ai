"""embeddings.index_stats() — the corpus size shown on the Research page."""

from types import SimpleNamespace

from app.ai import embeddings


def test_counts_chunks_and_distinct_sources(monkeypatch):
    embeddings.reset()
    meta = [{"source": "Pakistan Penal Code", "text": "a"},
            {"source": "Pakistan Penal Code", "text": "b"},
            {"source": "Contract Act, 1872", "text": "c"}]
    monkeypatch.setattr(embeddings, "_INDEX", SimpleNamespace(ntotal=3))
    monkeypatch.setattr(embeddings, "_META", meta)
    try:
        assert embeddings.index_stats() == {"chunks": 3, "documents": 2}
    finally:
        embeddings.reset()


def test_recomputed_when_index_size_changes(monkeypatch):
    embeddings.reset()
    monkeypatch.setattr(embeddings, "_INDEX", SimpleNamespace(ntotal=1))
    monkeypatch.setattr(embeddings, "_META", [{"source": "A"}])
    try:
        assert embeddings.index_stats()["chunks"] == 1
        monkeypatch.setattr(embeddings, "_INDEX", SimpleNamespace(ntotal=2))
        monkeypatch.setattr(embeddings, "_META", [{"source": "A"}, {"source": "B"}])
        assert embeddings.index_stats() == {"chunks": 2, "documents": 2}
    finally:
        embeddings.reset()


def test_no_index_reports_zero(monkeypatch, tmp_path):
    embeddings.reset()
    monkeypatch.setattr(embeddings.settings, "FAISS_INDEX_PATH", str(tmp_path / "missing.faiss"))
    monkeypatch.setattr(embeddings.settings, "FAISS_METADATA_PATH", str(tmp_path / "missing.json"))
    try:
        assert embeddings.index_stats() == {"chunks": 0, "documents": 0}
    finally:
        embeddings.reset()
