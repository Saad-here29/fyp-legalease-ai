"""Document analysis + OCR request/response schemas."""

import uuid
from datetime import datetime

from app.models.enums import DocumentType, FileType
from app.schemas.common import APIModel


class DocumentRead(APIModel):
    id: uuid.UUID
    case_id: uuid.UUID | None
    filename: str
    document_type: DocumentType
    file_type: FileType
    size_bytes: int
    extracted_text: str | None
    summary: str | None
    created_at: datetime


class DocumentAnalysisResult(APIModel):
    document_id: uuid.UUID
    summary: str
    key_clauses: list[str]
    parties: list[str]
    dates: list[str]
    risks: list[str]
