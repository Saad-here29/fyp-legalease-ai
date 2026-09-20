"""Shared enum types used across ORM models and Pydantic schemas.

Every value here is backed by actual usage evidence in the codebase (routers,
services, tests) at the time this module was reconstructed — see
C:\\Users\\Saadullah\\.claude\\plans\\read-project-context-md-fully-before-peppy-kettle.md
for the audit trail. CaseType and DocumentType are known-incomplete: only the
values exercised by existing code/tests are listed.
"""

import enum


def values_callable(enum_cls: type[enum.Enum]) -> list[str]:
    """Passed to every SQLAlchemy Enum(...) column so the DB stores the
    member's lowercase `.value` (e.g. "lawyer") instead of SQLAlchemy's
    default of the member's `.name` (e.g. "LAWYER")."""
    return [member.value for member in enum_cls]


class UserRole(str, enum.Enum):
    LAWYER = "lawyer"
    CLIENT = "client"
    STUDENT = "student"


class CaseStatus(str, enum.Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    HEARING_SCHEDULED = "hearing_scheduled"
    CLOSED = "closed"


class CaseType(str, enum.Enum):
    CUSTODY = "custody"
    INHERITANCE = "inheritance"
    DIVORCE = "divorce"
    MAINTENANCE = "maintenance"


class RoleInCase(str, enum.Enum):
    LAWYER = "lawyer"
    CLIENT = "client"
    WITNESS = "witness"
    JUDGE = "judge"


class DocumentType(str, enum.Enum):
    OTHER = "other"


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    PNG = "png"
    JPG = "jpg"


class SenderType(str, enum.Enum):
    USER = "user"
    AI = "ai"


class ContractType(str, enum.Enum):
    NDA = "nda"
    EMPLOYMENT = "employment"
    SERVICE_AGREEMENT = "service_agreement"
