"""Document upload + AI analysis router — /documents/* endpoints.

Implements UC-05 (Upload and Analyse Legal Document) and Algorithm 3
(Stream-and-Commit Document Upload). OCR + AI summarisation are run
synchronously here; in production they should be pushed onto Celery.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.client import get_ai_client
from app.core.config import settings
from app.core.exceptions import (
    FileTooLarge,
    NotAuthorized,
    NotFound,
    UnsupportedMediaType,
)
from app.db.session import SessionLocal, get_db
from app.middlewares.auth import CurrentUser
from app.models.document import Document, DocumentAnalysis
from app.models.enums import DocumentType, FileType
from app.schemas.documents import DocumentAnalysisResult, DocumentRead
from app.services.ocr_service import get_ocr_service

router = APIRouter()


class AttachToCaseRequest(BaseModel):
    case_id: uuid.UUID


_EXT_TO_FILE_TYPE = {
    "pdf": FileType.PDF,
    "docx": FileType.DOCX,
    "txt": FileType.TXT,
    "png": FileType.PNG,
    "jpg": FileType.JPG,
    "jpeg": FileType.JPG,
}


def _validate_and_classify(filename: str, size_bytes: int) -> FileType:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in _EXT_TO_FILE_TYPE:
        raise UnsupportedMediaType(
            message=f"Files of type .{ext} are not supported.",
            hint="Allowed: PDF, DOCX, TXT, PNG, JPG.",
        )
    max_bytes = settings.DOC_MAX_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLarge(
            message=f"File exceeds {settings.DOC_MAX_SIZE_MB} MB.",
            hint="Compress the document or split it into smaller files.",
        )
    return _EXT_TO_FILE_TYPE[ext]


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a legal document, run OCR, and persist metadata (UC-05)",
)
def upload_document(
    file: UploadFile = File(...),
    case_id: uuid.UUID | None = Form(default=None),
    document_type: DocumentType = Form(default=DocumentType.OTHER),
    user: CurrentUser = None,  # type: ignore[assignment]
    db: Session = Depends(get_db),
):
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Stream to disk while computing SHA-256 (Algorithm 3)
    storage_name = f"{uuid.uuid4().hex}_{file.filename}"
    storage_path = upload_dir / storage_name
    sha = hashlib.sha256()
    total = 0
    with storage_path.open("wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            sha.update(chunk)
            total += len(chunk)
            out.write(chunk)

    file_type = _validate_and_classify(file.filename or "", total)

    # OCR / text extraction
    ocr = get_ocr_service()
    extracted = ocr.extract(storage_path)

    doc = Document(
        case_id=case_id,
        uploaded_by_id=user.id,
        file_name=file.filename or storage_name,
        storage_path=str(storage_path),
        sha256_hash=sha.hexdigest(),
        file_type=file_type,
        file_size_bytes=total,
        document_type=document_type,
        extracted_text=extracted or None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return DocumentRead(
        id=doc.id,
        case_id=doc.case_id,
        filename=doc.file_name,
        document_type=doc.document_type,
        file_type=doc.file_type,
        size_bytes=doc.file_size_bytes,
        extracted_text=doc.extracted_text,
        summary=doc.summary_text,
        created_at=doc.created_at,
    )


@router.post(
    "/{document_id}/attach",
    response_model=DocumentRead,
    summary="Link an existing uploaded document to a case (lawyers only)",
)
def attach_to_case(
    document_id: uuid.UUID,
    payload: AttachToCaseRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    from app.services.case_service import CaseService
    doc = db.get(Document, document_id)
    if doc is None:
        raise NotFound("Document not found.")
    if doc.uploaded_by_id != user.id:
        raise NotAuthorized("You can only attach documents you uploaded.")

    # Reuse CaseService.get for the RBAC check (lawyer must own the case)
    case = CaseService(db).get(payload.case_id, user)
    doc.case_id = case.id
    db.commit()
    db.refresh(doc)

    return DocumentRead(
        id=doc.id,
        case_id=doc.case_id,
        filename=doc.file_name,
        document_type=doc.document_type,
        file_type=doc.file_type,
        size_bytes=doc.file_size_bytes,
        extracted_text=doc.extracted_text,
        summary=doc.summary_text,
        created_at=doc.created_at,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    summary="Fetch a single document's metadata + extracted text",
)
def get_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    doc = db.get(Document, document_id)
    if doc is None:
        raise NotFound("Document not found.")
    if doc.uploaded_by_id != user.id:
        # Lawyers can also view documents on their cases — simple check
        if not (doc.case and doc.case.assigned_lawyer_id == user.id):
            raise NotAuthorized("You do not have access to this document.")
    return DocumentRead(
        id=doc.id,
        case_id=doc.case_id,
        filename=doc.file_name,
        document_type=doc.document_type,
        file_type=doc.file_type,
        size_bytes=doc.file_size_bytes,
        extracted_text=doc.extracted_text,
        summary=doc.summary_text,
        created_at=doc.created_at,
    )


@router.post(
    "/{document_id}/analyze",
    response_model=DocumentAnalysisResult,
    summary="Run AI summarisation + clause/risk analysis on a document",
)
def analyze_document(
    document_id: uuid.UUID,
    user: CurrentUser,
    request_db: Session = Depends(get_db),
):
    """Split into three phases so no DB session is held open across the
    slow, synchronous call to the LLM. Supabase's connection pooler will
    kill an idle-in-transaction connection that sits open too long, which
    is exactly what a single long-lived session wrapping the LLM call risks
    turning into an intermittent 500 on this endpoint."""

    # The auth dependency loaded `user` through the request session, which
    # left a transaction open. Close it (the loaded user stays readable).
    request_db.close()

    # Phase 1 — short read: fetch the document, check access, get the text
    # to summarise. Session closes before we ever touch the network.
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            raise NotFound("Document not found.")
        if doc.uploaded_by_id != user.id and not (
            doc.case and doc.case.assigned_lawyer_id == user.id
        ):
            raise NotAuthorized("You do not have access to this document.")

        text = doc.extracted_text or ""
        if not text.strip():
            # Re-attempt extraction in case it was uploaded before OCR was
            # configured — local/fast, fine to do inside this session.
            text = get_ocr_service().extract(Path(doc.storage_path)) or ""
            doc.extracted_text = text
            db.commit()
        document_type = doc.document_type

    # Phase 2 — the slow part. No DB session held while this runs.
    ai = get_ai_client()
    summary_text = ai.summarise(text, hint=f"Document type: {document_type.value}")

    # Phase 3 — short write: persist the result in a fresh session.
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        analysis = doc.analysis or DocumentAnalysis(document_id=doc.id)
        analysis.summary = summary_text
        analysis.identified_clauses = {"raw": summary_text[:2000]}
        analysis.risk_flags = {}
        analysis.document_classification = doc.document_type.value
        if doc.analysis is None:
            db.add(analysis)
        doc.summary_text = summary_text
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()

    return DocumentAnalysisResult(
        document_id=document_id,
        summary=summary_text,
        key_clauses=[],
        parties=[],
        dates=[],
        risks=[],
    )
