"""Database-agnostic column types.

Production runs on PostgreSQL where we want native UUID and JSONB. Unit tests
run on SQLite for speed, where those types fall back to Uuid (TEXT) and JSON.
The `with_variant` pattern lets a single column declaration adapt to both.
"""

from sqlalchemy import JSON, Uuid as _SAUuid
from sqlalchemy.dialects.postgresql import JSONB as _PGJSONB, UUID as _PGUUID

# Native UUID on PG; SQLAlchemy's portable Uuid type on SQLite.
UUIDType = _PGUUID(as_uuid=True).with_variant(_SAUuid(), "sqlite")

# JSONB on PG; plain JSON on SQLite.
JSONBType = _PGJSONB().with_variant(JSON(), "sqlite")
