"""kb-v2 B7: exact section lookup, scope gate, reference completeness (offline, no model calls)."""

from pathlib import Path

import pytest

from app.ai.citation_check import check_citations
from app.core.config import settings
from app.kb import catalog, exact_lookup

ROOT = Path(__file__).resolve().parents[3]
RECORDS = ROOT / "storage" / "kb" / "records"
HAS_RECORDS = RECORDS.exists() and any(RECORDS.glob("*.jsonl"))
INDEXES = (ROOT / "storage" / "faiss" / "legal_corpus.faiss").exists() and \
    (ROOT / "storage" / "kb" / "faiss_v2.faiss").exists()
needs_records = pytest.mark.skipif(not HAS_RECORDS, reason="kb records not built")


@pytest.fixture(autouse=True)
def real_kb(monkeypatch):
    monkeypatch.setattr(settings, "KB_DIR", str(ROOT / "storage" / "kb"))
    catalog.reset()
    yield
    catalog.reset()


# --------------------------------------------------------------------------- 0. exact section lookup

@needs_records
@pytest.mark.parametrize("question,law,section", [
    ("What is murder under Section 302 of the Pakistan Penal Code?", "Pakistan Penal Code, 1860", "302"),
    ("section 154 of the CrPC", "Code of Criminal Procedure, 1898", "154"),
    ("Article 10A of the Constitution", "Constitution of the Islamic Republic of Pakistan, 1973", "10A"),
    ("section 379 PPC", "Pakistan Penal Code, 1860", "379"),
    ("u/s 497 Cr.P.C. bail", "Code of Criminal Procedure, 1898", "497"),
    ("What does sec. 10 of the Contract Act say?", "Contract Act, 1872", "10"),
    ("Section 9 of the Muslim Family Laws Ordinance, 1961", "Muslim Family Laws Ordinance, 1961", "9"),
])
def test_exact_lookup_finds_the_named_section(question, law, section):
    hits = exact_lookup.exact_passages(question)
    assert hits and hits[0]["source"] == law and hits[0]["section"] == section
    assert hits[0]["exact_match"] is True and hits[0]["text"]


@needs_records
def test_each_number_goes_to_its_own_law():
    assert exact_lookup.find_refs("PPC section 302 and CrPC section 154") == [
        ("Pakistan Penal Code, 1860", "302"), ("Code of Criminal Procedure, 1898", "154")]
    assert exact_lookup.find_refs("Section 7 of the MFLO and section 2 of DMMA") == [
        ("Muslim Family Laws Ordinance, 1961", "7"), ("Dissolution of Muslim Marriages Act, 1939", "2")]
    # "of" after the number is not a section suffix
    assert exact_lookup.find_refs("Section 302 of the PPC") == [("Pakistan Penal Code, 1860", "302")]


@needs_records
@pytest.mark.parametrize("question", [
    "Section 302 of the Indian Penal Code",          # foreign law: never
    "What is the punishment for murder under the Indian Penal Code section 302?",
    "Section 999 of the Pakistan Penal Code",        # no such section: nothing special
    "What is section 302?",                          # no law named
    "Is marriage registration mandatory in Pakistan",
])
def test_exact_lookup_does_nothing(question):
    assert exact_lookup.exact_passages(question) == []


def test_merge_puts_exact_first_without_duplicates():
    exact = [{"doc_id": "a/b/s302", "relevance": 1.0}]
    semantic = [{"doc_id": "a/b/s303"}, {"doc_id": "a/b/s302"}, {"doc_id": "x"}, {"doc_id": "y"}, {"doc_id": "z"},
                {"doc_id": "w"}]
    merged = exact_lookup.merge(exact, semantic, top_k=5)
    assert [m["doc_id"] for m in merged] == ["a/b/s302", "a/b/s303", "x", "y", "z"]


@needs_records
@pytest.mark.skipif(not INDEXES, reason="search indexes not present")
def test_chat_retrieval_puts_the_exact_section_first(monkeypatch):
    from app.services.legal_chat_service import retrieve_passages
    monkeypatch.setattr(settings, "KB_V2", True)
    q = "What is murder under Section 302 of the Pakistan Penal Code?"
    passages = retrieve_passages(q, q, family="off")
    assert passages[0]["source"] == "Pakistan Penal Code, 1860" and passages[0]["section"] == "302"
    assert passages[0]["exact_match"] is True
    assert len(passages) <= settings.RAG_TOP_K
    assert len({p.get("doc_id") or p.get("chunk_id") for p in passages}) == len(passages)
    monkeypatch.setattr(settings, "KB_V2", False)              # flag off: no exact lookup
    assert not any(p.get("exact_match") for p in retrieve_passages(q, q, family="off"))


def test_section_in_the_question_is_not_flagged_when_its_record_was_retrieved():
    passages = [{"source": "Pakistan Penal Code, 1860", "section": "302",
                 "text": "Whoever commits qatl-e-amd shall, subject to the provisions of this Chapter be punished."}]
    ok = check_citations("Murder is punished under Section 302 of the Pakistan Penal Code [1].", passages)
    assert ok.unverified == [] and "(unverified)" not in ok.text
    other = check_citations("See Section 300 of the Pakistan Penal Code [1].", passages)
    assert other.unverified == ["Section 300 (Pakistan Penal Code)"]


# --------------------------------------------------------------------------- 2. scope gate

from app.kb import scope  # noqa: E402

DOWER = ("is the family court's blanket order demanding the total return of the dower property legally sustainable "
         "under Pakistani jurisprudence")
OFF_TOPIC = ["What is the capital of Australia and how many people live there?",
             "What is the weather forecast for Lahore tomorrow?", "Give me a recipe for chocolate cake.",
             "Who won the Cricket World Cup in 1992?", "How do I reset my Wi-Fi router?",
             "What is the best smartphone under 50,000 rupees?", "Explain how photosynthesis works.",
             "Write a poem about the monsoon.", "How many calories are in a plate of biryani?",
             "What is the exchange rate of the US dollar today?",
             "How do I register a company with the Corporate Affairs Commission in Nigeria?",
             "Is a verbal contract enforceable in Thailand?", "How do I file for divorce in California?",
             "What is the punishment for murder under the Indian Penal Code?",
             "How do I apply for a UK student visa?", "Can you recommend a good cricket bat?"]


def test_legal_terms_recognised():
    assert {"dower", "family court", "jurisprudence"} <= {t.lower() for t in scope.legal_terms(DOWER)}
    assert scope.legal_terms("Can bail be granted after an FIR under section 497?")
    assert scope.legal_terms("What does the Muslim Family Laws Ordinance say about nikah registration?")


@pytest.mark.parametrize("q", OFF_TOPIC)
def test_off_topic_and_foreign_questions_have_no_legal_terms(q):
    assert scope.legal_terms(q) == []


def _fake_search(scores):
    def search(query, top_k, filters=None):
        return [{"source": f"Act {i}", "doc_id": f"d/{query[:5]}/{i}", "text": "t", "relevance": s}
                for i, s in enumerate(scores.get(query, []))][:top_k]
    return search


def test_scope_fallbacks(monkeypatch):
    from app.services import legal_chat_service as svc
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(svc.exact_lookup, "exact_passages", lambda q: [])
    monkeypatch.setattr(svc.section_lookup, "section_passages", lambda q, p: [])
    monkeypatch.setattr(svc, "family_scope_applies", lambda *a: False)
    # 1. the rewrite drifts (0.60) but the raw question passes (0.70)
    monkeypatch.setattr(svc.embeddings, "search", _fake_search({"rewrite": [0.60], DOWER: [0.70, 0.64]}))
    got = svc.retrieve_passages(DOWER, "rewrite")
    assert [p["relevance"] for p in got] == [0.70]
    # 2. nothing passes, legal terms present: best passages down to the floor, both queries pooled
    monkeypatch.setattr(svc.embeddings, "search", _fake_search({"rewrite": [0.63, 0.55], DOWER: [0.643, 0.61, 0.59]}))
    got = svc.retrieve_passages(DOWER, "rewrite")
    assert [p["relevance"] for p in got] == [0.643, 0.63, 0.61]
    # off-topic: no legal terms, refused
    q = "Who won the Cricket World Cup in 1992?"
    monkeypatch.setattr(svc.embeddings, "search", _fake_search({"rewrite": [0.62], q: [0.63]}))
    assert svc.retrieve_passages(q, "rewrite") == []
    # flag off: unchanged behaviour (no fallbacks)
    monkeypatch.setattr(settings, "KB_V2", False)
    monkeypatch.setattr(svc.embeddings, "search", _fake_search({"rewrite": [0.60], DOWER: [0.70]}))
    assert svc.retrieve_passages(DOWER, "rewrite") == []


# --------------------------------------------------------------------------- 3. reference completeness

from app.ai.citation_check import normalize_markers  # noqa: E402

CHRISTIAN = {"source": "Christian Marriage Act, 1872",
             "text": "Every marriage between persons one or both of whom is a Christian shall be registered."}
MFLO_S5 = {"source": "Muslim Family Laws Ordinance, 1961", "section": "5",
           "text": "Every marriage solemnized under Muslim Law shall be registered in accordance with this Ordinance."}


def test_wrong_source_for_the_act_named_is_flagged():
    r = check_citations("The Muslim Family Laws Ordinance obliges every Muslim marriage to be registered [1].",
                        [CHRISTIAN])
    assert "Act named but not found in the retrieved text: Muslim Family Laws Ordinance" in r.unverified
    assert ("[1] cites Christian Marriage Act, 1872, but the sentence names Muslim Family Laws Ordinance"
            in r.unverified)
    assert "(unverified)" not in r.text and "Note:" in r.text


def test_act_named_without_any_source_is_flagged():
    r = check_citations("Under the Muslim Family Laws Ordinance, registration of a nikah is compulsory.", [CHRISTIAN])
    assert r.unverified == ["Act named but not found in the retrieved text: Muslim Family Laws Ordinance"]


def test_correct_citations_are_not_flagged():
    r = check_citations("The Muslim Family Laws Ordinance requires registration [2]; so does the Christian "
                        "Marriage Act [1].", [CHRISTIAN, MFLO_S5])
    assert r.unverified == []
    r = check_citations("Under the MFLO, section 5 requires registration [1].", [MFLO_S5])
    assert r.unverified == []
    # an Act mentioned inside the cited passage's own text is not a mismatch
    mflo_s3 = {"source": "Muslim Family Laws Ordinance, 1961", "section": "3",
               "text": "the provisions of the Arbitration Act, 1940 (X of 1940) shall not apply to any Arbitration "
                       "Council."}
    assert check_citations("Section 3 says the Arbitration Act, 1940 does not apply [1].", [mflo_s3]).unverified == []


def test_grouped_markers_are_split_so_every_source_is_listed():
    assert normalize_markers("See [1, 2] and [3-5] and [2][4].") == "See [1][2] and [3][4][5] and [2][4]."
    r = check_citations("Short answer: registration is compulsory [1, 2].", [CHRISTIAN, MFLO_S5])
    assert "[1][2]" in r.text and r.removed_markers == []


def test_act_name_with_extra_words_still_matches_its_source():
    mflo_s8 = {"source": "Muslim Family Laws Ordinance, 1961", "section": "8",
               "text": "the provisions of section 7 shall, mutatis mutandis and so far as applicable, apply."}
    r = check_citations("The right can also be exercised under the Application of the Muslim Family Laws "
                        "Ordinance, 1961 [1].", [mflo_s8])
    assert r.unverified == []


def test_prompt_source_line_carries_section_and_heading():
    from app.services.legal_chat_service import source_label
    assert source_label({"section": "302", "heading": "Punishment of qatl-i-amd", "exact_match": True}) == \
        " - s.302 Punishment of qatl-i-amd (the section named in the question)"
    assert source_label({"section": "Schedule item 2", "heading": "Dower"}) == " - Schedule item 2 Dower"
    assert source_label({"source": "THE PAKISTAN PENAL CODE", "text": "..."}) == ""     # v1 chunk: unchanged


def test_compose_answer_passes_sections_to_the_check():
    from app.services.legal_chat_service import compose_answer

    class AI:
        def chat(self, history, system):
            assert "[1] Source: Pakistan Penal Code, 1860 - s.302 Punishment of qatl-i-amd" in system
            return "Murder is punished under Section 302 of the Pakistan Penal Code [1]."
    p = {"source": "Pakistan Penal Code, 1860", "section": "302", "heading": "Punishment of qatl-i-amd",
         "text": "Whoever commits qatl-e-amd shall, subject to the provisions of this Chapter be punished.",
         "exact_match": True}
    checked = compose_answer(AI(), [p], [{"role": "user", "content": "q"}], "en")
    assert checked.unverified == [] and "(unverified)" not in checked.text
