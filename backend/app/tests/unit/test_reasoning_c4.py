"""kb-v2 C4: the Document Analysis reasoning layer, with a mocked model (no
Groq calls). The document is the Crl.P. 187-P/2026 demo order in
docs/demo/; the mocked reply mixes real quotes with planted bad items."""

import json
from pathlib import Path

import pymupdf
import pytest
from sqlalchemy.orm import sessionmaker

from app.ai import reasoning
from app.ai.client import RateLimitedError
from app.api.v1 import documents as documents_api
from app.core.config import settings
from app.core.exceptions import AIServiceUnavailable
from app.core.security import hash_password
from app.kb import catalog
from app.models.document import Document, DocumentAnalysis
from app.models.enums import DocumentType, FileType, UserRole
from app.models.user import User

ROOT = Path(__file__).resolve().parents[4]
PDF = ROOT / "docs/demo/crl_p_187_p_2026/crl.p._187_p_2026.pdf"
MOCK = (Path(__file__).resolve().parents[1] / "fixtures/reasoning/crl_p_187_mock.json").read_text(encoding="utf-8")
TEXT = "\n".join(p.get_text() for p in pymupdf.open(PDF))
NER = ["Nadar Khan", "Saadullah", "Zardali Khan", "Zafar Khan", "Siraj", "10.07.2026", "21.09.2026", "11.04.2022",
       "Criminal Petition No.187-P of 2026", "Cr.MB No.1862-P/26", "FIR No.360/22", "sections 302/324/34 PPC"]


class FakeAI:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def complete_json(self, prompt, system, max_tokens):
        self.calls.append({"prompt": prompt, "system": system, "max_tokens": max_tokens})
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture
def kb(tmp_path, monkeypatch):
    """A knowledge base holding PPC ss. 302, 324 and 34 (and no CrPC)."""
    d = tmp_path / "kb" / "records"
    d.mkdir(parents=True)
    recs = [{"doc_id": f"legalease-corpus/pakistan-penal-code-1860/s{n}", "title": "Pakistan Penal Code, 1860",
             "section": n, "heading": h, "text": "..."} for n, h in (("302", "Punishment of qatl-i-amd"),
                                                                    ("324", "Attempt to commit qatl-i-amd"),
                                                                    ("34", "Acts done by several persons"))]
    (d / "pakistan-penal-code-1860.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    monkeypatch.setattr(settings, "KB_DIR", str(tmp_path / "kb"))
    monkeypatch.setattr(settings, "KB_V2_METADATA_PATH", str(tmp_path / "none.json"))
    monkeypatch.setattr(settings, "SCRAPED_V2", False)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", False)
    catalog.reset()
    yield
    catalog.reset()


# --------------------------------------------------------------------------- (a) quotes

def test_quote_matching_normalises_case_space_punctuation_and_hyphen_splits():
    doc = reasoning.norm("suffering from terminal or life-\nthreatening illnesses,  nor it has been RECORDED")
    assert reasoning.quote_found("terminal or life-threatening illnesses", doc)
    assert reasoning.quote_found("Terminal or life threatening illnesses nor it has been recorded", doc)
    assert reasoning.quote_found("terminal or … nor it has been recorded", doc)          # ellipsis: parts in order
    assert not reasoning.quote_found("nor it has been recorded … terminal or", doc)
    assert not reasoning.quote_found("life-threatening", doc)                            # too short to prove anything
    assert not reasoning.quote_found("terminal or fatal illnesses", doc)


def test_good_reply_on_the_demo_order(kb):
    out, err = reasoning.analyse(TEXT, NER, ai=FakeAI(MOCK))
    assert err is None
    c = out["counts"]
    assert (c["returned"], c["kept"], c["dropped"]) == (26, 22, 4)
    assert c["dropped_reasons"] == {"quote not found in the document": 2,
                                    "mentions a date, number or section not in the document": 2}
    assert [s["step"] for s in out["court_reasoning"]] == [1, 2, 3, 4]
    assert set(out["arguments"]) == {"petitioner", "complainant"}       # the State's only item had a fake quote
    assert len(out["arguments"]["petitioner"]) == 2                      # "FIR No. 999/2025" dropped
    assert all(i["evidence"] and i["verified"] for i in out["issues"])
    assert out["holding_or_outcome"]["text"].startswith("Bail after arrest granted")
    assert out["disclaimer"] == "AI-assisted analysis; verify against the original"
    assert out["coverage"]["partial"] is False and out["related_cases_note"] is None


# --------------------------------------------------------------------------- (b) mentions

def test_dates_numbers_and_names_must_be_in_the_document():
    doc_norm = reasoning.norm(TEXT)
    miss, names = reasoning.mention_problems("Bail refused on 10.07.2026 in Cr.MB No.1862-P/2026 under section 302.",
                                             TEXT, doc_norm, NER)
    assert miss == [] and names == []
    miss, _ = reasoning.mention_problems("Heard on 22.09.2026", TEXT, doc_norm, NER)
    assert miss == ["22.09.2026"]
    miss, _ = reasoning.mention_problems("FIR No. 361 was lodged", TEXT, doc_norm, NER)
    assert miss == ["FIR No. 361"]
    miss, _ = reasoning.mention_problems("charged under section 497", TEXT, doc_norm, NER)
    assert miss == ["section 497"]
    miss, _ = reasoning.mention_problems("in Criminal Petition No. 188-P of 2026", TEXT, doc_norm, NER)
    assert miss == ["No. 188-P of 2026"]
    miss, _ = reasoning.mention_problems("decided on 21st Sept, 2026", TEXT, doc_norm, NER)
    assert miss == []
    _, names = reasoning.mention_problems("Counsel for Imran Ahmed argued", TEXT, doc_norm, NER)
    assert names == ["Imran Ahmed"]


def test_an_unknown_name_is_flagged_not_dropped(kb):
    reply = json.dumps({"issues": [{"text": "Whether Imran Ahmed gave a statement.",
                                    "evidence": "Heard the learned counsel for the parties, perused the record"}]})
    out, _ = reasoning.analyse(TEXT, NER, ai=FakeAI(reply))
    issue = out["issues"][0]
    assert issue["verified"] is False and issue["flags"] == ["name not found in the document: Imran Ahmed"]
    assert out["counts"]["flagged"] == 1 and out["counts"]["kept"] == 1


# --------------------------------------------------------------------------- (c) statutes

def test_statutes_are_looked_up_in_the_knowledge_base(kb):
    reply = json.dumps({"statutes_cited": [
        {"act": "PPC", "section": "302/324/34", "evidence": "registered under sections 302/324/34 PPC"},
        {"act": "Pakistan Penal Code", "section": "302", "evidence": "registered under sections 302/324/34 PPC"},
        {"act": "PPC", "section": "411", "evidence": "registered under sections 302/324/34 PPC"},
        {"act": "Peshawar Police Rules", "section": "12", "evidence": "registered under sections 302/324/34 PPC"}]})
    out, _ = reasoning.analyse(TEXT, NER, ai=FakeAI(reply))
    got = {(s["act"], s["section"]): s for s in out["statutes_cited"]}
    assert set(got) == {("PPC", "302"), ("PPC", "324"), ("PPC", "34"), ("PPC", "411"),
                        ("Peshawar Police Rules", "12")}                    # the repeated s.302 is listed once
    assert got[("PPC", "302")]["status"] == "verified"
    assert got[("PPC", "302")]["kb_record_id"] == "legalease-corpus/pakistan-penal-code-1860/s302"
    assert got[("PPC", "302")]["kb_law_id"] == "pakistan-penal-code-1860"
    assert got[("PPC", "411")]["status"] == "not_found"
    assert got[("Peshawar Police Rules", "12")]["status"] == "not_checked"
    assert out["counts"]["statutes"] == {"verified": 3, "law_held": 0, "not_found": 1, "not_checked": 1}


# --------------------------------------------------------------------------- (d) related cases

def test_related_cases_only_with_judgments_on(kb, monkeypatch):
    from app.kb import judgment_search
    seen = []

    def fake_search(q, top_k, min_score):
        seen.append((top_k, min_score))
        return [{"doc_id": "judgment/x/1", "display_name": "A v. B", "case_name": "A v. B",
                 "court": "Supreme Court of Pakistan", "year": 2023, "paragraph": 4, "score": 0.61,
                 "text": "Bail was refused because the evidence connected the accused.", "case_number": "C.P. 1"}]
    monkeypatch.setattr(judgment_search, "search", fake_search)
    out, _ = reasoning.analyse(TEXT, NER, ai=FakeAI(MOCK))
    assert all("related_cases" not in i for i in out["issues"]) and not seen
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    out, _ = reasoning.analyse(TEXT, NER, ai=FakeAI(MOCK))
    assert out["issues"][0]["related_cases"][0]["doc_id"] == "judgment/x/1"
    assert seen[0] == (6, 0.58) and "not cited in this document" in out["related_cases_note"]


# --------------------------------------------------------------------------- failures

def test_malformed_json_gives_null_and_a_reason(kb):
    out, err = reasoning.analyse(TEXT, NER, ai=FakeAI("Sure! Here is the brief: issues are bail and age."))
    assert out is None and "wasn't in the expected format" in err
    out, _ = reasoning.analyse(TEXT, NER, ai=FakeAI("```json\n" + MOCK + "\n```"))           # fenced: accepted
    assert out["counts"]["kept"] == 22


def test_429_backs_off_and_retries(kb):
    waits = []
    ai = FakeAI(RateLimitedError("busy", retry_after=7), RateLimitedError("busy"), MOCK)
    out, err = reasoning.analyse(TEXT, NER, ai=ai, sleep=waits.append)
    assert err is None and out["counts"]["kept"] == 22 and waits == [7, 10.0] and len(ai.calls) == 3


def test_429_that_outlasts_the_wait_is_a_clear_message(kb, monkeypatch):
    monkeypatch.setattr(settings, "REASONING_MAX_WAIT", 12)
    waits = []
    ai = FakeAI(*[RateLimitedError("busy")] * 5)
    out, err = reasoning.analyse(TEXT, NER, ai=ai, sleep=waits.append)
    assert out is None and "8,000 tokens a minute" in err and "Try Analyse again in a minute" in err
    assert waits == [5.0]
    out, err = reasoning.analyse(TEXT, NER, ai=FakeAI(RateLimitedError("day", retry_after=3600)), sleep=waits.append)
    assert out is None and "daily limit" in err


def test_service_down_gives_null_and_a_reason(kb):
    out, err = reasoning.analyse(TEXT, NER, ai=FakeAI(AIServiceUnavailable(message="down")))
    assert out is None and "didn't respond" in err


# --------------------------------------------------------------------------- budget and long documents

def test_prompt_fits_the_budget(kb):
    ai = FakeAI(MOCK)
    out, _ = reasoning.analyse(TEXT, NER, ai=ai)
    total = out["prompt_tokens_estimate"] + ai.calls[0]["max_tokens"]
    assert ai.calls[0]["max_tokens"] == settings.REASONING_MAX_TOKENS and total <= 6500
    assert "exact quotation" in ai.calls[0]["system"] and "JSON" in ai.calls[0]["system"]


def test_long_document_is_analysed_in_parts(kb):
    filler = "\n\n".join(f"Paragraph {i}. The record was perused and nothing of note arises here at all." * 3
                         for i in range(700))
    doc = "HEAD OF THE ORDER Criminal Petition No.187-P of 2026\n\n" + filler + "\n\nTAIL: the petition is allowed."
    ai = FakeAI(*[json.dumps({"issues": []})] * settings.REASONING_MAX_CALLS)
    out, _ = reasoning.analyse(doc, ["Zafar Khan"], ai=ai, sleep=lambda s: None)
    assert len(ai.calls) == settings.REASONING_MAX_CALLS and out["coverage"]["partial"] is True
    assert "HEAD OF THE ORDER" in ai.calls[0]["prompt"] and "the petition is allowed" in ai.calls[-1]["prompt"]
    assert f"about {out['coverage']['percent']}% of it" in out["coverage"]["note"]
    parts, cov = reasoning.plan(TEXT)
    assert len(parts) == 1 and cov["partial"] is False and cov["note"] is None


# --------------------------------------------------------------------------- the endpoint

@pytest.fixture
def lawyer(db_session):
    u = User(email="lawyer4@gmail.com", password_hash=hash_password("x"), full_name="Lawyer", role=UserRole.LAWYER,
             is_active=True, is_verified=True)
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def endpoint(db_session, engine, lawyer, kb, monkeypatch):
    from app.ai import ner
    monkeypatch.setattr(documents_api, "SessionLocal", sessionmaker(bind=engine))

    class Summariser:
        def summarise(self, text, hint="", focus_gaps=False):
            return ("1) Summary\nBail granted.\n5) Points to review\n- No bail petition is mentioned.\n"
                    "- No date is given for the recovery memo.")
    monkeypatch.setattr(documents_api, "get_ai_client", lambda: Summariser())
    monkeypatch.setattr(ner, "extract_entities", lambda text: ner.NerResult(available=False))
    doc = Document(uploaded_by_id=lawyer.id, file_name="crl.pdf", storage_path="uploads/x.pdf", sha256_hash="0" * 64,
                   file_type=FileType.PDF, file_size_bytes=1, document_type=DocumentType.OTHER, extracted_text=TEXT)
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    db_session.refresh(lawyer)
    return doc


def test_flag_off_response_and_saved_analysis_unchanged(db_session, lawyer, endpoint, monkeypatch):
    monkeypatch.setattr(settings, "REASONING_V2", False)
    monkeypatch.setattr(reasoning, "analyse", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no call")))
    res = documents_api.analyze_document(endpoint.id, lawyer, db_session)
    dumped = res.model_dump()
    assert "reasoning" not in dumped and "reasoning_error" not in dumped and "review_points_removed" not in dumped
    assert len(dumped["risks"]) == 2                                      # no absence check with the flag off
    saved = db_session.query(DocumentAnalysis).filter_by(document_id=endpoint.id).one()
    assert saved.identified_clauses == {"source": "llm_summary", "items": []}


def test_flag_on_returns_and_saves_the_reasoning(db_session, lawyer, endpoint, monkeypatch):
    monkeypatch.setattr(settings, "REASONING_V2", True)
    from app.ai import client
    monkeypatch.setattr(client, "get_ai_client", lambda: FakeAI(MOCK))
    res = documents_api.analyze_document(endpoint.id, lawyer, db_session).model_dump()
    assert res["reasoning_error"] is None and res["reasoning"]["counts"]["kept"] == 22
    assert res["summary"].startswith("1) Summary")                       # the rest of the analysis is untouched
    assert res["risks"] == ["No date is given for the recovery memo."] and res["review_points_removed"] == 1
    db_session.expire_all()
    saved = db_session.query(DocumentAnalysis).filter_by(document_id=endpoint.id).one()
    assert saved.identified_clauses["reasoning"]["counts"]["dropped"] == 4


def test_flag_on_failure_still_returns_the_analysis(db_session, lawyer, endpoint, monkeypatch):
    monkeypatch.setattr(settings, "REASONING_V2", True)
    from app.ai import client
    monkeypatch.setattr(client, "get_ai_client", lambda: FakeAI("not json"))
    res = documents_api.analyze_document(endpoint.id, lawyer, db_session).model_dump()
    assert res["reasoning"] is None and "expected format" in res["reasoning_error"]
    assert res["summary"].startswith("1) Summary")
