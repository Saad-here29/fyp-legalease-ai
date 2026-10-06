"""kb-v2 sectioner and statute records (offline, small fixtures in the corpus's real shapes)."""

import json
from collections import Counter
from pathlib import Path

import pytest

from app.kb.records import CORPUS_SOURCE, make_records, validate
from app.kb.sectioner import (
    join_ocr_splits,
    page_spans,
    parse_toc,
    split,
    strip_footnotes,
    windows,
)

# Pakistan Code PDF text, flattened: CONTENTS, enacting formula, "N. Heading.—",
# per-page footnotes before "Page N of M", an amendment marker, a SCHEDULE.
PDF_FIXTURE = (
    "Page 1 of 3 THE SAMPLE FAMILY ACT, 1964 CONTENTS 1. Short title and extent . 2. Definitions . "
    "3. Maintenance . 3A. Interim maintenance . 4. [Omitted.] SCHEDULE "
    "Page 2 of 3 THE SAMPLE FAMILY ACT, 1964 ACT NO. XXXV OF 1964 [18th July, 1964] An Act to make "
    "provision for family courts. WHEREAS it is expedient; It is hereby enacted as follows:— "
    "1. Short title and extent.—(1) This Act may be called the Sample Family Act, 1964. "
    "2. Definitions .― In this Act, (a) “Court” means a Family Court; 2[(b) “wi fe” includes a "
    "divorced wife;] 1Subs. by Ord. 55 of 2002, s. 2. 2Ins. ibid. Page 3 of 3 "
    "3. Maintenance.—A Court may order maintenance. 3A. Interim maintenance.—At any stage the Court may "
    "pass an interim order. 4. [Sample amendment of another Act.] Omitted by Ord. 21 of 1960, s. 3. "
    "SCHEDULE [see section 3] 1. Dower. 2. Maintenance."
)

CSV_FIXTURE = (
    "Chapter I — Preliminary\nSection 1 — Short title\n(1) This Order may be called the Sample Order.\n\n"
    "Chapter I — Preliminary\nSection 2 — Interpretation\n(1) In this Order, “Court” includes all Judges.\n\n"
    "Chapter II — Witnesses\nSection 4 — Who may testify\nAll persons shall be competent to testify.\n"
)

# Older glued extraction: no spaces after numbers, "Page2of66" + section 22 run together.
GLUED_TOC = ("SECTIONS:PRELIMINARY1.Short title.2.Definitions.3.Courts.Page2of6622.Stay.23.Bar.")


def test_pdf_sections_toc_detection_and_schedule():
    res = split(PDF_FIXTURE, "statute_pdf")
    assert res.method == "pdf_toc"
    assert (res.found, res.expected, res.missing) == (5, 5, [])
    ids = [s.section for s in res.sections]
    assert ids == ["1", "2", "3", "3A", "4", "Schedule"]
    s = {x.section: x for x in res.sections}
    assert s["1"].heading == "Short title and extent"
    assert s["1"].text == "(1) This Act may be called the Sample Family Act, 1964"
    assert s["3A"].text == "At any stage the Court may pass an interim order"
    # an Omitted section whose body heading differs from the TOC is still found
    assert s["4"].text.startswith("Omitted by Ord. 21 of 1960")
    assert s["Schedule"].text.startswith("[see section 3] 1. Dower")


def test_pdf_footnotes_removed_and_marker_dropped():
    s = {x.section: x for x in split(PDF_FIXTURE, "statute_pdf").sections}
    assert "Subs. by Ord. 55" not in s["2"].text
    assert "Page" not in s["2"].text
    # "2[(b) ..." keeps the bracketed text, without the footnote number
    assert "[(b) “wi fe” includes a divorced wife;]" in s["2"].text


def test_ocr_join_is_conservative():
    vocab = Counter({"wife": 500, "council": 300, "wi": 1, "fe": 2, "coun": 1, "cil": 1, "a": 9000,
                     "gain": 40, "again": 200, "in": 9000, "to": 9000, "into": 800})
    assert join_ocr_splits("the wi fe and the Coun cil", vocab) == "the wife and the Council"
    # real word pairs stay apart: "a" and "in"/"to" are commoner than the joined word
    assert join_ocr_splits("a gain went in to it", vocab) == "a gain went in to it"
    assert join_ocr_splits("the wi fe", None) == "the wi fe"
    # a trailing fragment that isn't a word is judged on the first piece ("d" is a common clause label)
    vocab.update({"declared": 1100, "declare": 580, "d": 9000, "s": 9000, "section": 5000, "sections": 900})
    assert join_ocr_splits("was declare d void", vocab) == "was declared void"
    assert join_ocr_splits("under section s. 5", vocab) == "under section s. 5"


def test_csv_section_table():
    res = split(CSV_FIXTURE, "statute_section_table")
    assert [s.section for s in res.sections] == ["1", "2", "4"]
    assert res.sections[2].heading == "Who may testify"
    assert res.sections[0].text == "(1) This Order may be called the Sample Order."
    assert res.missing == ["3"] and res.expected == 4 and res.found == 3


def test_glued_toc_and_page_marker():
    toc = parse_toc(GLUED_TOC.replace("Page2of66", " "))
    assert [n for n, _ in toc] == ["1", "2", "3", "22", "23"]
    text = "x Page 1 of 66 y Page2of6622.Stay z"
    spans = page_spans(text)
    assert [text[s:e].strip() for s, e in spans] == ["Page 1 of 66", "Page2of66"]


def test_toc_ignores_numbers_inside_headings():
    toc = parse_toc("1. Short title. 9. Professional communications. 10. Article 9 to apply to "
                    "interpreters, etc. 11. Privilege. 6 Repeal of s. 5 of Act, XXVI of 1937.")
    assert [n for n, _ in toc] == ["1", "9", "10", "11"]


def test_heading_first_layout():
    text = ("CONTENTS 1. The Republic ........ 3 2. Islam to be State religion ....... 3 "
            "WHEREAS the people; Now, therefore, we enact this Constitution. "
            "The Republic and its territories 1. (1) Pakistan shall be a Federal Republic. "
            "Islam to be State religion 2. Islam shall be the State religion of Pakistan.")
    res = split(text, "statute_pdf")
    assert res.method == "pdf_toc_heading_first"
    s = {x.section: x for x in res.sections}
    assert s["1"].text == "(1) Pakistan shall be a Federal Republic"
    assert s["2"].text == "Islam shall be the State religion of Pakistan"


def test_no_page_breaks_means_no_footnote_cut():
    body = "1. Title.—This Act. 1Subs. is part of the text here."
    assert strip_footnotes(body) == body


def test_windows_cover_text():
    text = " ".join(f"w{i}" for i in range(1000))
    parts = windows(text, size=200)
    assert " ".join(parts) == text and all(len(p) <= 200 for p in parts)


META = {"title": "Sample Family Act, 1964", "year": 1964, "category": None, "act_number": None,
        "status": "current", "source": CORPUS_SOURCE, "source_tier": 2, "source_url": None,
        "original_file": None, "scraped_at": None, "jurisdiction": "Pakistan"}


def test_records_are_valid():
    recs = make_records(META, split(PDF_FIXTURE, "statute_pdf").sections)
    assert [r["doc_id"] for r in recs][:2] == ["legalease-corpus/sample-family-act-1964/s1",
                                               "legalease-corpus/sample-family-act-1964/s2"]
    assert recs[-1]["doc_id"].endswith("/schedule")
    for r in recs:
        assert validate(r) == []


def test_unsectioned_records_have_null_section():
    recs = make_records(META, None, raw_text="word " * 600)
    assert len(recs) > 1
    assert all(r["section"] is None and r["heading"] is None and r["sectioned"] is False for r in recs)
    assert all(validate(r) == [] for r in recs)


def test_validate_catches_problems():
    rec = make_records(META, split(PDF_FIXTURE, "statute_pdf").sections)[0]
    assert "content_hash does not match text" in validate(dict(rec, text="changed"))
    assert any("status" in e for e in validate(dict(rec, status="old")))
    assert any("tier 3" in e for e in validate(dict(rec, source_tier=3)))
    assert any("unknown fields" in e for e in validate(dict(rec, extra=1)))
    assert any("missing" in e for e in validate({k: v for k, v in rec.items() if k != "year"}))


RECORDS = Path(__file__).resolve().parents[3] / "storage" / "kb" / "records"


@pytest.mark.skipif(not list(RECORDS.glob("*.jsonl")), reason="records not built (scripts/kb/build_records.py)")
def test_all_built_records_match_the_schema():
    bad, n, ids = [], 0, set()
    for path in RECORDS.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            n += 1
            errs = validate(rec)
            if rec["doc_id"] in ids:
                errs.append("duplicate doc_id")
            ids.add(rec["doc_id"])
            if errs:
                bad.append((path.name, rec.get("doc_id"), errs))
    assert n > 0
    assert bad == []
