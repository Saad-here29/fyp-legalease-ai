"""Knowledge base v2, Phase A: the Pakistan Code category map.

Fetches ONLY the Pakistan Code category index and the 23 category listing
pages (no law pages, no PDFs), with the scraper's polite Fetcher: identified
User-Agent, 2 s per request, robots.txt respected. Then matches every listed
title to our corpus (docs/architecture/corpus_statute_list.md) by normalised title + year.

    python scripts/kb/build_category_map.py            # fetch + match, write outputs
    python scripts/kb/build_category_map.py --offline  # re-match from the saved HTML

Outputs (worktree):
    backend/storage/kb/raw/pakistancode_categories/*.html   saved listing pages (gitignored)
    backend/storage/kb/category_map.json                      categories, laws, matches
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from lxml import html  # noqa: E402

from app.scraping.parse import normalise_title  # noqa: E402

BASE = "https://pakistancode.gov.pk/english/"
INDEX = BASE + "LGu0xVD.php"
KB = ROOT / "backend" / "storage" / "kb"
RAW = KB / "raw" / "pakistancode_categories"
YEAR = re.compile(r"\b(1[6-9]\d\d|20\d\d)\b")


def year_of(*texts: str) -> int | None:
    for t in texts:
        m = YEAR.findall(t or "")
        if m:
            return int(m[-1]) if "Promulgation" not in (t or "") else int(m[0])
    return None


STATUS_NOTE = re.compile(r"\((repealed[^)]*|under review|omitted[^)]*|expired[^)]*|lapsed[^)]*)\)", re.I)
ACRONYM = re.compile(r"\(\s*[A-Z]{2,8}(?:\s+\d{4})?\s*\)")
BOILERPLATE = re.compile(r"^\s*(?:under\s+(?:proof\s*reading|review)\s+)?(?:page\s+\d+\s+of\s+\d+\s+)?(?:[a-z]\s+)?(?=the|\w)", re.I)


def status_of(title: str) -> str:
    """Pakistan Code annotates titles: '(Repealed by Act XIV of 2015)', '(Under Review)'."""
    m = STATUS_NOTE.search(title or "")
    if not m:
        return "current"
    return "repealed" if m.group(1).lower().startswith(("repealed", "omitted", "expired", "lapsed")) else "under_review"


def clean_title(title: str) -> str:
    t = STATUS_NOTE.sub(" ", title or "")
    letters = [ch for ch in t if ch.isalpha()]
    # Strip "(CPC)", "(ANF 1997)" only from mixed-case titles: in an ALL-CAPS
    # title "(CONTROL)" is part of the name, not an abbreviation.
    if letters and sum(ch.isupper() for ch in letters) / len(letters) < 0.6:
        t = ACRONYM.sub(" ", t)
    if re.match(r"^\s*(under\s|page\s)", t, re.I):
        t = BOILERPLATE.sub("", t)
    return " ".join(t.split())


def title_key(title: str) -> str:
    """normalise_title of the cleaned title, without the year, so
    'Divorce Act,1869', 'THE DIVORCE ACT, 1869' and 'Divorce Act' share a key."""
    return YEAR.sub("", normalise_title(clean_title(title))).strip()


def keys_for(title: str) -> list[str]:
    k = title_key(title)
    return [k, k[len("pakistan"):]] if k.startswith("pakistan") and len(k) > 12 else [k]


def load_corpus_titles(md_path: Path) -> list[dict]:
    rows = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|", line)
        if m:
            rows.append({"n": int(m.group(1)), "title": m.group(2), "chunks": int(m.group(3)),
                         "raw_source": m.group(4)})
    return rows


def parse_index(content: bytes) -> list[dict]:
    d = html.fromstring(content)
    cats, seen = [], set()
    for a in d.xpath("//a[contains(@href,'catid=')]"):
        href = a.get("href")
        m = re.search(r"catid=(\d+)", href)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        cats.append({"catid": int(m.group(1)), "name": " ".join(a.text_content().split()), "url": urljoin(INDEX, href)})
    # Badge counts "(69)" appear in the same order as the categories in the page text.
    text = " ".join(d.text_content().split())
    for c in cats:
        m = re.search(re.escape(c["name"]) + r"\s*\((\d+)\)", text)
        c["badge_count"] = int(m.group(1)) if m else None
    return cats


def parse_category(content: bytes, page_url: str) -> list[dict]:
    d = html.fromstring(content)
    laws = []
    for title_div in d.xpath("//div[contains(@class,'accordion-section-title')]"):
        a = title_div.xpath(".//a")
        if not a:
            continue
        title = " ".join(a[0].text_content().split())
        content_div = title_div.xpath("following-sibling::div[contains(@class,'accordion-section-content')][1]")
        meta = " ".join(content_div[0].text_content().split()) if content_div else ""
        # "Family Laws | VII of 1909 | Promulgation Date: October 22 1909"
        parts = [p.strip() for p in meta.split("|")]
        act_number = parts[1] if len(parts) > 1 and re.search(r"\bof\b", parts[1]) else None
        date = re.search(r"Promulgation Date:\s*(.+)$", meta)
        laws.append({"title": title, "url": urljoin(page_url, a[0].get("href")), "act_number": act_number,
                     "promulgation_date": date.group(1).strip() if date else None,
                     "year": year_of(title, act_number or "", date.group(1) if date else "")})
    return laws


def match(laws: list[dict], corpus: list[dict]) -> None:
    """exact: same cleaned title (year agrees when both have one).
    near: difflib ratio >= 0.93 on the cleaned title, same year (OCR spellings);
          counted as held, listed for review.
    possible: ratio >= 0.85, same year; NOT counted as held (e.g. a renamed Act)."""
    by_key: dict[str, list[dict]] = {}
    for c in corpus:
        for k in keys_for(c["title"]):
            by_key.setdefault(k, []).append(c)
    keys = list(by_key)
    for law in laws:
        law["status"] = status_of(law["title"])
        law["clean_title"] = clean_title(law["title"])
        cands, how = [], None
        for k in keys_for(law["title"]):
            if by_key.get(k):
                cands, how = by_key[k], "exact"
                break
        if not cands:
            for cutoff, label in ((0.93, "near"), (0.85, "possible")):
                close = difflib.get_close_matches(title_key(law["title"]), keys, n=1, cutoff=cutoff)
                if close:
                    cands, how = by_key[close[0]], label
                    break
        if cands and law["year"]:
            same_year = [c for c in cands if year_of(clean_title(c["title"])) in (None, law["year"])]
            cands = same_year
            if not cands:
                how = None   # same name, different year: a different Act
        seen, uniq = set(), []
        for c in cands:
            if c["n"] not in seen:
                seen.add(c["n"])
                uniq.append({"n": c["n"], "title": c["title"]})
        law["match"] = {"how": how, "corpus": uniq} if uniq else None


def classify_unmatched(title: str) -> str:
    t = title.lower()
    if re.search(r"punjab|sindh|khyber|pakhtunkhwa|n\.?w\.?f\.?p|balochistan|west pakistan|bengal|bombay|karachi|lahore", t):
        return "provincial or pre-1955 regional law"
    if re.search(r"\brules?\b|regulations?|order\b|instructions|estacode|manual", t):
        return "rules / regulations / orders / manual"
    if len(re.sub(r"[^a-z]", "", t)) < 6 or "page" in t:
        return "boilerplate title (extraction failed)"
    return "federal title not in any category listing (or a spelling we couldn't match)"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="use the saved HTML; no requests")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(UTC).isoformat(timespec="seconds")

    if args.offline:
        index_html = (RAW / "index.html").read_bytes()
    else:
        from app.scraping.fetcher import DisallowedError, Fetcher
        f = Fetcher(max_pages=30)
        try:
            r = f.get(INDEX)
        except DisallowedError as e:
            print(f"STOP: robots.txt disallows the category index: {e}")
            return 3
        if r.status != 200:
            print(f"STOP: category index returned HTTP {r.status}")
            return 3
        index_html = r.content
        (RAW / "index.html").write_bytes(index_html)
    cats = parse_index(index_html)
    print(f"{len(cats)} categories on the index page")

    for c in cats:
        path = RAW / f"cat_{c['catid']:02d}.html"
        if not args.offline:
            r = f.get(c["url"])
            if r.status != 200:
                print(f"STOP: {c['name']} returned HTTP {r.status}")
                return 3
            path.write_bytes(r.content)
        c["laws"] = parse_category(path.read_bytes(), c["url"])
        c["listed_count"] = len(c["laws"])
        print(f"  {c['name']:24} badge {c['badge_count']!s:>4}  listed {c['listed_count']:4}")

    corpus = load_corpus_titles(ROOT / "docs" / "architecture" / "corpus_statute_list.md")
    for c in cats:
        match(c["laws"], corpus)
        c["held"] = sum(1 for law in c["laws"] if law["match"] and law["match"]["how"] != "possible")
        c["possible"] = sum(1 for law in c["laws"] if law["match"] and law["match"]["how"] == "possible")
        c["missing"] = c["listed_count"] - c["held"]
        c["status_counts"] = {st: sum(1 for law in c["laws"] if law["status"] == st)
                              for st in ("current", "under_review", "repealed")}

    matched_n = {m["n"] for c in cats for law in c["laws"]
                 if law["match"] and law["match"]["how"] != "possible" for m in law["match"]["corpus"]}
    unmatched = [dict(c, reason=classify_unmatched(c["title"])) for c in corpus if c["n"] not in matched_n]
    dup_groups: dict[str, list[int]] = {}
    for c in corpus:
        dup_groups.setdefault(title_key(c["title"]) + "|" + str(year_of(clean_title(c["title"]))), []).append(c["n"])
    dups = {n for g in dup_groups.values() if len(g) > 1 for n in g}
    for u in unmatched:
        if u["n"] in dups:
            u["reason"] = "duplicate spelling of another corpus title"
    out = {"source": "Pakistan Code (pakistancode.gov.pk), category listing pages only",
           "index_url": INDEX, "fetched_at": fetched_at if not args.offline else "see raw/ file times",
           "corpus_list": "docs/architecture/corpus_statute_list.md", "corpus_titles": len(corpus),
           "matching": "normalise_title (leading number/'the' dropped, letters+digits only) without the year; "
                       "then the year must agree when both sides have one; 'near' = difflib ratio >= 0.93",
           "categories": cats, "corpus_unmatched": unmatched}
    (KB / "category_map.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    total_listed = sum(c["listed_count"] for c in cats)
    print(f"listed laws {total_listed}, held {sum(c['held'] for c in cats)}, corpus titles matched {len(matched_n)}"
          f" of {len(corpus)}; unmatched corpus titles {len(unmatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
