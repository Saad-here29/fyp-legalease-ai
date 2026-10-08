"""kb-v2 C13: chat answer quality, on synthetic text (no model calls)."""

import pytest

from app.ai.citation_check import check_citations

FINE_ACT = {"source": "Sample Offences Act, 2005", "section": "7", "heading": "Penalty", "text": (
    "7. Penalty.- Whoever commits the offence under this Act shall be punishable with imprisonment for a term "
    "which may extend to ten years but shall not be less than three years, and with fine which may extend to "
    "twenty-five million rupees, and the property shall be liable to forfeiture.")}
DISPOSSESSION = {"source": "Illegal Dispossession Act, 2005", "section": "3", "heading": "Prevention of illegal "
                 "possession of property", "text": (
                     "3. (2) Whoever contravenes the provisions of sub-section (1) shall be punished with "
                     "imprisonment which may extend to ten years and with fine.")}


def check(answer, passages=(FINE_ACT,)):
    return check_citations(answer, list(passages), consequences=True)


# --------------------------------------------------------------------------- 1a: the body is never marked

def test_answer_body_is_never_edited():
    answer = "Under section 9 of the Sample Offences Act the penalty is death [1]."
    r = check(answer)
    assert r.text.startswith(answer) and "(unverified)" not in r.text
    assert r.unverified and r.text.split("\n\nNote:")[0] == answer


# --------------------------------------------------------------------------- 1d: number words and scales

@pytest.mark.parametrize("answer", [
    "The offence carries imprisonment of three to ten years and a fine of up to Rs 25 million [1].",
    "It is punishable with imprisonment for 3-10 years and a fine up to Rs. 2,50,00,000 [1].",
    "Imprisonment may extend to ten years, with a fine of twenty-five million rupees [1].",
    "A fine of up to 2.5 crore rupees and imprisonment for between three and ten years may be imposed [1].",
])
def test_equivalent_figures_are_not_flagged(answer):
    assert check(answer).unverified == []


def test_compound_numbers_are_read_whole():
    text = {"source": "Sample Procedure Act, 2001", "text": "The appeal shall be filed within one hundred and "
            "twenty days, failing which the court may impose a fine of five thousand rupees."}
    assert check("The appeal must be filed within 120 days, or a fine of Rs. 5,000 may be imposed [1].",
                 [text]).unverified == []


def test_a_real_mismatch_is_still_flagged():
    r = check("The offence is punishable with imprisonment for five years [1].")
    assert r.unverified == ["Figure not in the retrieved text: 5 years"]


def test_a_wrong_amount_is_still_flagged():
    r = check("The offence is punishable with a fine of Rs 25 lakh [1].")
    assert r.unverified == ["Figure not in the retrieved text: Rs 2,500,000"]


# --------------------------------------------------------------------------- 1b: statute titles

def test_words_in_a_statute_title_are_never_flagged():
    answer = ("Under the Illegal Dispossession Act, 2005, whoever dispossesses an owner shall be punished with "
              "imprisonment which may extend to ten years [1].")
    r = check(answer, [DISPOSSESSION])
    assert r.unverified == [] and r.text == answer


# --------------------------------------------------------------------------- 1c: generic words

@pytest.mark.parametrize("word", ["an offence", "an offense", "illegal", "a criminal offence", "punishable",
                                  "liable to a penalty", "liable to punishment"])
def test_generic_consequence_words_are_not_checked(word):
    passage = {"source": "Sample Registration Act, 1990", "text": "Every deed shall be registered within thirty "
               "days of its execution."}
    r = check(f"Failing to register the deed is {word} [1].", [passage])
    assert r.unverified == []


@pytest.mark.parametrize("claim, item", [
    ("is void", '"void"'), ("is voidable", '"voidable"'), ("is invalid", '"invalid"'),
    ("is punishable with death", '"punishable with death"'),
    ("carries imprisonment for life", '"imprisonment for life"'),
])
def test_specific_consequences_are_checked(claim, item):
    passage = {"source": "Sample Registration Act, 1990", "text": "Every deed shall be registered within thirty "
               "days of its execution."}
    r = check(f"An unregistered deed {claim} [1].", [passage])
    assert r.unverified == [f"Legal consequence not stated in the retrieved text: {item}"]


def test_forfeiture_stated_in_the_text_passes():
    assert check("The property is liable to forfeiture [1].").unverified == []


# --------------------------------------------------------------------------- 2: case law in Chat

from app.core.config import settings  # noqa: E402
from app.kb import judgments as jd  # noqa: E402
from app.services import legal_chat_service as chat  # noqa: E402

PROSE = ("The petitioner was dispossessed of the land by the respondents without any lawful authority, and the "
         "complaint under section 3 of the Illegal Dispossession Act was rightly entertained by the trial court, "
         "which found that possession had been taken by force and directed its restoration to the owner.")
STATUTE = [{"source": "Illegal Dispossession Act, 2005", "section": "3", "text": "3. Prevention of illegal possession."}]


def _case(doc, para_text, *, name="Ahmad Khan v. Bashir Ahmad", number="Crl.A. 12 of 2019", para=7, score=0.7):
    return {"doc_id": doc, "display_name": name, "case_name": name, "court": "Supreme Court of Pakistan",
            "year": 2019, "case_number": number, "paragraph": para, "text": para_text, "paragraph_text": para_text,
            "prefix": f"{name} - para {para}:", "score": score, "topics": []}


@pytest.mark.parametrize("text", [
    "Leave to appeal is granted.",                                                         # under 25 words
    "IN THE SUPREME COURT OF PAKISTAN (Appellate Jurisdiction) PRESENT: Mr. Justice A, Mr. Justice B. Ahmad Khan "
    "Petitioner Versus Bashir Ahmad Respondents. For the petitioner: Mr. C. Date of hearing: 1.1.2019. " * 2,
    "Reliance was placed on PLD 2010 SC 1, 2015 SCMR 33, 2012 SCMR 900, PLD 2001 SC 10 and 2019 SCMR 4 by "
    "the learned counsel.",                                                                # a citation list
    "(Possession) (Owner) (Complaint) (Dispossession) (Property) (Restoration) (Trespass) (Occupier) (Force) "
    "(Land) (Order) with the words of the Act read as a whole and applied to the owner of property here.",
    "1. PLD 2010 SC 1 at page 9.\n2. 2015 SCMR 33 at page 40.\n3. 2012 SCMR 900.\n4. PLD 2001 SC 10.\n"
    "5. 2019 SCMR 4 at page 7 of the report.",                                             # a footnote list
])
def test_unusable_paragraphs_are_dropped_at_any_paragraph_number(text):
    assert not chat.case_paragraph_ok(text)


def test_readable_prose_is_kept():
    assert chat.case_paragraph_ok(PROSE)


def test_a_case_must_share_a_distinctive_term():
    terms = chat.distinctive_terms("Someone took over my land by force, what can I do?", STATUTE)
    assert chat.shares_term(PROSE, terms)                                  # statute name and section 3
    unrelated = ("The tax assessment was framed after notice, the assessee was heard at length and the appellate "
                 "tribunal rightly held that the addition to income was justified on the material before it.")
    assert not chat.shares_term(unrelated, terms)
    generic = chat.distinctive_terms("Can I file an appeal in the High Court?", [])
    assert generic["terms"] == set()                                       # court-process words aren't distinctive


@pytest.mark.parametrize("rec, title", [
    ({"case_name": "Ahmad Khan v. Bashir Ahmad", "court": "Supreme Court of Pakistan", "year": 2019},
     "Ahmad Khan v. Bashir Ahmad (Supreme Court of Pakistan, 2019)"),
    ({"case_name": None, "case_number": "C.P. 9 of 2020", "court": "Supreme Court of Pakistan", "year": 2020},
     "C.P. 9 of 2020 (Supreme Court of Pakistan)"),
    ({"case_name": "Supreme Court of Pakistan", "case_number": None, "court": "Supreme Court of Pakistan",
      "year": 2021}, None),
    ({"case_name": None, "case_number": None, "court": "Supreme Court of Pakistan", "year": 2021}, None),
    ({"case_name": "Judgment (Supreme Court of Pakistan)", "court": "Supreme Court of Pakistan", "year": 2021}, None),
])
def test_case_titles(rec, title):
    assert jd.case_title(rec) == title


def test_chat_cases_are_filtered_titled_and_deduplicated(monkeypatch):
    from app.kb import judgment_search
    hits = [_case("a", PROSE), _case("b", PROSE.replace("rightly", "correctly"), name="Ali v. State"),
            _case("c", PROSE, name=None, number=None), _case("d", "Leave granted.", para=12)]
    monkeypatch.setattr(judgment_search, "search", lambda q, top_k, min_score: hits)
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    got = chat.retrieve_judgments("land taken by force", "Someone took my land by force", STATUTE)
    assert [j["doc_id"] for j in got] == ["a"]                          # b duplicates a; c has no title; d is short
    assert got[0]["display_name"] == "Ahmad Khan v. Bashir Ahmad (Supreme Court of Pakistan, 2019)"
    assert got[0]["prefix"] == "Ahmad Khan v. Bashir Ahmad (Supreme Court of Pakistan, 2019) - para 7:"


def test_k_zero_turns_cases_off_in_chat_only(monkeypatch):
    from app.kb import judgment_search
    from app.services.research_service import ResearchService
    calls = []
    monkeypatch.setattr(judgment_search, "search", lambda q, **k: calls.append(k) or [_case("a", PROSE)])
    monkeypatch.setattr(settings, "JUDGMENTS_V2", True)
    monkeypatch.setattr(settings, "JUDGMENTS_CHAT_K", 0)
    assert chat.retrieve_judgments("land", "my land", STATUTE) == [] and calls == []
    svc = ResearchService.__new__(ResearchService)
    svc._search_query = ("land", "land")
    assert [r.doc_id for r in svc.search_judgments("land")] == ["a"]     # Research still lists judgments
    assert settings.JUDGMENTS_CHAT_MIN == 0.58


# --------------------------------------------------------------------------- 3: citation numbering and spacing

def _p(source, text, doc=None):
    return {"source": source, "text": text, **({"doc_id": doc} if doc else {})}


def test_sources_are_renumbered_without_gaps_in_citation_order():
    passages = [_p("A Act", "a"), _p("B Act", "b"), _p("C Act", "c"), _p("D Act", "d")]
    text, ordered = chat.renumber_sources("Short answer: x [4]. More [1][4]. Note: [4] cites D Act, but ...", passages)
    assert text == "Short answer: x [1]. More [2] [1]. Note: [1] cites D Act, but ..."
    assert [p["source"] for p in ordered] == ["D Act", "A Act", "B Act", "C Act"]     # cited first, then the rest


def test_the_same_source_twice_is_merged():
    passages = [_p("A Act", "a", "a/s1"), _p("B Act", "b", "b/s2"), _p("A Act", "a", "a/s1")]
    text, ordered = chat.renumber_sources("See [3] and [2][1].", passages)
    assert text == "See [1] and [2] [1]." and [p["doc_id"] for p in ordered] == ["a/s1", "b/s2"]
    text, _ = chat.renumber_sources("See [1][3].", passages)
    assert text == "See [1]."                                                          # merged pair shown once


def test_markers_get_a_space_before_them():
    passages = [_p("A Act", "a"), _p("B Act", "b")]
    text, _ = chat.renumber_sources("Registered[1].\n[2] starts a line; (see [1]) and [link](http://x).", passages)
    assert text == "Registered [1].\n[2] starts a line; (see [1]) and [link](http://x)."


# --------------------------------------------------------------------------- 4: the right section

S6 = {"source": "Sample Tenancy Act, 2010", "section": "6", "heading": "Notice", "text": (
    "6. Notice.- (1) The landlord shall give the tenant notice in writing. (2) The notice shall state the grounds.")}
S7 = {"source": "Sample Tenancy Act, 2010", "section": "7", "heading": "Penalty", "text": (
    "7. Penalty.- Whoever contravenes section 6(2) shall be punishable with imprisonment which may extend to "
    "six months, or with fine which may extend to fifty thousand rupees.")}


def test_prompt_rules_on_section_numbers(monkeypatch):
    monkeypatch.setattr(settings, "KB_V2", True)
    prompt = chat.build_system_prompt("[1] Source: Sample Tenancy Act, 2010 - s.7 Penalty\n...", "en")
    assert "never under a section number that is only mentioned inside a passage's text" in prompt
    assert '"see section N"' in prompt
    monkeypatch.setattr(settings, "KB_V2", False)
    assert "SECTION NUMBERS" not in chat.build_system_prompt("x", "en")          # flags off: prompt unchanged


def test_a_penalty_under_the_right_section_passes():
    r = check("Under section 7, failing to state the grounds is punishable with imprisonment up to six months or "
              "a fine up to Rs. 50,000 [2].", [S6, S7])
    assert r.unverified == []


def test_a_penalty_under_a_section_only_mentioned_in_the_text_is_listed():
    r = check("Under section 6(2), failing to state the grounds is punishable with imprisonment up to six months "
              "[1].", [S6, S7])
    assert r.unverified == ["6 months is given for section 6, but that section's retrieved text doesn't state it"]
    assert "(unverified)" not in r.text.split("\n\nNote:")[0]


def test_a_section_that_was_not_retrieved_cannot_carry_a_figure():
    r = check("Section 9 allows thirty days to appeal [1].", [S6, S7])
    assert "30 days is given for section 9, but that section's retrieved text doesn't state it" in r.unverified


# --------------------------------------------------------------------------- 5: neighbouring sections

@pytest.fixture
def act(monkeypatch):
    from app.kb import catalog
    ids = [f"core/sample-family-act/s{n}" for n in (7, 8, 9, 10)]
    records = {d: {"doc_id": d, "section": d.rsplit("s", 1)[1], "heading": f"Heading {d[-1]}",
                   "text": f"Text of {d}.", "status": "repealed" if d.endswith("s10") else "current",
                   "_law": "sample-family-act"} for d in ids}
    data = {"laws": {"sample-family-act": {"title": "Sample Family Act, 1999", "record_ids": ids, "scraped": False}},
            "records": records}
    monkeypatch.setattr(catalog, "data", lambda: data)
    monkeypatch.setattr(settings, "KB_V2", True)
    return ids


def _sec(d, score, kb="v2"):
    return {"source": "Sample Family Act, 1999", "doc_id": d, "kb": kb, "relevance": score, "text": "t",
            "status": "current"}


def test_neighbours_join_after_the_retrieved_passages(act):
    other = _sec("core/other-act/s3", 0.66)
    out = chat.add_neighbours([_sec(act[1], 0.72), other])
    assert [p["doc_id"] for p in out] == [act[1], "core/other-act/s3", act[0], act[2]]
    assert out[2]["neighbour"] and out[2]["section"] == "7" and out[2]["text"] == f"Text of {act[0]}."


def test_no_neighbours_below_the_gate_or_for_old_index_chunks(act):
    assert chat.add_neighbours([_sec(act[1], 0.60)]) == [_sec(act[1], 0.60)]
    v1 = {"source": "Old corpus", "text": "x", "relevance": 0.9}
    assert chat.add_neighbours([v1]) == [v1]


def test_neighbours_already_retrieved_or_repealed_are_not_added(act):
    out = chat.add_neighbours([_sec(act[2], 0.8), _sec(act[1], 0.7)])
    assert [p["doc_id"] for p in out] == [act[2], act[1]]          # s8 already there; s10 repealed
