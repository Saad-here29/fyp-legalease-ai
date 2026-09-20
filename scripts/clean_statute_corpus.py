"""Clean and merge the raw statute sources into one corpus, and clean the
lawyer-authored QA eval set.

Inputs  (data/raw/):
  statutes/Datatset For FAISS.csv        — section-level rows, some rows
                                            mislabeled under the wrong "Book"
                                            due to a parsing bug upstream.
  statutes/pakistan_code_pdf_data.json   — one entry per scanned statute PDF,
                                            keyed by meaningless hash filename,
                                            with duplicates and dead "repealed
                                            law" stubs.
  qa_eval/Legal_QA_dataset_From_lawyers.csv — has a stray unnamed column.

Outputs (data/processed/):
  statutes/legal_statutes_corpus.json    — one record per statute/document:
                                            {title, source_type, text}.
  qa_eval/Legal_QA_dataset_From_lawyers_clean.csv — Query, Response only.

`data/raw/qa_eval/combined_legal_dataset.csv` is intentionally left untouched
and separate — it's a distinct, larger eval/reference set, not merged here.

Run from the project root:  python scripts/clean_statute_corpus.py
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

CSV_PATH = RAW / "statutes" / "Datatset For FAISS.csv"
JSON_PATH = RAW / "statutes" / "pakistan_code_pdf_data.json"
QA_PATH = RAW / "qa_eval" / "Legal_QA_dataset_From_lawyers.csv"

OUT_CORPUS = OUT / "statutes" / "legal_statutes_corpus.json"
OUT_QA = OUT / "qa_eval" / "Legal_QA_dataset_From_lawyers_clean.csv"


# ===================================================================
# Part 1 — "Datatset For FAISS.csv": fix mislabeled Book values
# ===================================================================

# The 6 statutes named in the task, using the CSV's own (legally accurate)
# spelling as the canonical string — left untouched.
REAL_BOOKS = {
    "Pakistan Penal Code",
    "Code of Criminal Procedure, 1898",
    "Qanun-e-Shahadat Order, 1984",
    "Transfer of Property Act",
    "Limitation Act, 1908",
    "Muslim Family Laws Ordinance, 1961",
}

# "Code of Criminal Procedure, 1899".."1939" (and a stray "1897"): a parsing
# bug incremented the year per row instead of keeping "1898". Confirmed by
# content — chapter titles (PRELIMINARY, POWERS OF COURTS, ARREST, SCHEDULE
# V, ...) all match the real CrPC 1898 structure. Safe to relabel.
_CRPC_YEAR_RE = re.compile(r"^Code of Criminal Procedure, 18[0-9]{2}$|^Code of Criminal Procedure, 19[0-4][0-9]$")

# "Chatbot Info": not statute content at all (chatbot FAQ/credits) — drop.
DROP_BOOKS = {"Chatbot Info"}

# "Police Law": genuinely a different, real statute (confirmed by its own
# text: "This Order may be called the Police Order, 2002") — not one of the
# 6 named, not a mislabeling of one of them either. Kept as its own 7th
# statute rather than dropped, since the content is legitimate and confidently
# identified — flagged in the run report rather than silently dropped.
POLICE_LAW_TITLE = "Police Order, 2002"


def load_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_statute_docs_from_csv(rows: list[dict]) -> tuple[list[dict], dict]:
    """Group CSV rows into one document per statute, fixing Book labels."""
    fixed_ct = 0
    dropped_ct = 0
    kept_as_police_ct = 0
    by_book: dict[str, list[dict]] = {}

    for row in rows:
        book = row["Book"].strip()
        if book in DROP_BOOKS:
            dropped_ct += 1
            continue
        if book == "Police Law":
            book = POLICE_LAW_TITLE
            kept_as_police_ct += 1
        elif book not in REAL_BOOKS and _CRPC_YEAR_RE.match(book):
            book = "Code of Criminal Procedure, 1898"
            fixed_ct += 1
        elif book not in REAL_BOOKS:
            # Unknown anomaly not covered by the rules above — not confidently
            # determinable, so drop rather than guess.
            dropped_ct += 1
            continue
        by_book.setdefault(book, []).append(row)

    docs = []
    for book, book_rows in by_book.items():
        lines = []
        for r in book_rows:
            chap = f"Chapter {r['Chapter Number']} — {r['Chapter Title']}".strip(" —")
            lines.append(f"{chap}\nSection {r['Section']} — {r['Heading']}\n{r['Defination']}")
        docs.append(
            {
                "title": book,
                "source_type": "statute_section_table",
                "text": "\n\n".join(lines),
            }
        )

    stats = {
        "csv_rows_total": len(rows),
        "csv_rows_dropped": dropped_ct,
        "csv_rows_relabeled_crpc": fixed_ct,
        "csv_rows_kept_as_police_order": kept_as_police_ct,
        "csv_documents": len(docs),
    }
    return docs, stats


# ===================================================================
# Part 2 — "pakistan_code_pdf_data.json": dedupe, drop stubs, extract titles
# ===================================================================

def _collapse_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")


def _ratio_single_char_tokens(text: str, n: int = 500) -> float:
    t = _collapse_newlines(text[:n])
    toks = [tok for tok in t.split(" ") if tok]
    if len(toks) < 15:
        return 0.0
    return sum(1 for tok in toks if len(tok) == 1) / len(toks)


def _fix_letter_spacing(text: str) -> str:
    """Some PDFs extracted with one character per token: single space
    separates letters *within* a word, U+00A0 (nbsp) separates words."""
    t = _collapse_newlines(text)
    return t.replace(" ", "").replace("\xa0", " ")


def _normalize_whitespace(s: str) -> str:
    s = s.replace("\xa0", " ").replace("\xad", "").replace("‑", "-")
    s = _collapse_newlines(s)
    s = re.sub(r"(?<=\d) (?=\d)", "", s)  # "20 17" -> "2017" (split digit OCR artifact)
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


_BOILERPLATE_RE = re.compile(
    r"^\s*(?:Page\s*\d+\s*of\s*\d+\s*[.:|]?\s*"
    r"|U\s*pdated\s+till\s+[\d.\-/]+\s*"
    r"|CONTENTS?\s*[.:|]?\s*"
    r"|[-_|.\s]+)+",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"(1[7-9]\d{2}|20[0-2]\d)")
_CUT_KEYWORDS_RE = re.compile(r"\b(CONTENTS|PREAMBLE|SECTIONS)\b", re.IGNORECASE)


def _alpha_ratio(s: str) -> float:
    letters = sum(1 for ch in s if ch.isalpha())
    return letters / max(1, len(s.replace(" ", "")))


def clean_and_title(raw_text: str, file_name: str, max_len: int = 140) -> tuple[str, str, str]:
    """Returns (title, cleaned_text, method) for one raw JSON entry."""
    text = raw_text
    letter_spaced = _ratio_single_char_tokens(raw_text) > 0.6
    if letter_spaced:
        text = _fix_letter_spacing(raw_text)
    cleaned_text = _normalize_whitespace(text)

    stripped = cleaned_text
    prev = None
    while stripped != prev:
        prev = stripped
        stripped = _BOILERPLATE_RE.sub("", stripped).strip()
    search_space = stripped or cleaned_text

    m = _YEAR_RE.search(search_space)
    if m and m.start() < max_len:
        title = search_space[: m.end()].strip(" |.,")
        if title and _alpha_ratio(title) > 0.5:
            return title, cleaned_text, "year"

    km = _CUT_KEYWORDS_RE.search(search_space)
    candidate = search_space[: km.start()].strip(" |.,") if km else search_space[:80].strip(" |.,")
    if candidate and 4 <= len(candidate) <= max_len and _alpha_ratio(candidate) > 0.5:
        return candidate, cleaned_text, "keyword-cut"

    # Genuinely garbled OCR (mojibake gazette scans) — no readable title
    # extractable; use the filename stem rather than nonsense text.
    fallback_title = file_name.replace(".pdf.txt", "").replace(".txt", "")
    return fallback_title, cleaned_text, "filename-fallback"


def build_statute_docs_from_json(entries: list[dict]) -> tuple[list[dict], dict]:
    seen_text: set[str] = set()
    deduped = []
    for e in entries:
        if e["text"] in seen_text:
            continue
        seen_text.add(e["text"])
        deduped.append(e)
    removed_dupes = len(entries) - len(deduped)

    kept = [e for e in deduped if len(e["text"]) >= 100]
    removed_stubs = len(deduped) - len(kept)

    method_counts: Counter = Counter()
    docs = []
    for e in kept:
        title, text, method = clean_and_title(e["text"], e["file_name"])
        method_counts[method] += 1
        docs.append({"title": title, "source_type": "statute_pdf", "text": text})

    stats = {
        "json_entries_total": len(entries),
        "json_removed_exact_duplicates": removed_dupes,
        "json_removed_short_stubs": removed_stubs,
        "json_documents": len(docs),
        "json_title_methods": dict(method_counts),
    }
    return docs, stats


# ===================================================================
# Part 3 — QA eval CSV cleanup
# ===================================================================

def clean_qa_csv(src: Path, dst: Path) -> dict:
    with src.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    kept = [
        {"Query": r["Query"].strip(), "Response": r["Response"].strip()}
        for r in rows
        if r.get("Query", "").strip() and r.get("Response", "").strip()
    ]

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Query", "Response"])
        w.writeheader()
        w.writerows(kept)

    return {"qa_rows_total": len(rows), "qa_rows_kept": len(kept)}


# ===================================================================
# Main
# ===================================================================

def main() -> None:
    csv_rows = load_csv_rows(CSV_PATH)
    csv_docs, csv_stats = build_statute_docs_from_csv(csv_rows)

    with JSON_PATH.open(encoding="utf-8") as f:
        json_entries = json.load(f)
    json_docs, json_stats = build_statute_docs_from_json(json_entries)

    all_docs = csv_docs + json_docs

    OUT_CORPUS.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CORPUS.open("w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)

    qa_stats = clean_qa_csv(QA_PATH, OUT_QA)

    report = {**csv_stats, **json_stats, **qa_stats, "total_merged_documents": len(all_docs)}
    print(json.dumps(report, indent=2))

    with (OUT / "statutes" / "corpus_build_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
