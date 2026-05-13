"""Role-Based Access Control dependency.

Usage:

    from app.middlewares.rbac import require_role
    from app.models.enums import UserRole

    @router.post(
        "/cases",
        dependencies=[Depends(require_role(UserRole.LAWYER))],
    )
    def create_case(...):
        ...

The dependency returns the authenticated user when the role matches and
raises HTTP 403 (NotAuthorized) otherwise. SEC-03 — RBAC on every protected
endpoint.
"""

from typing import Callable

from fastapi import Depends

from app.core.exceptions import NotAuthorized
from app.middlewares.auth import get_current_user
from app.models.enums import UserRole
from app.models.user import User


def require_role(*allowed_roles: UserRole) -> Callable:
    if not allowed_roles:
        raise ValueError("require_role needs at least one role")

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise NotAuthorized(
                "You don't have permission to perform this action.",
            )
        return user

    return _dep


# Convenience aliases
require_lawyer = require_role(UserRole.LAWYER)
require_client = require_role(UserRole.CLIENT)
require_student = require_role(UserRole.STUDENT)
require_lawyer_or_student = require_role(UserRole.LAWYER, UserRole.STUDENT)
