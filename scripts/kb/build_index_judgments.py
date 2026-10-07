"""kb-v2 C1: pilot selection and the judgments index (incremental, resumable).

Writes a NEW index, backend/storage/kb/faiss_judgments.* (git-ignored); the
statute indexes are never touched (the builder refuses their paths). Vectors
are cached in backend/storage/kb/vector_cache_judgments/, saved every 1,000,
so an interrupted run resumes where it stopped: just run the same command again.

    cd backend
    python ../scripts/kb/build_index_judgments.py --pilot 400 --select-only     # choose the pilot, no embedding
    python ../scripts/kb/build_index_judgments.py --pilot 400 --measure 500     # speed on 500 chunks
    python ../scripts/kb/build_index_judgments.py --pilot 400 --max-chunks 1000 # small test build
    python ../scripts/kb/build_index_judgments.py --pilot 400 --budget 0        # full pilot, no time limit
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import embeddings  # noqa: E402
from app.kb import judgments as jd  # noqa: E402

KB = ROOT / "backend" / "storage" / "kb"
ALL = KB / "judgments" / "records"
PILOT = KB / "judgments" / "pilot"


def load(d: Path) -> list[dict]:
    out = []
    for p in sorted(d.glob("*.jsonl")):
        out += [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=400, help="judgments in the pilot")
    ap.add_argument("--select-only", action="store_true")
    ap.add_argument("--measure", type=int, default=0, help="embed this many chunks once and report the speed")
    ap.add_argument("--max-chunks", type=int, default=None, help="build from only the first N chunks (testing)")
    ap.add_argument("--budget", type=float, default=420.0, help="seconds of embedding per run; 0 = no limit")
    args = ap.parse_args()

    recs = load(ALL)
    if not recs:
        print(f"No judgment records in {ALL}. Run scripts/kb/inventory_judgments.py first.")
        return 2
    pilot = jd.select_pilot(recs, args.pilot)
    PILOT.mkdir(parents=True, exist_ok=True)
    with (PILOT / "pilot.jsonl").open("w", encoding="utf-8") as f:
        for r in pilot:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    fam = sum(1 for r in pilot if set(r["topics"]) & set(jd.FAMILY_TOPICS))
    print(f"pilot: {len(pilot)} judgments ({fam} family-law) of {len(recs)} records "
          f"({sum(1 for r in recs if r['quality']['exclude'])} excluded)")
    if args.select_only:
        return 0

    model = embeddings._load_model()
    chunks = jd.make_chunks(pilot, model.tokenizer)
    print(f"pilot chunks: {len(chunks)}")
    if args.measure:
        sample = [c["chunk_text"] for c in chunks[: args.measure]]
        t0 = time.perf_counter()
        embeddings.embed(sample)
        dt = time.perf_counter() - t0
        rate = len(sample) / dt
        print(f"speed: {len(sample)} chunks in {dt:.1f} s = {rate:.1f} chunks/s; "
              f"full pilot ({len(chunks)} chunks) about {len(chunks) / rate / 60:.1f} min")
        return 0
    idx, meta = jd.index_paths()
    manifest = jd.build_index(PILOT, ROOT / "backend" / idx, ROOT / "backend" / meta, tokenizer=model.tokenizer,
                             embed=embeddings.embed, time_budget=None if args.budget == 0 else args.budget,
                             max_chunks=args.max_chunks)
    print(json.dumps(manifest, indent=1))
    if not manifest["complete"]:
        print(f"INCOMPLETE: {manifest['still_missing']} chunks left. Run the same command again to continue.")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
