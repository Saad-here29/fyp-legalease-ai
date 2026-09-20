"""Contract Drafting & Compliance tables.

Contract holds one row per drafted contract; every draft/redraft creates a
new ContractVersion rather than overwriting the last one, so version
history is just "list ContractVersion rows for this contract_id". Compliance
results are stored directly on the ContractVersion they were checked
against — no separate check-history table (checks are deterministic and
cheap to rerun; see the module design note for the reasoning).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import JSONBType, UUIDType
from app.models.enums import ContractType, values_callable


class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("cases.id"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    contract_type: Mapped[ContractType] = mapped_column(
        Enum(ContractType, name="contract_type", values_callable=values_callable),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # The filled-in field values submitted at draft time (disclosing_party,
    # effective_date, ...) — kept so a redraft can reuse/adjust them.
    fields: Mapped[dict] = mapped_column(JSONBType, nullable=False)

    versions: Mapped[list["ContractVersion"]] = relationship(
        back_populates="contract", order_by="ContractVersion.version_number"
    )


class ContractVersion(Base):
    __tablename__ = "contract_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("contracts.id"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Result of the last deterministic compliance check run against this
    # version's content — {"all_passed": bool, "results": [...]}. Null until
    # a check has been run at least once.
    compliance_result: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    # Immutable row (a redraft creates a new version, never edits one in
    # place) — no updated_at, same reasoning as ActivityLog/ChatMessage.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    contract: Mapped["Contract"] = relationship(back_populates="versions")
