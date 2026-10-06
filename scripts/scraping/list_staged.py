"""List the scraped documents in a throwaway schema: title, source, URL, fetch
date, status and hash. Never prints the document text.

    python <worktree>/scripts/scraping/list_staged.py --schema scrapelive_1791254533
    python <worktree>/scripts/scraping/list_staged.py --schema scrapelive_1791254533 --all

Run it from the main backend folder (so the settings find the database URL).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--all", action="store_true", help="every version and status, not only the latest staged rows")
    args = ap.parse_args()
    if args.schema == "public" or not args.schema.startswith("scrape"):
        print("Only throwaway schemas named scrape* are listed.", file=sys.stderr)
        return 2

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    url = os.environ.get("DATABASE_URL")
    if not url:
        from app.core.config import settings
        url = settings.DATABASE_URL
    engine = create_engine(make_url(url).set(port=5432))
    where = "" if args.all else "where status = 'staged' and is_latest"
    sql = text(f'''select title, source_name, content_type, status, change_kind, version,
                          to_char(fetched_at at time zone 'Asia/Karachi', 'YYYY-MM-DD HH24:MI') as fetched_pkt,
                          left(content_hash, 12) as hash12, source_url
                   from "{args.schema}".scraped_documents {where}
                   order by fetched_at, source_name, title''')
    with engine.connect() as c:
        rows = c.execute(sql).fetchall()
        runs = c.execute(text(f'''select to_char(started_at at time zone 'Asia/Karachi', 'YYYY-MM-DD HH24:MI') as at,
                                         pages_checked, new_count, changed_count, error_count
                                  from "{args.schema}".scrape_runs where not dry_run order by started_at''')).fetchall()
    print(f"{len(rows)} {'documents' if args.all else 'staged documents (latest versions)'} in schema {args.schema}\n")
    for r in rows:
        print(f"- {r.title}\n    {r.source_name} ({r.content_type}) | {r.status}/{r.change_kind} v{r.version} | "
              f"fetched {r.fetched_pkt} PKT | sha256 {r.hash12}…\n    {r.source_url}")
    print(f"\nRuns ({len(runs)}):")
    for r in runs:
        print(f"  {r.at} PKT  pages {r.pages_checked:3}  new {r.new_count}  changed {r.changed_count}  errors {r.error_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
