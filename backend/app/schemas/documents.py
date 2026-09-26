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


class NamedEntity(APIModel):
    text: str
    count: int
    score: float


class DocumentAnalysisResult(APIModel):
    """Two sources, kept distinct:
    - NER model (fine-tuned on Pakistani court judgments): `parties`,
      `dates`, `references`, `entities`. Empty when `ner_available` is false.
    - LLM summary: `summary`, plus `key_clauses` / `risks` parsed from its
      numbered sections (`clauses_and_risks_source` says so)."""

    document_id: uuid.UUID
    summary: str
    key_clauses: list[str]
    parties: list[str]
    dates: list[str]
    risks: list[str]
    references: list[str] = []
    entities: dict[str, list[NamedEntity]] = {}
    ner_available: bool = False
    entities_source: str = "ner_model"
    clauses_and_risks_source: str = "llm_summary"
