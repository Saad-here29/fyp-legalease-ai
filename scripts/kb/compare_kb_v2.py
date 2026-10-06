"""kb-v2 Phase B2 step 4: retrieval before/after (KB_V2 off vs on). Offline.

Raw questions, no LLM rewrite, top 5, the live 0.65 threshold. Reads the live
v1 index read-only (FAISS_INDEX_PATH / FAISS_METADATA_PATH from the
environment, pointing at the main checkout) and faiss_v2. Writes
docs/chat_baseline_2026-10-06.md (flag off; only if missing) and
docs/kb_v2_comparison_2026-10-06.md.

    cd backend && HF_HUB_OFFLINE=1 FAISS_INDEX_PATH=... FAISS_METADATA_PATH=... python ../scripts/kb/compare_kb_v2.py
"""

from __future__ import annotations

import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

from build_records import CORE  # noqa: E402

from app.ai import embeddings  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.kb import index_v2  # noqa: E402
from app.kb.index_v2 import load_records  # noqa: E402

DOCS = ROOT / "docs"
THRESHOLD = settings.RAG_SIMILARITY_THRESHOLD
MFLO, FCA, DMMA = ("Muslim Family Laws Ordinance, 1961", "West Pakistan Family Courts Act, 1964",
                   "Dissolution of Muslim Marriages Act, 1939")
PPC, CRPC, QSO = "Pakistan Penal Code, 1860", "Code of Criminal Procedure, 1898", "Qanun-e-Shahadat Order, 1984"
CON, CA = "Constitution of the Islamic Republic of Pakistan, 1973", "Contract Act, 1872"
GWA, TPA, SRA = "Guardians and Wards Act, 1890", "Transfer of Property Act, 1882", "Specific Relief Act, 1877"

# (id, question, accepted (law, section) pairs). Accept-either rules: G04 s.7 or s.9;
# G20 Art.17 or Art.79; G07/G10 FCA s.5 or the FCA Schedule.
GOLD = [
    ("G01", "On what grounds can a Muslim woman obtain a decree for the dissolution of her marriage?", [(DMMA, "2")]),
    ("G02", "What is the punishment for qatl-i-amd under the Pakistan Penal Code?", [(PPC, "302")]),
    ("G03", "What are the essential elements of a valid contract under the Contract Act, 1872?", [(CA, "10")]),
    ("G04", "If a husband pronounces talaq while his wife is pregnant, when does the talaq take effect, and can she "
            "claim maintenance during that period?", [(MFLO, "7"), (MFLO, "9")]),
    ("G05", "Can a husband marry a second wife without the permission of the Arbitration Council?", [(MFLO, "6")]),
    ("G06", "What is the procedure for talaq under the Muslim Family Laws Ordinance?", [(MFLO, "7")]),
    ("G07", "What can a wife do if her husband does not pay her maintenance?",
     [(MFLO, "9"), (FCA, "5"), (FCA, "Schedule")]),
    ("G08", "Can a grandchild inherit from the grandfather if the grandchild's father died before the grandfather?",
     [(MFLO, "4")]),
    ("G09", "How can a mother get custody of her minor child under the Guardians and Wards Act?", [(GWA, "25")]),
    ("G10", "Which court hears suits for dissolution of marriage, dower and maintenance?",
     [(FCA, "5"), (FCA, "Schedule")]),
    ("G11", "What happens at the pre-trial stage of a case in a Family Court?", [(FCA, "10")]),
    ("G12", "Can a wife get her marriage dissolved if her husband has not maintained her for two years?", [(DMMA, "2")]),
    ("G13", "How does the Pakistan Penal Code define qatl-i-amd?", [(PPC, "300")]),
    ("G14", "What is the punishment for cheating and dishonestly inducing delivery of property?", [(PPC, "420")]),
    ("G15", "What is the punishment for defamation under the Pakistan Penal Code?", [(PPC, "500")]),
    ("G16", "What is the punishment for theft?", [(PPC, "379")]),
    ("G17", "When can bail be granted in a non-bailable offence?", [(CRPC, "497")]),
    ("G18", "How is a First Information Report recorded for a cognizable offence?", [(CRPC, "154")]),
    ("G19", "What is the punishment for rape under the Pakistan Penal Code?", [(PPC, "376")]),
    ("G20", "How many witnesses are required to attest a document creating a financial obligation?",
     [(QSO, "17"), (QSO, "79")]),
    ("G21", "Is the right to a fair trial a fundamental right in Pakistan?", [(CON, "10A")]),
    ("G22", "What is the writ jurisdiction of a High Court?", [(CON, "199")]),
    ("G23", "What compensation can be claimed for breach of contract?", [(CA, "73")]),
    ("G24", "How is a sale of immovable property made under the Transfer of Property Act?", [(TPA, "54")]),
    ("G25", "Can a person file a suit for a declaration of their title to property?", [(SRA, "42")]),
    ("G26", "Can a minor enter into a valid contract?", [(CA, "11")]),
]
OFF_TOPIC = [
    ("O01", "What is the capital of Australia and how many people live there?"),
    ("O02", "What is the weather forecast for Lahore tomorrow?"),
    ("O03", "Give me a recipe for chocolate cake."),
    ("O04", "Who won the Cricket World Cup in 1992?"),
    ("O05", "How do I reset my Wi-Fi router?"),
    ("O06", "What is the best smartphone under 50,000 rupees?"),
    ("O07", "Explain how photosynthesis works."),
    ("O08", "Write a poem about the monsoon."),
    ("O09", "How many calories are in a plate of biryani?"),
    ("O10", "What is the exchange rate of the US dollar today?"),
    ("O11", "How do I register a company with the Corporate Affairs Commission in Nigeria?"),
    ("O12", "Is a verbal contract enforceable in Thailand?"),
    ("O13", "How do I file for divorce in California?"),
    ("O14", "What is the punishment for murder under the Indian Penal Code?"),
    ("O15", "How do I apply for a UK student visa?"),
]
FAMILY = [
    ("CR-01", "Why is the Nikah Nama important in a dower dispute?", [(MFLO, "10"), (MFLO, "5")]),
    ("CR-02", "A wife claims that her dowry articles remain in the husband's possession after separation. "
              "What remedy may be available?", [(FCA, "Schedule"), (FCA, "5")]),
    ("CR-03", "Can a spouse lawfully retain the other's personal property merely because the marriage has ended?",
     [(FCA, "Schedule"), (FCA, "5")]),
    ("CR-04", "What is a suit for restitution of conjugal rights?", [(FCA, "Schedule"), (FCA, "9")]),
    ("CR-05", "Why is territorial jurisdiction important in a Family Court case?", [(FCA, "5")]),
    ("CR-06", "Can a family-law advocate knowingly present false facts before the court merely to secure relief "
              "for the client?", []),
    ("CR-07", "A wife files a suit seeking dissolution of marriage, unpaid dower, maintenance and recovery of dowry "
              "articles. The husband denies all allegations and claims that the wife left the matrimonial home "
              "without justification. What should the court determine?",
     [(FCA, "Schedule"), (FCA, "5"), (DMMA, "2")]),
    ("CR-08", "If a wife claims unpaid dower, who must establish the relevant facts?", [(MFLO, "10"), (FCA, "17")]),
]


def letters(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


class SectionGuess:
    """Which kb section a v1 chunk's text comes from: the record of the same law
    sharing the most 30-letter shingles (at least 30% of the chunk's)."""

    def __init__(self, records: list[dict]) -> None:
        self.v1_to_title = {c: t for t, _y, copies in CORE for c in copies}
        self.by_title: dict[str, list[tuple[str, str]]] = {}
        for r in records:
            self.by_title.setdefault(r["title"], []).append((r["section"] or "", letters(r["text"])))

    def __call__(self, hit: dict) -> tuple[str | None, str | None]:
        if hit.get("kb") == "v2":
            return hit["source"], hit["section"]
        title = self.v1_to_title.get(hit.get("source"))
        if not title:
            return None, None
        t = letters(embeddings.record_text(hit))
        sh = [t[i:i + 30] for i in range(0, max(1, len(t) - 30), 10)]
        if not sh:
            return title, None
        best, best_n = None, 0
        for sec, txt in self.by_title.get(title, []):
            n = sum(1 for s in sh if s in txt)
            if n > best_n:
                best, best_n = sec, n
        return title, (best if best_n >= 0.3 * len(sh) else None)


def run(question: str, on: bool) -> list[dict]:
    settings.KB_V2 = on
    return embeddings.search(question, top_k=5)


def label(hit: dict, guess) -> str:
    title, sec = guess(hit)
    name = title or hit.get("source")
    if sec is None:
        s = "(contents/other)" if title else ""
    else:
        s = (f"s.{sec}" if sec[:1].isdigit() else sec) + ("" if hit.get("kb") == "v2" else " ~")
    return f"{name} {s} ({hit['relevance']:.3f})".replace("  ", " ")


def gold_rank(hits: list[dict], accepted, guess) -> int | None:
    for i, h in enumerate(hits, 1):
        title, sec = guess(h)
        if sec and any(title == t and (sec == s or (s == "Schedule" and sec.startswith("Schedule")))
                       for t, s in accepted):
            return i
    return None


LAWYER_CSV = ROOT.parent / "fyp-legalease-ai-main" / "data" / "processed" / "qa_eval" / \
    "Legal_QA_dataset_From_lawyers_clean.csv"
SWEEP = (0.60, 0.62, 0.65)


def lawyer_questions() -> list[str]:
    import csv
    with LAWYER_CSV.open(encoding="utf-8") as f:
        return [r["Query"].strip() for r in csv.DictReader(f) if r["Query"].strip()]


def main() -> int:
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="kb_v2_comparison_2026-10-06.md")
    ap.add_argument("--sweep", action="store_true", help="also run the 78 lawyer questions and a threshold sweep")
    args = ap.parse_args()
    global OUT_NAME
    OUT_NAME = args.out
    n1 = embeddings.build_or_load()
    n2 = index_v2._V2_INDEX.load()
    print(f"v1 {n1} chunks, v2 {n2} chunks")
    guess = SectionGuess(load_records(ROOT / "backend" / "storage" / "kb" / "records"))
    rows = []
    for qid, q, acc in GOLD + [(i, q, None) for i, q in OFF_TOPIC] + FAMILY:
        off, on = run(q, False), run(q, True)
        settings.KB_V2 = True
        deep = embeddings.search(q, top_k=50)
        rows.append({"id": qid, "q": q, "accepted": acc, "off": off, "on": on,
                     "on_rank50": gold_rank(deep, acc, guess) if acc else None,
                     "sched_rank50": gold_rank(deep, [(FCA, "Schedule")], guess),
                     "off_rank": gold_rank(off, acc, guess) if acc else None,
                     "on_rank": gold_rank(on, acc, guess) if acc else None})
        print(qid, rows[-1]["off_rank"], rows[-1]["on_rank"], f"{off[0]['relevance']:.3f}", f"{on[0]['relevance']:.3f}")
    lawyers = []
    if args.sweep:
        for n, q in enumerate(lawyer_questions(), 1):
            off, on = run(q, False), run(q, True)
            lawyers.append({"id": f"L{n:02d}", "q": q, "off": off[0]["relevance"] if off else 0.0,
                            "on": on[0]["relevance"] if on else 0.0})
        print(f"{len(lawyers)} lawyer questions")
    settings.KB_V2 = False
    write_baseline(rows, guess)
    write_comparison(rows, guess, n1, n2, lawyers)
    return 0


OUT_NAME = "kb_v2_comparison_2026-10-06.md"


def sweep_section(rows, lawyers) -> list[str]:
    gold = [r for r in rows if r["id"].startswith("G")]
    off_t = [r for r in rows if r["id"].startswith("O")]

    def gold_ok(r, t):
        k = r["on_rank"]
        return k is not None and r["on"][k - 1]["relevance"] >= t

    out = ["## Threshold under KB_V2 (KB_V2_THRESHOLD; default left at 0.65)\n\n"
           f"Same raw-question retrieval, KB_V2 ON. **Answered** = the top passage scores at or above the threshold "
           f"(otherwise the chat refuses). The {len(lawyers)} lawyer questions have no section labels, so for them "
           "only answered/refused is measured, not correctness; several are foreign-law questions (e.g. the "
           "Nigerian CAC one) that *should* be refused.\n\n"
           "| Threshold | Lawyer questions answered / refused | Gold answered from the right section (top 5) | "
           "Off-topic that would pass |\n|---|---|---|---|\n"]
    n = len(lawyers)
    a = sum(x["off"] >= 0.65 for x in lawyers)
    g = sum(1 for r in gold if r["off_rank"] and r["off"][r["off_rank"] - 1]["relevance"] >= 0.65)
    o = [r["id"] for r in off_t if r["off"] and r["off"][0]["relevance"] >= 0.65]
    out.append(f"| OFF (v1) at 0.65, for reference | {a} / {n - a} | {g}/26 | {len(o)}/15 {', '.join(o)} |\n")
    for t in SWEEP:
        a = sum(x["on"] >= t for x in lawyers)
        g = sum(gold_ok(r, t) for r in gold)
        o = [r["id"] for r in off_t if r["on"] and r["on"][0]["relevance"] >= t]
        out.append(f"| ON at {t:.2f} | {a} / {n - a} | {g}/26 | {len(o)}/15 {', '.join(o)} |\n")
    out.append("\n")
    return out


def fmt_hits(hits, guess, n=3) -> str:
    return "<br>".join(f"{i}. {label(h, guess)}" for i, h in enumerate(hits[:n], 1))


def write_baseline(rows, guess) -> None:
    path = DOCS / "chat_baseline_2026-10-06.md"
    if path.exists():
        print("baseline exists; not rewritten")
        return
    lines = ["# Retrieval baseline (live v1 index, 2026-10-06)\n\n"
         "Flag state: KB_V2 off (the live behaviour). Raw question embedded as typed (no LLM rewrite), top 5, "
         f"threshold {THRESHOLD}. Index: `backend/storage/faiss/legal_corpus.faiss` "
         f"({embeddings._INDEX.ntotal} chunks). A section marked `~` is inferred: the v1 chunk's text overlaps "
         "that kb section (the v1 index has no section field). Built by `scripts/kb/compare_kb_v2.py`.\n\n"
         "| ID | Question | Top 5 (score) | Passes 0.65 |\n|---|---|---|---|\n"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['q'][:90]}{'…' if len(r['q']) > 90 else ''} | {fmt_hits(r['off'], guess, 5)} | "
                 f"{sum(1 for h in r['off'] if h['relevance'] >= THRESHOLD)} |\n")
    path.write_text("".join(lines), encoding="utf-8")


def write_comparison(rows, guess, n1, n2, lawyers=()) -> None:
    gold = [r for r in rows if r["id"].startswith("G")]
    off_t = [r for r in rows if r["id"].startswith("O")]
    fam = [r for r in rows if r["id"].startswith("CR")]

    def hit5(r, side):
        k = r[f"{side}_rank"]
        return k is not None and r[side][k - 1]["relevance"] >= THRESHOLD

    def top1(r, side):
        return r[side][0]["relevance"] if r[side] else 0.0

    worse = [r for r in gold + fam if r["accepted"] and (
        (r["off_rank"] and not r["on_rank"]) or (r["off_rank"] and r["on_rank"] and r["on_rank"] > r["off_rank"]))]
    phase = " after Phase B3 (schedule items, community gating)" if "b3" in OUT_NAME else ""
    lines = [f"# Knowledge base v2: retrieval before/after{phase} (2026-10-06)\n\n"
         f"Retrieval only, no model calls. Raw question (no LLM rewrite), top 5, threshold {THRESHOLD} (unchanged). "
         f"**OFF** = live v1 index ({n1} chunks). **ON** = `KB_V2`: faiss_v2 ({n2} section chunks) first, then v1 "
         "without the v1 chunks of any law v2 holds, merged by score. A `~` section on a v1 hit is inferred from "
         "text overlap with the kb records (v1 has no section field); \"(contents/other)\" = a v1 chunk of that law "
         "that matches no single section (a contents list, or text spanning sections).\n\n"
         "A gold hit = an accepted section in the top 5 **and** at or above 0.65 (it would reach the model). "
         "Accept-either: G04 s.7 or s.9; G20 Art.17 or Art.79; G07/G10 FCA s.5 or the FCA Schedule.\n\n"]
    lines.append("## Summary\n\n")
    g_off, g_on = sum(hit5(r, "off") for r in gold), sum(hit5(r, "on") for r in gold)
    a_off, a_on = sum(1 for r in gold if r["off_rank"]), sum(1 for r in gold if r["on_rank"])
    o_off = [r["id"] for r in off_t if top1(r, "off") >= THRESHOLD]
    o_on = [r["id"] for r in off_t if top1(r, "on") >= THRESHOLD]
    lines.append(f"| | OFF | ON |\n|---|---:|---:|\n"
             f"| Gold hit-rate at top 5, passing 0.65 | {g_off}/26 ({g_off / 26:.0%}) | {g_on}/26 ({g_on / 26:.0%}) |\n"
             f"| Gold in top 5 at any score | {a_off}/26 | {a_on}/26 |\n"
             f"| Off-topic questions passing 0.65 (would be answered) | {len(o_off)}/15 {', '.join(o_off)} | "
             f"{len(o_on)}/15 {', '.join(o_on)} |\n"
             f"| Family CR-01..CR-08 with an expected section in top 5 (passing) | "
             f"{sum(hit5(r, 'off') for r in fam if r['accepted'])}/7 | {sum(hit5(r, 'on') for r in fam if r['accepted'])}/7 |\n\n")
    lines.append("**Got worse** (gold found OFF but lower or missing ON): "
             + (", ".join(f"{r['id']} (rank {r['off_rank']} → {r['on_rank'] or 'not in top 5'})" for r in worse)
                or "none") + ".\n\n")
    lost = [r["id"] for r in gold + fam if r["accepted"] and hit5(r, "off") and not hit5(r, "on")]
    if lost:
        lines.append(f"Gold hits lost at the threshold: {', '.join(lost)}.\n\n")
    if lawyers:
        lines += sweep_section(rows, lawyers)

    # score distribution
    gs = sorted(top1(r, "on") for r in gold)
    os_ = sorted(top1(r, "on") for r in off_t)
    gh = sorted(r["on"][r["on_rank"] - 1]["relevance"] for r in gold if r["on_rank"])

    def dist(xs):
        return f"min {xs[0]:.3f} · median {st.median(xs):.3f} · max {xs[-1]:.3f}" if xs else "–"
    lines.append("## Score distribution with KB_V2 ON (does 0.65 still fit?)\n\n"
             f"| Set | Top-1 score |\n|---|---|\n| Gold questions (26) | {dist(gs)} |\n"
             f"| The gold section's own score (where found, {len(gh)}) | {dist(gh)} |\n"
             f"| Off-topic (15) | {dist(os_)} |\n\n")
    for name, xs in (("Gold top-1", gs), ("Off-topic top-1", os_)):
        lines.append(f"- {name}, sorted: " + ", ".join(f"{x:.3f}" for x in xs) + "\n")
    below = [r["id"] for r in gold if r["on_rank"] and r["on"][r["on_rank"] - 1]["relevance"] < THRESHOLD]
    weak = [r["id"] for r in gold if r["on_rank"] and THRESHOLD <= r["on"][r["on_rank"] - 1]["relevance"] < 0.70]
    lines.append(f"\nGold sections found ON but scoring under 0.65 (refused): {', '.join(below) or 'none'}. "
             f"In the 0.65-0.70 weak band: {', '.join(weak) or 'none'}. Highest off-topic top-1 ON: "
             f"{os_[-1]:.3f} ({max(off_t, key=lambda r: top1(r, 'on'))['id']}).\n\n")

    # FCA schedule
    lines.append("## FCA Schedule (dower, restitution, dowry, personal property)\n\n"
             "| ID | Schedule rank OFF (top 5) | Schedule rank ON (top 5) | Score ON | Schedule rank ON, top 50 |\n"
             "|---|---|---|---|---|\n")
    for r in fam + [x for x in gold if x["id"] in ("G07", "G10")]:
        def sched_rank(side, r=r):
            for i, h in enumerate(r[side], 1):
                t, s = guess(h)
                if t == FCA and s and s.startswith("Schedule"):
                    return i, h["relevance"], s
            return None, None, None
        ro, _, _ = sched_rank("off")
        rn, sn, which = sched_rank("on")
        lines.append(f"| {r['id']} | {ro or '–'} | {f'{rn} ({which})' if rn else '–'} | {f'{sn:.3f}' if sn else '–'} | "
                 f"{r['sched_rank50'] or '> 50'} |\n")

    # per question
    lines.append("\n## Per question (top 3)\n\n| ID | OFF top 3 | ON top 3 | Gold rank OFF → ON |\n|---|---|---|---|\n")
    for r in rows:
        gr = "–" if not r["accepted"] else (f"{r['off_rank'] or '✗'} → {r['on_rank'] or '✗'}"
                                            + ("" if r["on_rank"] else f" (ON top 50: {r['on_rank50'] or '> 50'})"))
        lines.append(f"| **{r['id']}** {r['q'][:70]}{'…' if len(r['q']) > 70 else ''} | {fmt_hits(r['off'], guess)} | "
                 f"{fmt_hits(r['on'], guess)} | {gr} |\n")
    (DOCS / OUT_NAME).write_text("".join(lines), encoding="utf-8")
    raw = [{k: v for k, v in r.items() if k not in ("off", "on")} | {
        "off": [{"source": h["source"], "section": guess(h)[1], "score": h["relevance"]} for h in r["off"]],
        "on": [{"source": h["source"], "section": guess(h)[1], "score": h["relevance"]} for h in r["on"]]}
        for r in rows]
    with open(ROOT / "backend" / "storage" / "kb" / OUT_NAME.replace(".md", "_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    raise SystemExit(main())
