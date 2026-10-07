"""AI Legal Research router — /research/* endpoints.

Implements UC-06 (Search Legal Library by Semantic Query). Returns ranked
passages from Pakistani statutes and judgments via FAISS semantic search.
"""


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import embeddings
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.schemas.research import (
    ResearchIndexStats,
    ResearchSearchRequest,
    ResearchSearchResponse,
    StructuredAnalysis,
    StructuredAnalysisRequest,
)
from app.services.research_service import ResearchService, filter_coverage

router = APIRouter()


@router.get(
    "/stats",
    response_model=ResearchIndexStats,
    summary="Size of the searchable library (passages and source statutes)",
)
def index_stats():
    # Public: two counts, shown on the (logged-out) landing page as well
    # as the Research page, plus scraping freshness (counts and dates only;
    # cached, and never fails the endpoint). Declared before GET /{entry_id}
    # so "stats" isn't parsed as an id.
    from app.db.session import SessionLocal
    from app.scraping.stats import cached_scrape_updates
    try:
        coverage = filter_coverage()
    except Exception as e:  # noqa: BLE001 — a count on the page must never fail the endpoint
        logger.warning(f"Filter coverage unavailable: {e}")
        coverage = None
    if settings.SCRAPED_V2:              # kb-v2 C3: the update log file, no database
        from app.kb import scraped
        updates = scraped.research_updates()
    else:
        updates = cached_scrape_updates(SessionLocal)
    return {**embeddings.index_stats(), "updates": updates, "filter_coverage": coverage}


@router.post(
    "/search",
    response_model=ResearchSearchResponse,
    summary="Semantic search over the legal library (UC-06)",
)
def search(
    payload: ResearchSearchRequest,
    user: CurrentUser,  # auth-gated, but no role restriction — all roles search
    db: Session = Depends(get_db),
):
    scope = payload.scope if settings.JUDGMENTS_V2 else "statutes"
    service = ResearchService(db)
    results = [] if scope == "judgments" else service.search(
        query=payload.query,
        top_k=payload.top_k,
        court=payload.court if scope == "statutes" else None,   # judgments only, under All
        year_from=payload.year_from,
        year_to=payload.year_to,
        case_type=payload.case_type,
        category=payload.category,
        jurisdiction=payload.jurisdiction,
        source_tier=payload.source_tier,
        include_repealed=payload.include_repealed,
    )
    active = any(v not in (None, "") for v in (payload.category, payload.jurisdiction, payload.source_tier,
                                               payload.year_from, payload.year_to))
    extra = {}
    if settings.JUDGMENTS_V2:
        judgments = [] if scope == "statutes" else service.search_judgments(
            payload.query, year_from=payload.year_from, year_to=payload.year_to, court=payload.court)
        extra = {"scope": scope, "judgments": [j.model_dump() for j in judgments]}
        if scope == "judgments":
            active = any(v is not None for v in (payload.year_from, payload.year_to)) or bool(payload.court)
    return ResearchSearchResponse(
        **extra,
        query=payload.query,
        total=len(results),
        results=results,
        weak_matches=bool(results)
        and max(r.relevance for r in results) < embeddings.similarity_threshold(),
        filters_active=active,
        filter_coverage=filter_coverage() if active and scope != "judgments" else None,
    )


@router.post(
    "/analyze",
    response_model=StructuredAnalysis,
    summary="Run a structured legal breakdown (Issue / Findings / Judgment / Legal Basis / Relevance) on a passage",
)
def analyze_passage(
    payload: StructuredAnalysisRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    # Same split as /documents/analyze and /chat/message, minus the write
    # phase (nothing is persisted here). Phase 1 is the auth lookup, which
    # left a transaction open on this session: close it so no connection
    # sits idle-in-transaction during the LLM call, which Supabase's pooler
    # kills (-> intermittent 500). Phase 2 needs no DB.
    db.close()
    return ResearchService(db).structured_analysis(
        text=payload.text,
        source=payload.source,
        user_query=payload.user_query,
    )

