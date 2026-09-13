"""Reference corpus table — seeded Pakistani statutes + judgments.

Reconstructed from ai/seed_corpus.py, api/v1/research.py and schemas/research.py.
`document_type` here is a plain string ("statute"/"judgment"), unrelated to the
DocumentType enum used for uploaded case documents — same English word, two
different concepts. No embedding column: this implementation stores vectors
only in the external FAISS index file, never in Postgres (docs/database-schema.md
describes an `embedding_vector` column that was never actually implemented —
see the reconstruction plan for this divergence).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UUIDType


class LegalCorpusEntry(Base):
    __tablename__ = "legal_corpus"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    section_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False)
    # "statute" | "judgment" — free-form string, not an enum (see module docstring).
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    court: Mapped[str | None] = mapped_column(String(150), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Write-only today (set by the seed/corpus-builder, never read back by any
    # route) — kept for corpus-builder chunk bookkeeping.
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Read by the research API and present in ResearchEntryDetail, but never
    # populated by seed_corpus.py — always NULL on seeded rows.
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
