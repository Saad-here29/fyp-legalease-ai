"""AI Legal Research request/response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field

from app.schemas.common import APIModel


class ResearchSearchRequest(APIModel):
    query: str = Field(min_length=2, max_length=2000)
    court: str | None = None
    year_from: int | None = Field(default=None, ge=1800, le=2100)   # statutes go back to the 1830s
    year_to: int | None = Field(default=None, ge=1800, le=2100)
    case_type: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)
    # Knowledge-base filters (kb-v2 B4). A result is kept only if its law's
    # metadata is known and matches; see ResearchService.search.
    category: str | None = Field(default=None, max_length=100)
    jurisdiction: str | None = Field(default=None, max_length=50)
    source_tier: int | None = Field(default=None, ge=1, le=3)
    # Statutes / Judgments / All (kb-v2 C2). Used only when JUDGMENTS_V2 is
    # on; otherwise every search is a statute search, as before. Judgments
    # take year_from, year_to and court; the other filters are statute-only.
    scope: Literal["statutes", "judgments", "all"] = "statutes"


class JudgmentResult(APIModel):
    """A judgment's best-matching paragraph (app/kb/judgment_search.py)."""
    doc_id: str                 # /kb/judgments/{doc_id}
    display_name: str
    court: str | None
    year: int | None
    case_number: str | None
    paragraph: int
    snippet: str
    text: str
    relevance: float
    topics: list[str] = []


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
    # Present when the passage's law has knowledge-base metadata (kb-v2).
    section: str | None = None
    heading: str | None = None
    category: str | None = None
    jurisdiction: str | None = None
    source_tier: int | None = None
    source_url: str | None = None
    kb_law_id: str | None = None      # /kb/documents/{id}
    kb_record_id: str | None = None   # /kb/records/{id}


class FilterCoverage(APIModel):
    """Searchable documents whose metadata (category and year) is known, so
    the Research filters can apply to them: `known` of `total`."""
    known: int
    total: int


class SourceUpdate(APIModel):
    name: str
    content_type: str | None = None
    checked: int = 0
    new: int = 0
    changed: int = 0
    errors: int = 0


class ScrapeUpdates(APIModel):
    """Freshness from the latest scraping run (scripts/scrape_laws.py).
    available is false until the scraping tables exist and a run has finished.
    New and changed documents are staged for review, not searchable."""
    available: bool = False
    last_checked: datetime | None = None
    last_updated: datetime | None = None
    pages_checked: int | None = None
    new: int | None = None
    changed: int | None = None
    errors: int | None = None
    sources: list[SourceUpdate] = []
    # kb-v2 C3 (SCRAPED_V2): staged documents that pass validation are
    # searchable once embedded, so the page doesn't say "not yet searchable".
    searchable: bool = False


class ResearchIndexStats(APIModel):
    chunks: int       # passages in the FAISS index
    documents: int    # distinct source statutes
    updates: ScrapeUpdates = ScrapeUpdates()   # additive; the search itself is unchanged
    filter_coverage: FilterCoverage | None = None


class ResearchSearchResponse(APIModel):
    # With JUDGMENTS_V2 on, the response also carries "scope" and
    # "judgments" (list[JudgmentResult]); off, it is exactly as before.
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="allow")

    query: str
    total: int
    results: list[ResearchResult]
    # True when no passage reaches the chat's relevance threshold: results are
    # still listed (filtering them would empty valid searches such as "khula
    # procedure", best 0.55), but the page says they may not be relevant.
    weak_matches: bool = False
    filters_active: bool = False
    filter_coverage: FilterCoverage | None = None


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
