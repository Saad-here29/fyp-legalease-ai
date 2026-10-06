"""kb-v2 index: chunk rule, builder, and the KB_V2 search switch (offline)."""

import json
import re
from pathlib import Path

import numpy as np
import pytest

from app.ai import embeddings
from app.core.config import settings
from app.kb import index_v2
from app.kb.records import CORPUS_SOURCE, make_records
from app.kb.sectioner import Section

faiss = pytest.importorskip("faiss")


class WordTokenizer:
    """Stand-in for the model tokenizer: one token per word or punctuation mark."""

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
        out = {"input_ids": list(range(len(spans)))}
        if return_offsets_mapping:
            out["offset_mapping"] = spans
        return out


TOK = WordTokenizer()
META = {"title": "Sample Family Act, 1964", "year": 1964, "category": "Family Laws", "act_number": None,
        "status": "current", "source": CORPUS_SOURCE, "source_tier": 1, "source_url": None,
        "original_file": None, "scraped_at": None, "jurisdiction": "Pakistan"}


def records():
    long = " ".join(f"word{i}" for i in range(700))
    return make_records(META, [Section("2", "Definitions", "In this Act, wife includes a divorced wife."),
                               Section("9", "Maintenance", long),
                               Section("Schedule", None, "1. Dower. 2. Maintenance. 4. Restitution of conjugal rights.")])


# --------------------------------------------------------------------------- chunk rule

def test_prefix_forms():
    r = records()
    assert index_v2.prefix_for(r[0]) == "Sample Family Act, 1964 - s.2 Definitions:"
    assert index_v2.prefix_for(r[2]) == "Sample Family Act, 1964 - Schedule:"
    assert index_v2.prefix_for({**r[0], "section": None, "heading": None}) == "Sample Family Act, 1964:"


def test_no_chunk_over_the_limit_and_prefix_counted():
    for rec in records():
        chunks = index_v2.chunk_record(rec, TOK)
        prefix = index_v2.prefix_for(rec)
        for c in chunks:
            assert c["text"].startswith(prefix)
            assert len(TOK(c["text"])["input_ids"]) <= index_v2.MAX_TOKENS
    long = index_v2.chunk_record(records()[1], TOK)
    assert len(long) > 5
    # windows overlap and together cover the whole section
    body = records()[1]["text"]
    assert long[0]["start"] == 0 and long[-1]["end"] == len(body)
    assert all(b["start"] < a["end"] for a, b in zip(long, long[1:], strict=False))


def test_very_long_heading_is_shortened():
    rec = {**records()[0], "heading": " ".join(["heading"] * 200)}
    for c in index_v2.chunk_record(rec, TOK):
        assert len(TOK(c["text"])["input_ids"]) <= index_v2.MAX_TOKENS
        assert "…" in c["text"]


def _real_tokenizer():
    try:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(f"sentence-transformers/{settings.EMBEDDING_MODEL_NAME}",
                                             local_files_only=True)
    except Exception:  # noqa: BLE001
        return None


def test_chunk_rule_with_the_real_tokenizer():
    tok = _real_tokenizer()
    if tok is None:
        pytest.skip("embedding model tokenizer not cached")
    rec = {**records()[1], "text": "The Family Court shall have exclusive jurisdiction to entertain, hear and "
                                   "adjudicate upon matters specified in Part I of the Schedule. " * 30}
    for c in index_v2.chunk_record(rec, tok):
        assert len(tok(c["text"], add_special_tokens=False)["input_ids"]) <= 120
        assert len(tok(c["text"])["input_ids"]) <= 128           # with the model's special tokens


BUILT = Path(__file__).resolve().parents[3] / settings.KB_V2_METADATA_PATH


@pytest.mark.skipif(not BUILT.exists(), reason="faiss_v2 not built (scripts/kb/build_index_v2.py)")
def test_every_built_chunk_is_within_120_tokens():
    tok = _real_tokenizer()
    if tok is None:
        pytest.skip("embedding model tokenizer not cached")
    data = json.loads(BUILT.read_text(encoding="utf-8"))
    texts = [c["chunk_text"] for c in data["chunks"]]
    lengths = [len(ids) for ids in tok(texts, add_special_tokens=False)["input_ids"]]
    assert max(lengths) <= 120
    assert len(texts) == data["manifest"]["chunks"]


# --------------------------------------------------------------------------- builder

def fake_embed(texts):
    """Deterministic unit vectors: a bag of hashed words."""
    out = np.zeros((len(texts), 384), np.float32)
    for i, t in enumerate(texts):
        for w in re.findall(r"\w+", t.lower()):
            out[i, hash(w) % 384] += 1.0
        out[i] /= max(np.linalg.norm(out[i]), 1e-9)
    return out


def write_records(tmp_path):
    d = tmp_path / "records"
    d.mkdir()
    (d / "sample.jsonl").write_text("\n".join(json.dumps(r) for r in records()), encoding="utf-8")
    return d


def test_builder_writes_a_new_index(tmp_path):
    d = write_records(tmp_path)
    m = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2_meta.json", tokenizer=TOK, embed=fake_embed,
                       excluded_v1_sources=["THE SAMPLE FAMILY ACT, 1964"])
    index = faiss.read_index(str(tmp_path / "v2.faiss"))
    meta = json.loads((tmp_path / "v2_meta.json").read_text(encoding="utf-8"))
    assert index.ntotal == m["chunks"] == len(meta["chunks"]) and m["records"] == 3
    c = meta["chunks"][0]
    for k in ("doc_id", "title", "section", "heading", "source_tier", "category", "year", "jurisdiction",
              "source_type", "source_url"):
        assert k in c
    assert meta["manifest"]["excluded_v1_sources"] == ["THE SAMPLE FAMILY ACT, 1964"]


def test_builder_refuses_the_live_index_paths(tmp_path, monkeypatch):
    d = write_records(tmp_path)
    live = tmp_path / "legal_corpus.faiss"
    monkeypatch.setattr(settings, "FAISS_INDEX_PATH", str(live))
    with pytest.raises(ValueError):
        index_v2.build(d, live, tmp_path / "m.json", tokenizer=TOK, embed=fake_embed, excluded_v1_sources=[])


# --------------------------------------------------------------------------- the switch

V1_META = [
    {"source": "THE SAMPLE FAMILY ACT, 1964", "source_type": "statute", "chunk_id": 0,
     "text": "old OCR copy: maintenance of wi fe"},
    {"source": "Contract Act, 1872", "source_type": "statute", "chunk_id": 1, "text": "contract consideration"},
    {"source": "Some Judgment", "source_type": "judgment", "chunk_id": 2, "text": "maintenance appeal",
     "court": "Lahore High Court", "year": 2001},
    {"source": "Old Act", "source_type": "statute", "chunk_id": 3, "text": "maintenance wife court",
     "year": 1950},
]


def _search_before_kb_v2(query, top_k, filters=None):
    """Verbatim copy of embeddings.search as it was before KB_V2 (for the
    byte-identical check)."""
    _INDEX, _META, embed, record_kind = embeddings._INDEX, embeddings._META, embeddings.embed, embeddings.record_kind  # noqa: N806
    if _INDEX is None or _INDEX.ntotal == 0 or not _META:
        return []
    qvec = embed([query])
    scores, ids = _INDEX.search(qvec, min(top_k * 3, _INDEX.ntotal))
    raw = [(_META[i], float(s)) for s, i in zip(scores[0], ids[0], strict=True) if 0 <= i < len(_META)]
    if filters:
        court = (filters.get("court") or "").lower()
        ym = filters.get("year_from")
        yM = filters.get("year_to")  # noqa: N806
        case_type = (filters.get("case_type") or "").lower()

        def _ok(meta):
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


@pytest.fixture
def v1(monkeypatch):
    index = faiss.IndexFlatIP(384)
    index.add(fake_embed([m["text"] for m in V1_META]))
    monkeypatch.setattr(embeddings, "_INDEX", index)
    monkeypatch.setattr(embeddings, "_META", V1_META)
    monkeypatch.setattr(embeddings, "embed", fake_embed)
    return index


QUERIES = [("maintenance of wife", 5, None), ("contract", 2, None),
           ("maintenance", 4, {"court": "lahore", "year_from": 1990, "year_to": 2005}),
           ("maintenance", 4, {"case_type": "statute", "year_from": 1960}), ("nothing matches", 3, {})]


def test_flag_off_is_byte_identical_to_before(v1, monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", False)

    def boom(*a, **k):
        raise AssertionError("v2 must not be touched when KB_V2 is off")
    monkeypatch.setattr(index_v2, "search", boom)
    for q, k, f in QUERIES:
        now = json.dumps(embeddings.search(q, top_k=k, filters=f), sort_keys=False)
        before = json.dumps(_search_before_kb_v2(q, k, f), sort_keys=False)
        assert now.encode() == before.encode()


@pytest.fixture
def v2(v1, tmp_path, monkeypatch):
    d = write_records(tmp_path)
    index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2_meta.json", tokenizer=TOK, embed=fake_embed,
                   excluded_v1_sources=["THE SAMPLE FAMILY ACT, 1964"])
    monkeypatch.setattr(settings, "KB_V2_INDEX_PATH", str(tmp_path / "v2.faiss"))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "v2_meta.json"))
    monkeypatch.setattr(settings, "KB_V2", True)
    index_v2.reset()
    yield
    index_v2.reset()


def test_flag_on_merges_and_drops_stale_duplicates(v2):
    hits = embeddings.search("maintenance of wife divorced", top_k=6)
    sources = [h["source"] for h in hits]
    assert "THE SAMPLE FAMILY ACT, 1964" not in sources            # old OCR copy excluded
    assert "Sample Family Act, 1964" in sources
    assert [h["relevance"] for h in hits] == sorted((h["relevance"] for h in hits), reverse=True)
    v2_hits = [h for h in hits if h.get("kb") == "v2"]
    assert len({h["doc_id"] for h in v2_hits}) == len(v2_hits)     # one hit per section
    for h in v2_hits:
        for k in ("source", "source_type", "chunk_id", "text", "relevance", "section", "heading",
                  "source_tier", "source_url"):
            assert k in h
        assert embeddings.record_text(h) and embeddings.record_source(h) == h["source"]
    assert any(h["source"] == "Contract Act, 1872" or h["source"] == "Old Act" for h in hits)


def test_flag_on_filters_apply_to_v2_hits(v2):
    hits = embeddings.search("maintenance", top_k=10, filters={"year_to": 1960})
    assert all((h.get("year") or 0) <= 1960 for h in hits)
    assert not any(h.get("kb") == "v2" for h in hits)              # the 1964 Act is filtered out


def test_flag_on_without_the_v2_files_falls_back(v1, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "KB_V2_INDEX_PATH", str(tmp_path / "missing.faiss"))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "missing.json"))
    index_v2.reset()
    hits = embeddings.search("contract", top_k=2)
    assert [h["source"] for h in hits] == [h["source"] for h in _search_before_kb_v2("contract", 2)]
    index_v2.reset()


def test_passage_is_section_or_window_excerpt():
    full = "x" * 100
    assert index_v2.passage({"start": 0}, full) == full
    long = " ".join(f"w{i}" for i in range(2000))
    p = index_v2.passage({"start": 5000}, long)
    assert 1100 <= len(p) <= 1300 and p in long
