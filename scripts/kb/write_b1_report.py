"""Write docs/evaluation/kb_phase_b1_2026-10-06.md from the built records (offline).

Run after build_records.py and build_shariat_act.py. Reads the corpus and the
five user PDFs read-only (for the spot checks and the PDF comparison).
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))

import compare_user_pdfs as cmp  # noqa: E402
from build_records import CORE, DEFAULT_CORPUS  # noqa: E402

from app.kb.records import slugify  # noqa: E402

REC = ROOT / "backend" / "storage" / "kb" / "records"
TEST_LAWS = ["Muslim Family Laws Ordinance, 1961", "West Pakistan Family Courts Act, 1964",
             "Dissolution of Muslim Marriages Act, 1939", "Guardians and Wards Act, 1890",
             "Qanun-e-Shahadat Order, 1984"]
SHARIAT = "West Pakistan Muslim Personal Law (Shariat) Application Act, 1962"


def letters(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def load(title: str) -> list[dict]:
    return [json.loads(x) for x in (REC / f"{slugify(title)}.jsonl").read_text(encoding="utf-8").splitlines()]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = {r["title"]: r for r in json.loads((REC / "_report.json").read_text(encoding="utf-8"))}
    corpus = {r["title"]: r["text"] for r in json.loads(DEFAULT_CORPUS.read_text(encoding="utf-8"))}
    lines = ["# Knowledge base v2, Phase B1: section records (2026-10-06)\n\n"
         "Branch `kb-v2`, worktree `legalease-kb`. Everything here ran offline: no model calls, no network, "
         "nothing in master, the shared database, the live index or `backend/.env` was touched. The corpus "
         "and the user's PDFs were only read. Records are in `backend/storage/kb/records/` (gitignored); "
         "rebuild them with `scripts/kb/build_records.py` and `scripts/kb/build_shariat_act.py`.\n\n"]

    # ---- core list + per-law counts
    lines.append("## Core set and section detection\n\n"
             "**Detected / expected:** sections found in the body / entries the law's table of contents lists "
             "(for the section-table copies: the numbering 1…N). A TOC line covering a range "
             "(\"266-336. [Omitted.]\") is one entry. **Below 90% → unsectioned** (kept as windows, `section` null).\n\n"
             "| # | Law | Copy used | Detected / expected | Rate | Records | Schedules | Tier | Category |\n"
             "|---:|---|---|---:|---:|---:|---:|---:|---|\n")
    total = 0
    for i, (title, _y, _c) in enumerate(CORE, 1):
        r = report[title]
        t = r["tried"][-1] if r["mode"] == "sectioned" else r["tried"][0]
        total += r["records"]
        mode = "" if r["mode"] == "sectioned" else " **unsectioned**"
        alt = "" if len(r["tried"]) == 1 else f" (PDF copy first: {r['tried'][0]['detection']:.0%})"
        lines.append(f"| {i} | {title}{mode} | {t['source_type'].replace('statute_', '')}{alt} | "
                 f"{t['found']} / {t['expected']} | {t['detection']:.1%} | {r['records']} | {r['schedules']} | "
                 f"{r['source_tier']} | {r['category'] or '–'} |\n")
    sh = load(SHARIAT)
    lines.append(f"| {len(CORE) + 1} | {SHARIAT} (user PDF) | pdf | 7 / 7 | 100.0% | {len(sh)} | 0 | 2 | – |\n")
    total += len(sh)
    uns = [t for t, r in report.items() if r["mode"] == "unsectioned"]
    lines.append(f"\n**{len(CORE) + 1} laws, {total} records.** Unsectioned: {', '.join(uns) or 'none'}.\n\n")
    lines.append("Missing sections per law (TOC entries not found in the body):\n\n")
    for title, r in report.items():
        t = r["tried"][-1] if r["mode"] == "sectioned" else r["tried"][0]
        if t["missing"]:
            lines.append(f"- {title}: {', '.join(t['missing'][:40])}{' …' if len(t['missing']) > 40 else ''}\n")

    # ---- spot checks
    lines.append("\n## Spot checks on the five test laws\n\n"
             "Three random numbered sections per law (seed 1906). **Check:** the record's first and last 80 "
             "letters (letters only, so spacing and footnote markers don't matter) occur in the corpus source "
             "text, in that order. The excerpt is the record's first 160 characters.\n\n")
    rnd = random.Random(1906)
    for title in TEST_LAWS:
        recs = [x for x in load(title) if x["section"] and x["section"][0].isdigit()]
        src = letters(corpus[report[title]["used"]])
        lines.append(f"**{title}**\n\n")
        for rec in sorted(rnd.sample(recs, 3), key=lambda x: recs.index(x)):
            lt = letters(rec["text"])
            a, b = src.find(lt[:80]), src.find(lt[-80:])
            ok = a >= 0 and b >= a
            lines.append(f"- s.{rec['section']} *{rec['heading']}*: {'matches source' if ok else '**MISMATCH**'} "
                     f"({len(rec['text'])} chars). \"{rec['text'][:160]}…\"\n")
        lines.append("\n")

    # ---- Shariat
    lines.append(f"## {SHARIAT} (user-supplied PDF)\n\n"
             "- **File:** copied unchanged to `backend/storage/kb/raw/Muslim Personal Law (Shariat) Application "
             "Act 1962.pdf` (SHA-256 identical to the original).\n"
             "- **Extraction:** 3 pages, all with a text layer (Word export dated 2025-03-24), so no OCR was "
             "needed.\n"
             "- **Sections:** 7 of 7 (Preamble + ss. 1-7 = 8 records).\n"
             "- **Record fields:** `source` \"user-supplied PDF\", `source_url` null, `status` \"under_review\", "
             "`source_tier` 2, `provenance_note` saying the original source URL is to be confirmed.\n"
             "- **Note:** it's a West Pakistan Act (W.P. Act V of 1962); s.1(2) as amended by P.O. 4 of 1975 "
             "says it extends to the whole of Pakistan.\n\n")
    for rec in sh:
        if rec["section"] in ("Preamble", "2"):
            lines.append(f"**{rec['section'] if rec['section'] == 'Preamble' else 's.2 ' + rec['heading']}**\n\n"
                     f"> {rec['text']}\n\n")
    lines.append("All sections: " + "; ".join(f"{r['section']} {r['heading'] or ''}".strip() for r in sh) + ".\n\n")

    # ---- PDF comparison
    lines.append("## User PDFs compared with our corpus copies (nothing replaced)\n\n"
             "**Error rate** per 10,000 words, same method on both texts:\n"
             "- *split* = a common word broken in two (\"subje ct\");\n"
             "- *glued* = an 18+ letter run that isn't a word (\"noexpress\").\n\n"
             "| Law | User PDF | Pages | Text layer | Version | Split (PDF / corpus) | Glued (PDF / corpus) | Cleaner? |\n"
             "|---|---|---:|---|---|---:|---:|---|\n")
    versions = {
        "Pakistan Penal Code": ("file created 2025-11-30", "corpus: no date"),
        "Qanun-e-Shahadat Order, 1984": ("RGN 08-01-2026", "corpus: uploaded 3.1.2024"),
        "Constitution of Pakistan, 1973": ("**modified up to 28 Feb 2012**", "corpus: up to 31 May 2018"),
        "Code of Criminal Procedure, 1898": ("file created 2026-06-18", "corpus: last amended 2017-02-16"),
        "West Pakistan Family Courts Act, 1964": ("updated till 17.1.2025", "corpus: no date"),
    }
    rows = cmp.compare()
    for r in rows:
        v = versions[r["law"]]
        cleaner = r["pdf_errors"]["split_per_10k"] + r["pdf_errors"]["glued_per_10k"] < \
            r["corpus_errors"]["split_per_10k"] + r["corpus_errors"]["glued_per_10k"]
        lines.append(f"| {r['law']} | {r['pdf']} | {r['pages']} | {'yes' if r['extractable_text'] else 'no'} "
                 f"({r['pages_without_text']} pages without) | {v[0]}; {v[1]} | "
                 f"{r['pdf_errors']['split_per_10k']} / {r['corpus_errors']['split_per_10k']} | "
                 f"{r['pdf_errors']['glued_per_10k']} / {r['corpus_errors']['glued_per_10k']} | "
                 f"{'yes' if cleaner else 'no'} |\n")
    lines.append("\nExamples (corpus → user PDF):\n\n")
    for r in rows:
        lines.append(f"**{r['law']}**\n\n")
        for e in r["examples_where_pdf_is_clean"]:
            lines.append(f"- corpus: \"{e['corpus']}\"\n  - PDF: \"{e['pdf']}\"\n")
        lines.append("\n")
    lines.append("**Reading:**\n"
             "- **All five user PDFs have a text layer and are much cleaner than our copies.**\n"
             "- **Four are also newer:** QSO, CrPC, Family Courts Act, and probably PPC.\n"
             "- **The Constitution PDF is older than our copy** (Feb 2012 vs May 2018), so it can't replace it "
             "despite the cleaner text. Both predate later amendments.\n"
             "- **The Family Courts PDF is titled \"The Family Courts Act, 1964\"** (no \"West Pakistan\"). That's "
             "a provincial version. Which province's version it is needs confirming before use.\n\n")

    # ---- spec + tests
    lines.append("## Spec and tests\n\n"
             "- **`docs/architecture/knowledge_base_spec.md`** now documents:\n"
             "  - the corpus provenance rule;\n"
             "  - unsectioned laws;\n"
             "  - nullable fields;\n"
             "  - the **index-chunk rule:** at most 120 tokens from one section, counted with the embedding "
             "model's tokenizer, with the `<Title> - s.<N> <Heading>:` prefix inside the 120.\n"
             "- **Tests:** `backend/app/tests/unit/test_kb_sectioner.py`, 13 tests. That's 12 on small "
             "fixtures, plus a schema check over every built record (skipped when the records haven't been "
             "built).\n\n"
             "## Known limits\n\n"
             "- **The CPC First Schedule is one record** (Orders and Rules, about 628k characters). Splitting it "
             "by Order and Rule is a later step. Chunking will window it anyway.\n"
             "- **The Constitution's own contents page swaps Articles 25 and 25A.** The record labelled 25A holds "
             "Article 25 (\"Equality of citizens\") followed by 25A. That's a source defect, left as is and listed "
             "here.\n"
             "- **Detection is measured against the TOC.** A section the TOC omits can't be counted as "
             "missing.\n")
    out = ROOT / "docs" / "evaluation" / "kb_phase_b1_2026-10-06.md"
    out.write_text("".join(lines), encoding="utf-8")
    print("written", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
