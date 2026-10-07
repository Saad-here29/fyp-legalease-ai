"""Query hints (kb-v2 C5, C8): retrieval only, never answers.

backend/storage/kb/query_hints.json lists hints {id, triggers, unless, terms,
exact_sections}. A trigger is a list of words that must all appear in the
question (whole words, any order); a hint fires on any of its triggers unless
one of its "unless" words appears, and never for a question naming another
country's law. Then:
  - its terms (procedural search words) are appended to the query before
    embedding (expand);
  - its exact sections ([law title, section], resolved to record ids against
    the records when the file is read; a missing one is dropped and logged)
    join the hybrid ranking in index_v2.search (exact_doc_ids).
Hints never state a conclusion and are never shown to the model or the user.
Applied with KB_V2 and QUERY_HINTS on.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger

_CACHE: dict = {"sig": None, "hints": []}


def _path() -> Path:
    return Path(settings.QUERY_HINTS_PATH)


def _resolve(pairs: list) -> tuple[list[str], list]:
    """([record ids], [missing pairs]) for [law title, section] pairs."""
    from app.kb import catalog
    by = {(r.get("title"), str(r.get("section"))): rid for rid, r in catalog.data()["records"].items()}
    ids, missing = [], []
    for title, section in pairs:
        rid = by.get((title, str(section)))
        (ids.append(rid) if rid else missing.append([title, section]))
    return ids, missing


def hints() -> list[dict]:
    p = _path()
    try:
        st = p.stat()
    except OSError:
        return []
    sig = (str(p), st.st_mtime_ns, st.st_size)
    if _CACHE["sig"] != sig:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out = []
            for h in data.get("hints", []):
                if not h.get("triggers"):
                    continue
                h = {**h, "triggers": [[w.lower() for w in (t if isinstance(t, list) else [t])] for t in h["triggers"]]}
                h["doc_ids"], missing = _resolve(h.get("exact_sections") or [])
                if missing:
                    logger.warning(f"Query hint {h['id']}: sections not in the records, dropped: {missing}")
                out.append(h)
            _CACHE.update(sig=sig, hints=out)
        except (OSError, ValueError) as e:
            logger.warning(f"Query hints unreadable ({e}); none applied")
            _CACHE.update(sig=sig, hints=[])
    return _CACHE["hints"]


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", (text or "").lower()))


def matching(question: str) -> list[dict]:
    """Hints with a trigger whose words are all in the question and none of whose
    "unless" words are. None for a question about another country's law."""
    from app.kb.exact_lookup import FOREIGN
    if FOREIGN.search(question or ""):
        return []
    words = _words(question)
    return [h for h in hints()
            if any(all(w in words for w in t) for t in h["triggers"]) and not (set(h.get("unless", [])) & words)]


def expand(question: str) -> str:
    """The question plus the matching hints' search terms (unchanged if none)."""
    found = [h for h in matching(question) if h.get("terms")]
    if not found:
        return question
    logger.info(f"Query hints: {', '.join(h['id'] for h in found)}")
    return question + " " + " ".join(h["terms"] for h in found)


def exact_doc_ids(question: str) -> list[str]:
    """Record ids of the matching hints' exact sections, in hint order."""
    out: list[str] = []
    for h in matching(question):
        out += [d for d in h.get("doc_ids", []) if d not in out]
    return out


def reset() -> None:
    _CACHE.update(sig=None, hints=[])
