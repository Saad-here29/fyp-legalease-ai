"""Import every model module so Base.metadata sees all tables.

`app/main.py` does `import app.models` on startup purely for this
side effect — see the noqa comment there.
"""

from app.models import (
    audit,  # noqa: F401
    case,  # noqa: F401
    chat,  # noqa: F401
    client,  # noqa: F401
    contract,  # noqa: F401
    document,  # noqa: F401
    enums,  # noqa: F401
    lawyer,  # noqa: F401
    legal_corpus,  # noqa: F401
    student,  # noqa: F401
    user,  # noqa: F401
)

__all__ = [
    "audit",
    "case",
    "chat",
    "client",
    "contract",
    "document",
    "enums",
    "lawyer",
    "legal_corpus",
    "student",
    "user",
]
