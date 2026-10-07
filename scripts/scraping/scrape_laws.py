"""Scheduled scraping of Pakistani law websites into a staging table (prototype).

    python scripts/scraping/scrape_laws.py --dry-run --limit 5               # fetch + compare, write nothing
    python scripts/scraping/scrape_laws.py --schema scrapetest_x --limit 10  # write to a throwaway schema
    python scripts/scraping/scrape_laws.py --sources "Pakistan Code" --limit 3 --dry-run
    python scripts/scraping/scrape_laws.py --dry-run --limit 3 --out run1.json            # remember hashes
    python scripts/scraping/scrape_laws.py --dry-run --limit 3 --compare-with run1.json   # unchanged / changed, no DB

kb-v2 C3, file staging (no database; run from backend/):
    python ../scripts/scraping/scrape_laws.py --stage-files                        # default caps PC 800, KP 60, FSC 100
    python ../scripts/scraping/scrape_laws.py --stage-files --caps "Pakistan Code=10,Khyber Pakhtunkhwa Code=10,Federal Shariat Court=10"
    python ../scripts/scraping/scrape_laws.py --stage-files --budget 0             # no time limit
    python ../scripts/scraping/scrape_laws.py --stage-files --reparse              # rebuild records from saved originals, no network
Writes backend/storage/kb/scraped/ (originals + manifest, records, quarantine,
state.json, update_log.jsonl). Pakistan Code fetches the Acts its category
listings name that we don't hold first. Stops after --budget seconds (default
900); run the same command again to continue (URLs fetched in the last
--skip-within-hours are skipped). Exit code 3 when stopped early, 1 on failure.

Sources and their selectors: scripts/scraping/sources.json (only "enabled"
sources run). Limits: identified User-Agent, 2 s between requests per site
(longer if robots.txt asks), retries with back-off, a page cap per run
(--max-pages) and a PDF cap (--limit). Writes require --schema while this is
a prototype branch: the shared database's public schema has no scraping
tables until the merge is approved. See docs/scraping.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources-file", type=Path, default=ROOT / "scripts" / "scraping" / "sources.json")
    ap.add_argument("--sources", default="", help="comma-separated source names (default: all enabled)")
    ap.add_argument("--limit", type=int, default=10, help="max PDFs (documents) per run, split across sources")
    ap.add_argument("--max-pages", type=int, default=60, help="hard cap on requests' pages per run")
    ap.add_argument("--dry-run", action="store_true", help="fetch and compare, write nothing")
    ap.add_argument("--schema", default=None, help="database schema to write to (required unless --dry-run)")
    ap.add_argument("--corpus", type=Path, default=ROOT / "data" / "processed" / "statutes" / "legal_statutes_corpus.json",
                    help="statute corpus whose titles count as already known")
    ap.add_argument("--out", type=Path, default=None, help="write the run summary JSON here")
    ap.add_argument("--compare-with", type=Path, default=None,
                    help="dry run only: an earlier --out JSON whose hashes count as the stored versions")
    ap.add_argument("--stage-files", action="store_true",
                    help="kb-v2 C3: stage into backend/storage/kb/scraped/ (files, no database)")
    ap.add_argument("--caps", default="", help='per-source document caps, e.g. "Pakistan Code=120,Federal Shariat Court=100"')
    ap.add_argument("--budget", type=float, default=900.0, help="--stage-files: seconds of fetching; 0 = no limit")
    ap.add_argument("--reparse", action="store_true",
                    help="--stage-files: rebuild records and quarantine from the saved originals (no network)")
    ap.add_argument("--skip-within-hours", type=float, default=20.0,
                    help="--stage-files: skip URLs fetched this recently (resume); 0 = refetch everything")
    args = ap.parse_args()
    if args.stage_files:
        return stage_files(args)
    if args.compare_with and not args.dry_run:
        print("--compare-with is for dry runs; a real run compares with the database.", file=sys.stderr)
        return 2

    if not args.dry_run and not args.schema:
        print("Refusing to write without --schema: the scraping tables only exist in throwaway schemas "
              "until the merge is approved. Use --dry-run, or --schema NAME.", file=sys.stderr)
        return 2

    from app.scraping.fetcher import Fetcher
    from app.scraping.report import previous_hashes, render
    from app.scraping.runner import load_corpus_titles, run

    sources = json.loads(args.sources_file.read_text(encoding="utf-8"))
    if args.sources:
        wanted = {s.strip() for s in args.sources.split(",")}
        sources = [s for s in sources if s["name"] in wanted]
        for s in sources:
            s["enabled"] = s.get("enabled") and True
    corpus_titles: set[str] = set()
    if args.corpus.exists():
        corpus_titles = load_corpus_titles(json.loads(args.corpus.read_text(encoding="utf-8")))
    print(f"{sum(1 for s in sources if s.get('enabled'))} enabled source(s); {len(corpus_titles)} corpus titles"
          f"{'' if args.corpus.exists() else ' (corpus file not found: nothing counts as already known)'}")

    db = None
    if args.schema:
        from sqlalchemy import create_engine, event, text
        from sqlalchemy.engine import make_url
        from sqlalchemy.orm import sessionmaker

        url = os.environ.get("DATABASE_URL")
        if not url:
            from app.core.config import settings
            url = settings.DATABASE_URL
        # Session pooler (5432) so the per-connection search_path holds.
        engine = create_engine(make_url(url).set(port=5432), pool_pre_ping=True)

        @event.listens_for(engine, "connect")
        def _schema(dbapi_conn, _rec):
            cur = dbapi_conn.cursor()
            cur.execute(f'SET search_path TO "{args.schema}"')
            cur.close()
            # Commit, or the pool's rollback-on-return would undo the SET and
            # later queries would look in the public schema.
            dbapi_conn.commit()

        with engine.connect() as c:
            ok = c.execute(text("select count(*) from information_schema.tables where table_schema=:s "
                                "and table_name in ('scraped_documents','scrape_runs')"), {"s": args.schema}).scalar()
        if ok != 2:
            print(f"Schema {args.schema!r} has no scraping tables; run the migration there first.", file=sys.stderr)
            return 2
        db = sessionmaker(bind=engine)()

    fetcher = Fetcher(max_pages=args.max_pages, max_pdfs=args.limit)
    previous = None
    if args.compare_with:
        previous = previous_hashes(json.loads(args.compare_with.read_text(encoding="utf-8")))
        print(f"Comparing with {args.compare_with} ({len(previous)} documents)")
    summary = run(sources, fetcher, db=db, corpus_titles=corpus_titles, limit=args.limit, dry_run=args.dry_run,
                  previous=previous)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_source", "items")}, ensure_ascii=False))
    for name, c in summary["per_source"].items():
        print(f"  {name:28} checked {c['checked']:3}  new {c['new']:3}  changed {c['changed']:3}  "
              f"unchanged {c['unchanged']:3}  baseline {c['baseline']:3}  errors {c['errors']:3}  {c['status']}")
    print(render(summary))
    if args.out:
        args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


DEFAULT_CAPS = {"Pakistan Code": 800, "Khyber Pakhtunkhwa Code": 60, "Federal Shariat Court": 100}     # PC 800: kb-v2 C8


def parse_caps(text: str) -> dict[str, int]:
    caps = dict(DEFAULT_CAPS)
    for part in filter(None, (p.strip() for p in text.split(","))):
        name, _, n = part.rpartition("=")
        if not name or not n.strip().isdigit():
            raise SystemExit(f"--caps: expected NAME=NUMBER, got {part!r}")
        caps[name.strip()] = int(n)
    return caps


def stage_files(args) -> int:
    """kb-v2 C3: the three verified sources, staged as files (no database)."""
    from app.core.config import settings
    from app.scraping import kb_run
    from app.scraping.fetcher import Fetcher

    caps = parse_caps(args.caps)
    sources = json.loads(args.sources_file.read_text(encoding="utf-8"))
    wanted = {s.strip() for s in args.sources.split(",")} if args.sources else set(DEFAULT_CAPS)
    sources = [s for s in sources if s["name"] in wanted and s.get("status") == "verified" and s.get("enabled")]
    sources.sort(key=lambda s: list(DEFAULT_CAPS).index(s["name"]) if s["name"] in DEFAULT_CAPS else 99)
    if not sources:
        print("No verified, enabled source selected.", file=sys.stderr)
        return 1
    if args.reparse:
        counts = kb_run.reparse(sources)
        for name, c in counts.items():
            print(f"  {name:26} staged {c['new'] + c['changed']:3}  held {c['already_held']:3}  "
                  f"quarantined {c['quarantined']:3}  missing original {c['errors']:3}")
        return 0 if not any(c["errors"] for c in counts.values()) else 3
    cmap_path = Path(settings.KB_DIR) / "category_map.json"
    priority = {}
    if cmap_path.exists():
        priority["Pakistan Code"] = kb_run.pakistan_code_priority(json.loads(cmap_path.read_text(encoding="utf-8")))
    total = sum(caps.get(s["name"], 0) for s in sources)
    fetcher = Fetcher(max_pages=total * 3 + 60, max_pdfs=total)
    names = ", ".join(f"{s['name']} (cap {caps.get(s['name'], 0)})" for s in sources)
    print(f"Staging {names}; {len(priority.get('Pakistan Code', []))} Pakistan Code Acts not held come first; "
          f"budget {'none' if not args.budget else f'{args.budget:.0f} s'}")
    try:
        summary = kb_run.run(sources, fetcher, caps=caps, priority=priority,
                             budget=args.budget or None, skip_within_hours=args.skip_within_hours)
    except Exception as e:  # noqa: BLE001 — a failed run must exit non-zero, with the reason
        print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    for name, e in summary["per_source"].items():
        print(f"  {name:26} fetched {e['fetched']:3}  new {e['new']:3}  changed {e['changed']:3}  "
              f"unchanged {e['unchanged']:3}  held {e['already_held']:3}  quarantined {e['quarantined']:3}  "
              f"errors {e['errors']:3}  resumed-skip {e['skipped_recent']:3}  {e['status']}")
    print(f"{fetcher.requests_made} requests. Embed with: python ../scripts/kb/build_index_scraped.py")
    if args.out:
        args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if summary["complete"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
