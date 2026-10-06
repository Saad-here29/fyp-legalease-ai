"""kb-v2 Phase B1: records for the user-supplied Shariat Application Act PDF.

Reads backend/storage/kb/raw/Muslim Personal Law (Shariat) Application Act 1962.pdf
(copied there unchanged from the user's folder), extracts its text layer with
PyMuPDF (the app's OCR path is used only if a page has no text layer), splits
it into sections, and writes backend/storage/kb/records/
west-pakistan-muslim-personal-law-shariat-application-act-1962.jsonl.
Offline: no network, no model calls.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import pymupdf  # noqa: E402

from app.kb.records import make_records, slugify, validate  # noqa: E402
from app.kb.sectioner import Section, clean_body, split  # noqa: E402

PDF_NAME = "Muslim Personal Law (Shariat) Application Act 1962.pdf"
RAW = ROOT / "backend" / "storage" / "kb" / "raw" / PDF_NAME
OUT = ROOT / "backend" / "storage" / "kb" / "records"
TITLE = "West Pakistan Muslim Personal Law (Shariat) Application Act, 1962"


def extract(path: Path) -> tuple[str, list[str]]:
    doc = pymupdf.open(path)
    pages, how = [], []
    for page in doc:
        t = page.get_text()
        if len(t.strip()) < 100:               # scanned page: fall back to the app's OCR
            from app.services.ocr_service import OCRService
            t = OCRService().extract_text(path.read_bytes(), path.name)
            how.append("ocr")
            pages = [t]
            break
        pages.append(t)
        how.append("text layer")
    return "\n".join(pages), how


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    text, how = extract(RAW)
    res = split(text, "statute_pdf")
    flat = re.sub(r"\s+", " ", text)
    m = re.search(r"Preamble\.\s*(WHEREAS.*?)It is hereby enacted as follows", flat)
    sections = list(res.sections)
    if m:
        sections.insert(0, Section("Preamble", None, clean_body(m.group(1)).rstrip(" ;") + ";"))
    meta = {
        "title": TITLE, "year": 1962, "category": None, "act_number": "West Pakistan Act No. V of 1962",
        "status": "under_review", "source": "user-supplied PDF", "source_tier": 2, "source_url": None,
        "original_file": f"backend/storage/kb/raw/{PDF_NAME}", "scraped_at": None, "jurisdiction": "Pakistan", "audience": "general",
        "provenance_note": ("Supplied by the user as a PDF (Word export dated 2025-03-24, 'RGN Date: "
                            "24-03-2025'); the original source URL is to be confirmed. Enacted as a West "
                            "Pakistan Act; s.1(2) as amended by P.O. 4 of 1975 extends it to the whole of "
                            "Pakistan."),
    }
    recs = make_records(meta, sections)
    errs = [(r["doc_id"], validate(r)) for r in recs if validate(r)]
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{slugify(TITLE)}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"extraction: {set(how)}; pages {len(how)}; {res.method} found {res.found}/{res.expected} "
          f"missing {res.missing}; records {len(recs)}; invalid {errs}")
    for r in recs:
        print(f"--- {r['section']} | {r['heading']}\n{r['text']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
