"""Statute section records (docs/knowledge_base_spec.md § a) and their validation."""

from __future__ import annotations

import re

from app.kb.sectioner import Section, windows
from app.scraping.parse import content_hash

CORPUS_SOURCE = "LegalEase corpus (Pakistan Code-derived; original download provenance not recorded)"
JURISDICTIONS = {"Pakistan", "Punjab", "Sindh", "KP", "Balochistan", "ICT"}
STATUSES = {"current", "under_review", "repealed"}
REQUIRED = ("doc_id", "title", "section", "heading", "text", "source_type", "jurisdiction", "category", "year",
            "act_number", "source", "source_tier", "source_url", "original_file", "scraped_at", "content_hash",
            "status")
OPTIONAL = ("provenance_note", "sectioned")


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower().replace("'", "")).strip("-")


def _source_slug(source: str) -> str:
    return {"Pakistan Code": "pakistan-code"}.get(source, "legalease-corpus" if source.startswith("LegalEase")
                                                   else slugify(source))


def section_id(section: str) -> str:
    return "s" + section if section[0].isdigit() else slugify(section)


def make_records(meta: dict, sections: list[Section] | None, raw_text: str | None = None) -> list[dict]:
    """One record per section; or, for an unsectioned law (sections None),
    one per ~1200-character window with section and heading null."""
    base = f"{_source_slug(meta['source'])}/{slugify(meta['title'])}"
    out, seen = [], {}
    if sections is None:
        parts = [(None, None, w, f"w{i + 1}") for i, w in enumerate(windows(raw_text or ""))]
    else:
        parts = []
        for s in sections:
            sid = section_id(s.section)
            seen[sid] = seen.get(sid, 0) + 1
            if seen[sid] > 1:                     # the same number printed twice: keep both, distinct ids
                sid = f"{sid}-{seen[sid]}"
            parts.append((s.section, s.heading, s.text, sid))
    for section, heading, text, sid in parts:
        rec = {
            "doc_id": f"{base}/{sid}",
            "title": meta["title"],
            "section": section,
            "heading": heading,
            "text": text,
            "source_type": "statute",
            "jurisdiction": meta["jurisdiction"],
            "category": meta["category"],
            "year": meta["year"],
            "act_number": meta["act_number"],
            "source": meta["source"],
            "source_tier": meta["source_tier"],
            "source_url": meta["source_url"],
            "original_file": meta["original_file"],
            "scraped_at": meta["scraped_at"],
            "content_hash": content_hash(text),
            "status": meta["status"],
            "sectioned": sections is not None,
        }
        if meta.get("provenance_note"):
            rec["provenance_note"] = meta["provenance_note"]
        out.append(rec)
    return out


def validate(rec: dict) -> list[str]:
    """Problems with one record against the spec; [] when valid."""
    errs = [f"missing {k}" for k in REQUIRED if k not in rec]
    extra = set(rec) - set(REQUIRED) - set(OPTIONAL)
    if extra:
        errs.append(f"unknown fields {sorted(extra)}")
    if errs:
        return errs

    def typ(k, *types):
        if not isinstance(rec[k], types):
            errs.append(f"{k} has type {type(rec[k]).__name__}")

    for k in ("doc_id", "title", "text", "source"):
        typ(k, str)
        if isinstance(rec[k], str) and not rec[k].strip():
            errs.append(f"{k} is empty")
    for k in ("section", "heading", "category", "act_number", "source_url", "original_file", "scraped_at",
              "provenance_note"):
        if k in rec:
            typ(k, str, type(None))
    typ("year", int)
    if rec["source_type"] != "statute":
        errs.append("source_type must be 'statute'")
    if rec["jurisdiction"] not in JURISDICTIONS:
        errs.append(f"jurisdiction {rec['jurisdiction']!r}")
    if rec["status"] not in STATUSES:
        errs.append(f"status {rec['status']!r}")
    if rec["source_tier"] not in (1, 2, 3):
        errs.append(f"source_tier {rec['source_tier']!r}")
    if rec["source_tier"] == 3:
        errs.append("tier 3 sources are never ingested")
    if isinstance(rec["text"], str) and rec["content_hash"] != content_hash(rec["text"]):
        errs.append("content_hash does not match text")
    if rec.get("sectioned") is False and rec["section"] is not None:
        errs.append("unsectioned record must have section null")
    if rec.get("sectioned", True) and not rec["section"]:
        errs.append("sectioned record needs a section")
    if isinstance(rec["year"], int) and not 1800 <= rec["year"] <= 2100:
        errs.append(f"year {rec['year']}")
    return errs
