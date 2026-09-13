"""Audit trail table — every privileged action, per SEC-04.

Reconstructed from middlewares/audit.py (write_audit) and every call site in
services/*.py. Matches docs/database-schema.md field-for-field — the
highest-confidence model in this reconstruction. No `updated_at`: audit rows
are write-once and never mutated.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBType, UUIDType


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    # Nullable: pre-auth failures (e.g. LOGIN_FAILED_NO_USER) log with no user.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, nullable=True)
    old_values: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
