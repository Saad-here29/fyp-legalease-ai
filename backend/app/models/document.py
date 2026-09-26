"""Uploaded document + AI analysis tables.

Reconstructed from api/v1/documents.py and schemas/documents.py. Note the
deliberate name mismatch: the ORM column is `summary_text`, the API schema
field is `summary` (DocumentRead maps one to the other explicitly).
"""

import uuid
from typing import Optional

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import JSONBType, UUIDType
from app.models.enums import DocumentType, FileType, values_callable


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    # Nullable: a document can be uploaded stand-alone and attached to a case
    # later via POST /documents/{id}/attach.
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("cases.id"), nullable=True
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="file_type", values_callable=values_callable), nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", values_callable=values_callable),
        default=DocumentType.OTHER,
        nullable=False,
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped[Optional["Case"]] = relationship(back_populates="documents")  # noqa: F821
    analysis: Mapped[Optional["DocumentAnalysis"]] = relationship(
        back_populates="document", uselist=False
    )


class DocumentAnalysis(Base, TimestampMixin):
    __tablename__ = "document_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("documents.id"), unique=True, nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    identified_clauses: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    risk_flags: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    # Legal NER output grouped by entity type: {type: [{text, count, score}]}
    extracted_entities: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    document_classification: Mapped[str | None] = mapped_column(String(50), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="analysis")
