"""File staging for scraped laws and judgments (kb-v2 C3). No database.

Everything lives under KB_DIR/scraped/ (git-ignored):

    originals/<source>/<sha16>.<pdf|html>   every page and PDF, byte for byte
    originals/manifest.jsonl                url, role, fetch date, SHA-256, path
    records/statutes/<slug>.jsonl           section records (spec § a)
    records/judgments/<source>.jsonl        judgment records (spec § b2)
    quarantine/<source>/<id>.json           rejected items, with the reason
    state.json                              per URL: text hash, outcome, fetch date
    update_log.jsonl                        one line per source per run

Validation (validate_statute / validate_judgment) rejects: empty or
near-empty text, a PDF with no text layer, garbled text (too few letters, or
mostly split single letters), a statute with no recognisable sections, a
missing title or year, and the same text twice in one run. Quarantined items
are never indexed. A core law (by title) or text identical to an item staged
in an earlier run is "already held" and skipped.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.kb import judgments as jd
from app.kb.records import make_records, slugify
from app.kb.records import validate as validate_record
from app.kb.sectioner import build_vocab, split_pdf, split_schedule_items
from app.scraping.parse import content_hash, normalise_title

SOURCES = {
    "Pakistan Code": {"jurisdiction": "Pakistan", "kind": "statute", "tier": 1},
    "Khyber Pakhtunkhwa Code": {"jurisdiction": "KP", "kind": "statute", "tier": 1},
    "Federal Shariat Court": {"jurisdiction": "Pakistan", "kind": "judgment", "tier": 1,
                              "court": "Federal Shariat Court"},
}
STATUTE_MIN_CHARS = 300            # non-space characters; a two-section Act has more
MIN_LETTER_RATIO = 0.55            # letters / non-space characters
MAX_SPLIT_LETTERS = 0.35           # single-letter tokens / tokens ("T h e  A c t")
MIN_DETECTION = 0.5                # sections found / sections the numbering or contents imply


class Quarantine(Exception):  # noqa: N818 — a decision, not an error
    """The item is rejected; the message is the reason."""


class Held(Exception):  # noqa: N818
    """The item is already in the knowledge base; the message says how."""


def utcnow() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def scraped_dir() -> Path:
    return Path(settings.KB_DIR) / "scraped"


def source_slug(source: str) -> str:
    return slugify(source)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    """A stored path as the records show it (relative to the backend folder)."""
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


# --------------------------------------------------------------------------- originals, manifest, state

def save_original(source: str, url: str, content: bytes, content_type: str, role: str, fetched_at: str,
                  requested_url: str | None = None) -> Path:
    """Save a fetched page or PDF unchanged and add it to the manifest."""
    digest = sha256(content)
    ext = ".pdf" if content[:4] == b"%PDF" or "pdf" in content_type.lower() else ".html"
    folder = scraped_dir() / "originals" / source_slug(source)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{digest[:16]}{ext}"
    if not path.exists():
        path.write_bytes(content)
    entry = {"source": source, "url": url, "role": role, "fetched_at": fetched_at, "sha256": digest,
             "content_type": content_type, "bytes": len(content), "path": rel(path),
             **({"requested_url": requested_url} if requested_url and requested_url != url else {})}
    with (scraped_dir() / "originals" / "manifest.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def load_state() -> dict:
    p = scraped_dir() / "state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_state(state: dict) -> None:
    p = scraped_dir() / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def append_log(entry: dict) -> None:
    p = scraped_dir() / "update_log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_log() -> list[dict]:
    p = scraped_dir() / "update_log.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def quarantine(source: str, url: str, title: str, reason: str, text: str, original: Path | None,
               fetched_at: str) -> Path:
    folder = scraped_dir() / "quarantine" / source_slug(source)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{sha256(url.encode())[:16]}.json"
    path.write_text(json.dumps({
        "source": source, "url": url, "title": title, "reason": reason, "fetched_at": fetched_at,
        "chars": len(text or ""), "sample": " ".join((text or "").split())[:600],
        "original": rel(original) if original else None,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- text

def pdf_text_info(content: bytes) -> tuple[str, dict]:
    import pymupdf
    with pymupdf.open(stream=io.BytesIO(content), filetype="pdf") as d:
        pages = [p.get_text() for p in d]
    return "\n".join(pages).strip(), {"format": "pdf", "pages": len(pages),
                                      "pages_without_text": sum(1 for t in pages if len(t.strip()) < 50)}


def text_problem(text: str, info: dict, min_chars: int) -> str | None:
    """Why this text can't be used, or None."""
    if info.get("pages") and info.get("pages_without_text", 0) > info["pages"] / 2:
        return f"no text layer on {info['pages_without_text']} of {info['pages']} pages (needs OCR)"
    body = re.sub(r"\s+", "", text or "")
    if len(body) < min_chars:
        return f"near-empty text ({len(body)} characters)"
    letters = sum(c.isalpha() for c in body) / len(body)
    if letters < MIN_LETTER_RATIO:
        return f"garbled text (letters are {letters:.0%} of characters)"
    tokens = (text or "").split()
    single = sum(1 for t in tokens if len(t) == 1 and t.isalpha()) / max(1, len(tokens))
    if single > MAX_SPLIT_LETTERS:
        return f"garbled text ({single:.0%} of words are single letters)"
    return None


_YEAR = re.compile(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)")
_DOC_TYPE = re.compile(r"\b(Constitution|Ordinance|Order|Regulations?|Rules|Code|Act)\b", re.I)
_REPEALED = re.compile(r"\(\s*Repeal(?:ed)?\b[^)]*\)?", re.I)      # "(Repealed by Act XVI of 2020)", "(Repeal by …"
_SHORT_TITLE = re.compile(
    r"\b(?:This|The)\s+(?:Act|Ordinance|Order|Regulations?)\s+may\s+be\s+called\s+(?:as\s+)?(?:the\s+)?"
    r"(.{5,220}?(?:1[89]\d\d|20\d\d))\s*\)?\s*[.;,]", re.I)
_SMALL = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with"}


def nice_title(title: str) -> str:
    """Tidy a listing title: no trailing full stop; ALL CAPS in title case."""
    t = " ".join((title or "").split()).rstrip(" .")
    if t.isupper():
        words = t.lower().split(" ")
        t = " ".join(w if (i and w in _SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))
        t = re.sub(r"\(([a-z])", lambda m: "(" + m.group(1).upper(), t)
    return t


def short_title(text: str) -> str | None:
    """The law's own short title ("This Act may be called the Stamp Act,
    1899."), from its first pages. None when it carries amendment marks (a
    footnote number, "*", brackets): the listing title is cleaner then."""
    m = _SHORT_TITLE.search(" ".join((text or "")[:12000].replace("\xad ", "-").replace("\xad", "-").split()))
    if not m:
        return None
    t = re.sub(r"(?<=[A-Za-z])- (?=[A-Za-z])", "-", " ".join(m.group(1).split())).strip(" ,.\"'“”")   # "Anti- Dumping"
    year = _YEAR.findall(t)[-1]
    if re.search(r"[*\[\]]", t) or re.sub(re.escape(year) + r"\W*$", "", t).strip() != t.rsplit(year, 1)[0].strip() \
            or re.search(r"\d", t.rsplit(year, 1)[0]):
        return None
    return t if 8 <= len(t) <= 200 else None



_AMENDMENT = re.compile(
    r"(?<![A-Za-z])(?:Subs(?:tituted)?\.?|Ins(?:erted)?\.?|Added|Omitted|Amended|Renumbered|Rep(?:ealed)?\.?)\s+by\s+"
    r"(?:the\s+)?([A-Z][^.;]{3,140}?(?:Act|Ordinance|Order|P\.?O\.?|Regulation)[^.;]{0,40}?"
    r"(?:\d{4}|[IVXLC]+\s+of\s+\d{4}))", re.I)


def clean_title(title: str) -> tuple[str, bool]:
    """(title without "(Repealed by …)", whether it says repealed)."""
    t = " ".join((title or "").split())
    repealed = bool(_REPEALED.search(t))
    return _REPEALED.sub("", t).strip(" ,"), repealed


def year_of(title: str, text: str = "") -> int | None:
    years = [int(y) for y in _YEAR.findall(title or "")]
    if years:
        return years[-1]
    m = re.search(r"\b(?:Act|Ordinance|Order|Regulation)\s+No\.?\s*[IVXLC\d]+\s+of\s+(1[89]\d\d|20\d\d)",
                  (text or "")[:4000], re.I)
    return int(m.group(1)) if m else None


def document_type(title: str) -> str | None:
    found = _DOC_TYPE.findall(title or "")
    return found[-1].capitalize() if found else None


def amendments(text: str, limit: int = 30) -> list[str]:
    """Amending laws named in the text's footnotes ("Subs. by the X Act, 2016")."""
    out: dict[str, None] = {}
    for m in _AMENDMENT.finditer(text or ""):
        out[" ".join(m.group(1).split()).rstrip(" ,(")] = None
        if len(out) >= limit:
            break
    return list(out)


# --------------------------------------------------------------------------- held

@lru_cache(maxsize=1)
def _core() -> tuple[frozenset[str], tuple[str, ...]]:
    titles, texts = set(), []
    for p in sorted((Path(settings.KB_DIR) / "records").glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                titles.add(normalise_title(r.get("title") or ""))
                texts.append(r.get("text") or "")
    return frozenset(titles - {""}), tuple(texts)


def core_law(title: str) -> bool:
    return normalise_title(title) in _core()[0]


@lru_cache(maxsize=1)
def vocab():
    return build_vocab(_core()[1])


def reset_caches() -> None:
    _core.cache_clear()
    vocab.cache_clear()


# --------------------------------------------------------------------------- records

@dataclass
class Item:
    source: str
    title: str
    url: str                       # the document page (or the PDF when the listing links straight to it)
    pdf_url: str | None = None
    meta: dict | None = None       # listing metadata (Pakistan Code category map): act_number, status, category


def statute_records(item: Item, text: str, info: dict, fetched_at: str, original: Path) -> list[dict]:
    """Section records for a scraped statute; raises Quarantine with the
    reason, or Held when it turns out to be a core law. The title is the
    law's own short title when its text gives one (a listing title can name
    another document: KP's "Amendment in Section 417 …" is the Prosecution
    Service (Amendment) Act, 2025), else the tidied listing title."""
    listing, repealed = clean_title(item.title)
    title = short_title(text) or nice_title(listing)
    if not title:
        raise Quarantine("missing title")
    if core_law(title):
        raise Held("a core law in the knowledge base")
    problem = text_problem(text, info, STATUTE_MIN_CHARS)
    if problem:
        raise Quarantine(problem)
    # The title's own year first: the listing's year can be the year of repeal.
    year = year_of(title) or (item.meta or {}).get("year") or year_of("", text)
    if not year:
        raise Quarantine("missing year")
    res = split_pdf(text, vocab())
    if res.found == 0 or res.detection < MIN_DETECTION:
        raise Quarantine(f"no recognisable sections (found {res.found} of {res.expected})")
    src = SOURCES[item.source]
    m = item.meta or {}
    status = "repealed" if repealed or m.get("status") == "repealed" else "under_review"
    slug = slugify(title) if not (Path(settings.KB_DIR) / "records" / f"{slugify(title)}.jsonl").exists() \
        else f"{slugify(title)}-{source_slug(item.source)}"
    meta = {
        "title": title, "year": int(year), "category": m.get("category"), "act_number": m.get("act_number"),
        "status": status, "source": item.source, "source_tier": src["tier"],
        "source_url": item.url, "original_file": rel(original), "scraped_at": fetched_at,
        "jurisdiction": src["jurisdiction"], "audience": "general", "slug": slug,
        "category_source": "Pakistan Code listing" if m.get("category") else None,
        "document_type": document_type(title), "amendments": amendments(text),
        "provenance_note": (f"Downloaded from the {item.source} website ({item.url}) on {fetched_at[:10]}; "
                            f"staged, not yet reviewed. {res.found} of {res.expected} sections found."),
    }
    secs, _labels = split_schedule_items(res.sections)
    recs = make_records(meta, secs)
    bad = [e for r in recs for e in validate_record(r)]
    if bad:
        raise Quarantine(f"record check failed: {bad[0]}")
    return recs


def judgment_record(item: Item, text: str, info: dict, fetched_at: str, original: Path, file_sha: str) -> dict:
    """A judgment record (spec § b2) for a scraped court judgment; raises Quarantine."""
    src = SOURCES[item.source]
    rec = jd.make_record(Path(rel(original)), text, info, source=item.source, file_sha=file_sha)
    reason = rec["quality"]["exclude"]
    if reason:
        raise Quarantine(reason)
    problem = text_problem(text, info, jd.NEAR_EMPTY_CHARS)
    if problem:
        raise Quarantine(problem)
    listing_title = " ".join((item.title or "").split())
    if not (rec["case_name"] or listing_title):
        raise Quarantine("missing title")
    year = rec["year"] or year_of(listing_title)
    if not year:
        raise Quarantine("missing year")
    # The court's own listing title ("Judgement on Khulla (Shariat Petition No.16-I of 2022 …)") when
    # the parties couldn't be read cleanly ("PETITIONER v. 1").
    name = rec["case_name"]
    if jd.name_is_weak(name) and listing_title:
        name = re.sub(r"^Judge?ments?\s+on\s+(?:the\s+)?", "", listing_title, flags=re.I).strip() or listing_title
    from requests.utils import requote_uri
    link = requote_uri(item.pdf_url or item.url)          # "Shariat Petition 16-I.pdf" -> "%20"
    rec.update({
        "doc_id": f"judgment/{source_slug(item.source)}/{sha256(item.url.encode())[:16]}",
        "court": src.get("court") or rec["court"], "year": int(year),
        "case_name": name,
        "source_tier": src["tier"], "source_url": link, "original_file": rel(original),
        "provenance_note": (f"Downloaded from the {item.source} website ({link}) on "
                            f"{fetched_at[:10]}; staged, not yet reviewed."),
        "listing_title": listing_title, "fetched_at": fetched_at, "scraped": True,
    })
    bad = jd.validate(rec)
    if bad:
        raise Quarantine(f"record check failed: {bad[0]}")
    return rec


def write_statute(recs: list[dict]) -> Path:
    d = scraped_dir() / "records" / "statutes"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{recs[0]['doc_id'].split('/')[1]}.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
    return path


def write_judgment(rec: dict) -> Path:
    d = scraped_dir() / "records" / "judgments"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{source_slug(rec['source'])}.jsonl"
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["doc_id"]] = r
    rows[rec["doc_id"]] = rec
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows.values()) + "\n", encoding="utf-8")
    return path


def text_hash(text: str) -> str:
    return content_hash(text)
