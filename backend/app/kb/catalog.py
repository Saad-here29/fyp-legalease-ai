"""Read-only view of the knowledge base for the /kb API and Research filters.

Reads the section records (storage/kb/records/*.jsonl), the faiss_v2
manifest and category_map.json; never writes. Everything is cached in
memory and reloaded when a file's modification time changes.

A law is addressed by its records file name ("guardians-and-wards-act-1890"),
a record by its doc_id ("legalease-corpus/guardians-and-wards-act-1890/s17").
Originals are served only from storage/kb/raw/, looked up by law id; a path
from the client is never used.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from app.core.config import settings

_LOCK = threading.Lock()
_CACHE: dict = {"key": None}
SOURCE_LABELS = {
    "user-supplied PDF": "user-supplied PDF - source URL to be confirmed",
}
CORPUS_LABEL = "LegalEase corpus (Pakistan Code-derived)"


def kb_dir() -> Path:
    return Path(settings.KB_DIR)


def source_label(source: str | None) -> str:
    if source and source.startswith("LegalEase corpus"):
        return CORPUS_LABEL
    return SOURCE_LABELS.get(source or "", source or "")


def _files() -> list[Path]:
    d = kb_dir()
    return sorted((d / "records").glob("*.jsonl")) + [d / "category_map.json", Path(settings.KB_V2_METADATA_PATH)]


def _stamp() -> tuple:
    return tuple((str(p), p.stat().st_mtime_ns) for p in _files() if p.exists())


def _load() -> dict:
    laws: dict[str, dict] = {}
    records: dict[str, dict] = {}
    for path in sorted((kb_dir() / "records").glob("*.jsonl")):
        recs = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        if not recs:
            continue
        first = recs[0]
        law_id = path.stem
        laws[law_id] = {
            "doc_id": law_id,
            "title": first["title"],
            "category": first.get("category"),
            "jurisdiction": first.get("jurisdiction"),
            "year": first.get("year"),
            "act_number": first.get("act_number"),
            "source": first.get("source"),
            "source_label": source_label(first.get("source")),
            "source_tier": first.get("source_tier"),
            "source_url": first.get("source_url"),
            "status": first.get("status"),
            "audience": first.get("audience") or "general",
            "source_version": first.get("source_version"),
            "provenance_note": first.get("provenance_note"),
            "sectioned": first.get("sectioned", True),
            "sections": len(recs),
            "original_file": first.get("original_file"),
            "record_ids": [r["doc_id"] for r in recs],
        }
        for r in recs:
            records[r["doc_id"]] = {**r, "_law": law_id}
    cmap_path = kb_dir() / "category_map.json"
    cmap = json.loads(cmap_path.read_text(encoding="utf-8")) if cmap_path.exists() else {"categories": []}
    chunks = None
    meta_path = Path(settings.KB_V2_METADATA_PATH)
    if meta_path.exists():
        try:
            with meta_path.open(encoding="utf-8") as f:
                head = f.read(4096)
            m = re.search(r'"chunks":\s*(\d+)', head)            # the manifest comes first; avoid parsing 14 MB
            chunks = int(m.group(1)) if m else None
        except OSError:
            chunks = None
    return {"laws": laws, "records": records, "cmap": cmap, "chunks": chunks,
            "v1_meta": _v1_metadata(cmap, laws)}


def _v1_metadata(cmap: dict, laws: dict) -> dict[str, dict]:
    """Old-index source name -> {category, year, jurisdiction, source_tier}, for
    titles that matched a Pakistan Code category listing (exact or near)."""
    out: dict[str, dict] = {}
    for c in cmap.get("categories", []):
        for law in c.get("laws", []):
            m = law.get("match")
            if not m or m.get("how") == "possible":
                continue
            for corpus in m.get("corpus", []):
                out[corpus["title"]] = {"category": c["name"], "year": law.get("year"),
                                        "jurisdiction": "Pakistan", "source_tier": 1}
    return out


def data() -> dict:
    key = _stamp()
    if _CACHE["key"] != key:
        with _LOCK:
            if _CACHE["key"] != key:
                _CACHE.update(_load(), key=key)
    return _CACHE


def reset() -> None:
    _CACHE.clear()
    _CACHE["key"] = None


# --------------------------------------------------------------------------- API views

def coverage(cmap: dict) -> dict:
    cats = cmap.get("categories", [])
    listed = sum(c.get("listed_count", 0) for c in cats)
    held = sum(c.get("held", 0) for c in cats)
    badge = sum(c.get("badge_count") or 0 for c in cats)
    return {
        "listed": listed, "held": held, "site_badge_total": badge, "not_listed": badge - listed,
        "note": (f"We hold {held} of the {listed} Acts the Pakistan Code lists in its categories. "
                 f"The site's category counts add up to {badge}; the other {badge - listed} are counted "
                 "there but not listed, so they could not be checked."),
        "source": "docs/kb_coverage_2026-10-06.md",
    }


def stats() -> dict:
    d = data()
    laws = list(d["laws"].values())

    def count(key):
        out: dict[str, int] = {}
        for law in laws:
            k = law.get(key)
            k = "None" if k is None else str(k)
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))

    return {
        "laws": len(laws),
        "section_records": len(d["records"]),
        "chunks": d["chunks"],
        "by_category": count("category"),
        "by_source_tier": count("source_tier"),
        "jurisdictions": sorted({law["jurisdiction"] for law in laws if law.get("jurisdiction")}),
        "coverage": coverage(d["cmap"]),
        # Every Pakistan Code category with listed Acts: the Research filter's choices
        # (old-index passages take their category from these listings).
        "categories": sorted(c["name"] for c in d["cmap"].get("categories", []) if c.get("listed_count")),
        "kb_v2_search": settings.KB_V2,
    }


PUBLIC_LAW_FIELDS = ("doc_id", "title", "category", "jurisdiction", "year", "act_number", "source", "source_label",
                     "source_tier", "source_url", "status", "audience", "source_version", "provenance_note",
                     "sectioned", "sections")


def public_law(law: dict) -> dict:
    out = {k: law.get(k) for k in PUBLIC_LAW_FIELDS}
    out["has_original"] = original_path(law["doc_id"]) is not None
    return out


def documents(q: str | None = None, category: str | None = None, tier: int | None = None,
              jurisdiction: str | None = None, year: int | None = None, status: str | None = None) -> list[dict]:
    words = [w for w in re.findall(r"[a-z0-9]+", (q or "").lower()) if w]
    out = []
    for law in data()["laws"].values():
        title = law["title"].lower()
        if words and not all(w in title for w in words):
            continue
        if category and (law.get("category") or "").lower() != category.lower():
            continue
        if tier is not None and law.get("source_tier") != tier:
            continue
        if jurisdiction and (law.get("jurisdiction") or "").lower() != jurisdiction.lower():
            continue
        if year is not None and law.get("year") != year:
            continue
        if status and law.get("status") != status:
            continue
        out.append(public_law(law))
    return sorted(out, key=lambda x: x["title"].lower())


def law(doc_id: str) -> dict | None:
    return data()["laws"].get(doc_id)


def sections(doc_id: str) -> list[dict] | None:
    law_ = law(doc_id)
    if law_ is None:
        return None
    recs = data()["records"]
    out = []
    for rid in law_["record_ids"]:
        r = recs[rid]
        text = " ".join(r["text"].split())
        out.append({"id": rid, "section": r.get("section"), "heading": r.get("heading"),
                    "preview": text[:200] + ("…" if len(text) > 200 else "")})
    return out


def record(record_id: str) -> dict | None:
    r = data()["records"].get(record_id)
    return None if r is None else {k: v for k, v in r.items() if k != "_law"}


def law_records(doc_id: str) -> list[dict] | None:
    law_ = law(doc_id)
    if law_ is None:
        return None
    return [record(rid) for rid in law_["record_ids"]]


def original_path(doc_id: str) -> Path | None:
    """The saved original of a law, only if it is a file directly inside
    storage/kb/raw/. The name comes from the law's own record (never from the
    client), and anything that resolves outside raw/ is refused."""
    law_ = data()["laws"].get(doc_id)
    if not law_ or not law_.get("original_file"):
        return None
    raw = (kb_dir() / "raw").resolve()
    name = Path(str(law_["original_file"]).replace("\\", "/")).name
    if not name or name in (".", ".."):
        return None
    p = (raw / name).resolve()
    try:
        p.relative_to(raw)
    except ValueError:
        return None
    if p.parent != raw or not p.is_file() or p.suffix.lower() not in (".pdf", ".html", ".htm"):
        return None
    return p


# --------------------------------------------------------------------------- research metadata

def v1_metadata(source: str | None) -> dict | None:
    return data()["v1_meta"].get(source or "")


def filter_coverage(v1_sources: set[str], excluded: set[str], kb_on: bool) -> dict:
    """How many searchable documents carry the metadata the Research filters
    use (a category and a year). Old-index documents count when their title
    matched a Pakistan Code listing; with KB_V2 on, the v2 laws replace their
    old-index copies."""
    meta = data()["v1_meta"]
    v1 = {s for s in v1_sources if not (kb_on and s in excluded)}
    known = sum(1 for s in v1 if s in meta)
    total = len(v1)
    if kb_on:
        laws = data()["laws"].values()
        known += sum(1 for law in laws if law.get("category") and law.get("year"))
        total += len(laws)
    return {"known": known, "total": total}
