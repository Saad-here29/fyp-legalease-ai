"""Judgment records for the Knowledge Base (kb-v2 C2), read-only.

Reads backend/storage/kb/judgments/records/*.jsonl (written by
scripts/kb/inventory_judgments.py), never the database. Each record line is
parsed once into a light summary plus its file offset; a judgment's
paragraphs are read back from that offset only when it is opened. Reloaded
when a records file changes.

Listed: usable records only (not near-empty, OCR-less, duplicate or a
law-report copy), with the same judgment from two datasets shown once (same
case number and year; the copy in the search index wins, then the one with
more metadata found, as in the pilot selection).

With SCRAPED_V2 on (kb-v2 C3), judgments scraped from court websites
(KB_DIR/scraped/records/judgments/*.jsonl) are listed too, with their source
URL and fetch date.

Never returned: the original file's path and the file / content hashes.
"""

from __future__ import annotations

import json
import threading
from collections import Counter
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.kb import judgments as jd

PUBLIC = ("doc_id", "display_name", "case_name", "court", "year", "judges", "case_number", "citation",
          "topics", "source", "source_type", "status", "provenance_note", "paragraph_count",
          "source_url", "fetched_at", "scraped")

_LOCK = threading.Lock()
_STATE: dict = {"sig": None, "usable": {}, "excluded": Counter(), "files": 0}
_LISTED: dict = {"key": None, "items": []}


def records_dir() -> Path:
    return Path(settings.KB_DIR) / "judgments" / "records"


def record_files() -> list[Path]:
    files = sorted(records_dir().glob("*.jsonl"))
    if settings.SCRAPED_V2:
        files += sorted((Path(settings.KB_DIR) / "scraped" / "records" / "judgments").glob("*.jsonl"))
    return files


def _signature() -> tuple:
    out = []
    for p in record_files():
        try:
            st = p.stat()
        except OSError:
            continue
        out.append((str(p), st.st_mtime_ns, st.st_size))
    return tuple(out)


def _summary(rec: dict, path: Path, offset: int) -> dict:
    return {
        "doc_id": rec["doc_id"], "display_name": jd.display_name(rec), "case_name": rec.get("case_name"),
        "court": rec.get("court"), "year": rec.get("year"), "judges": rec.get("judges") or [],
        "case_number": rec.get("case_number"), "citation": rec.get("citation"), "topics": rec.get("topics") or [],
        "source": rec.get("source"), "source_type": rec.get("source_type", "case_law"),
        "status": rec.get("status", "staged"), "provenance_note": rec.get("provenance_note", jd.PROVENANCE),
        "paragraph_count": len(rec.get("paragraphs") or []),
        "source_url": rec.get("source_url"), "fetched_at": rec.get("fetched_at"), "scraped": bool(rec.get("scraped")),
        "_path": path, "_offset": offset, "_dkey": jd.dedupe_key(rec),
        "_rank": (sum(bool(rec.get(f)) for f in ("case_name", "court", "judges", "case_number")),
                  (rec.get("quality") or {}).get("chars", 0)),
    }


def load() -> dict:
    """{doc_id: summary} of the usable records (reloaded when a file changes)."""
    sig = _signature()
    if sig == _STATE["sig"]:
        return _STATE["usable"]
    with _LOCK:
        if sig == _STATE["sig"]:
            return _STATE["usable"]
        usable, excluded = {}, Counter()
        for path_s, _m, _s in sig:
            path = Path(path_s)
            try:
                with path.open("rb") as f:
                    offset = 0
                    for line in f:
                        if line.strip():
                            try:
                                rec = json.loads(line)
                            except ValueError:
                                excluded["unreadable line"] += 1
                            else:
                                reason = (rec.get("quality") or {}).get("exclude")
                                if reason:
                                    excluded[reason] += 1
                                elif rec.get("doc_id"):
                                    usable[rec["doc_id"]] = _summary(rec, path, offset)
                        offset += len(line)
            except OSError as e:
                logger.warning(f"Judgment records: cannot read {path}: {e}")
        _STATE.update(sig=sig, usable=usable, excluded=excluded, files=len(sig))
        _LISTED["key"] = None
        logger.info(f"Judgment records: {len(usable)} usable, {sum(excluded.values())} excluded, {len(sig)} files")
    return usable


def listed(indexed: set[str] | frozenset[str] = frozenset()) -> list[dict]:
    """The usable judgments, one per case (cross-dataset copies merged)."""
    usable = load()
    key = (_STATE["sig"], frozenset(indexed))
    if _LISTED["key"] == key:
        return _LISTED["items"]
    best: dict = {}
    for s in usable.values():
        k = s["_dkey"] or s["doc_id"]
        rank = (s["doc_id"] in indexed, s["_rank"])
        if k not in best or rank > best[k][0]:
            best[k] = (rank, s)
    items = sorted((s for _r, s in best.values()),
                   key=lambda s: (-(s["year"] or 0), s["display_name"].lower()))
    _LISTED.update(key=key, items=items)
    return items


def public(s: dict, indexed: set[str] | frozenset[str] = frozenset()) -> dict:
    return {**{k: s.get(k) for k in PUBLIC}, "indexed": s["doc_id"] in indexed}


def summary(doc_id: str) -> dict | None:
    return load().get(doc_id)


def record(doc_id: str) -> dict | None:
    """The full record (read from its file offset), or None."""
    s = summary(doc_id)
    if s is None:
        return None
    try:
        with s["_path"].open("rb") as f:
            f.seek(s["_offset"])
            return json.loads(f.readline())
    except (OSError, ValueError) as e:
        logger.warning(f"Judgment record {doc_id}: {e}")
        return None


def paragraph(doc_id: str, n: int) -> str | None:
    rec = record(doc_id)
    if rec is None:
        return None
    return next((p["text"] for p in rec.get("paragraphs") or [] if p.get("n") == n), None)


def detail(doc_id: str, indexed: set[str] | frozenset[str] = frozenset()) -> dict | None:
    s, rec = summary(doc_id), record(doc_id)
    if s is None or rec is None:
        return None
    return {**public(s, indexed),
            "paragraphs": [{"n": p.get("n"), "text": p.get("text", "")} for p in rec.get("paragraphs") or []]}


def stats(items: list[dict]) -> dict:
    years = Counter(s["year"] for s in items if s["year"])
    return {
        "courts": dict(Counter(s["court"] or "Unknown" for s in items).most_common()),
        "years": {"min": min(years) if years else None, "max": max(years) if years else None,
                  "by_year": dict(sorted(years.items()))},
        "topics": dict(Counter(t for s in items for t in s["topics"]).most_common()),
    }


def search_list(*, q: str | None = None, court: str | None = None, year: int | None = None,
                topic: str | None = None, indexed_only: bool = False,
                indexed: set[str] | frozenset[str] = frozenset()) -> tuple[list[dict], list[dict]]:
    """(all listed judgments, the ones matching the filters)."""
    items = listed(indexed)
    out = items
    if q:
        words = q.lower().split()
        out = [s for s in out if all(w in f"{s['display_name']} {s['case_name'] or ''} {s['case_number'] or ''} "
                                         f"{' '.join(s['judges'])}".lower() for w in words)]
    if court:
        out = [s for s in out if (s["court"] or "").lower() == court.lower()]
    if year is not None:
        out = [s for s in out if s["year"] == year]
    if topic:
        out = [s for s in out if topic.lower() in s["topics"]]
    if indexed_only:
        out = [s for s in out if s["doc_id"] in indexed]
    return items, out


def excluded_counts() -> dict:
    load()
    return dict(_STATE["excluded"])


def reset() -> None:
    _STATE.update(sig=None, usable={}, excluded=Counter(), files=0)
    _LISTED["key"] = None
