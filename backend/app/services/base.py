"""Base service class — every service holds a DB session and exposes
write_audit/commit helpers. Concrete services should inherit from this
to keep cross-cutting concerns consistent."""

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.middlewares.audit import write_audit


class BaseService:
    def __init__(self, db: Session, request: Request | None = None):
        self.db = db
        self.request = request

    def commit(self) -> None:
        self.db.commit()

    def audit(
        self,
        action: str,
        *,
        user_id: uuid.UUID | None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
    ) -> None:
        write_audit(
            self.db,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            request=self.request,
        )
