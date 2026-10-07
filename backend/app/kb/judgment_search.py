"""Search the judgments index (kb-v2 C2), behind settings.JUDGMENTS_V2.

The index is settings.JUDGMENTS_INDEX_PATH (built by
scripts/kb/build_index_judgments.py; its metadata is "<stem>_meta.json" next
to it unless JUDGMENTS_METADATA_PATH says otherwise). It is reloaded when
either file's modified time or size changes, so a finished build is picked up
without a restart. While a file is missing, unreadable or the pair doesn't
match (a build still writing), search returns nothing and the rest of the
app is unaffected.

search(): embed the query, keep the BEST paragraph per judgment, drop those
under JUDGMENTS_MIN_SCORE, return the top JUDGMENTS_TOP_K.

With SCRAPED_V2 also on (kb-v2 C3), judgments scraped from court websites
(faiss_scraped_judgments.*, app/kb/scraped.py) are searched too and merged
by score.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.kb import judgment_catalog as catalog
from app.kb import judgments as jd

PARAGRAPH_CHARS = 1200     # paragraph text returned with a hit (chat prompt): 3 cases add ~900 tokens


def paths() -> tuple[Path, Path]:
    idx = Path(settings.JUDGMENTS_INDEX_PATH)
    meta = Path(settings.JUDGMENTS_METADATA_PATH) if settings.JUDGMENTS_METADATA_PATH \
        else idx.with_name(idx.stem + "_meta.json")
    return idx, meta


def _sig(*files: Path) -> tuple | None:
    out = []
    for f in files:
        try:
            st = f.stat()
        except OSError:
            return None
        out.append((str(f.resolve()), st.st_mtime_ns, st.st_size))
    return tuple(out)


def scraped_paths() -> tuple[Path, Path]:
    return Path(settings.KB_SCRAPED_JUDGMENTS_INDEX_PATH), Path(settings.KB_SCRAPED_JUDGMENTS_METADATA_PATH)


class _Index:
    def __init__(self, paths_fn=None, *, scraped: bool = False) -> None:
        self.paths = paths_fn or paths
        self.scraped = scraped               # needs SCRAPED_V2 as well
        self.index = None
        self.chunks: list[dict] = []
        self.doc_ids: frozenset[str] = frozenset()
        self.sig: tuple | None = None
        self.failed: tuple | None = None
        self.lock = threading.Lock()

    def _clear(self) -> None:
        self.index, self.chunks, self.doc_ids, self.sig = None, [], frozenset(), None

    def ready(self) -> bool:
        """Loaded and current (reloads on a changed file). False when the flag
        is off, a file is missing, or the files can't be read as a pair."""
        if not settings.JUDGMENTS_V2 or (self.scraped and not settings.SCRAPED_V2):
            return False
        sig = _sig(*self.paths())
        if sig is None:
            if self.index is not None:
                logger.warning("Judgments index files gone; judgment search returns nothing")
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
                idx, meta = self.paths()
                data = json.loads(meta.read_text(encoding="utf-8"))
                index = faiss.read_index(str(idx))
                chunks = data["chunks"]
                if index.ntotal != len(chunks):
                    raise ValueError(f"index has {index.ntotal} vectors but metadata {len(chunks)} chunks")
            except Exception as e:  # noqa: BLE001 — a half-written build must never break the app
                logger.warning(f"Judgments index not usable yet ({type(e).__name__}: {str(e)[:160]}); "
                               "judgment search returns nothing until the files change")
                self._clear()
                self.failed = sig
                return False
            self.index, self.chunks, self.sig, self.failed = index, chunks, sig, None
            self.doc_ids = frozenset(c["doc_id"] for c in chunks)
            logger.info(f"Judgments index ready: {index.ntotal} chunks, {len(self.doc_ids)} judgments "
                        f"({self.paths()[0]})")
        return True


_INDEX = _Index()
_SCRAPED = _Index(scraped_paths, scraped=True)


def _ready() -> list[_Index]:
    return [ix for ix in (_INDEX, _SCRAPED) if ix.ready() and ix.index.ntotal]


def scraped_status() -> int | None:
    """Chunks in the scraped judgments index (None when a flag is off)."""
    if not (settings.JUDGMENTS_V2 and settings.SCRAPED_V2):
        return None
    return _SCRAPED.index.ntotal if _SCRAPED.ready() else 0


def status() -> dict:
    """For /health: chunk and judgment counts of the index being searched."""
    if not settings.JUDGMENTS_V2:
        return {"judgment_chunks": None, "judgments": None}
    if not _INDEX.ready():
        return {"judgment_chunks": 0, "judgments": 0}
    return {"judgment_chunks": _INDEX.index.ntotal, "judgments": len(_INDEX.doc_ids)}


def indexed_ids() -> frozenset[str]:
    return frozenset().union(*(ix.doc_ids for ix in (_INDEX, _SCRAPED) if ix.ready()))


def window_text(chunk: dict) -> str:
    """The chunk's text without the indexed prefix ("<name> (<court>, <year>) - para N:")."""
    text = chunk.get("chunk_text") or ""
    for marker in (f" - para {chunk.get('para')}:", " …:"):
        i = text.find(marker)
        if i >= 0:
            return text[i + len(marker):].strip()
    return text


_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_PRESENTATION = re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]")


def readable(text: str) -> bool:
    """kb-v2 C8: False for a paragraph that is mostly Arabic script (Quranic
    quotations, Urdu passages the English model reads badly) or holds many
    Arabic presentation-form characters (a PDF's broken text layer)."""
    letters = sum(ch.isalpha() for ch in text or "")
    if not letters:
        return False
    arabic = len(_ARABIC.findall(text))
    return arabic / letters <= 0.30 and len(_PRESENTATION.findall(text)) < 5


def _court_ok(court: str | None, wanted: str | None) -> bool:
    return not wanted or wanted.lower() in (court or "").lower()


def search(query: str, *, top_k: int | None = None, min_score: float | None = None,
           year_from: int | None = None, year_to: int | None = None, court: str | None = None) -> list[dict]:
    """Best paragraph per judgment, score >= min_score, top_k judgments.
    Each hit: doc_id, display_name, case_name, court, year, case_number,
    paragraph, text (the matched window), paragraph_text, prefix, score, topics."""
    indexes = _ready() if query.strip() else []
    if not indexes:
        return []
    from app.ai import embeddings
    top_k = settings.JUDGMENTS_TOP_K if top_k is None else top_k
    min_score = settings.JUDGMENTS_MIN_SCORE if min_score is None else min_score
    qvec = embeddings.embed([query])
    best: dict[str, tuple[float, dict]] = {}
    for ix in indexes:
        index, chunks, found = ix.index, ix.chunks, 0
        scores, ids = index.search(qvec, min(index.ntotal, max(top_k * 60, 600)))
        for s, i in zip(scores[0], ids[0], strict=True):
            if not 0 <= i < len(chunks) or float(s) < min_score:
                continue
            c = chunks[i]
            if c["doc_id"] in best or c.get("para") == 0 or not readable(window_text(c)):
                continue                       # para 0 is the heading and parties, not a holding
            yr = c.get("year")
            if (year_from is not None and (yr is None or yr < year_from)) or \
               (year_to is not None and (yr is None or yr > year_to)) or not _court_ok(c.get("court"), court):
                continue
            best[c["doc_id"]] = (float(s), c)
            found += 1
            if found >= top_k:
                break
    hits = []
    for s, c in sorted(best.values(), key=lambda x: -x[0])[:top_k]:
        summ = catalog.summary(c["doc_id"]) or {}
        rec = {"case_name": summ.get("case_name", c.get("case_name")), "court": summ.get("court", c.get("court")),
               "year": summ.get("year", c.get("year")), "case_number": summ.get("case_number")}
        para_text = catalog.paragraph(c["doc_id"], c["para"]) if summ else None
        window = window_text(c)
        if para_text and not readable(para_text):
            continue
        hits.append({
            "doc_id": c["doc_id"], "display_name": jd.display_name(rec), "case_name": rec["case_name"],
            "court": rec["court"], "year": rec["year"], "case_number": rec["case_number"],
            "paragraph": c["para"], "text": window,
            "paragraph_text": _around(para_text or window, window, PARAGRAPH_CHARS),
            "prefix": jd.shown_prefix(rec, c["para"]), "score": round(s, 4),
            "topics": summ.get("topics", c.get("topics") or []),
        })
    return hits


def _around(full: str, window: str, limit: int) -> str:
    """`full` if short; else `limit` characters starting a little before the window."""
    full = " ".join(full.split())
    if len(full) <= limit:
        return full
    i = full.find(" ".join(window.split())[:60])
    a = max(0, min(i - 200 if i > 0 else 0, len(full) - limit))
    a = full.rfind(" ", 0, a) + 1 if a else 0
    cut = full[a:a + limit]
    return ("… " if a else "") + cut.rsplit(" ", 1)[0] + " …"


def reset() -> None:
    global _INDEX, _SCRAPED
    _INDEX = _Index()
    _SCRAPED = _Index(scraped_paths, scraped=True)
