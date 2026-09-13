"""Lawyer role-profile table.

Split into its own module because services/auth_service.py does
`from app.models.lawyer import Lawyer` — moved out of user.py where it was
originally (incorrectly) defined alongside User.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import UUIDType


class Lawyer(Base, TimestampMixin):
    __tablename__ = "lawyers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), unique=True, nullable=False
    )
    bar_license_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    specialization: Mapped[str] = mapped_column(String(120), nullable=False)
    bar_year: Mapped[int] = mapped_column(Integer, nullable=False)
    bar_council: Mapped[str | None] = mapped_column(String(120), nullable=True)
