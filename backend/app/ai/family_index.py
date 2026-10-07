"""Family-law side index (step 4 of the Oct 2026 chat-quality work).

Why: the embedding model reads only the first 128 tokens of a chunk, and
99% of the 800-character chunks are longer. The Family Courts Act Schedule
("Dower", "Restitution of conjugal rights", "Dowry", "Personal property
and belongings of a wife") starts at token 130 of its chunk, so no query
could reach it (docs/evaluation/chat_review_family_law_2026-10-05.md, 3.3).

What: the chunks of a small allowlist of family statutes are re-embedded
in overlapping windows of at most WINDOW_TOKENS tokens, in memory, at
first use. The main index and its files are not touched. A chunk's score
is its best window; the model still sees the whole chunk.

  core       always searched in family scope
  minority   Christian, Hindu and Parsi personal law, only when the
             question names the community (otherwise the Divorce Act 1869
             and Married Women's Property Act crowd out Muslim family law)

The Qanun-e-Shahadat and the CPC are deliberately absent: FCA s.17 says
they don't apply to Family Court proceedings (except CPC ss.10-11).
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from pathlib import Path

from app.ai import embeddings
from app.core.config import settings
from app.core.logging import logger

# Embedding ~1,500 windows takes 1-2 minutes on CPU, so the vectors are
# cached on disk. Not under backend/storage/ (the main index lives there and
# is left untouched); rebuilt automatically when anything they depend on
# changes (see _fingerprint).
CACHE_PATH = Path("cache") / "family_index.npz"

WINDOW_TOKENS = 120
WINDOW_STRIDE = 60

# Normalised source-name fragments (lower case, letters and digits only).
CORE = (
    "muslimfamilylaws",           # MFLO 1961 (both copies in the corpus)
    "familycourtsact",            # West Pakistan Family Courts Act 1964
    "dissolutionofmuslimmarriages",
    "dowryandbridalgifts",
    "guardiansandwards",          # Guardians and Wards Act 1890
    "childmarriagerestraint",
    "majorityact",
)
MINORITY = (
    "christianmarriageact",
    "divorceact1869",
    "hindumarriageact",
    "hindumarriedwomen",
    "parsimarriageanddivorce",
    "marriedwomensproperty",
)

_FAMILY_TERMS_EN = (
    "nikah", "nikahnama", "nikah nama", "talaq", "khula", "dower", "mahr", "mehr",
    "dowry", "jahez", "jahiz", "dahej", "maintenance", "nafqa", "nafaqa", "custody",
    "hizanat", "guardian", "guardianship", "conjugal", "iddat", "family court",
    "divorce", "marriage", "married", "matrimonial", "wife", "wives", "husband",
    "spouse", "polygamy", "bridal", "jactitation", "minor child", "child marriage",
)
_FAMILY_TERMS_UR = ("نکاح", "طلاق", "خلع", "مہر", "جہیز", "نفقہ", "حضانت", "بیوی", "شوہر",
                    "عدت", "فیملی کورٹ", "سرپرست", "شادی")
_COMMUNITY_EN = ("christian", "hindu", "parsi", "sikh")
_COMMUNITY_UR = ("مسیحی", "عیسائی", "ہندو", "پارسی", "سکھ")

_EN_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in _FAMILY_TERMS_EN) + r")s?\b", re.I)
_COMMUNITY_RE = re.compile(r"\b(?:" + "|".join(_COMMUNITY_EN) + r")s?\b", re.I)


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def is_family_question(*texts: str) -> bool:
    """A family term of art in the question or its rewrite."""
    joined = " ".join(t for t in texts if t)
    return bool(_EN_RE.search(joined)) or any(t in joined for t in _FAMILY_TERMS_UR)


def names_community(*texts: str) -> bool:
    joined = " ".join(t for t in texts if t)
    return bool(_COMMUNITY_RE.search(joined)) or any(t in joined for t in _COMMUNITY_UR)


def tier_of(source: str | None) -> str | None:
    n = norm(source)
    if any(k in n for k in CORE):
        return "core"
    if any(k in n for k in MINORITY):
        return "minority"
    return None


class _FamilyIndex:
    def __init__(self) -> None:
        self.index = None
        self.parent: list[int] = []     # window -> position in embeddings._META
        self.tier: list[str] = []
        self.lock = threading.Lock()

    def build(self) -> int:
        if self.index is not None:
            return self.index.ntotal
        with self.lock:
            if self.index is not None:
                return self.index.ntotal
            import faiss
            import numpy as np
            if embeddings.build_or_load() == 0:
                return 0
            t0 = time.perf_counter()
            fp = _fingerprint()
            vecs = None
            if CACHE_PATH.exists():
                try:
                    with np.load(CACHE_PATH) as z:
                        if str(z["fingerprint"]) == fp:
                            vecs, parent = z["vectors"], z["parent"].tolist()
                            tier = z["tier"].tolist()
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Family index cache unreadable, rebuilding: {e}")
            source = "cache"
            if vecs is None:
                source = "built"
                tok = embeddings._load_model().tokenizer
                texts, parent, tier = [], [], []
                for pos, meta in enumerate(embeddings._META):
                    t = tier_of(embeddings.record_source(meta))
                    if t is None:
                        continue
                    for w in windows(embeddings.record_text(meta), tok):
                        texts.append(w)
                        parent.append(pos)
                        tier.append(t)
                vecs = embeddings.embed(texts)
                try:
                    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    np.savez(CACHE_PATH, fingerprint=fp, vectors=vecs,
                             parent=np.array(parent), tier=np.array(tier))
                except OSError as e:
                    logger.warning(f"Family index cache not written: {e}")
            index = faiss.IndexFlatIP(vecs.shape[1])
            index.add(vecs)
            self.parent, self.tier, self.index = parent, tier, index
            logger.info(
                f"Family index ({source}): {index.ntotal} windows from "
                f"{len(set(parent))} chunks in {time.perf_counter() - t0:.1f}s"
            )
            return index.ntotal

    def search(self, query: str, top_k: int, *, minority: bool) -> list[dict]:
        """Best `top_k` parent chunks, each scored by its best window."""
        if self.build() == 0:
            return []
        qv = embeddings.embed([query])
        scores, ids = self.index.search(qv, min(self.index.ntotal, 50 * top_k))
        best: dict[int, tuple[float, int]] = {}
        for s, w in zip(scores[0], ids[0], strict=True):
            if w < 0 or (self.tier[w] == "minority" and not minority):
                continue
            p = self.parent[w]
            if p not in best:
                best[p] = (float(s), int(w))
            if len(best) == top_k:
                break
        return [
            {**embeddings._META[p], "relevance": s, "family_window": w}
            for p, (s, w) in best.items()
        ]


def _fingerprint() -> str:
    """Everything the cached vectors depend on."""
    meta = Path(settings.FAISS_METADATA_PATH)
    st = meta.stat()
    key = json.dumps([str(meta.resolve()), st.st_size, st.st_mtime_ns, len(embeddings._META),
                      CORE, MINORITY, WINDOW_TOKENS, WINDOW_STRIDE,
                      settings.EMBEDDING_MODEL_NAME])
    return hashlib.sha256(key.encode()).hexdigest()


def windows(text: str, tokenizer) -> list[str]:
    """Overlapping slices of `text` of at most WINDOW_TOKENS tokens."""
    enc = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = enc["offset_mapping"]
    if len(offsets) <= WINDOW_TOKENS:
        return [text]
    out = []
    for start in range(0, len(offsets), WINDOW_STRIDE):
        span = offsets[start:start + WINDOW_TOKENS]
        out.append(text[span[0][0]:span[-1][1]])
        if start + WINDOW_TOKENS >= len(offsets):
            break
    return out


_INDEX = _FamilyIndex()


def search(query: str, top_k: int, *, minority: bool = False) -> list[dict]:
    return _INDEX.search(query, top_k, minority=minority)


def start_background_load() -> None:
    """Build (or load from cache) at startup when the feature is on, so the
    first family question doesn't wait for it."""
    if settings.FAMILY_INDEX:
        threading.Thread(target=_INDEX.build, name="family-index", daemon=True).start()


def stats() -> dict:
    _INDEX.build()
    return {"windows": _INDEX.index.ntotal if _INDEX.index is not None else 0,
            "chunks": len(set(_INDEX.parent)),
            "core_windows": _INDEX.tier.count("core"),
            "minority_windows": _INDEX.tier.count("minority")}
