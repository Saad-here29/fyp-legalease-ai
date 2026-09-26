"""Clause / risk extraction from the LLM document summary."""

from app.ai.summary_sections import extract_clauses_and_risks

BOLD_HEADINGS = """**1) Summary (plain-language)**
- The lessee rents the premises for two years.

---

**2) Parties (named individuals / entities)**

| Role | Name |
|------|------|
| Lessor | Ahmed Khan |

**4) Key clauses / obligations**
- **Rent:** Rs. 50,000 per month, payable by the 5th.
- **Termination** – either party on 60 days' written notice.
1. Security deposit of Rs. 150,000, refundable.

**5) Risk flags or missing standard clauses**
- No dispute-resolution / arbitration clause.
- *Governing law* not stated.
"""

TABLE_AND_HASH_HEADINGS = """### 4. Key Clauses
| Clause | Obligation |
|---|---|
| Confidentiality | Recipient keeps information secret for 3 years |
| Return of material | All copies returned on request |

### 5. Risk Flags
None identified beyond a missing <br> jurisdiction clause.
"""


def test_bold_headings_with_bullets():
    clauses, risks = extract_clauses_and_risks(BOLD_HEADINGS)
    assert clauses == [
        "Rent: Rs. 50,000 per month, payable by the 5th.",
        "Termination – either party on 60 days' written notice.",
        "Security deposit of Rs. 150,000, refundable.",
    ]
    assert risks == [
        "No dispute-resolution / arbitration clause.",
        "Governing law not stated.",
    ]


def test_tables_and_markdown_headings():
    clauses, risks = extract_clauses_and_risks(TABLE_AND_HASH_HEADINGS)
    assert clauses == [
        "Confidentiality — Recipient keeps information secret for 3 years",
        "Return of material — All copies returned on request",
    ]
    assert risks == ["None identified beyond a missing; jurisdiction clause."]


def test_intro_and_wrap_up_paragraphs_are_not_items():
    # Real gpt-oss output: a table, then an "Overall, ..." paragraph.
    text = (
        "**5) Risk flags / missing standard clauses**\n\n"
        "The main gaps are:\n\n"
        "| Issue | Why it matters |\n|-------|----------------|\n"
        "| **No governing law** | Jurisdiction unclear. |\n"
        "| **No enforcement** | Targets are aspirational. |\n\n"
        "*Overall, the document is informational rather than binding.*\n"
    )
    _, risks = extract_clauses_and_risks(text)
    assert risks == ["No governing law — Jurisdiction unclear.",
                     "No enforcement — Targets are aspirational."]


def test_paragraphs_used_when_section_has_no_list():
    text = "**5) Risk flags**\nNo material risks were identified.\n"
    assert extract_clauses_and_risks(text) == ([], ["No material risks were identified."])


def test_unstructured_summary_gives_empty_lists():
    assert extract_clauses_and_risks("Just a paragraph with no sections.") == ([], [])
    assert extract_clauses_and_risks("") == ([], [])


def test_sections_found_by_title_when_numbering_drifts():
    text = "**3) Key clauses**\n- Clause A\n**4) Risk flags**\n- Risk B\n"
    assert extract_clauses_and_risks(text) == (["Clause A"], ["Risk B"])
