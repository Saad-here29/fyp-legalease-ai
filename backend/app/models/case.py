"""Case + case-participant tables.

Reconstructed from services/case_service.py, api/v1/cases.py, and
schemas/cases.py. State machine lives in CaseService, not here — this module
only defines storage.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import UUIDType
from app.models.enums import CaseStatus, CaseType, RoleInCase, values_callable


class Case(Base, TimestampMixin):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    case_type: Mapped[CaseType] = mapped_column(
        Enum(CaseType, name="case_type", values_callable=values_callable), nullable=False
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status", values_callable=values_callable),
        default=CaseStatus.CREATED,
        nullable=False,
    )
    court_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_lawyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True
    )

    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="case"
    )
    participants: Mapped[list["CaseParticipant"]] = relationship(
        back_populates="case"
    )


class CaseParticipant(Base, TimestampMixin):
    __tablename__ = "case_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("cases.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    role_in_case: Mapped[RoleInCase] = mapped_column(
        Enum(RoleInCase, name="role_in_case", values_callable=values_callable), nullable=False
    )

    case: Mapped["Case"] = relationship(back_populates="participants")
