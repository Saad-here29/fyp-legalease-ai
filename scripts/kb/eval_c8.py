"""kb-v2 C8: retrieval-only evaluation on three separate sets. Offline, no LLM.

Sets: the 26 gold questions (scripts/kb/compare_kb_v2.py), the live-test
questions and 40 unseen questions (docs/eval/c8_questions.json, committed before
any C8 change). Demo configuration: KB_V2, QUERY_HINTS and SCRAPED_V2 on, raw
questions (no rewrite), top 5 of embeddings.search. A hit = an accepted Act and
section in the top 5 (any score). "chat" = the same check on the passages Chat
would send the model (app/services/legal_chat_service.retrieve_passages: 0.65
gate, exact section lookup, section expansion), i.e. whether the right section
reaches the model; no model is called.

    cd backend
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python ../scripts/kb/eval_c8.py --label baseline
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python ../scripts/kb/eval_c8.py --label hybrid --compare baseline

Writes docs/eval/c8_results_<label>.json; --compare prints per-set counts and
every question that got better or worse against an earlier label.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from compare_kb_v2 import GOLD, SectionGuess  # noqa: E402

from app.ai import embeddings  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.kb.index_v2 import load_records  # noqa: E402
from app.services import legal_chat_service as chat  # noqa: E402

EVAL = ROOT / "docs" / "eval"


def sets() -> dict[str, list[tuple[str, str, list]]]:
    data = json.loads((EVAL / "c8_questions.json").read_text(encoding="utf-8"))
    return {"gold": [(i, q, acc) for i, q, acc in GOLD],
            "live": [(x["id"], x["q"], [tuple(e) for e in x["expected"]]) for x in data["live"]],
            "unseen": [(x["id"], x["q"], [tuple(e) for e in x["expected"]]) for x in data["unseen"]]}


def rank(hits: list[dict], accepted, guess) -> int | None:
    for i, h in enumerate(hits, 1):
        if h.get("kb") == "scraped":
            continue
        title, sec = guess(h)
        if sec and any(title == t and (sec == s or (s == "Schedule" and sec.startswith("Schedule")))
                       for t, s in accepted):
            return i
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--compare", default=None)
    ap.add_argument("--off", default="", help="C8 retrieval features to switch off: hybrid,hint_sections")
    args = ap.parse_args()
    settings.KB_V2, settings.QUERY_HINTS, settings.SCRAPED_V2 = True, True, True
    off = {x.strip() for x in args.off.split(",") if x.strip()}
    settings.HYBRID_SEARCH = "hybrid" not in off
    settings.HINT_EXACT_SECTIONS = "hint_sections" not in off
    embeddings.build_or_load()
    guess = SectionGuess(load_records(Path(settings.KB_DIR) / "records"))
    out = {}
    for name, qs in sets().items():
        rows = []
        for qid, q, acc in qs:
            hits = embeddings.search(q, top_k=5)
            r = rank(hits, acc, guess)
            sent = chat.retrieve_passages(q, q)
            c = rank(sent, acc, guess)
            top = [f"{guess(h)[0] or h.get('source')} {guess(h)[1] or ''} ({h['relevance']:.3f})" for h in hits[:3]]
            rows.append({"id": qid, "q": q, "rank": r, "chat": c, "top3": top})
        out[name] = rows
        print(f"{name}: top5 {sum(1 for r in rows if r['rank'])}/{len(rows)} | "
              f"reaches the model {sum(1 for r in rows if r.get('chat'))}/{len(rows)}")
    (EVAL / f"c8_results_{args.label}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    if args.compare:
        old = json.loads((EVAL / f"c8_results_{args.compare}.json").read_text(encoding="utf-8"))
        for name in out:
            before = {r["id"]: r["rank"] for r in old[name]}
            better = [r["id"] for r in out[name] if (r["rank"] or 99) < (before.get(r["id"]) or 99)]
            worse = [r["id"] for r in out[name] if (r["rank"] or 99) > (before.get(r["id"]) or 99)]
            print(f"  {name}: {sum(1 for v in before.values() if v)} -> {sum(1 for r in out[name] if r['rank'])}"
                  f" | better {better} | worse {worse}")
            cb = {r["id"]: r.get("chat") for r in old[name]}
            if any(v is not None for v in cb.values()) or "chat" in old[name][0]:
                cw = [r["id"] for r in out[name] if cb.get(r["id"]) and not r.get("chat")]
                print(f"    reaches the model: {sum(1 for v in cb.values() if v)} -> "
                      f"{sum(1 for r in out[name] if r.get('chat'))} | lost {cw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
