"""kb-v2 Phase B1 step 5: compare user-supplied statute PDFs with our corpus copies.

Read-only: opens the PDFs where they are and the corpus JSON; copies nothing,
replaces nothing. Offline. Prints JSON to stdout.

Error measures (per 10,000 words, same method on both texts):
- split words: two adjacent pieces that form a common corpus word while each
  piece is rarer than the whole ("wi fe", "Coun cil"): extraction spacing errors;
- glued words: a run of 18+ letters that is not a corpus word ("ofthe",
  "prolongthe period", "ceremonycommon"): missing spaces.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import pymupdf  # noqa: E402

from app.kb.sectioner import build_vocab  # noqa: E402

CORPUS = ROOT.parent / "fyp-legalease-ai-main" / "data" / "processed" / "statutes" / "legal_statutes_corpus.json"
PAIRS = [
    ("Pakistan Penal Code", r"E:\Users\administratord5622ea3f15bfa00b17d2cf7770a8434.pdf", "THE PAKISTAN PENAL CODE"),
    ("Qanun-e-Shahadat Order, 1984", r"E:\Users\Qanun Shahdat Order.pdf", "THE QANUNESHAHADAT , 1984"),
    ("Constitution of Pakistan, 1973", r"E:\Users\Constituion of Islamic republic of Pakistan 1973.pdf",
     "THE CONSTITUTION OF THE ISLAMIC REPUBLIC OF PAKISTAN [As modified upto the 31st May, 2018"),
    ("Code of Criminal Procedure, 1898", r"E:\Users\Code of Criminal Procedure.pdf",
     "THE CODE OF CRIMINAL PROCEDURE , 1898"),
    ("West Pakistan Family Courts Act, 1964", r"E:\Users\Family Court Acts 1964.pdf",
     "THE WEST PAKISTAN FAMILY COURTS ACT, 1964"),
]
WORD = re.compile(r"[A-Za-z]+")


def errors(text: str, vocab) -> dict:
    words = WORD.findall(text)
    split, glued, split_ex, glued_ex = 0, 0, [], []
    for a, b in zip(words, words[1:], strict=False):
        j = (a + b).lower()
        cj = vocab.get(j, 0)
        if cj >= 10 and vocab.get(a.lower(), 0) < cj and vocab.get(b.lower(), 0) < cj:
            split += 1
            if len(split_ex) < 400:
                split_ex.append(f"{a} {b}")
    for w in words:
        if len(w) >= 18 and vocab.get(w.lower(), 0) < 3:
            glued += 1
            if len(glued_ex) < 400:
                glued_ex.append(w)
    n = max(1, len(words))
    return {"words": len(words), "split_per_10k": round(split * 1e4 / n, 1), "glued_per_10k": round(glued * 1e4 / n, 1),
            "split_examples": split_ex, "glued_examples": glued_ex}


def letters(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def example(corpus_text: str, pdf_text: str, broken: str) -> dict | None:
    """Context of a broken word in the corpus, and the same passage in the PDF."""
    i = corpus_text.find(broken)
    if i < 0:
        return None
    ctx = corpus_text[max(0, i - 40): i + len(broken) + 40]
    key = letters(corpus_text[max(0, i - 25): i + len(broken) + 25])
    pdf_letters, idx = [], []
    for k, ch in enumerate(pdf_text):
        if ch.isalpha():
            pdf_letters.append(ch.lower())
            idx.append(k)
    j = "".join(pdf_letters).find(key)
    if j < 0:
        return {"corpus": " ".join(ctx.split()), "pdf": None}
    a, b = idx[j], idx[j + len(key) - 1]
    return {"corpus": " ".join(ctx.split()), "pdf": " ".join(pdf_text[max(0, a - 15): b + 16].split())}


def compare() -> list[dict]:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    by = {r["title"]: r["text"] for r in corpus}
    vocab = build_vocab(r["text"] for r in corpus)
    out = []
    for name, pdf_path, ctitle in PAIRS:
        doc = pymupdf.open(pdf_path)
        pages = [p.get_text() for p in doc]
        text = "\n".join(pages)
        empty = sum(1 for p in pages if len(p.strip()) < 50)
        ctext = by[ctitle]
        e_pdf, e_cor = errors(text, vocab), errors(ctext, vocab)
        exs = []
        for broken in e_cor["split_examples"] + e_cor["glued_examples"]:
            ex = example(ctext, text, broken)
            if ex and ex["pdf"] and letters(ex["pdf"]) and broken not in ex["pdf"]:
                exs.append(ex)
            if len(exs) == 2:
                break
        first = " ".join(pages[0].split())[:160] if pages else ""
        out.append({
            "law": name, "pdf": Path(pdf_path).name, "pages": doc.page_count, "pages_without_text": empty,
            "extractable_text": empty < doc.page_count / 2, "pdf_chars": len(text), "corpus_title": ctitle,
            "corpus_chars": len(ctext), "pdf_first_page": first,
            "pdf_errors": {k: v for k, v in e_pdf.items() if not k.endswith("examples")},
            "corpus_errors": {k: v for k, v in e_cor.items() if not k.endswith("examples")},
            "examples_where_pdf_is_clean": exs,
        })
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(compare(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
