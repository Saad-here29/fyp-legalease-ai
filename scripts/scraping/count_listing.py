"""kb-v2 C8: count the laws a source's listing names, by first letter (no PDFs fetched).

Walks listing_urls and paged_listing exactly as a scraping run does (same
polite fetcher: identified User-Agent, 2 s per request, robots.txt), and
reports how many distinct laws each letter has. For the Pakistan Code it also
checks whether a letter has a second page (&page=2).

    cd backend
    python ../scripts/scraping/count_listing.py "Khyber Pakhtunkhwa Code"
    python ../scripts/scraping/count_listing.py "Pakistan Code"
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.scraping.fetcher import Fetcher  # noqa: E402
from app.scraping.kb_run import listing_pages  # noqa: E402
from app.scraping.parse import parse_listing  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    name = sys.argv[1]
    src = next(s for s in json.loads((ROOT / "scripts" / "scraping" / "sources.json").read_text(encoding="utf-8"))
               if s["name"] == name)
    f = Fetcher(max_pages=3000, max_pdfs=0)
    seen: dict[str, str] = {}
    done, pages = None, 0
    for url, letter, _n in listing_pages(src):
        if letter is not None and letter == done:
            continue
        page = f.get(url)
        pages += 1
        new = [i for i in parse_listing(page.content, page.url, src) if i.url not in seen]
        if letter is not None and not new:
            done = letter
            continue
        for i in new:
            seen[i.url] = i.title
    if name == "Pakistan Code":
        extra = 0
        for url in src.get("listing_urls", [])[:3]:
            page = f.get(url.replace("page=1", "page=2"))
            pages += 1
            extra += sum(1 for i in parse_listing(page.content, page.url, src) if i.url not in seen)
        print(f"page=2 adds {extra} new laws for the first three letters")
    by = Counter((t.strip().lstrip("'\"(").upper().removeprefix("THE ")[:1] or "?") for t in seen.values())
    print(json.dumps({"source": name, "listing_pages": pages, "laws": len(seen),
                      "by_letter": dict(sorted(by.items()))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
