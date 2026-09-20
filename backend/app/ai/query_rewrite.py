"""Query rewriting for retrieval — compress long, conversational user
questions into short, focused search queries before embedding.

Real questions run long and multi-clause; statute text uses crisp legal
terminology, so embedding the raw question directly under-matches. Short
queries are already close to how the corpus is phrased, so rewriting them
would just add latency for no benefit — only long ones go through the LLM.
"""

from __future__ import annotations

from app.ai.client import get_ai_client

REWRITE_THRESHOLD = 150


def rewrite_for_search(raw_query: str) -> str:
    """Returns a short, focused version of `raw_query` for embedding-based
    search when it's long enough to benefit; returns it unchanged otherwise
    — including on any AI failure, since search must never break because
    rewriting failed. Callers should keep using `raw_query` itself for
    anything shown to the user or persisted (chat history, echoed-back
    search query, etc.) — only the embedding/search call should see the
    rewritten version."""
    if len(raw_query) <= REWRITE_THRESHOLD:
        return raw_query
    return get_ai_client().rewrite_search_query(raw_query)
