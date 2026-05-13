"""SQLAlchemy engine and session factory.

Use `get_db` as a FastAPI dependency to obtain a session that closes after
the request finishes:

    from fastapi import Depends
    from sqlalchemy.orm import Session
    from app.db.session import get_db

    @router.get("/cases")
    def list_cases(db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# SQLite needs a different pool configuration than Postgres — it doesn't
# support pool_size/max_overflow, and it needs check_same_thread=False so
# FastAPI's request threads can share the connection.
_engine_kwargs: dict = {"echo": settings.DATABASE_ECHO}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_pre_ping=True, pool_size=10, max_overflow=20)

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
