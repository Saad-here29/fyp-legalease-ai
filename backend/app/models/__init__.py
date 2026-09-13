"""Import every model module so Base.metadata sees all tables.

`app/main.py` does `import app.models` on startup purely for this
side effect — see the noqa comment there.
"""

from app.models import audit  # noqa: F401
from app.models import case  # noqa: F401
from app.models import chat  # noqa: F401
from app.models import client  # noqa: F401
from app.models import document  # noqa: F401
from app.models import enums  # noqa: F401
from app.models import lawyer  # noqa: F401
from app.models import legal_corpus  # noqa: F401
from app.models import student  # noqa: F401
from app.models import user  # noqa: F401

__all__ = [
    "audit",
    "case",
    "chat",
    "client",
    "document",
    "enums",
    "lawyer",
    "legal_corpus",
    "student",
    "user",
]
