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
