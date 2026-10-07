"""kb-v2 C3: the weekly update (scrape, validate, stage, embed, log).

    cd backend
    python ../scripts/scraping/run_weekly.py
    python ../scripts/scraping/run_weekly.py --scrape-budget 0 --embed-budget 0   # no time limits

1. scripts/scrape_laws.py --stage-files: fetch the three verified sources up
   to their caps, save originals, validate (quarantine), stage records,
   write one update-log line per source;
2. scripts/kb/build_index_scraped.py: embed what changed into faiss_scraped*
   (incremental) and write an "index" line to the update log.

Exit code: 0 when both steps finished, 3 when a time budget stopped one of
them (the next run continues), 1 when a step failed. Output is appended to
backend/storage/kb/scraped/weekly_runs.log. Registered as a Windows task by
scripts/scraping/register_weekly_task.ps1 (run that yourself).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def step(name: str, cmd: list[str], log) -> int:
    log.write(f"\n== {datetime.now():%Y-%m-%d %H:%M:%S} {name}: {' '.join(cmd[1:])}\n")
    log.flush()
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"}
    rc = subprocess.run(cmd, cwd=BACKEND, stdout=log, stderr=subprocess.STDOUT, env=env, check=False).returncode
    log.write(f"== {name} exit code {rc}\n")
    log.flush()
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--caps", default="", help='per-source caps, e.g. "Pakistan Code=120" (default: 120 / 60 / 100)')
    ap.add_argument("--scrape-budget", type=float, default=3600.0, help="seconds of fetching; 0 = no limit")
    ap.add_argument("--embed-budget", type=float, default=3600.0, help="seconds of embedding; 0 = no limit")
    ap.add_argument("--skip-within-hours", type=float, default=12.0,
                    help="skip URLs fetched this recently (a rerun the same day continues; a week later rechecks all)")
    args = ap.parse_args()
    out = BACKEND / "storage" / "kb" / "scraped" / "weekly_runs.log"
    out.parent.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    with out.open("a", encoding="utf-8") as log:
        scrape = [py, str(ROOT / "scripts" / "scrape_laws.py"), "--stage-files", "--budget", str(args.scrape_budget),
                  "--skip-within-hours", str(args.skip_within_hours)] + (["--caps", args.caps] if args.caps else [])
        rc1 = step("scrape", scrape, log)
        if rc1 not in (0, 3):
            log.write("== FAILED at scrape; nothing embedded\n")
            print(f"scrape failed (exit {rc1}); see {out}", file=sys.stderr)
            return 1
        rc2 = step("embed", [py, str(ROOT / "scripts" / "kb" / "build_index_scraped.py"),
                             "--budget", str(args.embed_budget)], log)
        if rc2 not in (0, 3):
            print(f"embedding failed (exit {rc2}); see {out}", file=sys.stderr)
            return 1
    rc = 0 if rc1 == 0 and rc2 == 0 else 3
    print(f"weekly update {'complete' if rc == 0 else 'stopped by a time budget (the next run continues)'}; "
          f"log: {out}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
