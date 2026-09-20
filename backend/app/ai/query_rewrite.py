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
"""

from __future__ import annotations

from app.ai.client import get_ai_client


def rewrite_for_search(raw_query: str) -> str:
    """Returns a rewritten version of `raw_query` for embedding-based
    search — falls back to the original query unchanged on any AI failure,
    since search must never break because rewriting failed. Callers should
    keep using `raw_query` itself for anything shown to the user or
    persisted (chat history, echoed-back search query, etc.) — only the
    embedding/search call should see the rewritten version."""
    return get_ai_client().rewrite_search_query(raw_query)
