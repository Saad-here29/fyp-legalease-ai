"""kb-v2 B6: category overrides and near-empty sections kept out of faiss_v2."""

import json

import pytest

from app.core.config import settings
from app.kb import catalog, index_v2
from app.kb.records import CORPUS_SOURCE, make_records, validate
from app.kb.sectioner import Section

# --------------------------------------------------------------------------- category overrides


def test_override_file_is_documented_and_complete():
    overrides = catalog.category_overrides()
    by_title = {o["title"]: o for o in overrides}
    assert by_title["Pakistan Penal Code, 1860"]["category"] == "Criminal Laws"
    assert by_title["Code of Criminal Procedure, 1898"]["category"] == "Criminal Laws"
    assert by_title["Qanun-e-Shahadat Order, 1984"]["category"] == "Law of Evidence"
    for t in ("Muslim Family Laws Ordinance, 1961", "West Pakistan Family Courts Act, 1964",
              "West Pakistan Muslim Personal Law (Shariat) Application Act, 1962"):
        assert by_title[t]["category"] == "Family Laws"
    assert by_title["Constitution of the Islamic Republic of Pakistan, 1973"]["category"] == "Constitutional Law"
    assert all(o["reason"].strip() for o in overrides)          # a reason per line
    assert len(overrides) == 7


def rec(law, title, category=None, **kw):
    r = {"doc_id": f"legalease-corpus/{law}/s1", "title": title, "section": "1", "heading": "h",
         "text": "Some substantive text of the section, long enough to index.", "source_type": "statute",
         "jurisdiction": "Pakistan", "category": category, "year": kw.get("year", 1860), "act_number": None,
         "source": CORPUS_SOURCE, "source_tier": 2, "source_url": None, "original_file": None, "scraped_at": None,
         "content_hash": "x", "status": "current", "audience": "general"}
    return r


@pytest.fixture
def kb(tmp_path, monkeypatch):
    d = tmp_path / "kb"
    (d / "records").mkdir(parents=True)
    laws = {"pakistan-penal-code-1860": rec("pakistan-penal-code-1860", "Pakistan Penal Code, 1860"),
            "guardians-and-wards-act-1890": rec("guardians-and-wards-act-1890", "Guardians and Wards Act, 1890",
                                                category="Family Laws", year=1890),
            "constitution": rec("constitution", "Constitution of the Islamic Republic of Pakistan, 1973", year=1973),
            "unlisted-act": rec("unlisted-act", "Some Unlisted Act, 1999", year=1999)}
    for name, r in laws.items():
        (d / "records" / f"{name}.jsonl").write_text(json.dumps(r), encoding="utf-8")
    cmap = {"categories": [{"name": "Family Laws", "badge_count": 22, "listed_count": 19, "held": 19, "laws": [
        {"year": 1890, "match": {"how": "exact", "corpus": [{"title": "THE GUARDIANS AND WAR DS ACT, 1890"}]}}]}]}
    (d / "category_map.json").write_text(json.dumps(cmap), encoding="utf-8")
    monkeypatch.setattr(settings, "KB_DIR", str(d))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "none.json"))
    catalog.reset()
    yield d
    catalog.reset()


def test_laws_get_override_categories_with_their_source(kb):
    laws = {x["doc_id"]: x for x in catalog.documents()}
    assert laws["pakistan-penal-code-1860"]["category"] == "Criminal Laws"
    assert laws["pakistan-penal-code-1860"]["category_source"] == "LegalEase override"
    assert laws["constitution"]["category"] == "Constitutional Law"
    assert laws["guardians-and-wards-act-1890"]["category_source"] == "Pakistan Code listing"
    assert laws["unlisted-act"]["category"] is None and laws["unlisted-act"]["category_source"] is None
    assert [x["doc_id"] for x in catalog.documents(category="criminal laws")] == ["pakistan-penal-code-1860"]


def test_stats_count_override_categories(kb):
    s = catalog.stats()
    assert s["by_category"]["Criminal Laws"] == 1 and s["by_category"]["Constitutional Law"] == 1
    assert "Constitutional Law" in s["categories"] and "Law of Evidence" in s["categories"]


def test_old_index_titles_get_override_metadata(kb):
    m = catalog.v1_metadata("THE PAKISTAN PENAL CODE")
    assert m == {"category": "Criminal Laws", "year": 1860, "jurisdiction": "Pakistan", "source_tier": 2}
    assert catalog.v1_metadata("THE GUARDIANS AND WAR DS ACT, 1890")["source_tier"] == 1   # listing still wins
    assert catalog.v1_metadata("SOME RULES") is None


def test_filter_coverage_counts_overridden_laws(kb):
    v1 = {"THE PAKISTAN PENAL CODE", "Pakistan Penal Code", "THE GUARDIANS AND WAR DS ACT, 1890", "SOME RULES"}
    assert catalog.filter_coverage(v1, set(), kb_on=False) == {"known": 3, "total": 4}
    # with KB_V2 on: v2 laws replace their old copies; 3 of the 4 v2 laws have a category
    assert catalog.filter_coverage(v1, v1 - {"SOME RULES"}, kb_on=True) == {"known": 3, "total": 5}


def test_records_carry_category_source():
    meta = {"title": "Pakistan Penal Code, 1860", "year": 1860, "category": "Criminal Laws",
            "category_source": "LegalEase override", "act_number": None, "status": "current",
            "source": CORPUS_SOURCE, "source_tier": 2, "source_url": None, "original_file": None,
            "scraped_at": None, "jurisdiction": "Pakistan"}
    r = make_records(meta, [Section("302", "Punishment of qatl-i-amd", "Whoever commits qatl-e-amd shall be ...")])[0]
    assert r["category_source"] == "LegalEase override" and validate(r) == []


# --------------------------------------------------------------------------- near-empty sections


@pytest.mark.parametrize("section,text,why", [
    ("13", "Omitted by the Federal Laws (Revision and Declaration) Ordinance, 1981 (XXVII of 1981), s. 3 and Sch., II",
     "omitted / repealed note"),
    ("3", "[Punishment for male adult below twentyone years of age marrying a child] Omitted by the Muslim Family "
          "Laws Ordinance, 1961 (VIII of 1961), s.12", "omitted / repealed note"),
    ("16", "Rep. by A.O., 1937", "body under 40 characters"),
    ("2", "[Repealed.]", "body under 40 characters"),
    ("Schedule 1", "(See section 28) TABLE OF CONSANGUINITY", "body under 40 characters"),
    ("86", "All other documents are private", None),                       # a short real provision stays
    ("Schedule item 2", "Dower", None),                                     # schedule items are short on purpose
    ("Schedule item 9", "Omitted by Ord. 55 of 2002", "omitted / repealed note"),
    ("302", "Whoever commits qatl-e-amd shall, subject to the provisions of this Chapter be punished", None),
    ("5", "Omitted words are restored where the Court so orders and the parties consent to it in writing, and the "
          "Court shall record its reasons for doing so in the order sheet. " * 3, None),   # long text: not a note
])
def test_index_exclusion(section, text, why):
    assert index_v2.index_exclusion({"section": section, "text": text}) == why


def test_excluded_records_stay_out_of_the_index_but_are_counted(tmp_path):
    import re

    import numpy as np

    class Tok:
        def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
            spans = [m.span() for m in re.finditer(r"\w+|[^\w\s]", text)]
            out = {"input_ids": list(range(len(spans)))}
            if return_offsets_mapping:
                out["offset_mapping"] = spans
            return out

    def embed(texts):
        v = np.zeros((len(texts), 384), np.float32)
        v[:, 0] = 1.0
        return v

    meta = {"title": "Sample Act, 1900", "year": 1900, "category": None, "act_number": None, "status": "current",
            "source": CORPUS_SOURCE, "source_tier": 2, "source_url": None, "original_file": None,
            "scraped_at": None, "jurisdiction": "Pakistan"}
    recs = make_records(meta, [Section("1", "Short title", "This Act may be called the Sample Act, 1900."),
                               Section("2", "[Omitted.]", "Omitted by A.O., 1949, Schedule"),
                               Section("3", "[Repealed.]", "Rep. by the Repealing Act, 1938 (I of 1938), s.2 and Sch")])
    d = tmp_path / "records"
    d.mkdir()
    (d / "a.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    m = index_v2.build(d, tmp_path / "v2.faiss", tmp_path / "v2.json", tokenizer=Tok(), embed=embed,
                       excluded_v1_sources=[])
    data = json.loads((tmp_path / "v2.json").read_text(encoding="utf-8"))
    assert m["records"] == 3 and m["chunks"] == 1
    assert m["excluded_records"] == {"body under 40 characters": 1, "omitted / repealed note": 1}
    assert [c["section"] for c in data["chunks"]] == ["1"]
