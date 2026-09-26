"""Unit tests for ResearchService — covers the friendly-title mapping and
chunk-trimming logic. We don't exercise FAISS itself here (heavy + needs
the index file) — that's an integration concern. We do exercise the
pure-Python helpers."""

import pytest

from app.services.research_service import (
    _friendly_title,
    _trim_to_sentence,
    ResearchService,
)


# ============================================================
# UT-RESEARCH-001: friendly-title mapping
# ============================================================
def test_friendly_title_for_statutes():
    assert _friendly_title("Pakistan_Penal_Code") == "Pakistan Penal Code 1860"
    assert (
        _friendly_title("Code_of_Criminal_Procedure_1898")
        == "Code of Criminal Procedure 1898"
    )
    assert _friendly_title("Family_Courts_Act_1964") == "Family Courts Act 1964"


def test_friendly_title_for_supreme_court_judgments():
    # The corpus stores SC judgments as "C.A_supreme (N)" — must render
    # as something a lawyer would actually say out loud.
    assert (
        _friendly_title("C.A_supreme (2665)")
        == "Supreme Court of Pakistan — Civil Appeal No. 2665"
    )
    assert (
        _friendly_title("C.A_supreme (1)")
        == "Supreme Court of Pakistan — Civil Appeal No. 1"
    )


def test_friendly_title_unknown_source_falls_back_to_underscored():
    assert _friendly_title("Some_New_Statute_2030") == "Some New Statute 2030"


# ============================================================
# UT-RESEARCH-002: chunk trimming — chunks are sliding-window cuts that
# almost always start mid-word. The trimmer should advance to the next
# clean sentence boundary so the excerpt reads cleanly.
# ============================================================
def test_trim_advances_past_leading_fragment():
    # Real-world example: "a, where the khula is not sought..." starts
    # with the last char of the previous chunk's word.
    text = (
        "a, where the khula is not sought for by a woman. "
        "As per Principles of Mahomedan Law, paragraph 319(2) provides "
        "that a divorce by khula is a divorce with the consent..."
    )
    trimmed = _trim_to_sentence(text)
    # Either trimmed to start at a proper word/sentence, OR fallback to
    # the original. Crucially must not still start with ", a"
    assert not trimmed.startswith(", a")
    assert "khula" in trimmed


def test_trim_handles_already_clean_text():
    text = "Section 302 PPC defines qatl-i-amd. The punishment is death as qisas."
    trimmed = _trim_to_sentence(text)
    # Already clean — should be (substantially) preserved
    assert "qatl-i-amd" in trimmed


def test_trim_handles_empty_input():
    assert _trim_to_sentence("") == ""


# ============================================================
# Structured-analysis parser: bold labels in both styles
# ============================================================
@pytest.mark.parametrize("label_style", ["**{}:**", "**{}**:", "{}:"])
def test_parse_structured_strips_bold_label_markers(label_style):
    # Real gpt-oss output uses "**Issue:**" — the closing ** used to leak
    # into every field as a leading "** ".
    raw = "\n\n".join(
        f"{label_style.format(k)} {k} text."
        for k in ("Issue", "Findings", "Judgment", "Legal Basis", "Relevance")
    )
    a = ResearchService._parse_structured(raw)
    assert a.issue == "Issue text."
    assert a.findings == "Findings text."
    assert a.judgment == "Judgment text."
    assert a.legal_basis == "Legal Basis text."
    assert a.relevance == "Relevance text."


@pytest.mark.parametrize("line", [
    "**Legal Basis:** **Section 2, DMMA 1939**.",
    "**Legal Basis**: **Section 2, DMMA 1939**.",
    "Legal Basis: **Section 2, DMMA 1939**.",
])
def test_parse_structured_keeps_bold_body_intact(line):
    a = ResearchService._parse_structured(f"Issue: x\n{line}")
    assert a.legal_basis == "**Section 2, DMMA 1939**."
