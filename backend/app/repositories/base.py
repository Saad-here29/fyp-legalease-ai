"""Generic repository — common CRUD operations on any SQLAlchemy model.

Concrete repositories should inherit from this and add domain-specific
queries. Services NEVER write SQLAlchemy queries directly; they go through
a repository so query logic stays testable and swappable."""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id: UUID) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def get_or_404(self, entity_id: UUID) -> ModelT:
        from app.core.exceptions import NotFound

        instance = self.get(entity_id)
        if instance is None:
            raise NotFound(f"{self.model.__name__} not found.")
        return instance

    def list(self, *, offset: int = 0, limit: int = 20) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self.db.execute(select(func.count()).select_from(self.model)).scalar_one()

    def add(self, instance: ModelT) -> ModelT:
        self.db.add(instance)
        self.db.flush()
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()
