"""kb-v2 C7: the all-laws section index faiss_v2_all.* (35 core laws + records_all/).

faiss_v2 (the 35 core laws) is never touched. Vectors come from the same cache
as faiss_v2 (backend/storage/kb/vector_cache/), so the core laws' vectors are
reused; only new chunk texts need embedding. Two ways to get them:

  - on this laptop: run the build with a time budget, again and again
    (resumable, ~16 chunks/s);
  - on a Colab GPU: export the missing chunks, embed them there with
    scripts/kb/colab_embed.py, copy the .npz files it makes into
    backend/storage/kb/vector_cache/, then run the build (it finds them all).

    cd backend
    python ../scripts/kb/build_index_v2_all.py --export-chunks ../chunks_for_colab.jsonl   # what Colab needs
    python ../scripts/kb/build_index_v2_all.py --budget 0                                # build (all cached: seconds)
    python ../scripts/kb/build_index_v2_all.py                                           # 420 s of laptop embedding

The index is written only when every chunk has a vector; until then search
keeps using faiss_v2. Old-index passages of every law in faiss_v2_all are left
out of search, as for the 35 core laws. Exit code 0 complete, 3 stopped by the
budget, 1 failure.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from build_records import CORE  # noqa: E402

from app.ai import embeddings  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.kb import index_v2  # noqa: E402

KB = ROOT / "backend" / "storage" / "kb"
DIRS = [KB / "records", KB / "records_all"]
LAPTOP_CHUNKS_PER_SECOND = 16.0


def excluded_v1_sources() -> list[str]:
    """Every corpus copy of a law in faiss_v2_all (old-index source names are the corpus titles)."""
    out = {t for _title, _y, copies in CORE for t in copies}
    report = KB / "records_all" / "_report.json"
    if report.exists():
        for d in json.loads(report.read_text(encoding="utf-8"))["documents"]:
            if d["outcome"] == "sectioned":
                out.add(d["corpus_title"])
    return sorted(out)


def export_chunks(path: Path, tokenizer, limit: int | None) -> dict:
    """Write the chunks that have no cached vector yet as JSONL {key, text}."""
    recs = [r for d in DIRS for r in index_v2.load_records(d)]
    chunks, _texts = index_v2.make_chunks(recs, tokenizer)
    cache = index_v2.VectorCache(KB / "vector_cache")
    seen, missing = set(), []
    for c in chunks:
        k = index_v2.vector_key(c["chunk_text"])
        if k not in cache.vecs and k not in seen:
            seen.add(k)
            missing.append({"key": k, "text": c["chunk_text"]})
    out = missing[:limit] if limit else missing
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for m in out:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    return {"records": len(recs), "chunks": len(chunks), "unique_chunk_texts": len({index_v2.vector_key(c["chunk_text"])
                                                                                   for c in chunks}),
            "already_cached": len(cache.vecs), "to_embed": len(missing), "exported": len(out),
            "file": str(path), "file_mb": round(path.stat().st_size / 2**20, 1),
            "laptop_minutes_at_16_per_s": round(len(missing) / LAPTOP_CHUNKS_PER_SECOND / 60, 1),
            "model": settings.EMBEDDING_MODEL_NAME}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-chunks", type=Path, default=None, help="write the chunks still to embed (JSONL) and stop")
    ap.add_argument("--limit", type=int, default=None, help="--export-chunks: only the first N (a test)")
    ap.add_argument("--budget", type=float, default=420.0, help="seconds of laptop embedding per run; 0 = no limit")
    args = ap.parse_args()
    try:
        model = embeddings._load_model()
        if args.export_chunks:
            print(json.dumps(export_chunks(args.export_chunks, model.tokenizer, args.limit), indent=1))
            return 0
        idx, meta = ROOT / "backend" / settings.KB_V2_ALL_INDEX_PATH, ROOT / "backend" / settings.KB_V2_ALL_METADATA_PATH
        t0 = time.perf_counter()
        manifest = index_v2.build(DIRS, idx, meta, tokenizer=model.tokenizer, embed=embeddings.embed,
                                  excluded_v1_sources=excluded_v1_sources(), cache_dir=KB / "vector_cache",
                                  time_budget=None if args.budget == 0 else args.budget)
    except Exception as e:  # noqa: BLE001
        print(f"FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("laws", "excluded_v1_sources")}, indent=1))
    print(f"laws: {len(manifest['laws'])} | old-index sources left out: {len(manifest['excluded_v1_sources'])} | "
          f"{time.perf_counter() - t0:.0f} s")
    if not manifest["complete"]:
        print(f"INCOMPLETE: {manifest['still_missing']} chunks still to embed. Run again (or use Colab).")
        return 3
    print(f"Done: {idx.name} is in use after the backend restarts (KB_V2 on).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
