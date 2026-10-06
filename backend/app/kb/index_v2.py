"""Knowledge base v2 index: section-aware chunks of the kb records.

Chunk rule (docs/knowledge_base_spec.md § a2): a window of at most
MAX_TOKENS tokens (the embedding model's own tokenizer, special tokens not
counted) from ONE section record, starting with the prefix
"<Title> - s.<N> <Heading>:", which counts inside the limit.

Files (never the live v1 index):
    backend/storage/kb/faiss_v2.faiss       IndexFlatIP over L2-normalised vectors
    backend/storage/kb/faiss_v2_meta.json   {"manifest", "chunks": [...], "texts": {doc_id: section text}}

Search (settings.KB_V2): faiss_v2 first, then the v1 index without the
chunks of any law v2 holds, merged by score, in the v1 result shape plus
section, heading, source_tier and source_url.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger

MAX_TOKENS = 120
OVERLAP = 20
MAX_PREFIX = 60          # a very long heading is shortened so the window keeps >= 60 tokens
PASSAGE_CHARS = 1200     # text returned for a hit: the whole section, or this much around the window

CHUNK_FIELDS = ("doc_id", "title", "section", "heading", "source_tier", "category", "year", "jurisdiction",
                "source_type", "source_url", "status", "source", "audience")


# --------------------------------------------------------------------------- chunking

def prefix_for(rec: dict) -> str:
    sec, head = rec.get("section"), (rec.get("heading") or "").strip()
    if sec is None:
        return f"{rec['title']}:"
    if sec[0].isdigit():
        return f"{rec['title']} - s.{sec} {head}".rstrip() + ":"
    return f"{rec['title']} - {sec}" + (f" {head}" if head else "") + ":"


def _ntok(tokenizer, text: str) -> int:
    return len(tokenizer(text, add_special_tokens=False)["input_ids"])


def _fit_prefix(rec: dict, tokenizer) -> str:
    p = prefix_for(rec)
    if _ntok(tokenizer, p) <= MAX_PREFIX:
        return p
    head = rec.get("heading") or ""
    while head and _ntok(tokenizer, prefix_for({**rec, "heading": head + " …"})) > MAX_PREFIX:
        head = head.rsplit(" ", 1)[0] if " " in head else ""
    return prefix_for({**rec, "heading": (head + " …") if head else ""})


def chunk_record(rec: dict, tokenizer) -> list[dict]:
    """Windows of one record: [{"text", "start", "end", "window"}], every
    text <= MAX_TOKENS tokens, prefix included."""
    prefix = _fit_prefix(rec, tokenizer)
    body = rec["text"]
    enc = tokenizer(body, add_special_tokens=False, return_offsets_mapping=True)
    offs = [o for o in enc["offset_mapping"] if o[1] > o[0]]
    budget = MAX_TOKENS - _ntok(tokenizer, prefix + " x") + 1     # tokens left for the body
    out, start = [], 0
    while start < len(offs):
        size = min(budget, len(offs) - start)
        while True:
            a, b = offs[start][0], offs[start + size - 1][1]
            text = f"{prefix} {body[a:b]}"
            n = _ntok(tokenizer, text)
            if n <= MAX_TOKENS or size == 1:
                break
            size -= max(1, n - MAX_TOKENS)          # re-tokenising at the join can add a token or two
        out.append({"text": text, "start": a, "end": b, "window": len(out) + 1})
        if start + size >= len(offs):
            break
        start += max(1, size - OVERLAP)
    if not out:                                      # empty body: the prefix alone
        out.append({"text": prefix, "start": 0, "end": 0, "window": 1})
    return out


def load_records(records_dir: Path) -> list[dict]:
    recs = []
    for path in sorted(records_dir.glob("*.jsonl")):
        recs += [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return recs


def vector_key(text: str) -> str:
    """Cache key of one embedding input: the model name + the exact chunk text."""
    return hashlib.sha256(f"{settings.EMBEDDING_MODEL_NAME}\n{text}".encode()).hexdigest()


class VectorCache:
    """Embeddings already computed, keyed by vector_key, in shard files under
    `directory` (shard_00001.npz, ...). A shard is written after every
    `checkpoint` new vectors, so an interrupted build loses at most one shard."""

    def __init__(self, directory: Path) -> None:
        import numpy as np
        self.dir = directory
        self.vecs: dict[str, np.ndarray] = {}
        directory.mkdir(parents=True, exist_ok=True)
        for p in sorted(directory.glob("*.npz")):
            with np.load(p) as z:
                for k, v in zip(z["keys"].tolist(), z["vectors"], strict=True):
                    self.vecs[k] = v

    def add(self, keys: list[str], vectors) -> None:
        import numpy as np
        n = len(list(self.dir.glob("shard_*.npz"))) + 1
        tmp = self.dir / f"shard_{n:05d}.tmp.npz"
        np.savez(tmp, keys=np.array(keys), vectors=np.asarray(vectors, np.float32))
        tmp.replace(self.dir / f"shard_{n:05d}.npz")
        for k, v in zip(keys, vectors, strict=True):
            self.vecs[k] = v

    def seed_from_index(self, index_path: Path, meta_path: Path) -> int:
        """Reuse the vectors of an earlier faiss_v2 build (same chunk text =
        same vector). Returns how many were new to the cache."""
        import faiss
        if not (index_path.exists() and meta_path.exists()):
            return 0
        chunks = json.loads(meta_path.read_text(encoding="utf-8"))["chunks"]
        index = faiss.read_index(str(index_path))
        if index.ntotal != len(chunks):
            return 0
        vectors = index.reconstruct_n(0, index.ntotal)
        keys, vecs = [], []
        for c, v in zip(chunks, vectors, strict=True):
            k = vector_key(c["chunk_text"])
            if k not in self.vecs:
                keys.append(k)
                vecs.append(v)
        if keys:
            self.add(keys, vecs)
        return len(keys)


def make_chunks(recs: list[dict], tokenizer) -> tuple[list[dict], dict[str, str]]:
    chunks, texts = [], {}
    for rec in recs:
        texts[rec["doc_id"]] = rec["text"]
        for c in chunk_record(rec, tokenizer):
            chunks.append({**{k: rec.get(k) for k in CHUNK_FIELDS}, "window": c["window"],
                           "start": c["start"], "end": c["end"], "chunk_text": c["text"]})
    return chunks, texts


def build(records_dir: Path, index_path: Path, meta_path: Path, *, tokenizer, embed,
          excluded_v1_sources: list[str], cache_dir: Path | None = None, checkpoint: int = 1000,
          time_budget: float | None = None) -> dict:
    """Chunk every record and write a NEW index; refuses the live v1 paths.

    Incremental and resumable: vectors are looked up in the VectorCache
    (cache_dir, default <index dir>/vector_cache), seeded from the previous
    faiss_v2 build; only chunks whose text is new or changed are embedded,
    `checkpoint` at a time, each batch saved before the next. If
    `time_budget` seconds run out first, nothing is written over the
    existing index and the manifest says complete=False: run again to
    continue from the cache."""
    import faiss
    import numpy as np
    live = {Path(settings.FAISS_INDEX_PATH).resolve(), Path(settings.FAISS_METADATA_PATH).resolve()}
    if index_path.resolve() in live or meta_path.resolve() in live:
        raise ValueError("refusing to overwrite the live v1 index")
    t0 = time.perf_counter()
    cache = VectorCache(cache_dir or index_path.parent / "vector_cache")
    seeded = cache.seed_from_index(index_path, meta_path)
    recs = load_records(records_dir)
    chunks, texts = make_chunks(recs, tokenizer)
    t_chunk = time.perf_counter() - t0
    keys = [vector_key(c["chunk_text"]) for c in chunks]
    unique = list(dict.fromkeys(keys))
    missing = [k for k in unique if k not in cache.vecs]
    text_of = {k: c["chunk_text"] for k, c in zip(keys, chunks, strict=True)}
    embedded = 0
    for i in range(0, len(missing), checkpoint):
        if time_budget is not None and time.perf_counter() - t0 > time_budget:
            break
        part = missing[i:i + checkpoint]
        cache.add(part, embed([text_of[k] for k in part]))
        embedded += len(part)
    manifest = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "embedding_model": settings.EMBEDDING_MODEL_NAME, "normalised": True, "metric": "inner product",
        "max_tokens": MAX_TOKENS, "overlap": OVERLAP, "records": len(recs), "chunks": len(chunks),
        "laws": sorted({r["title"] for r in recs}),
        "excluded_v1_sources": sorted(excluded_v1_sources),
        "unique_chunk_texts": len(unique), "reused_vectors": len(unique) - len(missing),
        "embedded_now": embedded, "still_missing": len(missing) - embedded, "seeded_from_previous": seeded,
        "complete": embedded == len(missing),
        "chunk_seconds": round(t_chunk, 1), "total_seconds": round(time.perf_counter() - t0, 1),
    }
    if not manifest["complete"]:
        return manifest
    vectors = np.vstack([cache.vecs[k] for k in keys]).astype(np.float32) if keys else np.zeros((0, 384), np.float32)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_idx, tmp_meta = index_path.with_name(index_path.name + ".tmp"), meta_path.with_name(meta_path.name + ".tmp")
    faiss.write_index(index, str(tmp_idx))
    tmp_meta.write_text(json.dumps({"manifest": manifest, "chunks": chunks, "texts": texts}, ensure_ascii=False),
                        encoding="utf-8")
    tmp_idx.replace(index_path)
    tmp_meta.replace(meta_path)
    return manifest


# --------------------------------------------------------------------------- community gating

# A law whose audience isn't "general" is searched only when the question
# names its community (or the Act itself). Deterministic: keyword match, no
# model call. Urdu names as in app/ai/family_index.py.
AUDIENCE_TERMS = {
    "Christian": ("christian", "christians", "church", "مسیحی", "عیسائی"),
    "Parsi": ("parsi", "parsis", "zoroastrian", "پارسی"),
    "Hindu": ("hindu", "hindus", "ہندو"),
    "Sikh": ("sikh", "sikhs", "anand", "سکھ"),
    "Arya Samaj": ("arya", "hindu", "hindus", "ہندو"),
    "non-Muslim (other faiths)": ("non-muslim", "non muslim", "nonmuslim", "غیر مسلم", "hindu", "sikh", "buddhist",
                                  "jain", "jaina", "jewish", "jew", "inter-faith", "interfaith"),
    "non-Muslim (Christian, Parsi and others)": ("non-muslim", "non muslim", "nonmuslim", "غیر مسلم", "christian",
                                                 "christians", "parsi", "parsis", "zoroastrian"),
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def names_audience(query: str, audience: str | None, title: str | None) -> bool:
    """True if a law with this audience may be shown for this question."""
    if not audience or audience == "general":
        return True
    q = (query or "").lower()
    words = set(re.findall(r"[a-z]+(?:-[a-z]+)?", q))
    for term in AUDIENCE_TERMS.get(audience, ()):
        if (" " in term or "-" in term or not term.isascii()) and term in q:
            return True
        if term in words:
            return True
    # The Act's own title: with its year, or without it if the name has 2+
    # words besides "Act" ("Special Marriage Act" yes, "Divorce Act" no).
    t = re.sub(r"^the\s+", "", (title or "").lower())
    if _norm(t) and _norm(t) in _norm(q):
        return True
    stem = re.sub(r",?\s*\d{4}$", "", t)
    return len([w for w in re.findall(r"[a-z]+", stem) if w != "act"]) >= 2 and _norm(stem) in _norm(q)


# --------------------------------------------------------------------------- search

class _V2:
    def __init__(self) -> None:
        self.index = None
        self.chunks: list[dict] = []
        self.texts: dict[str, str] = {}
        self.excluded: set[str] = set()
        self.lock = threading.Lock()

    def load(self) -> int:
        if self.index is not None:
            return self.index.ntotal
        with self.lock:
            if self.index is None:
                import faiss
                idx, meta = Path(settings.KB_V2_INDEX_PATH), Path(settings.KB_V2_METADATA_PATH)
                if not (idx.exists() and meta.exists()):
                    logger.warning(f"KB_V2 is on but {idx} is missing; using the v1 index only")
                    return 0
                data = json.loads(meta.read_text(encoding="utf-8"))
                self.chunks, self.texts = data["chunks"], data["texts"]
                self.excluded = set(data["manifest"]["excluded_v1_sources"])
                self.index = faiss.read_index(str(idx))
                logger.info(f"KB v2 index ready: {self.index.ntotal} chunks")
        return self.index.ntotal


_V2_INDEX = _V2()


def passage(chunk: dict, full: str) -> str:
    """The whole section if short; otherwise PASSAGE_CHARS around the window."""
    if len(full) <= PASSAGE_CHARS:
        return full
    a = max(0, min(chunk["start"] - 200, len(full) - PASSAGE_CHARS))
    a = full.rfind(" ", 0, a) + 1 if a else 0
    b = full.find(" ", a + PASSAGE_CHARS)
    return full[a: b if b > 0 else len(full)]


def search(query: str, top_k: int, filters: dict | None = None) -> list[dict]:
    """faiss_v2 + the v1 index (without the laws v2 holds), merged by score."""
    from app.ai import embeddings
    qvec = embeddings.embed([query])
    hits: list[dict] = []
    if _V2_INDEX.load():
        scores, ids = _V2_INDEX.index.search(qvec, min(_V2_INDEX.index.ntotal, top_k * 30))
        best: dict[str, tuple[float, int]] = {}
        for s, i in zip(scores[0], ids[0], strict=True):
            if 0 <= i < len(_V2_INDEX.chunks):
                c = _V2_INDEX.chunks[i]
                if not names_audience(query, c.get("audience"), c["title"]):
                    continue
                d = c["doc_id"]
                if d not in best:
                    best[d] = (float(s), int(i))
        for d, (s, i) in best.items():
            c = _V2_INDEX.chunks[i]
            hit = {
                "source": c["title"], "source_type": c["source_type"], "chunk_id": i,
                "text": passage(c, _V2_INDEX.texts.get(d, "")),
                "section": c["section"], "heading": c["heading"], "source_tier": c["source_tier"],
                "source_url": c["source_url"], "category": c["category"], "year": c["year"],
                "jurisdiction": c["jurisdiction"], "audience": c.get("audience") or "general",
                "doc_id": d, "kb": "v2", "relevance": s,
            }
            if embeddings.passes_filters(hit, filters):
                hits.append(hit)
    old = embeddings._search_v1(query, top_k * 8, filters, qvec=qvec)
    hits += [h for h in old if h.get("source") not in _V2_INDEX.excluded]
    hits.sort(key=lambda h: h["relevance"], reverse=True)
    return hits[:top_k]


def reset() -> None:
    global _V2_INDEX
    _V2_INDEX = _V2()
