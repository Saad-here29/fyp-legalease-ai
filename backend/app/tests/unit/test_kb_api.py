"""kb-v2 B4: /api/v1/kb endpoints, Research knowledge-base filters, chat citation extras."""

import json
from types import SimpleNamespace

import pytest

from app.api.v1.chat import CitationRef
from app.core.config import settings
from app.kb import catalog
from app.main import app
from app.middlewares.auth import get_current_user
from app.services import research_service
from app.services.legal_chat_service import citation_extras

API = settings.API_V1_PREFIX + "/kb"


def rec(law, sec, heading, text, **kw):
    base = {"doc_id": f"legalease-corpus/{law}/s{sec}", "title": kw.pop("title"), "section": sec,
            "heading": heading, "text": text, "source_type": "statute", "jurisdiction": "Pakistan",
            "category": kw.pop("category", None), "year": kw.pop("year"), "act_number": None,
            "source": kw.pop("source", "LegalEase corpus (Pakistan Code-derived; original download provenance not "
                                       "recorded)"),
            "source_tier": kw.pop("tier", 2), "source_url": None, "original_file": kw.pop("original", None),
            "scraped_at": None, "content_hash": "x", "status": kw.pop("status", "current"),
            "audience": "general", "sectioned": True}
    return {**base, **kw}


@pytest.fixture
def kb(tmp_path, monkeypatch):
    d = tmp_path / "kb"
    (d / "records").mkdir(parents=True)
    (d / "raw").mkdir()
    (d / "raw" / "gwa.pdf").write_bytes(b"%PDF-1.4 fake")
    (tmp_path / "secret.pdf").write_bytes(b"%PDF secret outside raw")
    laws = {
        "guardians-and-wards-act-1890": [
            rec("guardians-and-wards-act-1890", "17", "Matters to be considered by the Court in appointing guardian",
                "(1) In appointing or declaring the guardian of a minor, the Court shall ... welfare of the minor.",
                title="Guardians and Wards Act, 1890", year=1890, category="Family Laws", tier=1,
                source="user-supplied PDF", original="backend/storage/kb/raw/gwa.pdf", status="under_review"),
            rec("guardians-and-wards-act-1890", "25", "Title of guardian to custody of ward", "If a ward leaves ...",
                title="Guardians and Wards Act, 1890", year=1890, category="Family Laws", tier=1,
                source="user-supplied PDF", original="backend/storage/kb/raw/gwa.pdf", status="under_review"),
        ],
        "pakistan-penal-code-1860": [
            rec("pakistan-penal-code-1860", "302", "Punishment of qatl-i-amd", "Whoever commits qatl-e-amd ...",
                title="Pakistan Penal Code, 1860", year=1860),
        ],
        "escape-one": [rec("escape-one", "1", "x", "t", title="Escape One Act, 1900", year=1900,
                           original="../../secret.pdf")],
        "escape-two": [rec("escape-two", "1", "x", "t", title="Escape Two Act, 1901", year=1901,
                           original=str(tmp_path / "secret.pdf"))],
    }
    for name, recs in laws.items():
        (d / "records" / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    cmap = {"categories": [
        {"name": "Family Laws", "badge_count": 22, "listed_count": 19, "held": 19, "laws": [
            {"year": 1890, "match": {"how": "exact", "corpus": [{"title": "THE GUARDIANS AND WAR DS ACT, 1890"}]}}]},
        {"name": "Civil Laws", "badge_count": 147, "listed_count": 100, "held": 95, "laws": [
            {"year": 1872, "match": {"how": "exact", "corpus": [{"title": "THE CONTRACT ACT, 1872"}]}},
            {"year": 1999, "match": {"how": "possible", "corpus": [{"title": "Maybe Act"}]}}]},
    ]}
    (d / "category_map.json").write_text(json.dumps(cmap), encoding="utf-8")
    monkeypatch.setattr(settings, "KB_DIR", str(d))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "missing_meta.json"))
    catalog.reset()
    yield {"dir": d, "laws": laws, "tmp": tmp_path}
    catalog.reset()


@pytest.fixture
def authed(client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="u1", role="student")
    yield client
    app.dependency_overrides.pop(get_current_user, None)


ENDPOINTS = ["/stats", "/documents", "/documents/pakistan-penal-code-1860",
             "/documents/pakistan-penal-code-1860/sections", "/documents/pakistan-penal-code-1860/download",
             "/documents/guardians-and-wards-act-1890/original", "/records/legalease-corpus/pakistan-penal-code-1860/s302"]


@pytest.mark.parametrize("path", ENDPOINTS)
def test_every_endpoint_needs_a_login(kb, client, path):
    assert client.get(API + path).status_code == 401


def test_stats(kb, authed):
    s = authed.get(API + "/stats").json()
    assert s["laws"] == 4 and s["section_records"] == 5
    assert s["by_category"]["Family Laws"] == 1 and s["by_source_tier"]["2"] == 3
    assert s["jurisdictions"] == ["Pakistan"]
    # listing categories plus the hand-written override categories (B6)
    assert s["categories"] == ["Civil Laws", "Constitutional Law", "Criminal Laws", "Family Laws", "Law of Evidence"]
    assert s["by_category"]["Criminal Laws"] == 1          # PPC via its override
    c = s["coverage"]
    assert (c["held"], c["listed"], c["site_badge_total"], c["not_listed"]) == (114, 119, 169, 50)
    assert "counted there but not listed" in c["note"]


def test_documents_and_filters(kb, authed):
    all_ = authed.get(API + "/documents").json()
    assert all_["total"] == 4
    g = next(x for x in all_["documents"] if x["doc_id"] == "guardians-and-wards-act-1890")
    assert g["sections"] == 2 and g["source_label"] == "user-supplied PDF - source URL to be confirmed"
    assert g["has_original"] is True and "original_file" not in g
    p = next(x for x in all_["documents"] if x["doc_id"] == "pakistan-penal-code-1860")
    assert p["source_label"] == "LegalEase corpus (Pakistan Code-derived)" and p["has_original"] is False

    def ids(**params):
        return [x["doc_id"] for x in authed.get(API + "/documents", params=params).json()["documents"]]
    assert ids(q="penal code") == ["pakistan-penal-code-1860"]
    assert ids(category="family laws") == ["guardians-and-wards-act-1890"]
    assert ids(tier=1) == ["guardians-and-wards-act-1890"]
    assert ids(year=1860) == ["pakistan-penal-code-1860"]
    assert ids(status="under_review") == ["guardians-and-wards-act-1890"]
    assert ids(jurisdiction="Sindh") == []
    assert authed.get(API + "/documents", params={"tier": 9}).status_code == 422


def test_sections_record_and_download(kb, authed):
    s = authed.get(API + "/documents/guardians-and-wards-act-1890/sections").json()
    assert [x["section"] for x in s["sections"]] == ["17", "25"]
    assert s["sections"][0]["id"] == "legalease-corpus/guardians-and-wards-act-1890/s17"
    assert s["sections"][0]["preview"].startswith("(1) In appointing")
    r = authed.get(API + "/records/legalease-corpus/guardians-and-wards-act-1890/s17").json()
    assert r == kb["laws"]["guardians-and-wards-act-1890"][0]                  # exactly the stored record
    dl = authed.get(API + "/documents/guardians-and-wards-act-1890/download")
    assert dl.status_code == 200 and "attachment" in dl.headers["content-disposition"]
    assert "guardians-and-wards-act-1890.json" in dl.headers["content-disposition"]
    assert json.loads(dl.content) == kb["laws"]["guardians-and-wards-act-1890"]


@pytest.mark.parametrize("path", ["/documents/nope", "/documents/nope/sections", "/documents/nope/download",
                                  "/documents/nope/original", "/records/legalease-corpus/nope/s1",
                                  "/records/nope"])
def test_unknown_ids_are_404(kb, authed, path):
    assert authed.get(API + path).status_code == 404


def test_original_is_served_only_from_raw(kb, authed):
    ok = authed.get(API + "/documents/guardians-and-wards-act-1890/original")
    assert ok.status_code == 200 and ok.content == b"%PDF-1.4 fake"
    assert ok.headers["content-type"] == "application/pdf"
    assert authed.get(API + "/documents/pakistan-penal-code-1860/original").status_code == 404   # none saved
    # a record whose original_file points outside raw/ (relative or absolute) never escapes
    assert authed.get(API + "/documents/escape-one/original").status_code == 404
    assert authed.get(API + "/documents/escape-two/original").status_code == 404


@pytest.mark.parametrize("path", ["/documents/..%2F..%2Fsecret/original", "/documents/%2E%2E/original",
                                  "/documents/..%5C..%5Csecret.pdf/original", "/documents/C:%5Csecret.pdf/original",
                                  "/documents/%2Fetc%2Fpasswd/original"])
def test_client_paths_cannot_escape(kb, authed, path):
    r = authed.get(API + path)
    assert r.status_code in (404, 405) and b"secret" not in r.content


def test_original_path_never_leaves_raw(kb):
    raw = (kb["dir"] / "raw").resolve()
    for law_id in ("guardians-and-wards-act-1890", "escape-one", "escape-two", "../escape-one", "/etc/passwd"):
        p = catalog.original_path(law_id)
        assert p is None or p.parent == raw


# --------------------------------------------------------------------------- research filters

V2_HIT = {"source": "Guardians and Wards Act, 1890", "kb": "v2", "doc_id": "legalease-corpus/guardians-and-wards-act-1890/s17",
          "section": "17", "heading": "Matters", "category": "Family Laws", "year": 1890, "jurisdiction": "Pakistan",
          "source_tier": 1, "source_url": None, "text": "In appointing a guardian", "relevance": 0.8, "chunk_id": 1}
V1_KNOWN = {"source": "THE CONTRACT ACT, 1872", "source_type": "statute", "chunk_id": 5, "text": "Contract text",
            "relevance": 0.7}
V1_UNKNOWN = {"source": "SOME RULES 1990", "source_type": "statute", "chunk_id": 9, "text": "Rules text",
              "relevance": 0.75}


@pytest.fixture
def research(kb, monkeypatch):
    calls = []

    def fake_search(query, top_k, filters=None):
        calls.append((query, top_k, filters))
        return [dict(h) for h in (V2_HIT, V1_UNKNOWN, V1_KNOWN)][:top_k]
    monkeypatch.setattr(research_service.embeddings, "search", fake_search)
    monkeypatch.setattr(research_service.embeddings, "build_or_load", lambda db=None: 1)
    monkeypatch.setattr(research_service, "rewrite_for_search", lambda q: q)
    return calls


def test_v1_metadata_comes_from_category_map(kb):
    assert catalog.v1_metadata("THE CONTRACT ACT, 1872") == {"category": "Civil Laws", "year": 1872,
                                                            "jurisdiction": "Pakistan", "source_tier": 1}
    assert catalog.v1_metadata("Maybe Act") is None              # 'possible' matches don't count
    assert catalog.v1_metadata("SOME RULES 1990") is None


def test_no_filters_keeps_every_result(research):
    out = research_service.ResearchService(None).search("q", top_k=3)
    assert [r.title for r in out] == ["Guardians and Wards Act, 1890", "SOME RULES 1990", "THE CONTRACT ACT, 1872"]
    g = out[0]
    assert (g.section, g.heading, g.source_tier, g.kb_law_id) == ("17", "Matters", 1, "guardians-and-wards-act-1890")
    assert g.kb_record_id == V2_HIT["doc_id"]
    assert out[2].category == "Civil Laws" and out[2].year == 1872 and out[2].kb_record_id is None


@pytest.mark.parametrize("filters,expected", [
    ({"category": "Civil Laws"}, ["THE CONTRACT ACT, 1872"]),
    ({"source_tier": 1}, ["Guardians and Wards Act, 1890", "THE CONTRACT ACT, 1872"]),
    ({"jurisdiction": "Pakistan"}, ["Guardians and Wards Act, 1890", "THE CONTRACT ACT, 1872"]),
    ({"year_from": 1880, "year_to": 1900}, ["Guardians and Wards Act, 1890"]),
    ({"year_from": 2000}, []),
    ({"category": "Tax Laws"}, []),
])
def test_filters_drop_unknown_metadata_and_mismatches(research, filters, expected):
    out = research_service.ResearchService(None).search("q", top_k=10, **filters)
    assert [r.title for r in out] == expected                   # SOME RULES (no metadata) never passes a filter


def test_filter_coverage_counts(kb, monkeypatch):
    monkeypatch.setattr(research_service.embeddings, "build_or_load", lambda db=None: 4)
    monkeypatch.setattr(research_service.embeddings, "_META", [
        {"source": "THE CONTRACT ACT, 1872"}, {"source": "THE CONTRACT ACT, 1872"}, {"source": "SOME RULES 1990"},
        {"source": "THE GUARDIANS AND WAR DS ACT, 1890"}])
    monkeypatch.setattr(settings, "KB_V2", False)
    assert research_service.filter_coverage() == {"known": 2, "total": 3}


def test_search_endpoint_reports_filters(kb, authed, research):
    r = authed.post(settings.API_V1_PREFIX + "/research/search",
                    json={"query": "guardian", "category": "Family Laws", "year_from": 1800, "year_to": 1950})
    body = r.json()
    assert r.status_code == 200 and body["filters_active"] is True
    assert [x["title"] for x in body["results"]] == ["Guardians and Wards Act, 1890"]
    assert body["filter_coverage"]["total"] >= body["filter_coverage"]["known"]
    plain = authed.post(settings.API_V1_PREFIX + "/research/search", json={"query": "guardian"}).json()
    assert plain["filters_active"] is False and plain["filter_coverage"] is None


# --------------------------------------------------------------------------- chat citations

def test_chat_citations_unchanged_for_v1_passages():
    assert citation_extras({"source": "X", "text": "t", "relevance": 0.7}) == {}
    before = CitationRef(n=1, source="X", excerpt="e").model_dump_json()
    assert before == '{"n":1,"source":"X","excerpt":"e"}'


def test_chat_citations_carry_section_for_v2_passages():
    extras = citation_extras(V2_HIT)
    assert extras == {"section": "17", "heading": "Matters", "doc_id": V2_HIT["doc_id"]}   # source_url None dropped
    ref = CitationRef(n=1, source="Guardians and Wards Act, 1890", excerpt="e", **extras)
    assert json.loads(ref.model_dump_json())["section"] == "17"
