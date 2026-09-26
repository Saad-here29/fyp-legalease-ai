"""AI Legal Research request/response schemas."""

from pydantic import Field

from app.schemas.common import APIModel


class ResearchSearchRequest(APIModel):
    query: str = Field(min_length=2, max_length=2000)
    court: str | None = None
    year_from: int | None = Field(default=None, ge=1900, le=2100)
    year_to: int | None = Field(default=None, ge=1900, le=2100)
    case_type: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)


class ResearchResult(APIModel):
    id: str
    title: str
    citation: str
    court: str | None
    year: int | None
    case_type: str | None
    excerpt: str
    text: str  # full chunk text — used by the detail view
    relevance: float


class ResearchIndexStats(APIModel):
    chunks: int       # passages in the FAISS index
    documents: int    # distinct source statutes


class ResearchSearchResponse(APIModel):
    query: str
    total: int
    results: list[ResearchResult]


class ResearchEntryDetail(APIModel):
    id: str
    title: str
    section_number: str | None
    document_type: str
    jurisdiction: str
    court: str | None
    year: int | None
    content: str
    source_url: str | None = None


class StructuredAnalysisRequest(APIModel):
    """Payload for /research/analyze — generate a structured legal breakdown
    of a passage. The passage itself is sent inline so the endpoint stays
    pure (no DB lookup) and works for both corpus results and OCR text."""

    text: str
    source: str | None = None
    user_query: str | None = None


class StructuredAnalysis(APIModel):
    issue: str
    findings: str
    judgment: str
    legal_basis: str
    relevance: str
    raw: str  # the LLM's full unstructured response, for transparency
