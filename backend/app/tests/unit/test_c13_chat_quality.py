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
