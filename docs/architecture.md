# Architecture Overview

LegalEase AI's runtime layout, the responsibilities of each layer, and the
concerns that cut across them. Updated October 2026 to match the code.

## 1. Pattern

**Layered (3-tier) architecture.** Everything is one bounded context (legal
practice), so separate services would add deployment and consistency
overhead without a scaling benefit.

```
┌──────────────────────────────────────────────────────────────┐
│ PRESENTATION — React 19 + Vite (frontend/)                   │
│ AppRouter → ProtectedRoute (role) → feature pages            │
│ Axios client: HttpOnly cookies, refresh-on-401               │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS, /api/v1 (JSON, multipart)
┌──────────────────────────────▼───────────────────────────────┐
│ APPLICATION — FastAPI (backend/app/)                         │
│ api/v1 routers → services (rules, roles, audit) → models     │
│ ai/: retrieval, query rewrite, citation check, NER, templates│
└───────┬──────────────────────┬───────────────────────┬───────┘
        │ SQLAlchemy           │ in-process            │ HTTPS
┌───────▼────────┐  ┌──────────▼───────────┐  ┌────────▼─────────┐
│ PostgreSQL     │  │ FAISS index + meta   │  │ Groq API         │
│ (Supabase)     │  │ NER model (PyTorch)  │  │ gpt-oss-120b     │
│ 14 tables      │  │ uploads/ (files)     │  │ (OpenAI, Gemini  │
│                │  │ backend/storage/     │  │  as fallbacks)   │
└────────────────┘  └──────────────────────┘  └──────────────────┘
```

## 2. Layer responsibilities

| Layer | Owns | Must not |
|---|---|---|
| Presentation | UI, design system, role-aware routing, API calls | Hold business rules or decide access |
| Application | Business rules, the case state machine, role checks, audit logging, AI orchestration | Render UI |
| Data | Persistence, transactions, vector search, file storage | Run business logic |

## 3. Backend modules (`backend/app/`)

| Folder | Contents |
|---|---|
| `api/v1/` | Thin routers: `auth`, `cases`, `chat`, `research`, `documents`, `contracts` |
| `services/` | Business logic: `auth_service`, `case_service`, `legal_chat_service`, `research_service`, `contract_service`, `ocr_service` (text extraction), plus the `base` service with audit logging |
| `repositories/` | `user_repository` (used by the auth service; other services query through the ORM directly) |
| `models/` | SQLAlchemy ORM, 14 tables (`docs/database-schema.md`) |
| `schemas/` | Pydantic request/response models |
| `ai/` | `embeddings` (FAISS + sentence-transformers), `client` (LLM providers), `query_rewrite`, `section_lookup`, `citation_check`, `ner`, `summary_sections`, `contract_templates` |
| `middlewares/` | `auth` (current user from the cookie or Bearer token, token-version check), `audit` |
| `core/` | `config` (settings from `.env`), `security` (bcrypt, JWT), `cookies`, `exceptions`, `logging` |
| `db/` | Engine, sessions (with a one-retry connection check), base and portable column types |
| `utils/` | Email sending and domain validation, contract placeholder scan |
| `tests/` | pytest suite (in-memory SQLite, no AI calls) |

## 4. AI pipeline

- **Chat** (`legal_chat_service`):
  1. Rewrite the question into a search query (small LLM call).
  2. FAISS top 5, with a 0.65 similarity threshold.
  3. Follow a retrieved contents list to the sections the user's question
     names.
  4. Refuse without an LLM call if nothing passes, in English or Urdu.
  5. Build the prompt: rules, numbered passages, a language instruction,
     and history capped at 2,000 tokens.
  6. Call the LLM.
  7. Run the citation check (unverified section numbers flagged, case
     citations removed).

  The database transaction is closed before any LLM call (Supabase's pooler
  kills idle transactions).
- **Research:** query rewrite, then FAISS, then results. "Analyse with AI"
  is a separate LLM call on one passage.
- **Document analysis:** an LLM summary (clauses and risks are parsed from
  its sections), run in parallel with the legal NER model (fine-tuned
  DistilBERT, CPU).
- **Contracts:** an LLM draft from a template. The compliance check is
  deterministic: keyword clauses plus an unfilled-placeholder scan.
- **Index:** built offline by `ai-services/corpus_builder/build_corpus.py`
  and loaded at first use. It isn't stored in PostgreSQL. The `legal_corpus`
  table is a legacy seed table that nothing reads.

## 5. Cross-cutting concerns

- **Auth:**
  - JWT HS256 (access 60 min, refresh 7 days) in HttpOnly cookies or a
    Bearer header;
  - bcrypt cost 12;
  - a per-user `token_version` claim that logout increments (revokes all
    tokens);
  - lockout after 5 failed logins (password reset unlocks);
  - email OTP (10 min) to verify signups.
- **Access control:** in the services, by role and by ownership (the
  assigned lawyer or linked client). `ProtectedRoute` in the frontend only
  decides navigation.
- **Audit:** privileged actions write to `activity_logs`. The case timeline
  is built from them.
- **Errors:** `AppException` subclasses produce `{error: {code, message,
  hint}}`. Database connection failures become a 503 after one retry.
- **Uploads:**
  - stored under generated names in `UPLOAD_DIR`;
  - type checked before writing, size capped while streaming;
  - files removed if anything after the write fails.
- **Logging:** loguru, daily rotation, 30 days kept (`backend/logs/`).
- **CORS:** limited to `CORS_ORIGINS`. API docs only in development.

## 6. Known limits

- **Latency:** the database is on Supabase in Singapore. A query takes
  0.2–0.4 s and a new connection about 4 s, so API calls typically take
  3–8 s.
- **Groq free tier:** 200k tokens/day, 8k/minute and 1,000 requests/day,
  shared by every AI feature.
- **Retrieval:** quality is limited by fixed 800-character chunks (and the
  embedding model's 128-token window). The section-based redesign is in
  `docs/retrieval_redesign.md`.
- **OCR:** for scanned files it needs Tesseract and Poppler on the server.
