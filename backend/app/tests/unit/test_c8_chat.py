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
    assert r.unverified == ["Penalty figure not in the retrieved text: 2 years, 5000 rupees"]


def test_the_models_own_headings_are_ignored_but_the_body_is_checked():
    answer = "### Penalty\n**Legal consequences**\nAn unregistered marriage is void [1]."
    r = check_citations(answer, PASSAGE, consequences=True)
    assert r.unverified == ['Legal consequence not stated in the retrieved text: "void"']
    assert _mask_headings(answer).splitlines()[0].strip() == "" and "void" in _mask_headings(answer)
