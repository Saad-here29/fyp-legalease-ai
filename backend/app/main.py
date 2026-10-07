"""FastAPI application entry point — wires routes, middleware, exception handlers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

import app.models  # noqa: F401  — registers every ORM class with Base.metadata
from app.core.config import settings
from app.core.exceptions import AppException, DatabaseUnavailable
from app.core.logging import configure_logging, logger
from app.db.base import Base
from app.db.session import engine, is_connection_error


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger.info(f"Starting {settings.APP_NAME} (env={settings.APP_ENV})")
    mode = run_mode()
    logger.info(
        f"Search mode: KB_V2={mode['kb_v2']} | v1 index {settings.FAISS_INDEX_PATH} "
        f"({mode['v1_index_chunks']} chunks) | v2 index "
        f"{settings.KB_V2_INDEX_PATH + ' (' + str(mode['v2_index_chunks']) + ' chunks)' if settings.KB_V2 else 'off'} "
        f"| threshold {mode['threshold']}"
    )

    # Auto-create tables on startup when running on SQLite (demo mode).
    # Production Postgres uses Alembic migrations and skips this branch.
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite schema ensured via create_all")


    # Legal NER model for Document Analysis (~13 s on CPU): load in a
    # background thread so startup isn't blocked; an analyze request that
    # arrives first waits on the loader's lock instead of failing.
    from app.ai import ner
    ner.start_background_load()

    # Family-law side index (only when FAMILY_INDEX is on): same idea.
    from app.ai import family_index
    family_index.start_background_load()

    # Judgments (only when JUDGMENTS_V2 is on): read the index and the
    # records list in the background so the first search doesn't wait.
    if settings.JUDGMENTS_V2:
        import threading

        from app.kb import judgment_catalog, judgment_search

        def _warm() -> None:
            try:
                logger.info(f"Judgments: {judgment_search.status()} | index {judgment_search.paths()[0]}")
                judgment_catalog.load()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Judgments warm-up failed: {e}")
        threading.Thread(target=_warm, name="judgments-warm", daemon=True).start()

    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-Powered Online Lawyer Management and Legal Assistance Platform",
    lifespan=lifespan,
    # API docs and the schema behind them are for development only; APP_DEBUG
    # alone used to expose them wherever it was left on.
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "hint": exc.hint}},
    )


def _field_name(loc) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "form")]
    return ".".join(parts).replace("_", " ") or "request"


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, exc: RequestValidationError):
    # FastAPI's own 422s had only Pydantic's "detail" list, so the UI could
    # show no message or hint (USE-04). Same shape as every other error now;
    # "detail" is kept for API clients that read it.
    errors = exc.errors()
    first = errors[0] if errors else {}
    message = f"{_field_name(first.get('loc', ()))}: {first.get('msg', 'invalid value')}"
    if len(errors) > 1:
        message += f" (and {len(errors) - 1} more)"
    return JSONResponse(
        status_code=422,
        content={
            "error": {"code": "validation_error", "message": message,
                      "hint": "Correct the highlighted field and try again."},
            "detail": jsonable_encoder(errors),
        },
    )


@app.exception_handler(DBAPIError)
async def db_error_handler(request, exc: DBAPIError):
    # A connection dropped mid-request: a clear 503 instead of a raw 500.
    # Anything else (bad SQL, constraint violations) stays a 500.
    if not is_connection_error(exc):
        raise exc
    logger.error(f"Database connection lost during {request.method} {request.url.path}: {exc.orig}")
    return await app_exception_handler(request, DatabaseUnavailable())


@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "env": settings.APP_ENV,
        "status": "running",
    }


def _faiss_ntotal(path: str) -> int | None:
    """Vectors in a saved flat FAISS index, read from its header (bytes 8-16)
    without loading the index; None if the file is missing or not flat."""
    import struct
    from pathlib import Path
    p = Path(path)
    try:
        with p.open("rb") as f:
            head = f.read(16)
    except OSError:
        return None
    if len(head) < 16 or not head.startswith(b"IxF"):
        return None
    return struct.unpack("<q", head[8:16])[0]


def run_mode() -> dict:
    """Which search mode this server runs in (see docs/DEMO_RUNBOOK.md)."""
    return {
        "kb_v2": settings.KB_V2,
        "v1_index_chunks": _faiss_ntotal(settings.FAISS_INDEX_PATH),
        "v2_index_chunks": _faiss_ntotal(settings.KB_V2_INDEX_PATH) if settings.KB_V2 else None,
        "threshold": settings.KB_V2_THRESHOLD if settings.KB_V2 else settings.RAG_SIMILARITY_THRESHOLD,
        "judgments_v2": settings.JUDGMENTS_V2,
        **_judgments_status(),
        "scraped_v2": settings.SCRAPED_V2,
        **_scraped_status(),
    }


def _scraped_status() -> dict:
    """Chunks in faiss_scraped and faiss_scraped_judgments (None when
    SCRAPED_V2 is off; 0 while an index is missing or being written)."""
    from app.kb import scraped
    try:
        return scraped.status()
    except Exception as e:  # noqa: BLE001 — /health must never fail
        logger.warning(f"Scraped status unavailable: {e}")
        return {"scraped_chunks": 0, "scraped_judgment_chunks": 0}


def _judgments_status() -> dict:
    """Chunks and judgments in the judgments index being searched (None when
    JUDGMENTS_V2 is off; 0 while the index is missing or still being written)."""
    from app.kb import judgment_search
    try:
        return judgment_search.status()
    except Exception as e:  # noqa: BLE001 — /health must never fail
        logger.warning(f"Judgments status unavailable: {e}")
        return {"judgment_chunks": 0, "judgments": 0}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", **run_mode()}


from app.api.v1 import auth as auth_router
from app.api.v1 import cases as cases_router
from app.api.v1 import chat as chat_router
from app.api.v1 import contracts as contracts_router
from app.api.v1 import documents as documents_router
from app.api.v1 import kb as kb_router
from app.api.v1 import research as research_router

app.include_router(
    auth_router.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["auth"],
)
app.include_router(
    cases_router.router,
    prefix=f"{settings.API_V1_PREFIX}/cases",
    tags=["cases"],
)
app.include_router(
    chat_router.router,
    prefix=f"{settings.API_V1_PREFIX}/chat",
    tags=["chat"],
)
app.include_router(
    research_router.router,
    prefix=f"{settings.API_V1_PREFIX}/research",
    tags=["research"],
)
app.include_router(
    documents_router.router,
    prefix=f"{settings.API_V1_PREFIX}/documents",
    tags=["documents"],
)
app.include_router(
    kb_router.router,
    prefix=f"{settings.API_V1_PREFIX}/kb",
    tags=["knowledge base"],
)
app.include_router(
    contracts_router.router,
    prefix=f"{settings.API_V1_PREFIX}/contracts",
    tags=["contracts"],
)
