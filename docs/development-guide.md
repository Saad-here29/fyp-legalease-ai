# Development Guide

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (for Postgres + Redis) OR local Postgres 16 + Redis 7
- Tesseract OCR (Windows: https://github.com/UB-Mannheim/tesseract/wiki)

## First-Time Setup

### 1. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL on `localhost:5432` and Redis on `localhost:6379`.

### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set OPENAI_API_KEY and TESSERACT_CMD
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs on http://localhost:8000  
API docs at http://localhost:8000/docs (in dev mode)

### 3. Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs on http://localhost:5173

### 4. Celery Worker (for OCR + notifications)

```powershell
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

`--pool=solo` is required on Windows.

## Daily Development

```powershell
# Backend live reload
uvicorn app.main:app --reload

# Run backend tests
pytest

# Run frontend tests
cd frontend
npm test

# Lint backend
ruff check app/
black --check app/

# Lint frontend
npm run lint
npm run format
```

## Coding Standards

- **Backend:** PEP 8 via Black + Ruff. Type hints everywhere. Pydantic for I/O.
- **Frontend:** ESLint + Prettier. JSDoc comments where types help. No console.log.
- **Naming:** PascalCase for components/classes, camelCase for functions, snake_case for Python and DB.
- **Commits:** Conventional commits (`feat(auth): ...`, `fix(api): ...`).

## Git Workflow

```
main         <- production-ready
develop      <- integration branch
feature/*    <- new features
fix/*        <- bug fixes
hotfix/*     <- urgent production fixes
```

- PRs go from `feature/*` → `develop`
- Releases merge `develop` → `main` and tag a version

## Testing

All four core service modules must have unit tests passing the documented
acceptance criteria from the Final Report:

- Authentication Service (UT-AUTH-001/002/003)
- Case Management Service (UT-CASE-001/002/003)
- Document Service (UT-DOC-xxx)
- AI Legal Chat Service (UT-CHAT-xxx)

Run before pushing:

```bash
pytest --cov=app --cov-report=term-missing
```
