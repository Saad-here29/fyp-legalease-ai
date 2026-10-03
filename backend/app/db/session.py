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

import time
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.exceptions import DatabaseUnavailable
from app.core.logging import logger


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


RETRY_DELAY_SECONDS = 0.5


def is_connection_error(exc: BaseException) -> bool:
    """A lost or refused database connection, as opposed to a bad query or
    a constraint violation."""
    return isinstance(exc, OperationalError | InterfaceError) or (
        isinstance(exc, DBAPIError) and exc.connection_invalidated
    )


def open_session() -> Session:
    """A session holding a live connection. The Supabase pooler sometimes
    drops or refuses a connection; retry once, then give up with a 503."""
    for attempt in (1, 2):
        db = SessionLocal()
        try:
            db.connection()  # check out now (pool_pre_ping validates it)
            return db
        except DBAPIError as e:
            db.close()
            if not is_connection_error(e):
                raise
            if attempt == 2:
                logger.error(f"Database connection failed twice: {e.__class__.__name__}: {e.orig}")
                raise DatabaseUnavailable() from e
            logger.warning(f"Database connection failed, retrying once: {e.__class__.__name__}: {e.orig}")
            time.sleep(RETRY_DELAY_SECONDS)
    raise AssertionError("unreachable")


def get_db() -> Generator[Session, None, None]:
    db = open_session()
    try:
        yield db
    finally:
        db.close()
