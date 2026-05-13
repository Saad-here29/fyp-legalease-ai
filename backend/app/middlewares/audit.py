"""Audit log writer — SEC-04 requires every privileged action to be logged.

Use as a callable from services after a write operation succeeds:

    from app.middlewares.audit import write_audit

    write_audit(
        db, user_id=user.id, action="LOGIN_OK", request=request,
    )

The function never raises — audit failure should not break the user-facing
operation. Failures are surfaced through the logger only.
"""

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.audit import ActivityLog


def write_audit(
    db: Session,
    *,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=_extract_ip(request),
            user_agent=_extract_user_agent(request),
        )
        db.add(log)
        db.flush()
    except Exception as e:  # never break the caller's flow
        logger.exception(f"Audit write failed for action={action}: {e}")


def _extract_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _extract_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")
