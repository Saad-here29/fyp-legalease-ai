"""Query rewriting for retrieval — always run the user's question through
the LLM before embedding, to do two things a raw string can't do for
itself: compress long/multi-clause questions down to the core issue, and
translate everyday phrasing into the legal terminology the corpus is
actually written in.

The second job matters even for short, clean questions — e.g. "What is
the correct legal procedure for a husband to pronounce divorce?" (71
chars) embeds closer to the Divorce Act 1869 (Christian civil divorce,
irrelevant) than to the Muslim Family Laws Ordinance's talaq procedure,
purely because the query says "divorce" and the wrong statute's title
does too. There's no length past which that stops being a problem, so
there's no threshold to gate this on — see rewrite_search_query() in
app/ai/client.py for the actual rewriting logic.

v2 (settings.REWRITE_V2) rewrites at temperature 0 with a prompt that
forbids adding statute names, and strip_unasked_statutes() removes any
the model adds anyway. Every rewrite is logged with the question and the
time it took, so a retrieval result can be traced to its query.
"""

from __future__ import annotations

import re
import time

from app.ai.client import get_ai_client
from app.core.config import settings
from app.core.logging import logger

# A statute named in full: capitalised words (with of/and/the/for between
# them) ending in Act/Ordinance/Order/Code/Rules, an optional year, and an
# optional preposition in front ("under the ... Act, 1964").
_PREP = r"(?:\b(?:under|in|per|from|by|of)\s+)?(?:the\s+)?"
_FULL_NAME = (
    _PREP
    + r"(?:Code of (?:Civil|Criminal) Procedure"
    + r"|(?:[A-Z][\w'’-]*\s+(?:(?:of|and|the|for)\s+)?){1,8}"
    + r"(?:Act|Ordinance|Order|Code|Rules))\b(?:,?\s*\d{4})?"
)
_ABBREVIATIONS = ("PPC", "CrPC", "CPC", "MFLO", "QSO", "DMMA", "FCA")
_ABBREV = _PREP + r"\b(?:" + "|".join(_ABBREVIATIONS) + r")\b"
_STATUTE = re.compile(f"{_FULL_NAME}|{_ABBREV}")

_GENERIC = {
    "under", "in", "per", "from", "by", "of", "the", "and", "for", "act",
    "ordinance", "order", "code", "rules", "law", "laws", "pakistan", "west",
}


def _named_in(question: str, name: str) -> bool:
    """True if the question itself names this statute: every distinctive
    word of the name (or the abbreviation itself) appears in it."""
    q = question.lower()
    words = [w for w in re.findall(r"[a-z][\w'’-]*", name.lower()) if w not in _GENERIC]
    abbrev = [w for w in re.findall(r"\b\w+\b", name) if w in _ABBREVIATIONS]
    if abbrev:
        return any(re.search(rf"\b{re.escape(a.lower())}\b", q) for a in abbrev)
    return bool(words) and all(w in q for w in words)


def strip_unasked_statutes(question: str, rewrite: str) -> str:
    """Remove statute names the rewrite added but the question didn't
    mention. A backstop for the v2 prompt's own rule: "Never add the name
    of an Act ... unless the user's question names it"."""
    out = _STATUTE.sub(lambda m: m.group(0) if _named_in(question, m.group(0)) else " ", rewrite)
    out = re.sub(r"\s+([,.;:])", r"\1", re.sub(r"\s{2,}", " ", out)).strip(" ,;:-")
    return out or rewrite


def rewrite_for_search(raw_query: str, *, v2: bool | None = None) -> str:
    """Returns a rewritten version of `raw_query` for embedding-based
    search — falls back to the original query unchanged on any AI failure,
    since search must never break because rewriting failed. Callers should
    keep using `raw_query` itself for anything shown to the user or
    persisted (chat history, echoed-back search query, etc.) — only the
    embedding/search call should see the rewritten version.

    `v2` defaults to settings.REWRITE_V2; the evaluation script passes it
    explicitly to compare both."""
    v2 = settings.REWRITE_V2 if v2 is None else v2
    t0 = time.perf_counter()
    rewrite = get_ai_client().rewrite_search_query(raw_query, v2=v2)
    model_rewrite = rewrite
    if v2:
        rewrite = strip_unasked_statutes(raw_query, rewrite)
    ms = int((time.perf_counter() - t0) * 1000)
    stripped = f" (statute removed from {model_rewrite!r})" if rewrite != model_rewrite else ""
    logger.info(
        f"Query rewrite {'v2' if v2 else 'v1'} ({ms} ms): "
        f"{raw_query[:300]!r} -> {rewrite!r}{stripped}"
    )
    return rewrite
