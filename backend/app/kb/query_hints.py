"""Query hints (kb-v2 C5): retrieval only, never answers.

backend/storage/kb/query_hints.json lists hints {id, triggers, unless,
terms}. When a trigger appears in the question (whole word or phrase, any
case) and none of its "unless" words do, the hint's terms are appended to
the query before it is embedded, so the section where the law is (e.g. MFLO
s.7 for a talaq question) ranks higher. The terms name Acts, sections and
procedural words; they never state a conclusion, and they are never shown to
the model or the user. Applied in embeddings.search with KB_V2 and
QUERY_HINTS on; the file is re-read when it changes. Evaluated in
docs/query_hints_eval_2026-10-07.md.
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
            _CACHE.update(sig=sig, hints=[h for h in data.get("hints", []) if h.get("triggers") and h.get("terms")])
        except (OSError, ValueError) as e:
            logger.warning(f"Query hints unreadable ({e}); none applied")
            _CACHE.update(sig=sig, hints=[])
    return _CACHE["hints"]


def _has(text: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(phrase.lower()) + r"(?![a-z])", text) is not None


def matching(question: str) -> list[dict]:
    """Hints whose trigger is in the question and whose "unless" words aren't.
    None for a question about another country's law ("divorce in California"):
    the terms would lift Pakistani sections past the scope gate."""
    from app.kb.exact_lookup import FOREIGN
    q = (question or "").lower()
    if FOREIGN.search(question or ""):
        return []
    return [h for h in hints()
            if any(_has(q, t) for t in h["triggers"]) and not any(_has(q, u) for u in h.get("unless", []))]


def expand(question: str) -> str:
    """The question plus the matching hints' search terms (unchanged if none)."""
    found = matching(question)
    if not found:
        return question
    logger.info(f"Query hints: {', '.join(h['id'] for h in found)}")
    return question + " " + " ".join(h["terms"] for h in found)


def reset() -> None:
    _CACHE.update(sig=None, hints=[])
