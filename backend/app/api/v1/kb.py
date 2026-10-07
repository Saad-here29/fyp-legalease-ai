"""Knowledge Base router — /kb/* (read-only, any logged-in user).

Browses the kb-v2 section records: the laws, their sections, each record in
the spec's JSON format (docs/knowledge_base_spec.md), a JSON download and,
when one was saved, the original file. Nothing here writes or touches the
database; the data comes from storage/kb/ (app/kb/catalog.py).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, Response

from app.core.config import settings
from app.core.exceptions import NotFound
from app.kb import catalog, judgment_catalog, judgment_search
from app.middlewares.auth import CurrentUser

router = APIRouter()


@router.get("/stats", summary="Knowledge base size, categories, tiers and coverage")
def kb_stats(user: CurrentUser):
    return catalog.stats()


@router.get("/documents", summary="Laws in the knowledge base, filterable")
def kb_documents(
    user: CurrentUser,
    q: str | None = Query(default=None, max_length=200, description="words in the title"),
    category: str | None = None,
    tier: int | None = Query(default=None, ge=1, le=3),
    jurisdiction: str | None = None,
    year: int | None = Query(default=None, ge=1800, le=2100),
    status: str | None = None,
):
    docs = catalog.documents(q=q, category=category, tier=tier, jurisdiction=jurisdiction, year=year, status=status)
    return {"total": len(docs), "documents": docs}


def _law_or_404(doc_id: str) -> dict:
    law = catalog.law(doc_id)
    if law is None:
        raise NotFound("No law with this id in the knowledge base.")
    return law


@router.get("/documents/{doc_id}", summary="One law's metadata")
def kb_document(doc_id: str, user: CurrentUser):
    return catalog.public_law(_law_or_404(doc_id))


@router.get("/documents/{doc_id}/sections", summary="A law's section records (id, number, heading, preview)")
def kb_sections(doc_id: str, user: CurrentUser):
    law = _law_or_404(doc_id)
    return {"doc_id": doc_id, "title": law["title"], "sections": catalog.sections(doc_id)}


@router.get("/documents/{doc_id}/download", summary="All of a law's records as a JSON file")
def kb_download(doc_id: str, user: CurrentUser):
    _law_or_404(doc_id)
    body = json.dumps(catalog.law_records(doc_id), ensure_ascii=False, indent=2)
    return Response(
        content=body.encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{doc_id}.json"'},
    )


@router.get("/documents/{doc_id}/original", summary="The saved original PDF/HTML, when one exists")
def kb_original(doc_id: str, user: CurrentUser):
    _law_or_404(doc_id)
    path = catalog.original_path(doc_id)
    if path is None:
        raise NotFound("No saved original for this law.")
    media = "application/pdf" if path.suffix.lower() == ".pdf" else "text/html"
    return FileResponse(path, media_type=media, filename=path.name)


@router.get("/records/{record_id:path}", summary="One section record, exactly in the spec's JSON format")
def kb_record(record_id: str, user: CurrentUser):
    rec = catalog.record(record_id)
    if rec is None:
        raise NotFound("No record with this id in the knowledge base.")
    return rec


# ----- Judgments (kb-v2 C2, settings.JUDGMENTS_V2) ---------------------------
# Read from storage/kb/judgments/records/*.jsonl, never the database. The
# original file's path and the file hash are never returned.

def _judgments_on() -> None:
    if not settings.JUDGMENTS_V2:
        raise NotFound("Judgments are not enabled on this server.")


@router.get("/judgments", summary="Judgments: counts, courts, years, topics and a paginated list")
def kb_judgments(
    user: CurrentUser,
    q: str | None = Query(default=None, max_length=200, description="words in the name, case number or judges"),
    court: str | None = Query(default=None, max_length=100),
    year: int | None = Query(default=None, ge=1900, le=2100),
    topic: str | None = Query(default=None, max_length=50),
    indexed: bool = Query(default=False, description="only judgments in the search index"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    _judgments_on()
    in_index = judgment_search.indexed_ids()
    every, found = judgment_catalog.search_list(q=q, court=court, year=year, topic=topic,
                                                indexed_only=indexed, indexed=in_index)
    start = (page - 1) * page_size
    return {
        "counts": {"judgments": len(every), "indexed": sum(1 for s in every if s["doc_id"] in in_index),
                   "excluded": judgment_catalog.excluded_counts(), **judgment_search.status()},
        **judgment_catalog.stats(every),
        "total": len(found), "page": page, "page_size": page_size,
        "judgments": [judgment_catalog.public(s, in_index) for s in found[start:start + page_size]],
    }


@router.get("/judgments/{doc_id:path}", summary="One judgment: metadata, numbered paragraphs, provenance, status")
def kb_judgment(doc_id: str, user: CurrentUser):
    _judgments_on()
    out = judgment_catalog.detail(doc_id, judgment_search.indexed_ids())
    if out is None:
        raise NotFound("No judgment with this id in the knowledge base.")
    return out
