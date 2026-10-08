"""kb-v2 C17: retrieval-only evaluation on four sets. Offline, no LLM.

The three C8 sets (26 gold, live, 40 unseen) are scored exactly as in
eval_c8.py, with its rank(); the 20 non-core questions
(docs/evaluation/c17_noncore_questions.json) have answers in laws held only in
the sectioned corpus or the scraped records, so a scraped hit counts there too
(the record's own title and section). Configuration as in eval_c8.py: KB_V2,
QUERY_HINTS and SCRAPED_V2 on, the all-laws index when present, raw questions,
top 5 of embeddings.search, and the passages Chat would send the model.

    cd backend
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python ../scripts/kb/eval_c17.py --label baseline
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python ../scripts/kb/eval_c17.py --label fix --compare baseline

Writes docs/evaluation/c17_results_<label>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from compare_kb_v2 import SectionGuess  # noqa: E402
from eval_c8 import rank, sets  # noqa: E402

from app.ai import embeddings  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.kb.index_v2 import load_records  # noqa: E402
from app.services import legal_chat_service as chat  # noqa: E402

OUT = ROOT / "docs" / "evaluation"


def noncore() -> list[tuple[str, str, list]]:
    data = json.loads((OUT / "c17_noncore_questions.json").read_text(encoding="utf-8"))
    return [(x["id"], x["q"], [tuple(e) for e in x["expected"]]) for x in data["noncore"]]


def rank_any(hits: list[dict], accepted) -> int | None:
    """Rank of the first hit (any index) whose record title and section are accepted."""
    for i, h in enumerate(hits, 1):
        if h.get("kb") in ("v2", "scraped") and (h.get("source"), str(h.get("section"))) in accepted:
            return i
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--compare", default=None)
    args = ap.parse_args()
    settings.KB_V2, settings.QUERY_HINTS, settings.SCRAPED_V2 = True, True, True
    embeddings.build_or_load()
    guess = SectionGuess(load_records(Path(settings.KB_DIR) / "records"))
    all_sets = {**sets(), "noncore": noncore()}
    out = {}
    for name, qs in all_sets.items():
        rows = []
        for qid, q, acc in qs:
            hits = embeddings.search(q, top_k=5)
            sent = chat.retrieve_passages(q, q)
            if name == "noncore":
                r, c = rank_any(hits, acc), rank_any(sent, acc)
            else:
                r, c = rank(hits, acc, guess), rank(sent, acc, guess)
            top = [f"{h.get('source')} {h.get('section') or ''} ({h['relevance']:.3f}, {h.get('kb') or 'v1'})"
                   for h in hits[:3]]
            rows.append({"id": qid, "q": q, "rank": r, "chat": c, "top3": top})
        out[name] = rows
        print(f"{name}: top5 {sum(1 for r in rows if r['rank'])}/{len(rows)} | "
              f"reaches the model {sum(1 for r in rows if r['chat'])}/{len(rows)}")
    (OUT / f"c17_results_{args.label}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                        encoding="utf-8")
    if args.compare:
        old = json.loads((OUT / f"c17_results_{args.compare}.json").read_text(encoding="utf-8"))
        for name in out:
            before = {r["id"]: r for r in old[name]}
            for key, label in (("rank", "top5"), ("chat", "reaches the model")):
                b = sum(1 for r in old[name] if r[key])
                a = sum(1 for r in out[name] if r[key])
                lost = [r["id"] for r in out[name] if before[r["id"]][key] and not r[key]]
                won = [r["id"] for r in out[name] if not before[r["id"]][key] and r[key]]
                print(f"  {name} {label}: {b} -> {a} | gained {won} | lost {lost}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
