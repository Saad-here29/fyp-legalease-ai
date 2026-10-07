"""kb-v2 C8: hybrid retrieval (BM25 + vectors, reciprocal rank fusion). Offline."""

import json
import re
from pathlib import Path

import numpy as np
import pytest

from app.core.config import settings
from app.kb import index_v2, lexical


def test_tokens_terms_and_section_numbers():
    q = lexical.query_tokens("What is murder under Section 302 of the Pakistan Penal Code?")
    assert "murder" in q and "qatl" in q and "sec302" in q and "of" not in q and "pakistan" not in q
    assert lexical.query_tokens("Article 25-A and s. 10A")[-2:] == ["sec25a", "sec10a"]
    assert lexical.section_token("302") == ["sec302"] and lexical.section_token("Schedule item 2") == []
    assert lexical.stem("liabilities") == "liability" and lexical.stem("witnesses") == "witnesse" \
        and lexical.stem("class") == "class"


def test_terms_glossary_has_no_question_text():
    # The glossary is single words (terms of art <-> English), never a phrase from a test question.
    assert all(" " not in k and all(" " not in v for v in vs) for k, vs in lexical.TERMS.items())


def test_bm25_ranks_heading_matches_first():
    bm = lexical.BM25()
    bm.add("cpc/s11", [("RES JUDICATA", 3), ("Code of Civil Procedure", 1), ("No court shall try any suit ...", 1)],
           extra=lexical.section_token("11"))
    bm.add("cpc/s10", [("Stay of suit", 3), ("Code of Civil Procedure", 1), ("No court shall proceed ...", 1)],
           extra=lexical.section_token("10"))
    assert bm.search(lexical.query_tokens("What is res judicata?"))[0][0] == "cpc/s11"
    assert bm.search(lexical.query_tokens("explain section 10"))[0][0] == "cpc/s10"
    assert bm.search(["nothing"]) == []


def test_rrf_rewards_agreement():
    fused = lexical.rrf([["a", "b", "c"], ["c", "a"]])
    assert sorted(fused, key=lambda k: -fused[k]) == ["a", "c", "b"]


# --------------------------------------------------------------------------- end to end with a tiny index

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


def rec(sec, heading, text):
    return {"doc_id": f"legalease-corpus/code-of-civil-procedure-1908/s{sec}", "title": "Code of Civil Procedure, 1908",
            "section": sec, "heading": heading, "text": text, "source_type": "statute", "jurisdiction": "Pakistan",
            "category": None, "year": 1908, "act_number": None, "source": "LegalEase corpus", "source_tier": 1,
            "source_url": None, "original_file": None, "scraped_at": None, "content_hash": "x", "status": "current",
            "audience": "general", "sectioned": True}


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    pytest.importorskip("faiss")
    d = tmp_path / "records"
    d.mkdir()
    recs = [rec("11", "Res judicata", "No court shall try any suit in which the matter directly and substantially "
                                      "in issue has been heard and finally decided by a competent court."),
            rec("10", "Stay of suit", "No court shall proceed with the trial of any suit in which the matter in issue "
                                      "is also directly in issue in a previously instituted suit."),
            rec("96", "Appeal from original decree", "An appeal shall lie from every decree passed by any court.")]
    (d / "cpc.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    monkeypatch.setattr(settings, "KB_V2_INDEX_PATH", str(tmp_path / "v2.faiss"))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "v2.json"))
    monkeypatch.setattr(settings, "KB_V2_ALL_INDEX_PATH", str(tmp_path / "none.faiss"))
    index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=WordTokenizer(), embed=fake_embed,
                   excluded_v1_sources=[], cache_dir=tmp_path / "cache")
    from app.ai import embeddings
    monkeypatch.setattr(embeddings, "embed", fake_embed)
    monkeypatch.setattr(embeddings, "_search_v1", lambda q, k, f=None, **kw: [])
    monkeypatch.setattr(settings, "HYBRID_MIN_COSINE", 0.0)
    index_v2.reset()
    yield
    index_v2.reset()


def test_hybrid_puts_the_heading_match_first(tiny, monkeypatch):
    q = "res judicata explained"
    monkeypatch.setattr(settings, "HYBRID_SEARCH", True)
    on = index_v2.search(q, 3)
    assert on[0]["section"] == "11"
    assert all(0.0 <= h["relevance"] <= 1.0001 for h in on)               # relevance stays the cosine score
    monkeypatch.setattr(settings, "HYBRID_SEARCH", False)
    off = index_v2.search(q, 3)                                          # off: plain score order, as before
    assert [h["relevance"] for h in off] == sorted((h["relevance"] for h in off), reverse=True)


def test_lexical_only_match_needs_the_minimum_cosine(tiny, monkeypatch):
    monkeypatch.setattr(settings, "HYBRID_SEARCH", True)
    monkeypatch.setattr(settings, "HYBRID_MIN_COSINE", 0.99)
    hits = index_v2.search("appeal", 3)
    assert all(h["relevance"] < 0.99 or h["section"] == "96" for h in hits)
    assert Path(settings.KB_V2_INDEX_PATH).exists()


# --------------------------------------------------------------------------- hints (C8 rules)

ROOT = Path(__file__).resolve().parents[4]
HINTS_FILE = ROOT / "backend" / "storage" / "kb" / "query_hints.json"


def _eval_questions() -> list[str]:
    import sys
    sys.path.insert(0, str(ROOT / "scripts" / "kb"))
    from compare_kb_v2 import FAMILY, GOLD, OFF_TOPIC
    from eval_query_hints import FAMILY10
    data = json.loads((ROOT / "docs" / "eval" / "c8_questions.json").read_text(encoding="utf-8"))
    return ([q for _i, q, _a in GOLD + FAMILY10] + [q for _i, q, _a in FAMILY] + [q for _i, q in OFF_TOPIC]
            + [x["q"] for x in data["live"] + data["unseen"]])


def _trigrams(text: str) -> set[tuple[str, ...]]:
    w = re.findall(r"[a-z]+", text.lower())
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def test_no_hint_contains_a_test_phrase():
    questions = set().union(*(_trigrams(q) for q in _eval_questions()))
    data = json.loads(HINTS_FILE.read_text(encoding="utf-8"))
    for h in data["hints"]:
        text = " ".join([h.get("terms", "")] + [" ".join(t) for t in h["triggers"]])
        shared = _trigrams(text) & questions
        assert not shared, (h["id"], shared)
        assert all(isinstance(t, list) and len(t) <= 2 for t in h["triggers"]), h["id"]


def test_every_exact_section_is_in_the_records(monkeypatch):
    from app.kb import catalog, query_hints
    monkeypatch.setattr(settings, "QUERY_HINTS_PATH", str(HINTS_FILE))
    monkeypatch.setattr(settings, "KB_DIR", str(ROOT / "backend" / "storage" / "kb"))
    catalog.reset()
    query_hints.reset()
    data = json.loads(HINTS_FILE.read_text(encoding="utf-8"))
    if not (ROOT / "backend" / "storage" / "kb" / "records").exists():
        pytest.skip("knowledge-base records not built here")
    for h, raw in zip(query_hints.hints(), data["hints"], strict=True):
        assert len(h["doc_ids"]) == len(raw["exact_sections"]), h["id"]
    assert query_hints.exact_doc_ids("talaq notice") == ["legalease-corpus/muslim-family-laws-ordinance-1961/s7"]
    query_hints.reset()
    catalog.reset()


def test_hint_sections_join_the_ranking(tiny, monkeypatch):
    monkeypatch.setattr(settings, "HYBRID_SEARCH", True)
    rid = "legalease-corpus/code-of-civil-procedure-1908/s96"
    plain = index_v2.search("matter in issue", 3)
    hinted = index_v2.search("matter in issue", 3, hint_ids=[rid])
    rank = [h["doc_id"] for h in hinted].index(rid)
    assert rid in [h["doc_id"] for h in hinted] and (rid not in [h["doc_id"] for h in plain]
                                                    or rank <= [h["doc_id"] for h in plain].index(rid))
