"""Citation grounding — unit cases built from real corpus passage formats,
plus a replay of real chat answers stored in fixtures/citation_replay.json:
3 answers from 2026-09-20 containing fabricated case law, and 4 clean
answers from 2026-09-25 (after the statute-only prompt fix)."""

import json
from pathlib import Path

import pytest

from app.ai.citation_check import check_citations, normalize_markers

MFLO_CSV = {
    "source": "Muslim Family Laws Ordinance, 1961",
    "text": (
        "Chapter I - Muslim Family Laws Ordinance 1969 Section 9 - Maintenance "
        "(1) If any husband fails to maintain his wife adequately, ... the "
        "Arbitration Council may issue a certificate specifying the amount."
    ),
}
MFLO_TOC = {
    "source": "THE MUSLIM FAMILY LAWS ORDINAN CE, 1961",
    "text": (
        "THE MUSLIM FAMILY LAWS ORDINAN CE, 1961 CONTENTS SECTIONS : 1. Short "
        "title . 6. Polygamy . 7. Talaq . 8. Dissolution of marriage otherwise "
        "than by talaq . 9. Maintenance . 10. Dower ."
    ),
}
FCA_PDF = {
    "source": "THE WEST PAKISTAN FAMILY COURTS ACT, 1964",
    "text": (
        "25. Family Court deemed to be a District Court for purposes of "
        "Guardians and Wards Act, 1890.―A Family Court shall be deemed ... "
        "3[25-A. Transfer of cases."
    ),
}
CRPC_XREF = {
    "source": "Code of Criminal Procedure, 1898",
    "text": "Section 54 - arrest of a person reasonably suspected of an offence "
            "under section 379 of the Pakistan Penal Code.",
}


def test_grounded_section_is_left_alone():
    answer = "Under Section 9 of the Muslim Family Laws Ordinance, 1961 the wife may apply [1]."
    r = check_citations(answer, [MFLO_CSV])
    assert r.text == answer
    assert r.unverified == [] and len(r.verified) == 1


def test_missing_section_is_flagged_with_note():
    answer = "Talaq notice is governed by Section 7 of the Muslim Family Laws Ordinance [1]."
    r = check_citations(answer, [MFLO_CSV])
    assert "Section 7 (unverified)" in r.text
    assert r.text.rstrip().endswith("Section 7 (Muslim Family Laws Ordinance).")
    assert "Note:" in r.text


def test_statute_aware_matching_rejects_wrong_act():
    # §9 exists in the MFLO passage, but the answer attributes it to the PPC.
    r = check_citations("See Section 9 PPC.", [MFLO_CSV])
    assert r.unverified and "(unverified)" in r.text


def test_ocr_split_title_and_toc_headings_count():
    r = check_citations("Section 8 of the MFLO deals with khula-type dissolution.", [MFLO_TOC])
    assert r.unverified == []


def test_alphanumeric_section_and_unicode_dashes():
    # Real output uses narrow no-break spaces and non-breaking hyphens.
    r = check_citations("Transfer is under Sec. 25‑A of the Family Courts Act.", [FCA_PDF])
    assert r.unverified == []


def test_range_is_expanded_and_partially_flagged():
    r = check_citations("MFLO Sections 8-11 cover this.", [MFLO_TOC])
    assert "(unverified: 11)" in r.text


def test_cross_reference_counts_for_the_named_statute():
    r = check_citations("Theft is punishable under section 379 of the Pakistan Penal Code.", [CRPC_XREF])
    assert r.unverified == []


def test_urdu_section_reference_with_urdu_digits():
    r = check_citations("دفعہ ۷ کے تحت نوٹس دینا لازم ہے۔", [MFLO_CSV], lang="ur")
    assert "(غیر مصدقہ)" in r.text and "نوٹ:" in r.text


def test_case_citation_sentence_removed():
    answer = (
        "The wife may seek maintenance [1]. In Mst. Saeeda v. Mst. Khadija, "
        "PLD 2005 SC 1234, the Supreme Court held otherwise. File before the Family Court."
    )
    r = check_citations(answer, [MFLO_CSV])
    assert "Saeeda" not in r.text and "PLD" not in r.text and "Supreme Court" not in r.text
    assert r.text.startswith("The wife may seek maintenance [1].")
    assert r.text.endswith("File before the Family Court.")
    assert "[case citation removed" in r.text


def test_case_citation_in_table_cell_removes_cell_only():
    answer = (
        "| Rule | Basis |\n|---|---|\n"
        "| Notice to chairman | Judicial practice (e.g., *Mst. X v. Mst. Y*, PLD 2005 SC 1). |\n"
    )
    r = check_citations(answer, [MFLO_CSV])
    assert "| Notice to chairman |" in r.text and "PLD" not in r.text
    assert r.text.count("|") == answer.count("|")


def test_case_citation_present_in_passage_is_kept():
    passage = {"source": "Some Act", "text": "as held in PLD 1967 SC 97 the rule is"}
    r = check_citations("This follows PLD 1967 SC 97.", [passage])
    assert r.removed_case_citations == [] and "PLD 1967 SC 97" in r.text


def test_out_of_range_source_markers_removed():
    r = check_citations("Maintenance is covered [1][7].", [MFLO_CSV])
    assert r.text == "Maintenance is covered [1]." and r.removed_markers == ["[7]"]


def test_year_after_alias_is_not_a_section():
    r = check_citations("the Muslim Family Laws Ordinance (MFLO 1961) applies", [MFLO_CSV])
    assert r.verified == [] and r.unverified == []


# ---- Replay of real stored answers ------------------------------------------

_REPLAY = json.loads(
    (Path(__file__).parent / "fixtures" / "citation_replay.json").read_text(encoding="utf-8")
)
_FABRICATED = {  # every fabricated reference in the 3 pre-fix answers
    "00ef66b8-939a-4d11-bc97-6966ea55e449": [
        "PLD 1995 SC 123", "PLD 2002 SC 456", "PLD 2008 SC 789",
        "Mst. Ayesha v. Mst. Fatima", "Mst. Saima v. Mst. Nazeer", "Mst. Hina v. Mst. Farida"],
    "df86b590-8bd6-412f-b366-91dab265e90f": ["PLD 2000 SC 1232", "Mst. Shabana v. Mst. Sultana"],
    "c4719d31-8601-4b53-87bd-4c9a4ebbf5e7": ["PLD 2005 SC 1234", "Mst. Saeeda v. Mst. Khadija"],
}


@pytest.mark.parametrize("case", [c for c in _REPLAY if c["kind"] == "fabricated"], ids=lambda c: c["id"][:8])
def test_replay_fabricated_citations_all_removed(case):
    r = check_citations(case["answer"], case["passages"])
    expected = _FABRICATED[case["id"]]
    assert sorted(r.removed_case_citations) == sorted(expected)
    shown = r.text.translate({0x202F: 32, 0xA0: 32})
    for cite in expected:
        assert cite not in shown


@pytest.mark.parametrize("case", [c for c in _REPLAY if c["kind"] == "clean"], ids=lambda c: c["id"][:8])
def test_replay_clean_answers_unchanged(case):
    r = check_citations(case["answer"], case["passages"])
    assert r.text == case["answer"]
    assert r.unverified == [] and r.removed_case_citations == []


# ----- The model's own "【n】" citation format --------------------------------
# gpt-oss sometimes cites as "【5】" or "【5†L1-L3】" (18% of stored answers,
# Sept 2026). These are rewritten to "[n]" before any check runs.

@pytest.mark.parametrize("raw, expected", [
    ("fine up to Rs 5,000【5】.", "fine up to Rs 5,000[5]."),
    ("to the Chairman【5†L1-L3】.", "to the Chairman[5]."),
    ("pregnancy【6†L5】 rule", "pregnancy[6] rule"),
    ("both【4, 5】.", "both[4][5]."),
    ("【 2 †source】", "[2]"),
    ("plain [3] marker and a link [text](http://x)", "plain [3] marker and a link [text](http://x)"),
    ("【not a number】", "【not a number】"),
])
def test_normalize_markers(raw, expected):
    assert normalize_markers(raw) == expected


def test_fullwidth_markers_in_range_are_kept_as_brackets():
    r = check_citations("Maintenance may be certified【1】 and ordered【1†L2-L3】.", [MFLO_CSV])
    assert "【" not in r.text
    assert r.text.count("[1]") == 2
    assert r.removed_markers == []


def test_fullwidth_marker_out_of_range_is_removed():
    # One passage supplied, so "【9】" / "【9†L1-L3】" point at nothing.
    r = check_citations("Maintenance may be certified【1】 and more【9】 and【9†L1-L3】.", [MFLO_CSV])
    assert "[1]" in r.text
    assert "9" not in r.text and "【" not in r.text
    assert r.removed_markers == ["[9]", "[9]"]
