"""Student role-profile table.

Split into its own module because services/auth_service.py does
`from app.models.student import Student` — moved out of user.py where it was
originally (incorrectly) defined alongside User.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import UUIDType


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), unique=True, nullable=False
    )
    university_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    university_name: Mapped[str] = mapped_column(String(150), nullable=False)
    current_year: Mapped[int] = mapped_column(Integer, nullable=False)
