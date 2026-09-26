"""Embedding model + FAISS index loader (Final Report Algorithm 4).

The canonical builder is `ai-services/corpus_builder/build_corpus.py`. This
module loads the index that builder writes to disk, lazily on first use,
and exposes a `search()` over it.

Metadata format from corpus_builder:
    { source, source_type, chunk_id, text }

Older 12-entry seed index used:
    { id, title, section_number, document_type, court, year, content }

`record_*` helpers below adapt both shapes transparently so the rest of
the codebase doesn't care which one is loaded.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger


_LOCK = threading.Lock()
_MODEL = None
_INDEX = None
_META: list[dict] = []


# ---- Metadata field helpers (handles both seed + corpus_builder formats) ----

def record_text(m: dict) -> str:
    return m.get("text") or m.get("content") or ""


def record_source(m: dict) -> str:
    """Human-readable source name (used in chat citations)."""
    return m.get("source") or m.get("title") or m.get("section_number") or "Unknown"


def record_kind(m: dict) -> str:
    """'statute' / 'judgment' (corpus_builder) or document_type (seed)."""
    return (
        m.get("source_type")
        or m.get("document_type")
        or ""
    ).lower()


# ---- Model + embedding -----------------------------------------------------

def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
    _MODEL = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _MODEL


def embed(texts: list[str]):
    """Return (N, dim) float32, L2-normalised — matches the index built by
    corpus_builder (which also normalises)."""
    import numpy as np
    model = _load_model()
    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return vectors.astype(np.float32)


# ---- Index loading + search ------------------------------------------------

def _index_paths() -> tuple[Path, Path]:
    idx = Path(settings.FAISS_INDEX_PATH)
    meta = Path(settings.FAISS_METADATA_PATH)
    idx.parent.mkdir(parents=True, exist_ok=True)
    return idx, meta


def build_or_load(_db: Session | None = None) -> int:
    """Load the FAISS index from disk. The corpus_builder script writes the
    canonical index; we do NOT rebuild it from the DB here.

    Returns the number of vectors in the index, or 0 if no index exists yet."""
    global _INDEX, _META
    if _INDEX is not None:
        return _INDEX.ntotal

    with _LOCK:
        if _INDEX is not None:
            return _INDEX.ntotal

        import faiss
        idx_path, meta_path = _index_paths()
        if not (idx_path.exists() and meta_path.exists()):
            logger.warning(
                f"FAISS index not found at {idx_path}. "
                "Run: python ai-services/corpus_builder/build_corpus.py"
            )
            return 0

        logger.info(f"Loading FAISS index from {idx_path}")
        _INDEX = faiss.read_index(str(idx_path))
        with open(meta_path, "r", encoding="utf-8") as f:
            _META = json.load(f)
        logger.info(f"FAISS index ready: {_INDEX.ntotal} vectors")
        return _INDEX.ntotal


def search(query: str, top_k: int, filters: dict | None = None) -> list[dict]:
    """Semantic search the legal corpus. Returns ranked metadata + relevance.

    `filters` is an optional dict: {court, year_from, year_to, case_type}.
    Filters apply post-search since the corpus is small enough.
    """
    if _INDEX is None or _INDEX.ntotal == 0 or not _META:
        return []

    qvec = embed([query])
    scores, ids = _INDEX.search(qvec, min(top_k * 3, _INDEX.ntotal))
    raw = [
        (_META[i], float(s))
        for s, i in zip(scores[0], ids[0])
        if 0 <= i < len(_META)
    ]

    if filters:
        court = (filters.get("court") or "").lower()
        ym = filters.get("year_from")
        yM = filters.get("year_to")
        case_type = (filters.get("case_type") or "").lower()

        def _ok(meta: dict) -> bool:
            # Filters are *exclusive on contradiction only* — a record with
            # no court / no year metadata is KEPT, because absence of
            # metadata in the corpus shouldn't punish the user (the SC
            # judgment archive ships with no per-judgment year info).
            if court:
                rec_court = (meta.get("court") or "").lower()
                if rec_court and court not in rec_court:
                    return False
            yr = meta.get("year")
            if yr is not None:
                if ym and yr < ym:
                    return False
                if yM and yr > yM:
                    return False
            if case_type:
                rec_kind = record_kind(meta).lower()
                if rec_kind and case_type not in rec_kind:
                    return False
            return True

        raw = [(m, s) for m, s in raw if _ok(m)]

    return [{**m, "relevance": s} for m, s in raw[:top_k]]


_STATS: dict | None = None


def index_stats() -> dict:
    """{"chunks", "documents"} for the loaded index, so the UI shows the
    real corpus size instead of a hard-coded number that goes stale after
    every rebuild. Counting distinct sources walks all metadata once, so the
    result is cached until `reset()`."""
    global _STATS
    chunks = build_or_load()
    if _STATS is None or _STATS["chunks"] != chunks:
        _STATS = {
            "chunks": chunks,
            "documents": len({record_source(m) for m in _META}) if chunks else 0,
        }
    return _STATS


def reset() -> None:
    """Forget the loaded index — call after rebuilding the corpus."""
    global _INDEX, _META, _STATS
    with _LOCK:
        _INDEX = None
        _META = []
        _STATS = None
