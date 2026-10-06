"""Scraping prototype tables (branch "scraping"; migration a3c5e7f90b12).

scraped_documents  one row per version of a document fetched from a source.
                   A changed document gets a new row; the old one stays with
                   is_latest = false. Nothing here is searchable or shown in
                   the UI: rows are "staged" until a person approves them.
scrape_runs        one row per run, with per-source counts.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBType, UUIDType

STATUSES = ("staged", "approved", "rejected")


class ScrapedDocument(Base):
    __tablename__ = "scraped_documents"
    __table_args__ = (Index("ix_scraped_documents_url_latest", "source_url", "is_latest"),)

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)   # statute / judgment
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # staged / approved / rejected. A statute already in the index (matched by
    # title) is stored as its baseline with status "approved".
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="staged")
    change_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)  # new / changed / baseline
    in_corpus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pages_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    changed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # {source name: {"checked", "new", "changed", "unchanged", "errors", "status"}}
    per_source: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
