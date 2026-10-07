"""kb-v2 C7: section every other law we hold (the old index's corpus) into records.

Offline, no model calls. Reads the corpus the old index was built from
(read-only) and category_map.json; runs each document through the same
sectioner and record builder as the 35 core laws (scripts/kb/build_records.py).

Kept: a title, a year, at least one numbered section, and at least 70% of the
sections its numbering or contents list implies. Everything else stays in the
old index only and is listed with the reason. Skipped: copies of the 35 core
laws, laws the scraper staged, and a second corpus copy of the same law (the
copy that sections better is kept).

Writes backend/storage/kb/records_all/<slug>.jsonl (git-ignored) and
records_all/_report.json.

    cd backend
    python ../scripts/kb/build_records_all.py [--corpus PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from build_records import AUDIENCE, CORE, DEFAULT_CORPUS  # noqa: E402

from app.kb.catalog import LISTING_SOURCE, OVERRIDE_SOURCE, override_category  # noqa: E402
from app.kb.records import CORPUS_SOURCE, make_records, slugify  # noqa: E402
from app.kb.records import validate as validate_record  # noqa: E402
from app.kb.sectioner import build_vocab, split, split_schedule_items  # noqa: E402
from app.scraping.parse import normalise_title  # noqa: E402
from app.scraping.stage import clean_title, nice_title, short_title, year_of  # noqa: E402

KB = ROOT / "backend" / "storage" / "kb"
OUT = KB / "records_all"
MIN_DETECTION = 0.70

_JURISDICTION = [(re.compile(r"\bpunjab\b", re.I), "Punjab"), (re.compile(r"\bsindh\b", re.I), "Sindh"),
                 (re.compile(r"khyber\s+pakhtunkhwa|n\.?\s?w\.?\s?f\.?\s?p\b|north[\s-]+west\s+frontier", re.I), "KP"),
                 (re.compile(r"\bbalochistan\b|\bbaluchistan\b", re.I), "Balochistan"),
                 (re.compile(r"islamabad\s+capital\s+territory|\bislamabad\b", re.I), "ICT")]
_AUDIENCE_WORDS = [(re.compile(r"\bhindus?\b", re.I), "Hindu"), (re.compile(r"\bchristians?\b", re.I), "Christian"),
                   (re.compile(r"\bparsis?\b", re.I), "Parsi"), (re.compile(r"\bsikhs?\b|\banand\b", re.I), "Sikh")]


def jurisdiction(title: str) -> str:
    """Provinces by name; "West Pakistan" laws are treated as Pakistan-wide, as for the core laws."""
    return next((j for rx, j in _JURISDICTION if rx.search(title)), "Pakistan")


def audience(title: str) -> str:
    """A law named for one community is searched only when the question names it (index_v2.AUDIENCE_TERMS)."""
    if title in AUDIENCE:
        return AUDIENCE[title]
    return next((a for rx, a in _AUDIENCE_WORDS if rx.search(title)), "general")


def listings(cmap: dict) -> dict[str, tuple[str, dict]]:
    """Corpus title -> (Pakistan Code category, listing) for exact and near matches."""
    out = {}
    for c in cmap.get("categories", []):
        for law in c.get("laws", []):
            m = law.get("match")
            if m and m.get("how") != "possible":
                for x in m.get("corpus", []):
                    out.setdefault(x["title"], (c["name"], law))
    return out


def scraped_titles() -> set[str]:
    out = set()
    for p in (KB / "scraped" / "records" / "statutes").glob("*.jsonl"):
        with p.open(encoding="utf-8") as f:
            out.add(normalise_title(json.loads(f.readline())["title"]))
    return out


def title_for(corpus_title: str, text: str, listing: dict | None) -> str:
    """The listing's clean title when the category map matched this copy;
    else the law's own short title; else the tidied corpus title."""
    if listing and listing.get("clean_title"):
        return clean_title(listing["clean_title"])[0]
    return short_title(text) or nice_title(clean_title(corpus_title)[0])


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    args = ap.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    print(f"corpus: {len(corpus)} documents, {sum(len(r.get('text') or '') for r in corpus):,} characters")
    cmap = json.loads((KB / "category_map.json").read_text(encoding="utf-8"))
    by_listing = listings(cmap)
    core_copies = {t for _title, _y, copies in CORE for t in copies}
    core_titles = {normalise_title(t) for t, _y, _c in CORE}
    held_scraped = scraped_titles()
    core_slugs = {p.stem for p in (KB / "records").glob("*.jsonl")}
    vocab = build_vocab(r["text"] for r in corpus)

    candidates: dict[str, dict] = {}       # slug -> best candidate
    report: list[dict] = []
    for r in corpus:
        ct, text = r["title"], r.get("text") or ""
        row = {"corpus_title": ct, "chars": len(text), "source_type": r.get("source_type")}
        if ct in core_copies:
            report.append({**row, "outcome": "skipped", "reason": "copy of one of the 35 core laws"})
            continue
        category, listing = by_listing.get(ct, (None, None))
        title = title_for(ct, text, listing)
        if normalise_title(title) in core_titles:
            report.append({**row, "title": title, "outcome": "skipped", "reason": "copy of one of the 35 core laws"})
            continue
        if normalise_title(title) in held_scraped:
            report.append({**row, "title": title, "outcome": "skipped", "reason": "held as a scraped law"})
            continue
        year = year_of(title) or (listing or {}).get("year") or year_of("", text)
        if not title.strip():
            report.append({**row, "outcome": "old index only", "reason": "no title"})
            continue
        if not year:
            report.append({**row, "title": title, "outcome": "old index only", "reason": "no year"})
            continue
        res = split(text, r.get("source_type") or "statute_pdf", vocab)
        row.update(title=title, year=year, method=res.method, expected=res.expected, found=res.found,
                   detection=round(res.detection, 3))
        if res.found == 0:
            report.append({**row, "outcome": "old index only", "reason": "no numbered sections found"})
            continue
        if res.detection < MIN_DETECTION:
            report.append({**row, "outcome": "old index only",
                           "reason": f"only {res.found} of {res.expected} sections found ({res.detection:.0%})"})
            continue
        slug = slugify(title)
        if slug in core_slugs:
            report.append({**row, "outcome": "skipped", "reason": "same name as a core law's file"})
            continue
        prev = candidates.get(slug)
        if prev is not None:
            loser, winner = (row, prev) if (res.detection, res.found) <= (prev["detection"], prev["found"]) \
                else (prev, row)
            report.append({**{k: v for k, v in loser.items() if not k.startswith("_")}, "outcome": "skipped",
                           "reason": f"second corpus copy of {title} (the other sections better)"})
            if winner is prev:
                continue
        candidates[slug] = {**row, "_res": res, "_category": category, "_listing": listing}

    OUT.mkdir(parents=True, exist_ok=True)
    for p in OUT.glob("*.jsonl"):
        p.unlink()
    kept = 0
    for slug, c in sorted(candidates.items()):
        res, listing, category = c["_res"], c["_listing"], c["_category"]
        category_source = LISTING_SOURCE if category else None
        if not category and override_category(c["title"]):
            category, category_source = override_category(c["title"]), OVERRIDE_SOURCE
        repealed = bool(listing and listing.get("status") == "repealed") or clean_title(c["corpus_title"])[1]
        meta = {
            "title": c["title"], "year": int(c["year"]), "category": category, "category_source": category_source,
            "act_number": (listing or {}).get("act_number"), "status": "repealed" if repealed else "current",
            "source": CORPUS_SOURCE, "source_tier": 1 if listing else 2, "source_url": None,
            "original_file": None, "scraped_at": None, "jurisdiction": jurisdiction(c["title"]),
            "audience": audience(c["title"]),
            "provenance_note": (f"From the LegalEase corpus (corpus title \"{c['corpus_title']}\"); sectioned "
                                f"automatically: {res.found} of {res.expected} sections found."),
        }
        secs, _labels = split_schedule_items(res.sections)
        recs = make_records(meta, secs)
        bad = [e for rec in recs for e in validate_record(rec)]
        row = {k: v for k, v in c.items() if not k.startswith("_")}
        if bad:
            report.append({**row, "outcome": "old index only", "reason": f"record check failed: {bad[0]}"})
            continue
        (OUT / f"{slug}.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in recs) + "\n",
                                          encoding="utf-8")
        report.append({**row, "outcome": "sectioned", "records": len(recs), "jurisdiction": meta["jurisdiction"],
                       "category": category, "audience": meta["audience"]})
        kept += 1
    outcomes = Counter(r["outcome"] for r in report)
    reasons = Counter(re.sub(r"\d+", "N", r["reason"]) for r in report if r.get("reason"))
    summary = {"corpus_documents": len(corpus), "corpus_chars": sum(len(r.get("text") or "") for r in corpus),
               "outcomes": dict(outcomes), "reasons": dict(reasons.most_common()),
               "laws_sectioned": kept, "records": sum(r.get("records", 0) for r in report)}
    (OUT / "_report.json").write_text(json.dumps({"summary": summary, "documents": report}, ensure_ascii=False,
                                                 indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
