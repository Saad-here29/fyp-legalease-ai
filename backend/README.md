# Backend

FastAPI service for LegalEase AI. It covers auth, cases, chat, research,
documents and contracts. Setup and run steps are in the root
[`README.md`](../README.md); architecture is in
[`docs/architecture/system-overview.md`](../docs/architecture/system-overview.md).

## Install

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt     # requirements.txt alone for production
copy .env.example .env
alembic upgrade head
```

- **`requirements.txt`** holds the runtime dependencies, all pinned. PyTorch
  comes from the CPU index declared at the top of the file.
- **`requirements-dev.txt`** adds pytest, httpx (for FastAPI's TestClient),
  faker, ruff, black, mypy, and `requests` for `scripts/`.

## Settings (`.env`)

Every setting in `app/core/config.py` is listed, with defaults, in
`.env.example`. The ones you must set:

| Setting | What |
|---|---|
| `DATABASE_URL` | PostgreSQL URL (Supabase in development) |
| `SECRET_KEY` | JWT signing key: long and random |
| `GROQ_API_KEY` | Groq key; `GROQ_MODEL=openai/gpt-oss-120b` |
| `APP_ENV` | `development` turns on `/docs` and non-Secure cookies; anything else is production |

Optional:
- `OPENAI_*` / `GEMINI_*`: fallback AI providers.
- `SMTP_*`: real OTP emails; otherwise codes are logged as `[DEV OTP]`.
- `TESSERACT_CMD`: path to `tesseract.exe`, for scanned PDFs and images
  (English + Urdu data needed; Poppler isn't).
- `NER_ENABLED`: `false` runs document analysis without the NER model.

## Files this needs that aren't in git

| Path | What | How to get it |
|---|---|---|
| `storage/faiss/legal_corpus.faiss` + `legal_corpus_meta.json` | The statute search index (53,739 passages, about 83 MB + 49 MB) | From the team, or rebuild (`../ai-services/README.md`) |
| `storage/models/legal_ner/` | Fine-tuned DistilBERT legal NER model (about 520 MB) | From the team, or retrain with the Colab notebook |
| `uploads/` | Uploaded documents, stored under generated names | Created on first upload |

## Run

```powershell
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
uvicorn app.main:app --port 8000
```

Run it in its own terminal window. API docs are at
`http://localhost:8000/docs` in development.

## Test and lint

```powershell
pytest            # 213 tests: in-memory SQLite, no AI calls (model code is stubbed)
ruff check app
```

- **Shared fixtures:** `app/tests/conftest.py` has the database and `client`
  fixtures.
- **Unit tests:** in `app/tests/unit/`.
- **HTTP tests:** some unit-folder tests go through FastAPI's TestClient.
  The two top-level files (`test_health.py`, `test_api_docs.py`) are HTTP
  tests too.

## Layout

| Folder | Holds |
|---|---|
| `app/api/v1/` | Routers |
| `app/services/` | Business logic and access rules |
| `app/ai/` | Retrieval, LLM client, citation checker, NER |
| `app/models/` / `app/schemas/` | ORM models / API models |
| `app/core/`, `app/db/`, `app/middlewares/`, `app/utils/`, `app/repositories/` | Supporting code |
| `alembic/versions/` | Migrations, listed in `docs/database-schema.md` |
