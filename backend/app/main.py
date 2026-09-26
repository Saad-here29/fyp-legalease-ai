"""FastAPI application entry point — wires routes, middleware, exception handlers."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.exceptions import AppException
from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.models  # noqa: F401  — registers every ORM class with Base.metadata


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    logger.info(f"Starting {settings.APP_NAME} (env={settings.APP_ENV})")

    # Auto-create tables on startup when running on SQLite (demo mode).
    # Production Postgres uses Alembic migrations and skips this branch.
    if settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite schema ensured via create_all")

    # Seed the legal corpus reference data if empty (Pakistani statutes +
    # landmark judgments). Idempotent — skips if rows already exist.
    try:
        from app.ai.seed_corpus import seed_legal_corpus
        with SessionLocal() as db:
            added = seed_legal_corpus(db)
            if added:
                logger.info(f"Seeded {added} legal corpus entries")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Corpus seed skipped: {e}")

    # Legal NER model for Document Analysis (~13 s on CPU): load in a
    # background thread so startup isn't blocked; an analyze request that
    # arrives first waits on the loader's lock instead of failing.
    from app.ai import ner
    ner.start_background_load()

    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="AI-Powered Online Lawyer Management and Legal Assistance Platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
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


@app.get("/", tags=["health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "env": settings.APP_ENV,
        "status": "running",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


from app.api.v1 import auth as auth_router
from app.api.v1 import cases as cases_router
from app.api.v1 import chat as chat_router
from app.api.v1 import contracts as contracts_router
from app.api.v1 import documents as documents_router
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
    contracts_router.router,
    prefix=f"{settings.API_V1_PREFIX}/contracts",
    tags=["contracts"],
)
