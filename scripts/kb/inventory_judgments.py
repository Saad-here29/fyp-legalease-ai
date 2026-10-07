"""kb-v2 C1: inventory judgment files and write judgment records (offline).

Reads ONLY the paths given (files, folders, .zip archives; .parquet needs
pyarrow). Nothing is copied: records keep each file's path and SHA-256.

    python scripts/kb/inventory_judgments.py --source "Supreme Court txt" PATH [PATH ...]
    python scripts/kb/inventory_judgments.py --source "SC PDFs" --glob "*.pdf" FOLDER

Writes backend/storage/kb/judgments/records/<source>.jsonl (git-ignored) and
backend/storage/kb/judgments/inventory_<source>.json, and prints the
inventory: file count, formats, size, extractable text, near-empty, needing
OCR, years, courts, duplicates (title and content hash), law-report copies.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.kb import judgments as jd  # noqa: E402

OUT = ROOT / "backend" / "storage" / "kb" / "judgments"
FIELDS = ("case_name", "court", "year", "judges", "case_number", "citation", "topics")


def iter_files(paths: list[Path], pattern: str):
    """(display path, a Path to read or None, bytes or None) for each file."""
    for p in paths:
        if p.is_dir():
            for f in sorted(p.rglob(pattern)):
                if f.is_file():
                    yield str(f), f, None
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                for name in sorted(z.namelist()):
                    if not name.endswith("/") and Path(name).match(pattern):
                        yield f"{p}!{name}", None, z.read(name)
        elif p.suffix.lower() == ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError:
                print(f"SKIP {p}: reading .parquet needs pyarrow (not installed)", file=sys.stderr)
                continue
            table = pq.read_table(p).to_pylist()
            col = next((c for c in ("text", "judgment", "content", "body") if table and c in table[0]), None)
            for i, row in enumerate(table):
                yield f"{p}#row{i}", None, str(row.get(col) or "").encode("utf-8")
        elif p.is_file():
            yield str(p), p, None


def read(display: str, path: Path | None, data: bytes | None) -> tuple[str, dict, str]:
    """(text, info, sha256 of the file bytes)."""
    import hashlib
    if path is not None:
        text, info = jd.read_text(path)
        return text, info, jd.sha256_file(path)
    suffix = Path(display.split("!")[-1].split("#")[0]).suffix.lower()
    sha = hashlib.sha256(data).hexdigest()
    if suffix == ".pdf":
        import pymupdf
        doc = pymupdf.open(stream=io.BytesIO(data), filetype="pdf")
        pages = [pg.get_text() for pg in doc]
        return "\n".join(pages), {"format": "pdf", "pages": len(pages),
                                  "pages_without_text": sum(1 for t in pages if len(t.strip()) < 50)}, sha
    return data.decode("utf-8", "replace"), {"format": suffix.lstrip(".") or "text", "pages": None,
                                             "pages_without_text": 0}, sha


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--source", required=True, help="a short name for this dataset")
    ap.add_argument("--glob", default="*", help="file pattern inside folders / archives (default: all)")
    ap.add_argument("--limit", type=int, default=None, help="stop after N files (for a quick look)")
    args = ap.parse_args()
    OUT.joinpath("records").mkdir(parents=True, exist_ok=True)

    recs, sizes, formats, errors = [], 0, Counter(), []
    for n, (display, path, data) in enumerate(iter_files(args.paths, args.glob)):
        if args.limit and n >= args.limit:
            break
        sizes += path.stat().st_size if path is not None else len(data or b"")
        formats[Path(display.split("!")[-1].split("#")[0]).suffix.lower() or "?"] += 1
        try:
            text, info, sha = read(display, path, data)
        except Exception as e:  # noqa: BLE001 — report and continue
            errors.append(f"{display}: {type(e).__name__}: {str(e)[:100]}")
            continue
        rec = jd.make_record(Path(display), text, info, source=args.source, file_sha=sha)
        rec["original_file"] = display
        if not rec["paragraphs"]:
            rec["paragraphs"] = [{"n": 1, "text": " ".join(text.split()) or "(no text)"}]
        recs.append(rec)

    # duplicates: same content hash, or same case name + year
    by_hash = Counter(r["content_hash"] for r in recs)
    by_title = Counter((r["case_name"], r["year"]) for r in recs if r["case_name"])
    seen_hash, seen_title = set(), set()
    for r in recs:
        key = (r["case_name"], r["year"])
        if r["quality"]["exclude"]:
            continue
        if r["content_hash"] in seen_hash:
            r["quality"]["exclude"] = "duplicate (same text)"
        elif r["case_name"] and key in seen_title:
            r["quality"]["exclude"] = "duplicate (same case name and year)"
        seen_hash.add(r["content_hash"])
        if r["case_name"]:
            seen_title.add(key)

    name = jd.slug(args.source)
    with (OUT / "records" / f"{name}.jsonl").open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    years = [r["year"] for r in recs if r["year"]]
    filled = {k: sum(1 for r in recs if r[k]) for k in FIELDS}
    inv = {
        "source": args.source, "paths": [str(p) for p in args.paths], "files": len(recs) + len(errors),
        "read_errors": errors[:20], "formats": dict(formats), "total_mb": round(sizes / 2**20, 1),
        "with_text": sum(1 for r in recs if r["quality"]["chars"] >= 200),
        "near_empty": sum(1 for r in recs if r["quality"]["near_empty"]),
        "needs_ocr": sum(1 for r in recs if r["quality"]["needs_ocr"]),
        "law_report_copies": sum(1 for r in recs if r["quality"]["law_report"]),
        "duplicate_text": sum(c - 1 for c in by_hash.values() if c > 1),
        "duplicate_title_year": sum(c - 1 for c in by_title.values() if c > 1),
        "excluded": dict(Counter(r["quality"]["exclude"] for r in recs if r["quality"]["exclude"])),
        "kept": sum(1 for r in recs if not r["quality"]["exclude"]),
        "year_range": [min(years), max(years)] if years else None,
        "courts": dict(Counter(r["court"] for r in recs).most_common()),
        "extraction_rate": {k: round(v / len(recs), 3) if recs else 0 for k, v in filled.items()},
        "topics": dict(Counter(t for r in recs for t in r["topics"]).most_common()),
        "law_report_files": [r["original_file"] for r in recs if r["quality"]["law_report"]][:50],
    }
    (OUT / f"inventory_{name}.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in inv.items() if k != "law_report_files"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
