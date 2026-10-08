"""kb-v2 C8: section expansion and the reference checker's normalisation. Offline."""

import pytest

from app.ai.citation_check import _figures, _mask_headings, check_citations
from app.core.config import settings
from app.kb import catalog, index_v2
from app.services import legal_chat_service as chat

LONG = " ".join(f"({i}) The authority shall keep a register of every licence issued under this Act." for i in range(400))


@pytest.fixture
def records(monkeypatch):
    recs = {f"law/s{i}": {"title": "Some Act, 2000", "section": str(i), "text": f"Full text of section {i}. " * 20}
            for i in range(1, 7)}
    recs["law/s9"] = {"title": "Some Act, 2000", "section": "9", "text": LONG}
    monkeypatch.setattr(index_v2._V2_INDEX, "texts", {k: v["text"] for k, v in recs.items()})
    monkeypatch.setattr(catalog, "data", lambda: {"records": recs})
    monkeypatch.setattr(settings, "SECTION_MAX_COUNT", 4)
    monkeypatch.setattr(settings, "SECTION_MAX_TOKENS", 700)
    return recs


def hit(doc_id, text="fragment"):
    return {"doc_id": doc_id, "kb": "v2", "text": text, "source": "Some Act, 2000", "relevance": 0.8}


def test_sections_get_their_full_text_once_and_at_most_four(records):
    v1 = {"source": "OLD COPY", "text": "old chunk", "relevance": 0.7}
    out = chat.expand_sections([hit("law/s1"), hit("law/s1"), v1, hit("law/s2"), hit("law/s3"), hit("law/s4"),
                                hit("law/s5")])
    assert [p.get("doc_id") for p in out] == ["law/s1", None, "law/s2", "law/s3", "law/s4"]
    assert out[0]["text"] == records["law/s1"]["text"] and out[0]["expanded"] is True
    assert out[1] == v1                                         # old-index chunks unchanged


def test_long_sections_are_capped(records):
    out = chat.expand_sections([hit("law/s9")])
    assert chat.count_tokens(out[0]["text"]) <= 702 and out[0]["text"].endswith("…")
    assert out[0]["text"].startswith("(0) The authority")


def test_expansion_only_with_kb_v2_and_the_switch(monkeypatch, records):
    seen = []
    monkeypatch.setattr(chat, "family_scope_applies", lambda *a: False)
    monkeypatch.setattr(chat.embeddings, "search", lambda q, top_k: [hit("law/s1", "frag")])
    monkeypatch.setattr(chat.embeddings, "similarity_threshold", lambda: 0.5)
    monkeypatch.setattr(chat.section_lookup, "section_passages", lambda q, p: [])
    monkeypatch.setattr(chat.exact_lookup, "exact_passages", lambda q: [])
    for kb_v2, switch in ((False, True), (True, False), (True, True)):
        monkeypatch.setattr(settings, "KB_V2", kb_v2)
        monkeypatch.setattr(settings, "SECTION_EXPANSION", switch)
        seen.append(chat.retrieve_passages("q", "q")[0]["text"])
    assert seen[0] == "frag" and seen[1] == "frag" and seen[2] == records["law/s1"]["text"]


# --------------------------------------------------------------------------- reference checker

@pytest.mark.parametrize("text, figures", [
    ("may extend to one thous and rupees", {(1000, "rupee")}),            # OCR split
    ("a fine of five thousand rupees", {(5000, "rupee")}),
    ("Rs. 5,000", {(5000, "rupee")}),
    ("three months or 3 months", {(3, "month")}),
    ("twenty-five years", {(25, "year")}),
    ("one hundred and twenty days", {(120, "day")}),
])
def test_figures_read_the_same_in_any_form(text, figures):
    assert _figures(text) == figures


PASSAGE = [{"source": "Muslim Family Laws Ordinance, 1961", "section": "5", "text": (
    "(4) Whoever contravenes the provisions of sub-section (3) shall be punishable with simple imprisonment for a "
    "term which may extent to three months, or with fine which may extend to one thous and rupees, or with both.")}]


def test_same_figures_in_other_words_are_not_flagged():
    answer = "Failing to report is punishable with up to 3 months' simple imprisonment or a fine of 1,000 rupees [1]."
    assert check_citations(answer, PASSAGE, consequences=True).unverified == []


def test_real_mismatches_are_still_caught():
    answer = "Failing to report is punishable with imprisonment for two years and a fine of five thousand rupees [1]."
    r = check_citations(answer, PASSAGE, consequences=True)
    assert r.unverified == ["Figure not in the retrieved text: 2 years", "Figure not in the retrieved text: Rs 5,000"]


def test_the_models_own_headings_are_ignored_but_the_body_is_checked():
    answer = "### Penalty\n**Legal consequences**\nAn unregistered marriage is void [1]."
    r = check_citations(answer, PASSAGE, consequences=True)
    assert r.unverified == ['Legal consequence not stated in the retrieved text: "void"']
    assert _mask_headings(answer).splitlines()[0].strip() == "" and "void" in _mask_headings(answer)


# --------------------------------------------------------------------------- cases (C8 item 4)

def test_readable_paragraphs():
    from app.kb.judgment_search import readable
    assert readable("The Court held that the wife is entitled to dower on demand.")
    assert not readable("قال الله تعالى وعاشروهن بالمعروف فان كرهتموهن فعسى ان تكرهوا شيئا " * 3 + " the Court")
    assert not readable("The verse " + "\ufefb\ufe8e\ufed3" * 4 + " was cited.")      # presentation forms
    assert not readable("12 34 --")


def _hit(doc, topics, score=0.7):
    para = (f"The learned counsel argued the {' and '.join(topics) or 'tax'} question at length, and having heard "
            "both sides and examined the record with care we find that the order under challenge was made within "
            "jurisdiction and calls for no interference by this Court.")
    return {"doc_id": doc, "display_name": doc, "case_name": f"{doc.title()} v. State", "court": "SC", "year": 2020,
            "case_number": None, "paragraph": 3, "text": para, "paragraph_text": para, "prefix": f"{doc} - para 3:",
            "score": score, "topics": topics}


def test_chat_cases_floor_and_family_topics(monkeypatch):
    from app.kb import judgment_search
    calls = []

    def fake(q, top_k, min_score):
        calls.append((top_k, min_score))
        return [_hit("bail case", ["bail"]), _hit("dower case", ["dower", "family"]), _hit("tax case", [])]
    monkeypatch.setattr(judgment_search, "search", fake)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    fam = chat.retrieve_judgments("dower mehr payment", "When must the husband pay the dower?")
    assert [j["doc_id"] for j in fam] == ["dower case"] and calls[0] == (settings.JUDGMENTS_CHAT_K * 8, 0.58)
    other = chat.retrieve_judgments("bail in a non-bailable offence", "When is bail granted?")
    # kb-v2 C13: only cases whose paragraph shares a distinctive term ("bail") with the question
    assert [j["doc_id"] for j in other] == ["bail case"] and calls[1] == (settings.JUDGMENTS_CHAT_K * 4, 0.58)


def test_case_rules_in_the_prompt():
    rules = chat.CASES_RULES
    assert "only in its own words" in rules and "general rule of law" in rules
    assert "Describe a statute section only in its own words or by its heading" in rules


# --------------------------------------------------------------------------- refusals (C8 item 5)

def test_foreign_and_refusal_detection():
    from app.kb import scope
    assert scope.foreign_only("What is the punishment for murder under the Indian Penal Code?")
    assert not scope.foreign_only("Is an Indian court decree enforceable in Pakistan?")
    assert not scope.foreign_only("What is the punishment for murder?")
    assert scope.is_refusal(chat.OUT_OF_SCOPE_REFUSAL["en"]) and scope.is_refusal(chat.OUT_OF_SCOPE_REFUSAL["ur"])
    assert not scope.is_refusal("Short answer: talaq needs notice to the Chairman [1]. " * 3)


@pytest.fixture
def chat_user(db_session):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User
    u = User(email="c8@gmail.com", password_hash=hash_password("x"), full_name="C Eight", role=UserRole.STUDENT,
             is_active=True, is_verified=True)
    db_session.add(u)
    db_session.commit()
    return u


class Model:
    def __init__(self, answer=None):
        self.answer, self.calls = answer, 0

    def chat(self, history, system=None):
        self.calls += 1
        return self.answer


def test_foreign_question_is_refused_with_no_sources(db_session, chat_user, monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(chat.embeddings, "build_or_load", lambda *a: 1)
    monkeypatch.setattr(chat, "rewrite_for_search", lambda q: (_ for _ in ()).throw(AssertionError("no rewrite")))
    svc = chat.LegalChatService(db_session)
    svc.ai = Model()
    reply = svc.send(chat_user, "What is the punishment for murder under the Indian Penal Code?")
    assert reply["response"] == chat.OUT_OF_SCOPE_REFUSAL["en"]
    assert reply["citations"] == [] and reply["sources"] == [] and svc.ai.calls == 0


def test_model_refusal_carries_no_sources_or_cases(db_session, chat_user, monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    monkeypatch.setattr(chat.embeddings, "build_or_load", lambda *a: 1)
    monkeypatch.setattr(chat, "rewrite_for_search", lambda q: q)
    monkeypatch.setattr(chat, "retrieve_passages", lambda *a, **k: [{"source": "Some Act", "text": "x",
                                                                     "relevance": 0.7}])
    monkeypatch.setattr(chat, "retrieve_judgments", lambda *a, **k: [_hit("a case", [])])
    svc = chat.LegalChatService(db_session)
    svc.ai = Model("This question is outside the scope of Pakistani law I can answer on.")
    reply = svc.send(chat_user, "Recommend a cricket bat for the law exam")
    assert reply["citations"] == [] and reply["sources"] == [] and reply["case_law"] == []


# --------------------------------------------------------------------------- repealed laws (C8 item 6)

@pytest.mark.parametrize("title, clean, repealed", [
    ("Women in Distress Act, 1996 (Repealed by Act XVI of 2020)", "Women in Distress Act, 1996", True),
    ("Boilers Act, 1923(Repeal by Ord. 52 of 2001, s,610)", "Boilers Act, 1923", True),
    ("Agricultural Census Act, 1958 (Repealed by Act XiV of 2011 s.3(w.e.f 31-05-2011))",
     "Agricultural Census Act, 1958", True),
    ("Some Act, 1900 (Repealed)", "Some Act, 1900", True),
    ("Federal Court(Repeal) Act, 2014", "Federal Court(Repeal) Act, 2014", False),       # a repealing Act: in force
    ("Jute (Repeal) Ordinance, 1983", "Jute (Repeal) Ordinance, 1983", False),
])
def test_repeal_read_from_the_title(title, clean, repealed):
    from app.scraping.stage import clean_title
    assert clean_title(title) == (clean, repealed)


def test_repealed_note_and_label():
    p = {"source": "Boilers Act, 1923", "section": "3", "heading": "Definitions", "status": "repealed", "text": "x"}
    assert chat.source_label(p).endswith("(REPEALED: this law has been repealed)")
    assert chat.repealed_note("A boiler must be registered [1].", [p]).endswith(
        "Note: Boilers Act, 1923 has been repealed and may no longer be in force.")
    assert chat.repealed_note("The Boilers Act, 1923 was repealed in 2001 [1].", [p]) == \
        "The Boilers Act, 1923 was repealed in 2001 [1]."
    assert chat.repealed_note("Fine [1].", [{**p, "status": "current"}]) == "Fine [1]."


def test_repealed_rule_only_when_a_repealed_passage_is_sent():
    class AI:
        system = ""

        def chat(self, history, system=None):
            AI.system = system
            return "Short answer: see [1]."
    p = {"source": "Boilers Act, 1923", "section": "3", "heading": "Definitions", "status": "repealed",
         "text": "In this Act boiler means ...", "relevance": 0.8}
    out = chat.compose_answer(AI(), [p], [{"role": "user", "content": "q"}], "en")
    assert "REPEALED LAWS:" in AI.system and "has been repealed" in out.text
    chat.compose_answer(AI(), [{**p, "status": "current"}], [{"role": "user", "content": "q"}], "en")
    assert "REPEALED LAWS:" not in AI.system


def test_search_leaves_out_repealed_unless_asked(monkeypatch):
    import numpy as np

    from app.ai import embeddings
    chunks = [{"doc_id": f"x/s{i}", "title": t, "section": "1", "heading": "h", "source_tier": 1, "category": None,
               "year": 1900, "jurisdiction": "Pakistan", "source_type": "statute", "source_url": None, "status": st,
               "source": "s", "audience": "general", "start": 0, "end": 5, "window": 1, "chunk_text": "text"}
              for i, (t, st) in enumerate((("Old Act, 1900", "repealed"), ("Live Act, 1950", "current")))]

    class Index:
        ntotal = 2

        def search(self, q, k):
            return np.array([[0.9, 0.8]]), np.array([[0, 1]])
    monkeypatch.setattr(index_v2._V2_INDEX, "index", Index())
    monkeypatch.setattr(index_v2._V2_INDEX, "chunks", chunks)
    monkeypatch.setattr(index_v2._V2_INDEX, "texts", {"x/s0": "old", "x/s1": "live"})
    monkeypatch.setattr(index_v2._V2_INDEX, "excluded", set())
    monkeypatch.setattr(embeddings, "embed", lambda t: np.ones((1, 4), np.float32))
    monkeypatch.setattr(embeddings, "_search_v1", lambda q, k, f=None, **kw: [
        {"source": "THE OLD COPY ACT, 1901", "text": "v1", "relevance": 0.7},
        {"source": "THE LIVE COPY ACT, 1951", "text": "v1", "relevance": 0.6}])
    monkeypatch.setattr(index_v2, "catalog_repealed", lambda: frozenset({"THE OLD COPY ACT, 1901"}))
    monkeypatch.setattr(settings, "HYBRID_SEARCH", False)
    default = [h["source"] for h in index_v2.search("q", 5)]
    assert default == ["Live Act, 1950", "THE LIVE COPY ACT, 1951"]
    wanted = [h["source"] for h in index_v2.search("q", 5, {"include_repealed": True})]
    assert wanted == ["Old Act, 1900", "Live Act, 1950", "THE OLD COPY ACT, 1901", "THE LIVE COPY ACT, 1951"]


def test_research_passes_include_repealed(monkeypatch):
    from app.services import research_service
    seen = []
    monkeypatch.setattr(research_service.embeddings, "build_or_load", lambda *a: 1)
    monkeypatch.setattr(research_service, "rewrite_for_search", lambda q: q)
    monkeypatch.setattr(research_service.embeddings, "search", lambda q, top_k, filters=None: seen.append(filters) or [])
    research_service.ResearchService(None).search("boilers", include_repealed=True)
    research_service.ResearchService(None).search("boilers")
    assert seen[0]["include_repealed"] is True and seen[1]["include_repealed"] is False


# --------------------------------------------------------------------------- supporting passages

def test_supporting_sections_join_once_the_gate_has_passed(monkeypatch):
    def h(doc, score, kb="v2"):
        return {"doc_id": doc, "kb": kb, "source": doc, "text": doc, "relevance": score}
    monkeypatch.setattr(chat, "family_scope_applies", lambda *a: False)
    monkeypatch.setattr(chat.embeddings, "similarity_threshold", lambda: 0.65)
    monkeypatch.setattr(chat.section_lookup, "section_passages", lambda q, p: [])
    monkeypatch.setattr(chat.exact_lookup, "exact_passages", lambda q: [])
    monkeypatch.setattr(settings, "KB_V2", True)
    monkeypatch.setattr(settings, "SECTION_EXPANSION", False)
    ranked = [h("a", 0.70), h("b", 0.58), {"source": "OLD", "text": "v1", "relevance": 0.60}, h("c", 0.50)]
    monkeypatch.setattr(chat.embeddings, "search", lambda q, top_k: list(ranked))
    monkeypatch.setattr(settings, "HYBRID_SEARCH", True)
    assert [p["source"] for p in chat.retrieve_passages("q", "q")] == ["a", "b"]     # section b joins; v1 and c don't
    monkeypatch.setattr(settings, "HYBRID_SEARCH", False)
    assert [p["source"] for p in chat.retrieve_passages("q", "q")] == ["a"]
    monkeypatch.setattr(settings, "HYBRID_SEARCH", True)
    monkeypatch.setattr(chat.embeddings, "search", lambda q, top_k: [h("b", 0.58)])
    monkeypatch.setattr(chat, "_scope_fallbacks", lambda *a: [])
    assert chat.retrieve_passages("q", "q") == []                                   # the gate is unchanged
