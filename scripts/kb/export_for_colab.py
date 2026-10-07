"""kb-v2 C8: ONE file of every chunk still to embed, for one Colab run.

Covers the three section indexes the builders make:
  - faiss_v2_all     (35 core laws + records_all/)   cache: storage/kb/vector_cache/
  - faiss_scraped    (scraped statutes)              cache: storage/kb/vector_cache_scraped/
  - faiss_scraped_judgments (scraped FSC judgments)  cache: storage/kb/vector_cache_scraped_judgments/
A chunk already in its index's cache is left out; the same text needed twice is
written once. Keys are sha256(model + chunk text), so Colab's .npz files can go
into all three cache folders (a vector a folder doesn't need is ignored).

    cd backend
    python ../scripts/kb/export_for_colab.py            # -> storage/kb/colab/chunks_for_colab.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai import embeddings  # noqa: E402
from app.kb import index_v2  # noqa: E402
from app.kb import judgments as jd  # noqa: E402
from app.kb import scraped  # noqa: E402

KB = ROOT / "backend" / "storage" / "kb"
OUT = KB / "colab" / "chunks_for_colab.jsonl"


def missing(texts: list[str], cache_dir: Path) -> list[tuple[str, str]]:
    cache = index_v2.VectorCache(cache_dir)
    return [(k, t) for t in texts if (k := index_v2.vector_key(t)) not in cache.vecs]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    tok = embeddings._load_model().tokenizer
    parts = {}
    recs = [r for d in (KB / "records", KB / "records_all") for r in index_v2.load_records(d)]
    chunks, _ = index_v2.make_chunks(recs, tok)
    parts["faiss_v2_all"] = (len(chunks), missing([c["chunk_text"] for c in chunks], KB / "vector_cache"))
    srecs = index_v2.load_records(scraped.statute_records_dir())
    schunks, _ = index_v2.make_chunks(srecs, tok)
    parts["faiss_scraped"] = (len(schunks), missing([c["chunk_text"] for c in schunks], KB / "vector_cache_scraped"))
    jrecs = [json.loads(x) for p in sorted(scraped.judgment_records_dir().glob("*.jsonl"))
             for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    jrecs = [r for r in jrecs if not (r.get("quality") or {}).get("exclude")]
    jchunks = jd.make_chunks(jrecs, tok)
    parts["faiss_scraped_judgments"] = (len(jchunks), missing([c["chunk_text"] for c in jchunks],
                                                              KB / "vector_cache_scraped_judgments"))
    seen, rows = set(), []
    for _total, miss in parts.values():
        for k, t in miss:
            if k not in seen:
                seen.add(k)
                rows.append({"key": k, "text": t})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    report = {name: {"chunks": total, "to_embed": len(miss)} for name, (total, miss) in parts.items()}
    report["file"] = {"path": str(args.out), "chunks": len(rows), "mb": round(args.out.stat().st_size / 2**20, 1),
                      "laptop_minutes_at_16_per_s": round(len(rows) / 16 / 60, 1)}
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
