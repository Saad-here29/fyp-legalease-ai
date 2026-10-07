"""Judgments in the knowledge base (kb-v2 Phase C1). Offline; no model calls.

From a judgment file (.txt or .pdf) to a judgment record
(docs/knowledge_base_spec.md § b), then to paragraph-aware index chunks:

  read_text        text of a .txt / .pdf file (PDF via its text layer; a page
                   without one is reported as needing OCR, not OCR'd here)
  quality          near-empty? scanned? a law-report publisher's copy (PLD,
                   SCMR, YLR … headnotes)? -> excluded from the index
  metadata         case_name, court, year, judges, case_number, citation,
                   topics; rule-based, from the first pages
  paragraphs       numbered paragraphs ("12. ...") or, failing that, blank-line
                   blocks, each with its index
  chunks           windows of at most 120 tokens from ONE paragraph, prefix
                   "<case_name> (<court>, <year>) - para <N>:" inside the 120
  build_index      incremental and resumable (VectorCache), writes
                   storage/kb/faiss_judgments.*, never the statute indexes

Large source files are not copied: a record keeps the file's path and SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

from app.core.config import settings
from app.kb import index_v2

PROVENANCE = "dataset supplied by the team; original source and licence to be confirmed"
NEAR_EMPTY_CHARS = 1500          # a judgment shorter than this is a stub, a cover page or a failed extraction
MIN_PARAGRAPH_CHARS = 40

# --------------------------------------------------------------------------- reading


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_text(path: Path) -> tuple[str, dict]:
    """(text, info) where info has pages, pages_without_text, format."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        raw = path.read_bytes()
        for enc in ("utf-8", "utf-16", "cp1252"):
            try:
                return raw.decode(enc), {"format": "txt", "pages": None, "pages_without_text": 0}
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", "replace"), {"format": "txt", "pages": None, "pages_without_text": 0}
    if suffix == ".pdf":
        import pymupdf
        doc = pymupdf.open(path)
        pages = [p.get_text() for p in doc]
        empty = sum(1 for t in pages if len(t.strip()) < 50)
        return "\n".join(pages), {"format": "pdf", "pages": len(pages), "pages_without_text": empty}
    raise ValueError(f"unsupported file type: {path.suffix}")


def content_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- quality

# A law-report publisher's copy: its citation in the header and headnotes
# (the publisher's summary) before the judgment.
_REPORT_CITE = re.compile(
    r"\b(?:PLD|PLJ|NLR|KLR)\s*\(?\d{4}\)?\s+(?:SC|FSC|Lahore|Lah|Karachi|Kar|Peshawar|Pesh|Quetta|Islamabad|Isl)\b"
    r"|\b\d{4}\s+(?:SCMR|MLD|CLC|YLR|PCr\.?\s?LJ|P\s?Cr\.?\s?L\s?J|PLC|CLD|PTD|SCJ|MLR|CLJ)\s+\d{1,5}\b")
_HEADNOTE = re.compile(r"\b(?:Head\s?notes?|HEADNOTE|Ratio\s+decidendi|Cases?\s+referred|Per\s+[A-Z][a-z]+,?\s+J\.)",
                       re.I)


def quality(text: str, info: dict) -> dict:
    head = text[:4000]
    report_cites = _REPORT_CITE.findall(head)
    flags = {
        "chars": len(text.strip()),
        "near_empty": len(text.strip()) < NEAR_EMPTY_CHARS,
        "needs_ocr": bool(info.get("pages")) and info.get("pages_without_text", 0) > info["pages"] / 2,
        "law_report": bool(report_cites) and bool(_HEADNOTE.search(text[:8000])),
        "report_citations": sorted(set(report_cites))[:5],
    }
    flags["exclude"] = (
        "near-empty" if flags["near_empty"] and not flags["needs_ocr"]
        else "needs OCR" if flags["needs_ocr"]
        else "law-report copy (publisher headnotes)" if flags["law_report"]
        else None)
    return flags


# --------------------------------------------------------------------------- metadata

_COURTS = [
    (r"supreme\s+court\s+of\s+pakistan", "Supreme Court of Pakistan"),
    (r"federal\s+shariat\s+court", "Federal Shariat Court"),
    (r"lahore\s+high\s+court", "Lahore High Court"),
    (r"(?:high\s+court\s+of\s+sindh|sindh\s+high\s+court)", "Sindh High Court"),
    (r"peshawar\s+high\s+court", "Peshawar High Court"),
    (r"(?:high\s+court\s+of\s+balochistan|balochistan\s+high\s+court)", "Balochistan High Court"),
    (r"islamabad\s+high\s+court", "Islamabad High Court"),
    (r"family\s+court", "Family Court"),
]
_CASE_NO = re.compile(
    r"\b((?:Civil|Criminal|Crl\.?|C\.|Constitutional|Const\.|Jail|Shariat|Writ|Family|Human\s+Rights)\s*"
    r"(?:Petitions?|Appeals?|Misc\.?\s*Applications?|Review\s+Petitions?|P\.|A\.|M\.?A\.|R\.?P\.)\s*"
    r"(?:No[s]?\.?\s*)?[\dA-Z][\w\-/. ]{0,25}?(?:of|/)\s*(?:19|20)\d{2})", re.I)
_SHORT_CASE_NO = re.compile(r"\b((?:Crl|C|Civ|Cr|W|F|J)\.?\s?[A-Z]{1,3}\.?\s?(?:No\.?\s*)?\d{1,5}(?:-[A-Z])?(?:/|\s+of\s+)(?:19|20)\d{2})")
_PARTIES = re.compile(
    r"([A-Z][^\n]{2,120}?)\s*(?:\.{2,}|…|,)?\s*(?:Petitioner|Appellant|Applicant)s?\b[\s\S]{0,200}?"
    r"\b(?:versus|vs\.?|v\.)\s*([A-Z][^\n]{2,120}?)\s*(?:\.{2,}|…|,)?\s*(?:Respondent|Opposite\s+part)", re.I)
_VERSUS = re.compile(r"^\s*(.{3,100}?)\s+(?:versus|vs\.?|v\.)\s+(.{3,100}?)\s*$", re.I | re.M)
_JUDGE_LINE = re.compile(
    r"(?:Present|Coram|Bench|Before)\s*[:\-]\s*([\s\S]{3,400}?)(?:\n\s*\n|Civil|Criminal|Crl|Petition|Appeal|For\s+the)",
    re.I)
_JUDGE_NAME = re.compile(r"((?:Mr\.?\s+|Mrs\.?\s+|Ms\.?\s+|Justice\s+)*[A-Z][A-Za-z.'\- ]{3,60}?),?\s*(?:C\.?J\.?|J\.|HCJ|ACJ)(?![A-Za-z])")
_DECIDED = re.compile(r"(?:Date\s+of\s+(?:hearing|decision|judgment|announcement)|Decided\s+on|Announced\s+on)"
                      r"\s*[:\-]?\s*[^\n]{0,30}?((?:19|20)\d{2})", re.I)
_YEAR = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")

TOPICS = {
    "family": r"family\s+court|family\s+laws?|matrimonial",
    "dower": r"\bdower\b|\bmahr\b|\bmehr\b|haq\s*mehr",
    "khula": r"\bkhula\b|\bkhulla\b",
    "talaq": r"\btalaq\b|\bdivorce\b",
    "dissolution": r"dissolution\s+of\s+(?:muslim\s+)?marriage",
    "nikah": r"\bnikah\b|nikahnama|nikah\s*nama",
    "custody": r"\bcustody\b|\bhizanat\b",
    "guardianship": r"\bguardian(?:ship)?\b|guardians\s+and\s+wards",
    "maintenance": r"\bmaintenance\b|\bnafqa\b|\bnafaqa\b",
    "bail": r"\bbail\b",
    "murder": r"qatl[\s-]*(?:e|i)[\s-]*amd|\bmurder\b|section\s+302",
    "contract": r"\bcontract\b|agreement\s+to\s+sell",
    "property": r"\bproperty\b|\bland\b|\bmutation\b|\btenan(?:t|cy)\b|\bpossession\b",
    "constitutional": r"article\s+199|article\s+184|fundamental\s+rights|writ\s+petition",
}
FAMILY_TOPICS = ("family", "dower", "khula", "talaq", "dissolution", "nikah", "custody", "guardianship", "maintenance")


def _clean_party(s: str) -> str:
    s = re.sub(r"\s+", " ", re.sub(r"[.…_]{2,}", " ", s)).strip(" ,.:;-")
    s = re.sub(r"^(?:\d+\.\s*)", "", s)
    return s[:90]


def metadata(text: str, *, filename: str = "") -> dict:
    """Rule-based metadata from the first pages. A field is None when the
    rules don't find it (never guessed)."""
    head = text[:6000]
    out: dict = {"case_name": None, "court": None, "year": None, "judges": [], "case_number": None,
                 "citation": None, "topics": []}
    m = _PARTIES.search(head)
    if m:
        out["case_name"] = f"{_clean_party(m.group(1))} v. {_clean_party(m.group(2))}"
    else:
        m = _VERSUS.search(head)
        if m and len(m.group(1)) < 100:
            out["case_name"] = f"{_clean_party(m.group(1))} v. {_clean_party(m.group(2))}"
    low = head.lower()
    for pat, name in _COURTS:
        if re.search(pat, low):
            out["court"] = name
            break
    m = _CASE_NO.search(head) or _SHORT_CASE_NO.search(head)
    if m:
        out["case_number"] = re.sub(r"\s+", " ", m.group(1)).strip(" .")
    m = _DECIDED.search(text[:12000]) or _DECIDED.search(text[-4000:])
    if m:
        out["year"] = int(m.group(1))
    elif out["case_number"] and _YEAR.search(out["case_number"]):
        out["year"] = int(_YEAR.findall(out["case_number"])[-1])
    m = _JUDGE_LINE.search(head)
    names = _JUDGE_NAME.findall(m.group(1)) if m else []
    if not names:
        names = _JUDGE_NAME.findall(text[-3000:])          # signatures at the end
    out["judges"] = list(dict.fromkeys(re.sub(r"\s+", " ", n).strip(" ,.") for n in names if len(n.split()) >= 2))[:5]
    cites = _REPORT_CITE.findall(head)
    # Only a neutral / court citation is stored; a publisher's citation is not copied (spec § b).
    neutral = re.search(r"\b(?:19|20)\d{2}\s+(?:SCP|LHC|SHC|PHC|BHC|IHC|FSC)\s+\d{1,5}\b", head)
    out["citation"] = neutral.group(0) if neutral else None
    out["report_citations_seen"] = sorted(set(cites))[:5]
    body = text.lower()
    out["topics"] = [t for t, pat in TOPICS.items() if len(re.findall(pat, body)) >= 2]
    return out


# --------------------------------------------------------------------------- paragraphs and records

_NUMBERED = re.compile(r"(?m)^\s*(\d{1,3})\s*[.)]\s+(?=\S)")


def paragraphs(text: str) -> list[dict]:
    """[{n, text}]: the judgment's own numbered paragraphs when it has at
    least three in order, else blank-line blocks numbered 1, 2, …"""
    marks = list(_NUMBERED.finditer(text))
    seq, want = [], 1
    for m in marks:
        if int(m.group(1)) == want:
            seq.append(m)
            want += 1
    out = []
    if len(seq) >= 3:
        lead = text[: seq[0].start()].strip()
        if len(lead) >= MIN_PARAGRAPH_CHARS:
            out.append({"n": 0, "text": " ".join(lead.split())})       # heading, parties, bench
        for i, m in enumerate(seq):
            end = seq[i + 1].start() if i + 1 < len(seq) else len(text)
            body = " ".join(text[m.end():end].split())
            if len(body) >= MIN_PARAGRAPH_CHARS:
                out.append({"n": int(m.group(1)), "text": body})
        return out
    n = 0
    for block in re.split(r"\n\s*\n", text):
        body = " ".join(block.split())
        if len(body) >= MIN_PARAGRAPH_CHARS:
            n += 1
            out.append({"n": n, "text": body})
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:80] or "judgment"


def make_record(path: Path, text: str, info: dict, *, source: str, file_sha: str | None = None) -> dict:
    meta = metadata(text, filename=path.name)
    q = quality(text, info)
    sha = file_sha or sha256_file(path)
    paras = paragraphs(text)
    return {
        "doc_id": f"judgment/{slug(source)}/{sha[:16]}",
        "case_name": meta["case_name"], "court": meta["court"], "year": meta["year"],
        "judges": meta["judges"], "case_number": meta["case_number"], "citation": meta["citation"],
        "topics": meta["topics"], "source_type": "case_law",
        "source": source, "source_tier": 2, "source_url": None,
        "original_file": str(path), "file_sha256": sha, "content_hash": content_hash(text),
        "provenance_note": PROVENANCE, "status": "staged",
        "quality": q, "report_citations_seen": meta["report_citations_seen"],
        "paragraphs": paras,
    }


REQUIRED = ("doc_id", "case_name", "court", "year", "judges", "case_number", "citation", "topics", "source_type",
            "source", "source_tier", "source_url", "original_file", "file_sha256", "content_hash",
            "provenance_note", "status", "paragraphs")


def validate(rec: dict) -> list[str]:
    errs = [f"missing {k}" for k in REQUIRED if k not in rec]
    if errs:
        return errs
    if rec["source_type"] != "case_law":
        errs.append("source_type must be case_law")
    if rec["provenance_note"] != PROVENANCE:
        errs.append("provenance_note")
    if not re.fullmatch(r"[0-9a-f]{64}", rec["file_sha256"] or ""):
        errs.append("file_sha256")
    if not isinstance(rec["judges"], list) or not isinstance(rec["topics"], list):
        errs.append("judges/topics must be lists")
    if rec["year"] is not None and not 1947 <= rec["year"] <= 2100:
        errs.append(f"year {rec['year']}")
    if not rec["paragraphs"] or any(not p.get("text") for p in rec["paragraphs"]):
        errs.append("paragraphs")
    return errs


# --------------------------------------------------------------------------- chunks

def chunk_prefix(rec: dict, n: int) -> str:
    name = rec.get("case_name") or "Judgment"
    bits = ", ".join(str(x) for x in (rec.get("court"), rec.get("year")) if x)
    return f"{name}" + (f" ({bits})" if bits else "") + f" - para {n}:"


def make_chunks(recs: list[dict], tokenizer) -> list[dict]:
    """Windows of at most index_v2.MAX_TOKENS tokens from ONE paragraph each,
    prefix included (the prefix is shortened if very long)."""
    chunks = []
    for rec in recs:
        for p in rec["paragraphs"]:
            prefix = chunk_prefix(rec, p["n"])
            while len(tokenizer(prefix, add_special_tokens=False)["input_ids"]) > index_v2.MAX_PREFIX:
                prefix = prefix[: int(len(prefix) * 0.8)].rsplit(" ", 1)[0] + " …:"
            for c in index_v2.chunk_record({"text": p["text"]}, tokenizer, prefix=prefix):
                chunks.append({"doc_id": rec["doc_id"], "para": p["n"], "window": c["window"],
                               "case_name": rec.get("case_name"), "court": rec.get("court"), "year": rec.get("year"),
                               "topics": rec.get("topics", []), "source_type": "case_law",
                               "source_tier": rec.get("source_tier"), "chunk_text": c["text"]})
    return chunks


# --------------------------------------------------------------------------- pilot selection

def select_pilot(recs: list[dict], n: int = 400) -> list[dict]:
    """Family-law judgments first (most family topics first), then a spread
    across years and judges (round-robin by year, preferring unseen judges)."""
    usable = [r for r in recs if not r["quality"]["exclude"]]
    fam = sorted((r for r in usable if set(r["topics"]) & set(FAMILY_TOPICS)),
                 key=lambda r: (-len(set(r["topics"]) & set(FAMILY_TOPICS)), r["doc_id"]))
    picked = fam[:n]
    ids = {r["doc_id"] for r in picked}
    rest = [r for r in usable if r["doc_id"] not in ids]
    by_year: dict = {}
    for r in sorted(rest, key=lambda r: r["doc_id"]):
        by_year.setdefault(r.get("year") or 0, []).append(r)
    seen_judges = {j for r in picked for j in r.get("judges", [])}
    while len(picked) < n and any(by_year.values()):
        for y in sorted(by_year):
            if not by_year[y] or len(picked) >= n:
                continue
            pool = by_year[y]
            best = next((r for r in pool if not set(r.get("judges", [])) <= seen_judges), pool[0])
            pool.remove(best)
            picked.append(best)
            seen_judges.update(best.get("judges", []))
    return picked


# --------------------------------------------------------------------------- index

def index_paths() -> tuple[Path, Path]:
    return Path(settings.KB_JUDGMENTS_INDEX_PATH), Path(settings.KB_JUDGMENTS_METADATA_PATH)


def build_index(records_dir: Path, index_path: Path, meta_path: Path, *, tokenizer, embed,
                cache_dir: Path | None = None, checkpoint: int = 1000, time_budget: float | None = None,
                max_chunks: int | None = None) -> dict:
    """Like index_v2.build: vectors cached by chunk text, embedded `checkpoint`
    at a time with a save after each batch, stop after `time_budget` seconds
    and resume on the next run. Refuses the statute index paths."""
    import faiss
    import numpy as np
    protected = {Path(settings.FAISS_INDEX_PATH).resolve(), Path(settings.FAISS_METADATA_PATH).resolve(),
                 Path(settings.KB_V2_INDEX_PATH).resolve(), Path(settings.KB_V2_METADATA_PATH).resolve()}
    if index_path.resolve() in protected or meta_path.resolve() in protected:
        raise ValueError("refusing to write over a statute index")
    t0 = time.perf_counter()
    cache = index_v2.VectorCache(cache_dir or index_path.parent / "vector_cache_judgments")
    recs = []
    for p in sorted(records_dir.glob("*.jsonl")):
        recs += [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    recs = [r for r in recs if not r.get("quality", {}).get("exclude")]
    chunks = make_chunks(recs, tokenizer)
    if max_chunks is not None:
        chunks = chunks[:max_chunks]
    keys = [index_v2.vector_key(c["chunk_text"]) for c in chunks]
    unique = list(dict.fromkeys(keys))
    missing = [k for k in unique if k not in cache.vecs]
    text_of = {k: c["chunk_text"] for k, c in zip(keys, chunks, strict=True)}
    embedded, t_embed = 0, 0.0
    for i in range(0, len(missing), checkpoint):
        if time_budget is not None and time.perf_counter() - t0 > time_budget:
            break
        part = missing[i:i + checkpoint]
        t1 = time.perf_counter()
        cache.add(part, embed([text_of[k] for k in part]))
        t_embed += time.perf_counter() - t1
        embedded += len(part)
    manifest = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "normalised": True, "metric": "inner product", "max_tokens": index_v2.MAX_TOKENS,
        "judgments": len(recs), "chunks": len(chunks), "reused_vectors": len(unique) - len(missing),
        "embedded_now": embedded, "still_missing": len(missing) - embedded, "complete": embedded == len(missing),
        "embed_seconds": round(t_embed, 1),
        "chunks_per_second": round(embedded / t_embed, 1) if t_embed else None,
        "total_seconds": round(time.perf_counter() - t0, 1),
        "courts": dict(Counter(r.get("court") for r in recs)),
    }
    if not manifest["complete"]:
        return manifest
    vectors = np.vstack([cache.vecs[k] for k in keys]).astype(np.float32) if keys else np.zeros((0, 384), np.float32)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_i, tmp_m = index_path.with_name(index_path.name + ".tmp"), meta_path.with_name(meta_path.name + ".tmp")
    faiss.write_index(index, str(tmp_i))
    tmp_m.write_text(json.dumps({"manifest": manifest, "chunks": chunks}, ensure_ascii=False), encoding="utf-8")
    tmp_i.replace(index_path)
    tmp_m.replace(meta_path)
    return manifest
