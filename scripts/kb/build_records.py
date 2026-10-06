"""kb-v2 Phase B1: section the core laws we already hold into JSONL records.

Offline: reads the corpus (read-only) and category_map.json; no network, no
model calls. Writes backend/storage/kb/records/<slug>.jsonl (gitignored) and
backend/storage/kb/records/_report.json.

    python scripts/kb/build_records.py [--corpus PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.kb.records import CORPUS_SOURCE, make_records, slugify  # noqa: E402
from app.kb.sectioner import build_vocab, split  # noqa: E402

DEFAULT_CORPUS = ROOT.parent / "fyp-legalease-ai-main" / "data" / "processed" / "statutes" / "legal_statutes_corpus.json"
KB = ROOT / "backend" / "storage" / "kb"
THRESHOLD = 0.90

# (canonical title, year, [corpus titles, preferred first]). Where we hold two
# copies, the Pakistan Code PDF text is preferred (it carries the amendments);
# the section-table copy is used only if the PDF copy sections below 90 %.
CORE = [
    # Family Laws (the 19 the Pakistan Code lists; all held)
    ("Anand Marriage Act, 1909", 1909, ["THE ANAND MARRIAGE ACT, 1909"]),
    ("Arya Marriage Validation Act, 1937", 1937, ["THE ARYA MARRIAGE VALIDATION ACT, 1937"]),
    ("Child Marriage Restraint Act, 1929", 1929, ["THE CHILD MARRIAGE RESTRAINT ACT, 1929"]),
    ("Christian Marriage Act, 1872", 1872, ["THE CHRISTIAN MARRIAGE ACT, 1872"]),
    ("Claims for Maintenance (Recovery Abroad) Ordinance, 1959", 1959,
     ["THE CLAIMS FOR MAINTENANCE (RECOVERY ABROAD) ORDINANCE, 1959"]),
    ("Dissolution of Muslim Marriages Act, 1939", 1939, ["THE DISSOLUTION OF MUSLIM MARRIAGES ACT, 1939"]),
    ("Divorce Act, 1869", 1869, ["THE DIVORCE ACT,1869"]),
    ("Dowry and Bridal Gifts (Restriction) Act, 1976", 1976, ["THE DOWRY AND BRIDAL GIFTS (RESTRICTION) ACT, 1976"]),
    ("Guardians and Wards Act, 1890", 1890, ["THE GUARDIANS AND WAR DS ACT, 1890"]),
    ("Hindu Disposition of Property Act, 1916", 1916, ["THE HINDU DISPOSITION OF PROPERTY ACT, 1916"]),
    ("Hindu Inheritance (Removal of Disabilities) Act, 1928", 1928,
     ["THE HINDU INHERITANCE (REMOVAL OF DISABILITIES) ACT, 1928"]),
    ("Hindu Marriage Disabilities Removal Act, 1946", 1946, ["THE HINDU MARRIAGE DISABILITIES REMOVAL ACT, 1946"]),
    ("Hindu Married Women's Right to Separate Residence and Maintenance Act, 1946", 1946,
     ["THE HINDU MARRIED WOMEN'S RIGHT TO SEPARATE RESIDENCE ANDMAINTENANCE ACT, 1946"]),
    ("Hindu Widows' Re-marriage Act, 1856", 1856, ["THE HINDU WIDOWS´ REMARRIAGE ACT, 1856"]),
    ("Hindu Women's Rights to Property Act, 1937", 1937, ["THE HINDU WOMEN S RIGHTS TO PROPERTY ACT, 1937"]),
    ("Marriage Functions (Prohibition of Ostentatious Displays and Wasteful Expenses) Ordinance, 2000", 2000,
     ["THE MARRIAGE FUNCTIONS (PROHIBITION OF OSTENTATIOUS DISPLAY AND WASTEFUL EXPENSES) ORDINANCE, 2000"]),
    ("Married Women's Property Act, 1874", 1874, ["THE MARRIED WOMEN'S PROPERTY ACT, 1874"]),
    ("Parsi Marriage and Divorce Act, 1936", 1936, ["THE PARSI MARRIAGE AND DIVORCE ACT, 1936"]),
    ("Special Marriage Act, 1872", 1872, ["THE SPECIAL MARRIAGE ACT, 1872"]),
    # Named core laws
    ("Muslim Family Laws Ordinance, 1961", 1961,
     ["THE MUSLIM FAMILY LAWS ORDINAN CE, 1961", "Muslim Family Laws Ordinance, 1961"]),
    ("West Pakistan Family Courts Act, 1964", 1964, ["THE WEST PAKISTAN FAMILY COURTS ACT, 1964"]),
    ("Qanun-e-Shahadat Order, 1984", 1984, ["THE QANUNESHAHADAT , 1984", "Qanun-e-Shahadat Order, 1984"]),
    ("Pakistan Penal Code, 1860", 1860, ["THE PAKISTAN PENAL CODE", "Pakistan Penal Code"]),
    ("Code of Criminal Procedure, 1898", 1898,
     ["THE CODE OF CRIMINAL PROCEDURE , 1898", "Code of Criminal Procedure, 1898"]),
    ("Code of Civil Procedure, 1908", 1908, ["THE CODE OF CIVIL PROCEDURE, 1908"]),
    ("Constitution of the Islamic Republic of Pakistan, 1973", 1973,
     ["THE CONSTITUTION OF THE ISLAMIC REPUBLIC OF PAKISTAN [As modified upto the 31st May, 2018"]),
    ("Contract Act, 1872", 1872, ["THE CONTRACT ACT, 1872"]),
    # Added: civil laws family and property disputes lean on (all held, all listed)
    ("Specific Relief Act, 1877", 1877, ["THE SPECIFIC RELIEF ACT, 1877"]),
    ("Limitation Act, 1908", 1908, ["THE LIMITATION ACT, 1908", "Limitation Act, 1908"]),
    ("Succession Act, 1925", 1925, ["THE SUCCESSION ACT, 1925"]),
    ("Transfer of Property Act, 1882", 1882, ["THE TRANSFER OF PROPERTY ACT, 1882", "Transfer of Property Act"]),
    ("Majority Act, 1875", 1875, ["THE MAJORITY ACT, 1875"]),
    ("Court-Fees Act, 1870", 1870, ["THE COURTFEES ACT, 1870"]),
    ("Registration Act, 1908", 1908, ["THE REGISTRATION ACT, 1908"]),
]


def listing_for(corpus_titles: list[str], cmap: dict) -> tuple[str | None, dict | None]:
    for c in cmap["categories"]:
        for law in c["laws"]:
            if law["match"] and law["match"]["how"] != "possible" and \
                    any(x["title"] in corpus_titles for x in law["match"]["corpus"]):
                return c["name"], law
    return None, None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    args = ap.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    by = {r["title"]: r for r in corpus}
    vocab = build_vocab(r["text"] for r in corpus)
    cmap = json.loads((KB / "category_map.json").read_text(encoding="utf-8"))
    out_dir = KB / "records"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = []
    for title, year, copies in CORE:
        tried = []
        chosen = None
        for ct in copies:
            r = by[ct]
            res = split(r["text"], r["source_type"], vocab)
            tried.append({"corpus_title": ct, "source_type": r["source_type"], "method": res.method,
                          "expected": res.expected, "found": res.found,
                          "detection": round(res.detection, 4), "missing": res.missing})
            if res.detection >= THRESHOLD:
                chosen = (ct, r, res)
                break
        category, law = listing_for(copies, cmap)
        meta = {
            "title": title, "year": year, "category": category,
            "act_number": law["act_number"] if law else None,
            "status": law["status"] if law else "current",
            "source": CORPUS_SOURCE, "source_tier": 1 if law else 2,
            "source_url": None, "original_file": None, "scraped_at": None,
            "jurisdiction": "Pakistan",
        }
        if chosen:
            ct, r, res = chosen
            recs = make_records(meta, res.sections)
            mode = "sectioned"
        else:
            ct = copies[0]
            recs = make_records(meta, None, raw_text=by[ct]["text"])
            mode = "unsectioned"
        path = out_dir / f"{slugify(title)}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_sched = sum(1 for x in recs if (x["section"] or "").startswith("Schedule"))
        report.append({"title": title, "mode": mode, "used": ct, "records": len(recs), "schedules": n_sched,
                       "category": category, "source_tier": meta["source_tier"], "status": meta["status"],
                       "tried": tried})
        t = tried[-1]
        print(f"{mode:11} {t['found']:4}/{t['expected']:<4} {t['detection']:6.1%}  recs {len(recs):5}  "
              f"sch {n_sched}  tier {meta['source_tier']}  {title}"
              + ("" if len(tried) == 1 else f"   [first copy {tried[0]['detection']:.1%}]"))
    (out_dir / "_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(report)} laws; unsectioned: {[x['title'] for x in report if x['mode'] == 'unsectioned']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
