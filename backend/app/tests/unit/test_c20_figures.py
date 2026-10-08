"""kb-v2 C20: no false figure alarms from section numbers or sections cited together; real errors still caught."""

import pytest

from app.ai.citation_check import _figures, check_citations

S302 = {"source": "Pakistan Penal Code, 1860", "section": "302", "text": (
    "302. Punishment of qatl-i-amd.- Whoever commits qatl-i-amd shall be (a) punished with death as qisas; "
    "(b) punished with death or imprisonment for life as ta'zir; or (c) punished with imprisonment of either "
    "description for a term which may extend to twenty-five years, where the punishment of qisas is not "
    "applicable.")}
S308 = {"source": "Pakistan Penal Code, 1860", "section": "308", "text": (
    "308. Punishment in qatl-i-amd not liable to qisas.- Where an offender is not liable to qisas under "
    "section 306 or the qisas is not enforceable under section 307, he shall be liable to diyat and may be "
    "punished with imprisonment of either description which may extend to twenty-five years as ta'zir.")}
S379 = {"source": "Pakistan Penal Code, 1860", "section": "379", "text": (
    "379. Punishment for theft.- Whoever commits theft shall be punished with imprisonment of either "
    "description for a term which may extend to three years, or with fine, or with both.")}


def check(answer, passages, **kw):
    return check_citations(answer, passages, consequences=True, **kw)


@pytest.mark.parametrize("text, figures", [
    ("Under s. 302, the court may award death.", set()),                 # "rs. 302" inside "under s. 302"
    ("Murderers 306 and offenders 307 are dealt with.", set()),          # "rs" ending other words
    ("Section 302, 308 apply.", set()),
    ("Under sections 306, 307, 25 years may be given.", {(25, "year")}),  # never 30630725 years
    ("Under s. 302 twenty-five years may be given.", {(25, "year")}),
    ("A fine of Rs 50,000 or Rs. 2,50,00,000 or PKR 1,000 or five thousand rupees.",
     {(50000, "rupee"), (25000000, "rupee"), (1000, "rupee"), (5000, "rupee")}),
])
def test_currency_only_with_a_real_marker_and_numbers_never_join(text, figures):
    assert _figures(text.lower()) == figures


def test_correct_murder_answer_has_no_false_items():
    answer = ("Short answer: murder is punished with death, imprisonment for life, or up to twenty-five years [1].\n\n"
              "- Under s. 302 and s. 308 the court may award death or imprisonment up to twenty-five years [1] [2].\n"
              "- Where the offender is not liable to qisas under sections 306, 307, he is liable to diyat and may "
              "also get imprisonment up to 25 years [2].\n")
    r = check(answer, [S302, S308])
    assert not any("is given for section" in u or "Figure not in" in u for u in r.unverified)


def test_a_figure_from_another_section_cited_in_the_same_paragraph_counts():
    answer = "Sections 302 and 308 apply [1] [2]. Under s. 308 imprisonment may extend to twenty-five years [2]."
    assert check(answer, [S302, S308]).unverified == []


def test_a_figure_stated_in_a_case_paragraph_counts():
    case = {"display_name": "A v. State", "case_name": "A v. State", "case_number": None, "paragraph": 4,
            "paragraph_text": "The appellant was sentenced to fourteen years under section 302(c)."}
    answer = "Under s. 302 the trial court gave fourteen years in that case [1]."
    r = check(answer, [S302], judgments=[case])
    assert not any("14 years" in u for u in r.unverified)


# --------------------------------------------------------------------------- real errors still caught

def test_a_wrong_amount_is_still_flagged():
    r = check("Theft is punished with up to three years or a fine of Rs 50,000 [1].", [S379])
    assert "Figure not in the retrieved text: Rs 50,000" in r.unverified


def test_a_wrong_period_is_still_flagged():
    r = check("Theft is punished with imprisonment for five years under section 379 [1].", [S379])
    assert any("5 years" in u for u in r.unverified)


def test_a_figure_none_of_the_cited_sections_states_is_still_flagged():
    r = check("Under s. 302 and s. 308 imprisonment may extend to forty years [1] [2].", [S302, S308])
    assert "40 years is given for section 302, 308, but that section's retrieved text doesn't state it" in r.unverified


def test_a_wrong_section_number_is_still_flagged():
    r = check("Murder is punished under section 309 of the Pakistan Penal Code [1].", [S302, S308])
    assert any(u.startswith("section 309") for u in r.unverified)
