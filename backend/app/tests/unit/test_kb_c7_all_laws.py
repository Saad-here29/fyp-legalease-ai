"""kb-v2 C7: every law at section level. Offline: a stand-in tokenizer and
embedding, and a stand-in sentence-transformers model for the Colab script."""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

from app.core.config import settings
from app.kb import catalog, index_v2

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

import build_index_v2_all  # noqa: E402
import build_records_all  # noqa: E402
import colab_embed  # noqa: E402


class WordTokenizer:
    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
        out = {"input_ids": list(range(len(spans)))}
        if return_offsets_mapping:
            out["offset_mapping"] = spans
        return out


def fake_embed(texts):
    out = np.zeros((len(texts), 384), np.float32)
    for i, t in enumerate(texts):
        for w in re.findall(r"\w+", t.lower()):
            out[i, hash(w) % 384] += 1.0
        out[i] /= max(np.linalg.norm(out[i]), 1e-9)
    return out


def rec(slug, title, sec, text):
    return {"doc_id": f"legalease-corpus/{slug}/s{sec}", "title": title, "section": sec, "heading": f"Heading {sec}",
            "text": text, "source_type": "statute", "jurisdiction": "Pakistan", "category": None, "year": 1990,
            "act_number": None, "source": "LegalEase corpus (Pakistan Code-derived; original download provenance not "
            "recorded)", "source_tier": 2, "source_url": None, "original_file": None, "scraped_at": None,
            "content_hash": "x", "status": "current", "audience": "general", "sectioned": True}


@pytest.fixture
def kb(tmp_path, monkeypatch):
    d = tmp_path / "kb"
    (d / "records").mkdir(parents=True)
    (d / "records_all").mkdir()
    (d / "records" / "core-act-1990.jsonl").write_text(
        json.dumps(rec("core-act-1990", "Core Act, 1990", "1", "The core act applies to everyone in Pakistan.")),
        encoding="utf-8")
    (d / "records_all" / "other-act-1991.jsonl").write_text("\n".join(json.dumps(rec(
        "other-act-1991", "Other Act, 1991", s, f"Section {s} of the other act says something about ports {s}."))
        for s in ("1", "2")), encoding="utf-8")
    monkeypatch.setattr(settings, "KB_DIR", str(d))
    for name in ("KB_V2_INDEX_PATH", "KB_V2_METADATA_PATH", "KB_V2_ALL_INDEX_PATH", "KB_V2_ALL_METADATA_PATH"):
        monkeypatch.setattr(settings, name, str(d / Path(getattr(settings, name)).name))
    catalog.reset()
    index_v2.reset()
    yield d
    catalog.reset()
    index_v2.reset()


# --------------------------------------------------------------------------- sectioning helpers

@pytest.mark.parametrize("title, place", [
    ("Punjab Land Revenue Act, 1967", "Punjab"), ("Sindh Arms Act, 2013", "Sindh"),
    ("N.W.F.P. Tenancy Act, 1950", "KP"), ("Khyber Pakhtunkhwa Police Act, 2017", "KP"),
    ("Islamabad Capital Territory Local Government Act, 2015", "ICT"), ("Balochistan Levies Act, 2010", "Balochistan"),
    ("West Pakistan Family Courts Act, 1964", "Pakistan"), ("Stamp Act, 1899", "Pakistan"),
])
def test_jurisdiction_from_the_title(title, place):
    assert build_records_all.jurisdiction(title) == place


def test_audience_and_title():
    assert build_records_all.audience("Hindu Marriage Act, 2017") == "Hindu"
    assert build_records_all.audience("Sikh Anand Karaj Marriage Act, 2018") == "Sikh"
    assert build_records_all.audience("Motor Vehicles Act, 1939") == "general"
    listing = {"clean_title": "Women in Distress Act, 1996 (Repealed by Act XVI of 2020)"}
    assert build_records_all.title_for("THE WOMEN IN DISTRESS ACT, 1996", "", listing) == "Women in Distress Act, 1996"
    assert build_records_all.title_for("THE MOTOR VEHICLES ACT, 1939", "This Act may be called the Motor Vehicles "
                                       "Act, 1939.", None) == "Motor Vehicles Act, 1939"
    assert build_records_all.title_for("THE CENSUS ORDINANCE , 1959", "", None) == "The Census Ordinance , 1959"


# --------------------------------------------------------------------------- index switch and build

def test_active_index_is_core_until_both_all_files_exist(kb):
    assert index_v2.active_paths()[2] == "core"
    Path(settings.KB_V2_ALL_INDEX_PATH).write_bytes(b"x")
    assert index_v2.active_paths()[2] == "core"               # half there: still the 35-law index
    Path(settings.KB_V2_ALL_METADATA_PATH).write_text("{}", encoding="utf-8")
    assert index_v2.active_paths() == (Path(settings.KB_V2_ALL_INDEX_PATH), Path(settings.KB_V2_ALL_METADATA_PATH),
                                       "all")


def test_build_from_both_folders_and_search_uses_it(kb, monkeypatch):
    pytest.importorskip("faiss")
    m = index_v2.build([kb / "records", kb / "records_all"], Path(settings.KB_V2_ALL_INDEX_PATH),
                       Path(settings.KB_V2_ALL_METADATA_PATH), tokenizer=WordTokenizer(), embed=fake_embed,
                       excluded_v1_sources=["THE OTHER ACT, 1991"], cache_dir=kb / "vector_cache")
    assert m["complete"] and m["records"] == 3 and m["laws"] == ["Core Act, 1990", "Other Act, 1991"]
    from app.ai import embeddings
    monkeypatch.setattr(embeddings, "embed", fake_embed)
    monkeypatch.setattr(embeddings, "_search_v1", lambda q, k, f=None, **kw: [
        {"source": "THE OTHER ACT, 1991", "text": "old copy", "relevance": 0.99},
        {"source": "Unrelated Act, 1950", "text": "kept", "relevance": 0.01}])
    hits = index_v2.search("other act ports", 5)
    sources = [h["source"] for h in hits]
    assert "Other Act, 1991" in sources and "THE OTHER ACT, 1991" not in sources and "Unrelated Act, 1950" in sources


def test_catalog_lists_sectioned_corpus_laws(kb):
    st = catalog.stats()
    assert st["laws"] == 2 and st["laws_by_set"] == {"core": 1, "corpus": 1, "scraped": 0}
    assert st["section_index"] == "core"
    law = catalog.public_law(catalog.law("other-act-1991"))
    assert law["set"] == "corpus" and law["sections"] == 2


def test_health_reports_the_active_section_index(kb, client, monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    assert client.get("/health").json()["v2_index"] == "core"
    monkeypatch.setattr(settings, "KB_V2", False)
    assert client.get("/health").json()["v2_index"] is None


# --------------------------------------------------------------------------- export and Colab round trip

def test_export_writes_only_chunks_without_a_vector(kb, monkeypatch, tmp_path):
    monkeypatch.setattr(build_index_v2_all, "KB", kb)
    monkeypatch.setattr(build_index_v2_all, "DIRS", [kb / "records", kb / "records_all"])
    out = tmp_path / "chunks.jsonl"
    info = build_index_v2_all.export_chunks(out, WordTokenizer(), None)
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert info["chunks"] == 3 and info["to_embed"] == 3 and len(rows) == 3
    assert all(r["key"] == index_v2.vector_key(r["text"]) for r in rows)
    cache = index_v2.VectorCache(kb / "vector_cache")
    cache.add([rows[0]["key"]], fake_embed([rows[0]["text"]]))
    info = build_index_v2_all.export_chunks(out, WordTokenizer(), None)
    assert info["to_embed"] == 2 and info["already_cached"] == 1
    assert build_index_v2_all.export_chunks(out, WordTokenizer(), 1)["exported"] == 1


class StubModel:
    def __init__(self, name, device=None):
        self.name = name

    def encode(self, texts, **kw):
        assert kw.get("normalize_embeddings") is True
        return fake_embed(texts)


def test_colab_script_writes_the_cache_format(kb, monkeypatch, tmp_path):
    assert colab_embed.MODEL == settings.EMBEDDING_MODEL_NAME            # the key depends on it
    import sentence_transformers
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", StubModel)
    monkeypatch.setattr(colab_embed, "SHARD", 2)
    chunks = tmp_path / "chunks.jsonl"
    texts = ["Core Act s.1 text", "Other Act s.1 text", "Other Act s.2 text"]
    chunks.write_text("\n".join(json.dumps({"key": index_v2.vector_key(t), "text": t}) for t in texts),
                      encoding="utf-8")
    written = colab_embed.main([str(chunks), str(tmp_path / "out"), "--device", "cpu", "--no-zip"])
    assert len(written) == 2 and all(Path(p).name.startswith("colab_") for p in written)    # 2 shards of <= 2
    cache = index_v2.VectorCache(tmp_path / "out")                     # the builder's own loader
    assert set(cache.vecs) == {index_v2.vector_key(t) for t in texts}
    v = cache.vecs[index_v2.vector_key(texts[0])]
    assert v.dtype == np.float32 and v.shape == (384,) and np.allclose(v, fake_embed([texts[0]])[0])


def test_colab_script_refuses_keys_that_dont_match(tmp_path, monkeypatch):
    import sentence_transformers
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer", StubModel)
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps({"key": "0" * 64, "text": "edited text"}), encoding="utf-8")
    with pytest.raises(SystemExit, match="keys don't match"):
        colab_embed.main([str(bad), str(tmp_path / "out"), "--device", "cpu", "--no-zip"])
