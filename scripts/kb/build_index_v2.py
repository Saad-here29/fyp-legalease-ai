"""kb-v2: embed every kb record into the NEW index faiss_v2 (incremental).

Vectors are cached (backend/storage/kb/vector_cache/, seeded from the
previous faiss_v2 build); only new or changed chunk texts are embedded,
1,000 at a time, each batch saved. A run stops embedding after
--budget seconds (default 420) and leaves the existing index untouched;
run it again to continue. The index is written only when every chunk has a
vector.

Same embedding model and normalisation as the live index
(app.ai.embeddings.embed: normalize_embeddings=True, IndexFlatIP). The live
index under backend/storage/faiss/ is never opened for writing.
Offline: run with HF_HUB_OFFLINE=1 so the cached model is used.

    cd backend && HF_HUB_OFFLINE=1 python ../scripts/kb/build_index_v2.py
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


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=420.0, help="seconds of embedding per run")
    args = ap.parse_args()
    t0 = time.perf_counter()
    model = embeddings._load_model()
    t_model = time.perf_counter() - t0
    # Every corpus copy of a law v2 holds (v1 'source' names are the corpus titles).
    excluded = sorted({t for _title, _y, copies in CORE for t in copies})
    manifest = index_v2.build(KB / "records", ROOT / "backend" / settings.KB_V2_INDEX_PATH,
                              ROOT / "backend" / settings.KB_V2_METADATA_PATH,
                              tokenizer=model.tokenizer, embed=embeddings.embed, excluded_v1_sources=excluded,
                              time_budget=args.budget)
    manifest["model_load_seconds"] = round(t_model, 1)
    for p in (settings.KB_V2_INDEX_PATH, settings.KB_V2_METADATA_PATH):
        if not manifest["complete"]:
            break
        manifest[f"size_{Path(p).name}"] = (ROOT / "backend" / p).stat().st_size
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("laws", "excluded_v1_sources")}, indent=1))
    print("laws:", len(manifest["laws"]), "| v1 sources excluded:", len(manifest["excluded_v1_sources"]))
    if not manifest["complete"]:
        print(f"INCOMPLETE: {manifest['still_missing']} chunks still to embed; run again to continue")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
