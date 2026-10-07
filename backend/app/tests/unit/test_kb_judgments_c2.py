"""kb-v2 C2: judgments in Research, Chat and the Knowledge Base (offline).

A 4-dimensional stand-in index (scores set by hand) and a stand-in
embedding; no model calls."""

import json
import math
import os
from types import SimpleNamespace

import numpy as np
import pytest

from app.ai import embeddings
from app.ai.citation_check import check_citations
from app.api.v1.chat import ChatMessageResponse
from app.core.config import settings
from app.core.security import hash_password
from app.kb import judgment_catalog, judgment_search
from app.kb import judgments as jd
from app.main import app
from app.middlewares.auth import get_current_user
from app.models.enums import UserRole
from app.models.user import User
from app.services import legal_chat_service as chat
from app.services import research_service

faiss = pytest.importorskip("faiss")
API = settings.API_V1_PREFIX
SC = "Supreme Court of Pakistan"


def _rec(doc, name, court, year, number, paras, topics, *, exclude=None, chars=9000, judges=("A. Judge",)):
    return {"doc_id": doc, "case_name": name, "court": court, "year": year, "judges": list(judges),
            "case_number": number, "citation": None, "topics": topics, "source_type": "case_law",
            "source": "test", "source_tier": 2, "source_url": None,
            "original_file": f"E:/secret/folder/{doc.rsplit('/', 1)[-1]}.txt", "file_sha256": "f" * 64,
            "content_hash": "c" * 64, "provenance_note": jd.PROVENANCE, "status": "staged",
            "quality": {"chars": chars, "exclude": exclude}, "report_citations_seen": [],
            "paragraphs": [{"n": n, "text": t} for n, t in paras]}


R1 = _rec("judgment/a/r1", "Ibrahim Khan v. Mst. Saima Khan", SC, 2024, "Civil Petition No. 4657 of 2022",
          [(1, "Heading."), (2, "Khula is a right of the wife to seek dissolution."), (3, "Petition dismissed.")],
          ["family", "khula"])
R2 = _rec("judgment/a/r2", "…Petitioner v. Station House Officer", SC, 2023, "Civil Petition No. 3718 of 2023",
          [(27, "The welfare of the minor decides custody.")], ["custody"])
R3 = _rec("judgment/a/r3", "Shaista Habib v. Muhammad Arif Habib", "Lahore High Court", 2023, "W.P. 16 of 2023",
          [(16, "Custody of the minor daughter."), (17, "Other matters.")], ["custody", "family"])
R4 = _rec("judgment/a/r4", "Empty Case v. Nobody", SC, 2020, "C.P. 1 of 2020", [(1, "x")], [],
          exclude="near-empty")
R5 = _rec("judgment/b/r5", None, None, 2024, "C.P. 4657 of 2022", [(1, "Same judgment, other dataset.")],
          ["khula"], chars=500)                 # same case number and year as R1, less metadata

# (record, paragraph, score against the query vector)
CHUNKS = [(R1, 1, 0.60), (R1, 2, 0.80), (R2, 27, 0.70), (R3, 16, 0.52), (R3, 17, 0.45)]


def _vec(score):
    return [score, math.sqrt(1 - score * score), 0.0, 0.0]


def write_index(path, chunks):
    index = faiss.IndexFlatIP(4)
    if chunks:
        index.add(np.array([_vec(s) for _r, _n, s in chunks], dtype=np.float32))
    faiss.write_index(index, str(path))
    meta = [{"doc_id": r["doc_id"], "para": n, "window": 1, "case_name": r["case_name"], "court": r["court"],
             "year": r["year"], "topics": r["topics"], "source_type": "case_law", "source_tier": 2,
             "chunk_text": f"{jd.chunk_prefix(r, n)} " + next(t for k, t in
                                                              [(p['n'], p['text']) for p in r['paragraphs']] if k == n)}
            for r, n, _s in chunks]
    path.with_name(path.stem + "_meta.json").write_text(json.dumps({"manifest": {}, "chunks": meta}),
                                                        encoding="utf-8")


@pytest.fixture
def jx(tmp_path, monkeypatch):
    kb = tmp_path / "kb"
    recs = kb / "judgments" / "records"
    recs.mkdir(parents=True)
    (recs / "a.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in (R1, R2, R3, R4)) + "\n",
                                  encoding="utf-8")
    (recs / "b.jsonl").write_text(json.dumps(R5) + "\n", encoding="utf-8")
    idx = kb / "faiss_judgments_dev.faiss"
    write_index(idx, CHUNKS)
    monkeypatch.setattr(settings, "KB_DIR", str(kb))
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    monkeypatch.setattr(settings, "JUDGMENTS_INDEX_PATH", str(idx))
    monkeypatch.setattr(settings, "JUDGMENTS_METADATA_PATH", "")
    monkeypatch.setattr(embeddings, "embed", lambda texts: np.array([[1, 0, 0, 0]] * len(texts), dtype=np.float32))
    judgment_search.reset()
    judgment_catalog.reset()
    yield SimpleNamespace(dir=kb, index=idx)
    judgment_search.reset()
    judgment_catalog.reset()


@pytest.fixture
def authed(client):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="u1", role="student")
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# --------------------------------------------------------------------------- names

@pytest.mark.parametrize("name, shown", [
    ("Ibrahim Khan v. Mst. Saima Khan", "Ibrahim Khan v. Mst. Saima Khan"),
    (None, "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("…Petitioner v. Station House Officer", "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("...Petitioner v. X", "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("Petitioner in both v. Muhammad Ghazanfar Khan", "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("A v. B", "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),                      # under 8 characters
    ("Khan and others v. Federation of Pakistan [2017 SCMR 2066]",                      # a cited precedent
     "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("(APUBTA) through its President. … Petitioner v. The Federation of Pakistan",      # real dev-index names
     "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("(In both cases) … Petitioner v. Salman Akram Raja and others", "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("1 Shaukat Aziz Siddiqui v. Federation of Pakistan and others (Const.P.No.76 of 2018 decided on",  # footnote
     "C.P. 9 of 2020 (Supreme Court of Pakistan, 2020)"),
    ("Sohail Ahmed (in both cases) v. Mst. Samreena Rasheed Memon", "Sohail Ahmed (in both cases) v. Mst. Samreena Rasheed Memon"),
])
def test_display_name_fallback(name, shown):
    assert jd.display_name({"case_name": name, "court": SC, "year": 2020, "case_number": "C.P. 9 of 2020"}) == shown


def test_display_name_without_a_case_number_and_the_shown_prefix():
    assert jd.display_name({"case_name": None, "court": SC, "year": 2021}) == f"Judgment ({SC}, 2021)"
    assert jd.display_name({"case_name": "", "court": None, "year": None}) == "Judgment"
    weak = {"case_name": "…Petitioner v. SHO", "court": SC, "year": 2023, "case_number": "C.P. 3718 of 2023"}
    assert jd.shown_prefix(weak, 27) == f"C.P. 3718 of 2023 ({SC}, 2023) - para 27:"      # court/year not repeated
    good = {"case_name": "Ibrahim Khan v. Saima", "court": SC, "year": 2024}
    assert jd.shown_prefix(good, 7) == f"Ibrahim Khan v. Saima ({SC}, 2024) - para 7:"
    # the indexed chunk text keeps the old prefix (vectors already built stay valid)
    assert jd.chunk_prefix(weak, 27).startswith("…Petitioner v. SHO")


# --------------------------------------------------------------------------- search

def test_search_keeps_the_best_paragraph_per_judgment(jx):
    hits = judgment_search.search("khula")
    assert [(h["doc_id"], h["paragraph"], h["score"]) for h in hits] == [
        ("judgment/a/r1", 2, 0.8), ("judgment/a/r2", 27, 0.7), ("judgment/a/r3", 16, 0.52)]   # 0.45 para dropped
    h1, h2 = hits[0], hits[1]
    assert h1["display_name"] == "Ibrahim Khan v. Mst. Saima Khan" and h1["court"] == SC and h1["year"] == 2024
    assert h1["case_number"] == "Civil Petition No. 4657 of 2022"             # from the record, not the index
    assert h1["text"] == "Khula is a right of the wife to seek dissolution."   # the indexed prefix is stripped
    assert h1["paragraph_text"] == h1["text"]
    assert h2["display_name"] == f"Civil Petition No. 3718 of 2023 ({SC}, 2023)"
    assert h2["prefix"] == f"Civil Petition No. 3718 of 2023 ({SC}, 2023) - para 27:"
    assert set(h1) == {"doc_id", "display_name", "case_name", "court", "year", "case_number", "paragraph",
                       "text", "paragraph_text", "prefix", "score", "topics"}


def test_search_minimum_score_top_k_and_filters(jx, monkeypatch):
    assert [h["doc_id"] for h in judgment_search.search("q", min_score=0.55)] == ["judgment/a/r1", "judgment/a/r2"]
    assert len(judgment_search.search("q", top_k=1)) == 1
    monkeypatch.setattr(settings, "JUDGMENTS_MIN_SCORE", 0.75)                 # configurable
    assert [h["doc_id"] for h in judgment_search.search("q")] == ["judgment/a/r1"]
    monkeypatch.setattr(settings, "JUDGMENTS_MIN_SCORE", 0.50)
    assert [h["doc_id"] for h in judgment_search.search("q", year_from=2024)] == ["judgment/a/r1"]
    assert [h["doc_id"] for h in judgment_search.search("q", year_to=2023)] == ["judgment/a/r2", "judgment/a/r3"]
    assert [h["doc_id"] for h in judgment_search.search("q", court="lahore")] == ["judgment/a/r3"]
    assert judgment_search.search("   ") == []


def test_health_reports_the_judgments_index(jx, client):
    body = client.get("/health").json()
    assert body["judgments_v2"] is True and body["judgment_chunks"] == 5 and body["judgments"] == 3


def test_missing_or_half_written_index_returns_nothing(jx, client):
    meta = jx.index.with_name(jx.index.stem + "_meta.json")
    good = meta.read_text(encoding="utf-8")
    meta.unlink()                                                             # build still writing
    assert judgment_search.search("q") == [] and judgment_search.status() == {"judgment_chunks": 0, "judgments": 0}
    assert client.get("/health").status_code == 200
    meta.write_text('{"manifest": {}, "chunks": [', encoding="utf-8")        # truncated
    assert judgment_search.search("q") == []
    meta.write_text(json.dumps({"manifest": {}, "chunks": json.loads(good)["chunks"][:2]}), encoding="utf-8")
    assert judgment_search.search("q") == []                                  # 5 vectors, 2 chunks: not a pair
    jx.index.write_bytes(b"not an index")
    assert judgment_search.search("q") == []
    write_index(jx.index, CHUNKS)                                             # the build finishes
    assert len(judgment_search.search("q")) == 3


def test_index_is_reloaded_when_the_file_changes(jx):
    assert len(judgment_search.search("q")) == 3
    write_index(jx.index, [(R3, 16, 0.90)])
    st = jx.index.stat()
    os.utime(jx.index, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    hits = judgment_search.search("q")
    assert [(h["doc_id"], h["score"]) for h in hits] == [("judgment/a/r3", 0.9)]
    assert judgment_search.status() == {"judgment_chunks": 1, "judgments": 1}


# --------------------------------------------------------------------------- endpoints

def test_judgments_list(jx, authed):
    body = authed.get(f"{API}/kb/judgments").json()
    assert body["counts"]["judgments"] == 3                  # R4 excluded, R5 is R1 from another dataset
    assert body["counts"]["indexed"] == 3 and body["counts"]["judgment_chunks"] == 5
    assert body["counts"]["excluded"] == {"near-empty": 1}
    assert body["courts"] == {SC: 2, "Lahore High Court": 1}
    assert body["years"]["min"] == 2023 and body["years"]["max"] == 2024
    assert body["topics"]["custody"] == 2
    assert body["total"] == 3 and [j["doc_id"] for j in body["judgments"]][0] == "judgment/a/r1"   # newest first
    row = body["judgments"][0]
    assert set(row) == set(judgment_catalog.PUBLIC) | {"indexed"}
    assert row["display_name"] == "Ibrahim Khan v. Mst. Saima Khan" and row["indexed"] is True
    weak = next(j for j in body["judgments"] if j["doc_id"] == "judgment/a/r2")
    assert weak["display_name"] == f"Civil Petition No. 3718 of 2023 ({SC}, 2023)"

    page = authed.get(f"{API}/kb/judgments", params={"page": 2, "page_size": 1}).json()
    assert page["total"] == 3 and len(page["judgments"]) == 1 and page["page"] == 2
    assert [j["doc_id"] for j in authed.get(f"{API}/kb/judgments", params={"q": "shaista"}).json()["judgments"]] \
        == ["judgment/a/r3"]
    assert authed.get(f"{API}/kb/judgments", params={"q": "3718"}).json()["total"] == 1
    assert authed.get(f"{API}/kb/judgments", params={"topic": "custody"}).json()["total"] == 2
    assert authed.get(f"{API}/kb/judgments", params={"court": "lahore high court", "year": 2023}).json()["total"] == 1


def test_judgment_detail(jx, authed):
    r = authed.get(f"{API}/kb/judgments/judgment/a/r1")
    body = r.json()
    assert body["paragraphs"] == [{"n": 1, "text": "Heading."},
                                  {"n": 2, "text": "Khula is a right of the wife to seek dissolution."},
                                  {"n": 3, "text": "Petition dismissed."}]
    assert body["provenance_note"] == "dataset supplied by the team; original source and licence to be confirmed"
    assert body["status"] == "staged" and body["indexed"] is True
    assert authed.get(f"{API}/kb/judgments/judgment/a/nope").status_code == 404
    assert authed.get(f"{API}/kb/judgments/judgment/a/r4").status_code == 404          # excluded


def test_file_path_and_hash_are_never_returned(jx, authed):
    for url in (f"{API}/kb/judgments", f"{API}/kb/judgments/judgment/a/r1", f"{API}/kb/judgments/judgment/b/r5"):
        text = authed.get(url).text
        assert "secret" not in text and "f" * 64 not in text and "c" * 64 not in text
        assert "original_file" not in text and "file_sha256" not in text and "content_hash" not in text


def test_the_indexed_copy_of_a_duplicate_is_listed(jx, authed):
    write_index(jx.index, [(R5, 1, 0.9)])                    # only the other dataset's copy is indexed
    ids = [j["doc_id"] for j in authed.get(f"{API}/kb/judgments").json()["judgments"]]
    assert "judgment/b/r5" in ids and "judgment/a/r1" not in ids


def test_judgment_endpoints_need_a_login(jx, client):
    assert client.get(f"{API}/kb/judgments").status_code == 401


# --------------------------------------------------------------------------- research

@pytest.fixture
def research(jx, monkeypatch):
    statute = {"source": "Muslim Family Laws Ordinance, 1961", "text": "Talaq notice.", "relevance": 0.7}
    monkeypatch.setattr(research_service.embeddings, "search", lambda q, top_k, filters=None: [dict(statute)])
    monkeypatch.setattr(research_service.embeddings, "build_or_load", lambda db=None: 1)
    rewrites = []
    monkeypatch.setattr(research_service, "rewrite_for_search", lambda q: rewrites.append(q) or q)
    return rewrites


def test_research_scopes(research, authed):
    url = f"{API}/research/search"
    stat = authed.post(url, json={"query": "khula"}).json()
    assert stat["scope"] == "statutes" and stat["judgments"] == [] and stat["total"] == 1

    jud = authed.post(url, json={"query": "khula", "scope": "judgments"}).json()
    assert jud["results"] == [] and jud["total"] == 0 and jud["scope"] == "judgments"
    j = jud["judgments"][0]
    assert {k: j[k] for k in ("doc_id", "display_name", "court", "year", "case_number", "paragraph")} == {
        "doc_id": "judgment/a/r1", "display_name": "Ibrahim Khan v. Mst. Saima Khan", "court": SC, "year": 2024,
        "case_number": "Civil Petition No. 4657 of 2022", "paragraph": 2}
    assert j["snippet"].startswith("Khula is a right") and j["relevance"] == 0.8

    both = authed.post(url, json={"query": "khula", "scope": "all"}).json()
    assert both["total"] == 1 and len(both["judgments"]) == 3
    assert research.count("khula") == 3                     # one rewrite per search, shared by both halves


def test_research_statute_filters_with_judgments(research, authed):
    url = f"{API}/research/search"
    body = authed.post(url, json={"query": "custody", "scope": "judgments", "year_from": 2024,
                                  "category": "Family Laws", "jurisdiction": "Punjab", "source_tier": 1}).json()
    assert [j["doc_id"] for j in body["judgments"]] == ["judgment/a/r1"]     # year applies; the rest is ignored
    assert body["filters_active"] is True and body["filter_coverage"] is None
    body = authed.post(url, json={"query": "custody", "scope": "judgments", "court": "Lahore"}).json()
    assert [j["doc_id"] for j in body["judgments"]] == ["judgment/a/r3"]


# --------------------------------------------------------------------------- flag off

def test_flag_off_behaves_as_before(jx, authed, research, monkeypatch):
    monkeypatch.setattr(settings, "JUDGMENTS_V2", False)
    assert judgment_search.search("khula") == []
    assert judgment_search.status() == {"judgment_chunks": None, "judgments": None}
    assert authed.get(f"{API}/kb/judgments").status_code == 404
    assert authed.get(f"{API}/kb/judgments/judgment/a/r1").status_code == 404
    body = authed.post(f"{API}/research/search", json={"query": "khula", "scope": "judgments"}).json()
    assert "judgments" not in body and "scope" not in body and body["total"] == 1      # a statute search
    assert set(body) == {"query", "total", "results", "weak_matches", "filters_active", "filter_coverage"}
    health = authed.get("/health").json()
    assert health["judgments_v2"] is False and health["judgment_chunks"] is None
    assert chat.retrieve_judgments("khula") == []
    assert chat.build_system_prompt("[1] x", "en") == chat.build_system_prompt("[1] x", "en", cases=None)
    assert "Reported cases" not in chat.build_system_prompt("[1] x", "en")


# --------------------------------------------------------------------------- grounding

J1 = {"display_name": "Ibrahim Khan v. Mst. Saima Khan", "case_name": "Ibrahim Khan v. Mst. Saima Khan",
      "case_number": "Civil Petition No. 4657 of 2022", "paragraph": 2}
J2 = {"display_name": f"Civil Petition No. 3718 of 2023 ({SC}, 2023)", "case_name": "…Petitioner v. SHO",
      "case_number": "Civil Petition No. 3718 of 2023", "paragraph": 27}
PASSAGES = [{"source": "Muslim Family Laws Ordinance, 1961", "text": "7. Talaq. (1) Notice to the Chairman."}]


def test_a_retrieved_case_with_its_paragraph_is_kept():
    answer = (f"Short answer: notice goes to the Chairman [1].\n"
              f"In Ibrahim Khan v. Saima Khan ({SC}, 2024), para 2, the Court described khula.\n"
              f"Civil Petition No. 3718 of 2023 ({SC}, 2023), para 27 puts the minor's welfare first.")
    r = check_citations(answer, PASSAGES, judgments=[J1, J2])
    assert r.text == answer and r.removed_case_citations == [] and r.unverified == []
    assert len(r.cases_verified) == 2


def test_a_case_not_retrieved_is_removed():
    answer = ("Notice goes to the Chairman [1].\nIn Muhammad Ali v. Fatima Bibi (Lahore High Court, 2010), "
              "para 4, the court held otherwise.\nC.P. 99/2020 decided it too.")
    r = check_citations(answer, PASSAGES, judgments=[J1])
    assert "Muhammad Ali" not in r.text and "99/2020" not in r.text
    assert "[case citation removed — not among the cases retrieved for this answer]" in r.text
    assert r.removed_case_citations == ["Muhammad Ali v. Fatima Bibi", "C.P. 99/2020"]
    assert "Notice goes to the Chairman [1]." in r.text


def test_a_wrong_paragraph_number_is_flagged():
    answer = f"In Ibrahim Khan v. Saima Khan ({SC}, 2024), para 9, the Court said so."
    r = check_citations(answer, PASSAGES, judgments=[J1])
    assert "para 9 (unverified)" in r.text
    assert r.unverified == ["Ibrahim Khan v. Mst. Saima Khan, para 9: not the paragraph retrieved (para 2)"]
    assert "case paragraphs retrieved" in r.text


def test_a_case_number_matches_by_number_and_year():
    ok = check_citations("Civil Petition No. 4657 of 2022, para 2 says so.", PASSAGES, judgments=[J1])
    assert ok.removed_case_citations == [] and ok.unverified == []
    wrong_year = check_citations("Civil Petition No. 4657 of 2021, para 2 says so.", PASSAGES, judgments=[J1])
    assert wrong_year.removed_case_citations == ["Civil Petition No. 4657 of 2021"]


def test_no_judgments_is_the_statute_only_check():
    answer = "In Ibrahim Khan v. Saima Khan, para 2, the Court described khula. Notice goes to the Chairman [1]."
    assert check_citations(answer, PASSAGES).text == check_citations(answer, PASSAGES, judgments=None).text
    assert "not in LegalEase's statute library" in check_citations(answer, PASSAGES).text


# --------------------------------------------------------------------------- chat

class FakeAI:
    def __init__(self, answer):
        self.answer, self.system = answer, None

    def chat(self, history, system=None):
        self.system = system
        return self.answer


@pytest.fixture
def chat_env(jx, db_session, monkeypatch):
    statute = {"source": "Muslim Family Laws Ordinance, 1961", "text": "7. Talaq. (1) Notice to the Chairman.",
               "relevance": 0.80}
    monkeypatch.setattr(chat, "rewrite_for_search", lambda q: q)
    monkeypatch.setattr(chat.embeddings, "build_or_load", lambda *a: 1)
    monkeypatch.setattr(chat, "retrieve_passages", lambda *a, **k: [dict(statute)])
    u = User(email="c2@gmail.com", password_hash=hash_password("x"), full_name="C Two", role=UserRole.STUDENT,
             is_active=True, is_verified=True)
    db_session.add(u)
    db_session.commit()

    def ask(answer, question="What is khula?"):
        ai = FakeAI(answer)
        svc = chat.LegalChatService(db_session)
        svc.ai = ai
        return svc.send(u, question), ai
    return ask


def test_chat_adds_reported_cases_and_a_case_law_group(chat_env):
    reply, ai = chat_env(f"Short answer: notice goes to the Chairman [1]. In Ibrahim Khan v. Saima Khan ({SC}, "
                         f"2024), para 2, the Court described khula. Also Muhammad Ali v. Fatima Bibi held so.")
    assert "--- Reported cases (context only) ---" in ai.system
    assert f"Case 1: Ibrahim Khan v. Mst. Saima Khan ({SC}, 2024) - para 2:\nKhula is a right" in ai.system
    assert f"Case 2: Civil Petition No. 3718 of 2023 ({SC}, 2023) - para 27:" in ai.system
    assert "Shaista" not in ai.system                               # 0.52: under JUDGMENTS_SHOW_MIN
    assert "never use a case in place of a statute" in ai.system.lower()
    assert ai.system.index("--- End authorities ---") < ai.system.index("Reported cases (context only)") \
        < ai.system.index("LANGUAGE:")
    assert "Muhammad Ali" not in reply["response"] and "Ibrahim Khan v. Saima Khan" in reply["response"]
    assert [c["n"] for c in reply["citations"]] == [1]                # [n] numbering: statutes only
    assert [(c["doc_id"], c["paragraph"]) for c in reply["case_law"]] == [("judgment/a/r1", 2), ("judgment/a/r2", 27)]
    assert all(c["relevance"] >= 0.55 for c in reply["case_law"])
    assert reply["confidence"] == "normal"                           # from the statute passage only
    assert ChatMessageResponse.model_validate(reply).model_dump()["case_law"] == reply["case_law"]


def test_chat_history_keeps_case_law_out_of_the_flags(chat_env):
    reply, _ai = chat_env("Short answer: see [1].")
    stored = [{"relevance": 0.66, "source": "x"}, {"kind": "case_law", "relevance": 0.9, "source": "y"}]
    assert chat.answer_flags(stored)["confidence"] == "low"          # 0.66 < 0.70; the case's 0.9 is ignored
    assert chat.answer_flags([{"kind": "case_law", "relevance": 0.9}]) == {"confidence": None, "family_scope": False}


def test_chat_with_the_flag_off_is_unchanged(chat_env, monkeypatch):
    monkeypatch.setattr(settings, "JUDGMENTS_V2", False)
    reply, ai = chat_env("Short answer: notice goes to the Chairman [1].")
    assert "Reported cases" not in ai.system and "case_law" not in reply
    assert set(reply) == {"response", "sources", "session_id", "citations", "response_time_ms", "confidence",
                          "family_scope"}


def test_judgments_are_not_searched_when_the_scope_gate_refuses(chat_env, monkeypatch):
    monkeypatch.setattr(chat, "retrieve_passages", lambda *a, **k: [])
    def no_search(*a, **k):
        raise AssertionError("judgments must not be searched for a refused question")
    monkeypatch.setattr(judgment_search, "search", no_search)
    reply, ai = chat_env("unused", question="Give me a cake recipe")
    assert ai.system is None and reply["case_law"] == []                # refused: no model call, no cases
