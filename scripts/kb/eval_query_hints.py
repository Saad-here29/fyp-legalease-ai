"""kb-v2 C5: retrieval-only evaluation of the query hints. Offline, no LLM.

The 26 gold questions (scripts/kb/compare_kb_v2.py) and 10 family-law
questions, raw (no rewrite), KB_V2 on, top 5: is an accepted Act + section
in the top 5, before (QUERY_HINTS off) and after (on)? Writes
docs/evaluation/query_hints_eval_2026-10-07.md and lists every question that got worse.

    cd backend
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python ../scripts/kb/eval_query_hints.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from compare_kb_v2 import (  # noqa: E402
    DMMA,
    FCA,
    GOLD,
    GWA,
    MFLO,
    OFF_TOPIC,
    SectionGuess,
    gold_rank,
)

from app.ai import embeddings  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.kb import query_hints  # noqa: E402
from app.kb.index_v2 import load_records  # noqa: E402

SHARIAT = "West Pakistan Muslim Personal Law (Shariat) Application Act, 1962"
FAMILY10 = [
    ("F01", "How does a husband give talaq to his wife in Pakistan?", [(MFLO, "7")]),
    ("F02", "After a divorce, what notice has to be sent to the Union Council chairman?", [(MFLO, "7")]),
    ("F03", "Can a wife get khula through the Family Court?", [(FCA, "10"), (DMMA, "2"), (FCA, "Schedule")]),
    ("F04", "When does the husband have to pay the dower to his wife?", [(MFLO, "10"), (FCA, "Schedule")]),
    ("F05", "Is it compulsory to register a nikah?", [(MFLO, "5")]),
    ("F06", "What does a Nikah Registrar do?", [(MFLO, "5")]),
    ("F07", "Who decides custody of a minor child after the parents separate?", [(GWA, "17"), (GWA, "25"),
                                                                              (FCA, "Schedule")]),
    ("F08", "Can the court appoint a guardian for a minor's property?", [(GWA, "7"), (GWA, "17")]),
    ("F09", "How is the property of a deceased Muslim divided among the heirs?", [(SHARIAT, "2"), (MFLO, "4")]),
    ("F10", "Can a wife claim maintenance from her husband?", [(MFLO, "9"), (FCA, "Schedule")]),
]
OUT = ROOT / "docs" / "evaluation" / "query_hints_eval_2026-10-07.md"


def search(q: str, hints_on: bool) -> list[dict]:
    settings.QUERY_HINTS = hints_on
    return embeddings.search(q, top_k=5)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    settings.KB_V2, settings.SCRAPED_V2 = True, False
    embeddings.build_or_load()
    guess = SectionGuess(load_records(Path(settings.KB_DIR) / "records"))
    rows = []
    for qid, q, acc in GOLD + FAMILY10:
        before, after = search(q, False), search(q, True)
        rb, ra = gold_rank(before, acc, guess), gold_rank(after, acc, guess)
        rows.append({"id": qid, "q": q, "hints": [h["id"] for h in query_hints.matching(q)],
                     "before": rb, "after": ra,
                     "sb": before[rb - 1]["relevance"] if rb else None, "sa": after[ra - 1]["relevance"] if ra else None,
                     "top_after": f"{guess(after[0])[0] or after[0].get('source')} {guess(after[0])[1] or ''}"
                     if after else ""})
        print(f"{qid} hints={rows[-1]['hints']} before={rb} after={ra}")

    def change(r):
        b, a = r["before"] or 99, r["after"] or 99
        return "same" if a == b else ("better" if a < b else "WORSE")

    def cell(rank, score):
        return f"#{rank} ({score:.3f})" if rank else "not in top 5"

    gold = [r for r in rows if r["id"].startswith("G")]
    fam = [r for r in rows if r["id"].startswith("F")]
    lines = ["# Query hints: retrieval before/after (2026-10-07)\n\n",
             "Offline: raw questions (no LLM rewrite), `KB_V2` on, scraped laws off, top 5. A hit = an accepted Act "
             "and section in the top 5, at any score. Hints: `backend/storage/kb/query_hints.json`; script: "
             "`scripts/kb/eval_query_hints.py`.\n\n",
             "| Set | Before (hints off) | After (hints on) |\n|---|---:|---:|\n"]
    for name, part in (("26 gold questions", gold), ("10 family-law questions", fam), ("All 36", rows)):
        lines.append(f"| {name} | {sum(1 for r in part if r['before'])}/{len(part)} | "
                     f"{sum(1 for r in part if r['after'])}/{len(part)} |\n")
    worse = [r for r in rows if change(r) == "WORSE"]
    lines.append(f"\n**Got worse:** {', '.join(r['id'] for r in worse) if worse else 'none'}.\n\n")
    lines.append("| ID | Question | Hints | Before | After | Change |\n|---|---|---|---|---|---|\n")
    for r in rows:
        lines.append(f"| {r['id']} | {r['q']} | {', '.join(r['hints']) or '-'} | {cell(r['before'], r['sb'] or 0)} | "
                     f"{cell(r['after'], r['sa'] or 0)} | {change(r)} |\n")
    # Off-topic and foreign-law questions: the hints must never lift one past the 0.65 gate.
    lines.append("\n**Off-topic and foreign-law questions** (15): best score before / after; the chat refuses "
                 "below 0.65.\n\n| ID | Question | Hints | Before | After |\n|---|---|---|---:|---:|\n")
    crossed = []
    for oid, q in OFF_TOPIC:
        b, a = search(q, False), search(q, True)
        sb, sa = (b[0]["relevance"] if b else 0), (a[0]["relevance"] if a else 0)
        if sa >= 0.65 > sb:
            crossed.append(oid)
        lines.append(f"| {oid} | {q} | {', '.join(h['id'] for h in query_hints.matching(q)) or '-'} | "
                     f"{sb:.3f} | {sa:.3f} |\n")
    lines.append(f"\nCrossed 0.65 because of the hints: {', '.join(crossed) if crossed else 'none'}.\n")
    still = [r for r in rows if not r["after"]]
    lines.append(f"\n**Still not in the top 5 with hints:** "
                 f"{', '.join(r['id'] + ' (top: ' + r['top_after'] + ')' for r in still) if still else 'none'}.\n")
    OUT.write_text("".join(lines), encoding="utf-8")
    print("".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
