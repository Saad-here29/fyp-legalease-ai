"""Client role-profile table.

Split into its own module because services/auth_service.py does
`from app.models.client import Client` — moved out of user.py where it was
originally (incorrectly) defined alongside User.
"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import UUIDType


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), unique=True, nullable=False
    )
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Nullable + unique: Postgres allows multiple NULLs in a unique index, so
    # clients who didn't supply a CNIC at signup don't collide with each other.
    cnic: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
