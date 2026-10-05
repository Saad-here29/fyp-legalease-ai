"""Document upload + AI analysis router — /documents/* endpoints.

Implements UC-05 (Upload and Analyse Legal Document) and Algorithm 3
(Stream-and-Commit Document Upload). OCR + AI summarisation are run
synchronously here; in production they should be pushed onto Celery.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import ner
from app.ai.client import get_ai_client
from app.ai.summary_sections import extract_clauses_and_risks
from app.core.config import settings
from app.core.exceptions import (
    FileTooLarge,
    NotAuthorized,
    NotFound,
    UnsupportedMediaType,
    ValidationFailed,
)
from app.core.logging import logger
from app.db.session import SessionLocal, get_db
from app.middlewares.auth import CurrentUser
from app.models.document import Document, DocumentAnalysis
from app.models.enums import DocumentType, FileType
from app.schemas.documents import DocumentAnalysisResult, DocumentRead, UploadCapabilities
from app.services.ocr_service import get_ocr_service, ocr_available

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


# Longest display name the documents.file_name column holds.
_MAX_NAME = 255
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _display_name(raw: str | None) -> str:
    """The client's filename, made safe to store and show: only its last
    path component (split on / and \ whatever the server OS), no control
    characters or null bytes, at most 255 characters with the extension
    kept. It is never used to build a path; see _storage_path()."""
    name = _CONTROL.sub("", raw or "")
    name = re.split(r"[\\/]", name)[-1].strip().strip(".")
    if not name:
        return "upload"
    if len(name) > _MAX_NAME:
        stem, dot, ext = name.rpartition(".")
        ext = ext if dot and 0 < len(ext) <= 10 else ""
        name = (stem if ext else name)[: _MAX_NAME - len(ext) - (1 if ext else 0)] + ("." + ext if ext else "")
    return name


def _storage_path(upload_dir: Path, ext: str) -> Path:
    """A generated name inside upload_dir: 32 hex characters plus the
    validated extension. No part of the client's filename reaches the
    path, so "../", "..\\", absolute paths or drive letters can't steer
    the write (Oct 2026 audit: "../../x.txt" escaped its folder)."""
    path = (upload_dir / f"{uuid.uuid4().hex}.{ext}").resolve()
    if path.parent != upload_dir.resolve():
        raise ValidationFailed("Invalid upload path.")
    return path


def _classify(filename: str) -> tuple[FileType, str]:
    """File type and extension from the (display) name, checked before
    anything is written to disk."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in _EXT_TO_FILE_TYPE:
        raise UnsupportedMediaType(
            message=f"Files of type .{ext} are not supported." if ext else "Files without an extension are not supported.",
            hint="Allowed: PDF, DOCX, TXT, PNG, JPG.",
        )
    return _EXT_TO_FILE_TYPE[ext], ext


def _too_large() -> FileTooLarge:
    return FileTooLarge(
        message=f"File exceeds {settings.DOC_MAX_SIZE_MB} MB.",
        hint="Compress the document or split it into smaller files.",
    )


def _extraction_warning(file_type: FileType, text: str | None) -> str | None:
    """Why an upload produced no text, or None if it produced some."""
    if text and text.strip():
        return None
    if file_type in (FileType.PNG, FileType.JPG) and not ocr_available():
        return ("No text could be read from this image: text recognition (OCR) "
                "is not installed on this server. Upload a PDF, DOCX or TXT instead.")
    if file_type == FileType.PDF and not ocr_available():
        return ("No text could be read: this PDF appears to be scanned, and text "
                "recognition (OCR) is not installed on this server. Upload a PDF "
                "with selectable text, or a DOCX or TXT.")
    return "No text could be extracted from this file, so it cannot be analysed."


@router.get(
    "/capabilities",
    response_model=UploadCapabilities,
    summary="Which file types can have their text extracted on this server",
)
def upload_capabilities(user: CurrentUser):
    ocr = ocr_available()
    return UploadCapabilities(
        ocr_available=ocr,
        accepted_types=["PDF", "DOCX", "TXT"] + (["PNG", "JPG"] if ocr else []),
    )


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

    display_name = _display_name(file.filename)
    # Type first: an unsupported file is refused before a byte is written
    # (Oct 2026 quality pass, R2: rejected uploads used to stay on disk).
    file_type, ext = _classify(display_name)
    max_bytes = settings.DOC_MAX_SIZE_MB * 1024 * 1024

    # Stream to disk while computing SHA-256 (Algorithm 3). Stop as soon as
    # the size limit is passed, and remove the file if anything below fails
    # — the size check, text extraction or the database write — so only
    # files with a document row are kept.
    storage_path = _storage_path(upload_dir, ext)
    sha = hashlib.sha256()
    total = 0
    try:
        with storage_path.open("wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise _too_large()
                sha.update(chunk)
                out.write(chunk)

        # OCR / text extraction
        ocr = get_ocr_service()
        extracted = ocr.extract(storage_path)

        doc = Document(
            case_id=case_id,
            uploaded_by_id=user.id,
            file_name=display_name,
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
    except BaseException:
        storage_path.unlink(missing_ok=True)
        raise

    warning = _extraction_warning(file_type, extracted)
    if warning:
        logger.info(f"Upload {doc.id} ({file_type.value}): no text extracted")

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
        extraction_warning=warning,
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


# NER entity types surfaced in the flat response lists (all kept types
# are also returned grouped in `entities`).
_PARTY_TYPES = ("per", "org", "resp")
_REFERENCE_TYPES = ("caseno", "appealcaseno", "refcase", "ref", "refcourt", "appealcourt")


@router.post(
    "/{document_id}/analyze",
    response_model=DocumentAnalysisResult,
    summary="LLM summary + clauses/risks, and legal NER (parties, dates, references)",
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
        # Nothing to analyse (e.g. a scanned file with OCR unavailable):
        # refuse before any model call, rather than have the LLM "summarise"
        # an empty document and spend tokens on a meaningless reply.
        if not text.strip():
            raise ValidationFailed(
                message="This document has no extractable text to analyse.",
                hint="It may be a scanned or image-only file; OCR needs Tesseract and "
                "Poppler installed on the server. Upload a text-based PDF, DOCX or TXT.",
            )
        document_type = doc.document_type

    # Phase 2 — the slow part. No DB session held while this runs. The NER
    # model (CPU) and the LLM summary (network) are independent, so NER runs
    # in a worker thread while the LLM call is in flight.
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="ner") as pool:
        ner_future = pool.submit(ner.extract_entities, text)
        ai = get_ai_client()
        summary_text = ai.summarise(text, hint=f"Document type: {document_type.value}")
        try:
            ner_result = ner_future.result()
        except Exception as e:  # noqa: BLE001 — NER must never sink the summary
            logger.warning(f"NER failed on document {document_id}: {type(e).__name__}: {e}")
            ner_result = ner.NerResult(available=False)

    key_clauses, risks = extract_clauses_and_risks(summary_text)
    parties = [e.text for e in sorted(ner_result.by_type(*_PARTY_TYPES),
                                      key=lambda e: -e.count)]
    dates = [e.text for e in ner_result.by_type("date")]
    references = [e.text for e in ner_result.by_type(*_REFERENCE_TYPES)]
    entities = ner_result.as_json()

    # Phase 3 — short write: persist the result in a fresh session.
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        analysis = doc.analysis or DocumentAnalysis(document_id=doc.id)
        analysis.summary = summary_text
        analysis.identified_clauses = {"source": "llm_summary", "items": key_clauses}
        analysis.risk_flags = {"source": "llm_summary", "items": risks}
        analysis.extracted_entities = entities if ner_result.available else None
        analysis.document_classification = doc.document_type.value
        if doc.analysis is None:
            db.add(analysis)
        doc.summary_text = summary_text
        doc.updated_at = datetime.now(UTC)
        db.commit()

    return DocumentAnalysisResult(
        document_id=document_id,
        summary=summary_text,
        key_clauses=key_clauses,
        parties=parties,
        dates=dates,
        risks=risks,
        references=references,
        entities=entities,
        ner_available=ner_result.available,
    )
