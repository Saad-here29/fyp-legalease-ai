"""AI Legal Research router — /research/* endpoints.

Implements UC-06 (Search Legal Library by Semantic Query). Returns ranked
passages from Pakistani statutes and judgments via FAISS semantic search.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import NotFound
from app.db.session import get_db
from app.middlewares.auth import CurrentUser
from app.models.legal_corpus import LegalCorpusEntry
from app.schemas.research import (
    ResearchEntryDetail,
    ResearchSearchRequest,
    ResearchSearchResponse,
    StructuredAnalysis,
    StructuredAnalysisRequest,
)
from app.services.research_service import ResearchService

router = APIRouter()


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
    results = ResearchService(db).search(
        query=payload.query,
        top_k=payload.top_k,
        court=payload.court,
        year_from=payload.year_from,
        year_to=payload.year_to,
        case_type=payload.case_type,
    )
    return ResearchSearchResponse(
        query=payload.query,
        total=len(results),
        results=results,
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
    return ResearchService(db).structured_analysis(
        text=payload.text,
        source=payload.source,
        user_query=payload.user_query,
    )


@router.get(
    "/{entry_id}",
    response_model=ResearchEntryDetail,
    summary="Fetch the full text of a single corpus entry",
)
def get_entry(
    entry_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    row = db.get(LegalCorpusEntry, entry_id)
    if row is None:
        raise NotFound("Legal authority not found.")
    return ResearchEntryDetail(
        id=str(row.id),
        title=row.title,
        section_number=row.section_number,
        document_type=row.document_type,
        jurisdiction=row.jurisdiction,
        court=row.court,
        year=row.year,
        content=row.content,
        source_url=row.source_url,
    )
