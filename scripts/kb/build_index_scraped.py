"""kb-v2 C3: embed the scraped laws and judgments (incremental, resumable).

Writes faiss_scraped.* (statute sections from storage/kb/scraped/records/
statutes/) and faiss_scraped_judgments.* (judgments from .../judgments/), in
backend/storage/kb/ (git-ignored). Never writes faiss_v2, faiss_judgments or
the old index (the build refuses their paths). Vectors are cached by chunk
text (vector_cache_scraped*/), saved every 1,000, so a stopped run resumes:
run the same command again. Appends an "index" line to the update log.

    cd backend
    python ../scripts/kb/build_index_scraped.py              # 420 s of embedding per run
    python ../scripts/kb/build_index_scraped.py --budget 0   # no time limit

Exit code 0 when both indexes are complete, 3 when stopped by the budget
(run again), 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=420.0, help="seconds of embedding per run; 0 = no limit")
    args = ap.parse_args()

    from app.ai import embeddings
    from app.kb import scraped
    from app.scraping import stage

    try:
        model = embeddings._load_model()
        result = scraped.build(tokenizer=model.tokenizer, embed=embeddings.embed,
                               time_budget=None if args.budget == 0 else args.budget)
        stage.append_log(scraped.index_log_entry(result))
    except Exception as e:  # noqa: BLE001 — exit non-zero with the reason
        print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    s, j = result["statutes"], result["judgments"]
    print(json.dumps({"statutes": {k: s.get(k) for k in ("records", "chunks", "embedded_now", "reused_vectors",
                                                          "still_missing", "complete", "total_seconds")},
                      "excluded_v1_sources": s.get("excluded_v1_sources"),
                      "judgments": {k: j.get(k) for k in ("judgments", "chunks", "embedded_now", "still_missing",
                                                           "complete", "chunks_per_second")}},
                     ensure_ascii=False, indent=1))
    if not result["complete"]:
        print("INCOMPLETE: run the same command again to continue.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
