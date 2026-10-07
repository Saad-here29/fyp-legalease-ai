"""Scraped laws in search (kb-v2 C3, settings.SCRAPED_V2).

Index: faiss_scraped.* (statute section chunks from
KB_DIR/scraped/records/statutes/), built by build() with the same resumable
pattern as faiss_v2 (vector cache by chunk text, checkpoints, a time budget);
scraped court judgments go to faiss_scraped_judgments.* (searched by
app/kb/judgment_search.py). Neither build ever writes faiss_v2,
faiss_judgments or the old index.

Search (merged_search): the usual search (faiss_v2 + old index with KB_V2
on, the old index alone with it off) plus faiss_scraped, merged by score.
An Act in faiss_scraped that the old index also holds has its old-index
passages left out, as the 35 core laws' are (manifest
"excluded_v1_sources"). Reloaded when the index files change; missing or
half-written files mean no scraped results, nothing else changes.
"""

from __future__ import annotations

import json
import threading
from collections import Counter
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.scraping.parse import normalise_title


def scraped_dir() -> Path:
    return Path(settings.KB_DIR) / "scraped"


def statute_records_dir() -> Path:
    return scraped_dir() / "records" / "statutes"


def judgment_records_dir() -> Path:
    return scraped_dir() / "records" / "judgments"


def index_paths() -> tuple[Path, Path]:
    return Path(settings.KB_SCRAPED_INDEX_PATH), Path(settings.KB_SCRAPED_METADATA_PATH)


def judgment_index_paths() -> tuple[Path, Path]:
    return Path(settings.KB_SCRAPED_JUDGMENTS_INDEX_PATH), Path(settings.KB_SCRAPED_JUDGMENTS_METADATA_PATH)


def _protected() -> set[Path]:
    """Indexes a scraped build must never write."""
    return {Path(p).resolve() for p in (
        settings.FAISS_INDEX_PATH, settings.FAISS_METADATA_PATH, settings.KB_V2_INDEX_PATH,
        settings.KB_V2_METADATA_PATH, settings.KB_V2_ALL_INDEX_PATH, settings.KB_V2_ALL_METADATA_PATH,
        settings.KB_JUDGMENTS_INDEX_PATH, settings.KB_JUDGMENTS_METADATA_PATH,
        settings.JUDGMENTS_INDEX_PATH)}


def _sig(*files: Path) -> tuple | None:
    out = []
    for f in files:
        try:
            st = f.stat()
        except OSError:
            return None
        out.append((str(f.resolve()), st.st_mtime_ns, st.st_size))
    return tuple(out)


# --------------------------------------------------------------------------- statute index

class _Index:
    def __init__(self) -> None:
        self.index = None
        self.chunks: list[dict] = []
        self.texts: dict[str, str] = {}
        self.excluded: frozenset[str] = frozenset()
        self.sig: tuple | None = None
        self.failed: tuple | None = None
        self.lock = threading.Lock()

    def _clear(self) -> None:
        self.index, self.chunks, self.texts, self.excluded, self.sig = None, [], {}, frozenset(), None

    def ready(self) -> bool:
        if not settings.SCRAPED_V2:
            return False
        sig = _sig(*index_paths())
        if sig is None:
            self._clear()
            return False
        if sig == self.sig and self.index is not None:
            return True
        if sig == self.failed:
            return False
        with self.lock:
            if sig == self.sig and self.index is not None:
                return True
            try:
                import faiss
                idx, meta = index_paths()
                data = json.loads(meta.read_text(encoding="utf-8"))
                index = faiss.read_index(str(idx))
                if index.ntotal != len(data["chunks"]):
                    raise ValueError(f"index has {index.ntotal} vectors but metadata {len(data['chunks'])} chunks")
            except Exception as e:  # noqa: BLE001 — a half-written build must never break search
                logger.warning(f"Scraped index not usable yet ({type(e).__name__}: {str(e)[:160]})")
                self._clear()
                self.failed = sig
                return False
            self.index, self.chunks, self.texts = index, data["chunks"], data.get("texts", {})
            self.excluded = frozenset(data["manifest"].get("excluded_v1_sources", []))
            self.sig, self.failed = sig, None
            logger.info(f"Scraped index ready: {index.ntotal} chunks, {len({c['doc_id'] for c in self.chunks})} "
                        f"sections; {len(self.excluded)} old-index sources replaced")
        return True


_INDEX = _Index()


def status() -> dict:
    """For /health."""
    if not settings.SCRAPED_V2:
        return {"scraped_chunks": None, "scraped_judgment_chunks": None}
    from app.kb import judgment_search
    j = judgment_search.scraped_status()
    return {"scraped_chunks": _INDEX.index.ntotal if _INDEX.ready() else 0, "scraped_judgment_chunks": j}


def search_statutes(query: str, top_k: int, filters: dict | None = None, *, qvec=None) -> list[dict]:
    """Best chunk per section from faiss_scraped, in the faiss_v2 hit format
    (kb "scraped")."""
    if not _INDEX.ready() or not _INDEX.index.ntotal:
        return []
    from app.ai import embeddings
    from app.kb import index_v2
    if qvec is None:
        qvec = embeddings.embed([query])
    scores, ids = _INDEX.index.search(qvec, min(_INDEX.index.ntotal, top_k * 30))
    best: dict[str, tuple[float, int]] = {}
    for s, i in zip(scores[0], ids[0], strict=True):
        if 0 <= i < len(_INDEX.chunks):
            d = _INDEX.chunks[i]["doc_id"]
            if d not in best:
                best[d] = (float(s), int(i))
    hits = []
    for d, (s, i) in best.items():
        c = _INDEX.chunks[i]
        hit = {
            "source": c["title"], "source_type": c["source_type"], "chunk_id": i,
            "text": index_v2.passage(c, _INDEX.texts.get(d, "")),
            "section": c["section"], "heading": c["heading"], "source_tier": c["source_tier"],
            "source_url": c["source_url"], "category": c["category"], "year": c["year"],
            "jurisdiction": c["jurisdiction"], "audience": c.get("audience") or "general",
            "doc_id": d, "kb": "scraped", "relevance": s,
        }
        if embeddings.passes_filters(hit, filters):
            hits.append(hit)
    hits.sort(key=lambda h: h["relevance"], reverse=True)
    return hits[:top_k]


def merged_search(query: str, top_k: int, filters: dict | None = None) -> list[dict]:
    """The usual search plus faiss_scraped; old-index passages of a scraped
    Act are left out."""
    from app.ai import embeddings
    from app.kb import index_v2
    base = index_v2.search(query, top_k * 2, filters) if settings.KB_V2 else \
        embeddings._search_v1(query, top_k * 4, filters)
    if not _INDEX.ready():
        return base[:top_k]
    base = [h for h in base if h.get("kb") == "v2" or h.get("source") not in _INDEX.excluded]
    hits = base + search_statutes(query, top_k, filters)
    hits.sort(key=lambda h: h["relevance"], reverse=True)
    return hits[:top_k]


# --------------------------------------------------------------------------- build

def excluded_v1_sources(records: list[dict]) -> list[str]:
    """Old-index sources that are the same Act as a scraped law: same title
    (normalised), or the Pakistan Code category map matched them to the
    listing whose page we scraped."""
    from app.ai import embeddings
    titles = {normalise_title(r["title"]) for r in records}
    urls = {r.get("source_url") for r in records}
    out: set[str] = set()
    meta = Path(settings.FAISS_METADATA_PATH)
    if meta.exists():
        for m in json.loads(meta.read_text(encoding="utf-8")):
            src = embeddings.record_source(m)
            if src and normalise_title(src) in titles:
                out.add(src)
    cmap = Path(settings.KB_DIR) / "category_map.json"
    if cmap.exists():
        for c in json.loads(cmap.read_text(encoding="utf-8")).get("categories", []):
            for law in c.get("laws", []):
                if law.get("url") in urls and law.get("match") and law["match"].get("how") != "possible":
                    out.update(x["title"] for x in law["match"].get("corpus", []))
    return sorted(out)


def build(*, tokenizer, embed, time_budget: float | None = None) -> dict:
    """Build faiss_scraped (statutes), then faiss_scraped_judgments, each
    resumable. Returns both manifests and whether both are complete."""
    import time

    from app.kb import index_v2
    from app.kb import judgments as jd
    t0 = time.perf_counter()
    idx, meta = index_paths()
    jidx, jmeta = judgment_index_paths()
    for p in (idx, meta, jidx, jmeta):
        if p.resolve() in _protected():
            raise ValueError(f"refusing to write {p}: it is another index")
    sdir, jdir = statute_records_dir(), judgment_records_dir()
    sdir.mkdir(parents=True, exist_ok=True)
    jdir.mkdir(parents=True, exist_ok=True)
    recs = index_v2.load_records(sdir)
    kb = Path(settings.KB_DIR)
    statutes = index_v2.build(sdir, idx, meta, tokenizer=tokenizer, embed=embed,
                              excluded_v1_sources=excluded_v1_sources(recs),
                              cache_dir=kb / "vector_cache_scraped", time_budget=time_budget)
    left = None if time_budget is None else max(0.0, time_budget - (time.perf_counter() - t0))
    if statutes["complete"] and (left is None or left > 0):
        judgments = jd.build_index(jdir, jidx, jmeta, tokenizer=tokenizer, embed=embed,
                                   cache_dir=kb / "vector_cache_scraped_judgments", time_budget=left)
    else:
        judgments = {"complete": False, "still_missing": None, "note": "waits for the statute index"}
    return {"statutes": statutes, "judgments": judgments,
            "complete": bool(statutes["complete"] and judgments["complete"])}


def index_log_entry(result: dict) -> dict:
    """The update-log line for an index build: what is searchable, per source."""
    from app.kb import index_v2
    from app.scraping.stage import utcnow
    recs = index_v2.load_records(statute_records_dir())
    laws = Counter()
    for r in {r["doc_id"].rsplit("/", 1)[0]: r for r in recs}.values():
        laws[r["source"]] += 1
    judgments = Counter()
    for p in sorted(judgment_records_dir().glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                judgments[json.loads(line).get("source")] += 1
    s, j = result["statutes"], result["judgments"]
    return {"run_at": utcnow(), "kind": "index", "complete": result["complete"],
            "statute_chunks": s.get("chunks"), "judgment_chunks": j.get("chunks"),
            "excluded_v1_sources": len(s.get("excluded_v1_sources") or []),
            "per_source": {**laws, **judgments} if result["complete"] else {}}


# --------------------------------------------------------------------------- update log views

def updates(limit: int = 60) -> dict:
    """GET /kb/updates: the log (newest first), each scrape line with the
    number of that source's documents searchable after the latest complete
    index build that followed it (None: not embedded yet)."""
    from app.scraping.stage import read_log
    log = read_log()
    index_runs = [e for e in log if e.get("kind") == "index" and e.get("complete")]
    out = []
    for e in reversed(log):
        if e.get("kind") == "scrape":
            later = [i for i in index_runs if i["run_at"] >= e.get("finished_at", e["run_at"])]
            e = {**e, "indexed": later[0]["per_source"].get(e["source"], 0) if later else None}
        out.append(e)
        if len(out) >= limit:
            break
    q = Counter()
    for p in (scraped_dir() / "quarantine").glob("*/*.json"):
        try:
            q[json.loads(p.read_text(encoding="utf-8"))["reason"].split(" (")[0]] += 1
        except (OSError, ValueError, KeyError):
            continue
    return {"entries": out, "quarantine": dict(q.most_common()), "searchable": settings.SCRAPED_V2}


def research_updates() -> dict:
    """The Research page's "Sources checked" line (ScrapeUpdates) from the
    update log instead of the database."""
    from app.scraping.stage import read_log
    scrapes = [e for e in read_log() if e.get("kind") == "scrape"]
    if not scrapes:
        return {"available": False}
    latest = list({e["source"]: e for e in scrapes}.values())      # each source's latest check
    changed = [e for e in scrapes if e.get("new") or e.get("changed")]
    return {
        "available": True,
        "last_checked": max(e.get("finished_at") or e["run_at"] for e in latest),
        "last_updated": max(e.get("finished_at") or e["run_at"] for e in changed) if changed else None,
        "pages_checked": sum(e.get("fetched", 0) for e in latest),
        "new": sum(e.get("new", 0) for e in latest), "changed": sum(e.get("changed", 0) for e in latest),
        "errors": sum(e.get("errors", 0) for e in latest),
        "sources": [{"name": e["source"], "content_type": e.get("content_type"), "checked": e.get("fetched", 0),
                     "new": e.get("new", 0), "changed": e.get("changed", 0), "errors": e.get("errors", 0)}
                    for e in latest],
        "searchable": True,
    }


def reset() -> None:
    global _INDEX
    _INDEX = _Index()
