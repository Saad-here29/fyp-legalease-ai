# Architecture Overview

> Single source of truth for the LegalEase AI runtime topology, layer
> responsibilities, and cross-cutting concerns.

## 1. Architectural Pattern

**Layered Architecture (3-tier)** — chosen because the system operates in one
bounded context (legal case management). Microservices would add overhead
without the benefit of independent scaling per domain.

```
┌─────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                 │
│  React 19 + Vite (frontend/)                        │
│  Lawyer Dashboard | Client Portal | Student WS      │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS / WS
┌────────────────────▼────────────────────────────────┐
│  APPLICATION LAYER                                  │
│  FastAPI (backend/app/)                             │
│  Auth & RBAC | Cases & Docs | AI Chat & Research    │
│  Notifications & Audit                              │
└────────────────────┬────────────────────────────────┘
                     │ SQLAlchemy / FAISS / Blob API
┌────────────────────▼────────────────────────────────┐
│  DATA LAYER                                         │
│  PostgreSQL | Blob Storage | FAISS | Audit Log      │
└─────────────────────────────────────────────────────┘
                     │ (out-of-band)
              External LLM (OpenAI), Tesseract OCR
```

## 2. Layer Responsibilities

| Layer | Owns | Must Not |
|-------|------|----------|
| Presentation | UI, animations, role-aware routing, API calls | Talk to DB, hold business rules |
| Application | Business rules, state machines, RBAC, audit | Render UI, store files |
| Data | Persistence, transactions, vector search | Run business logic |

## 3. Module Boundaries (within backend/)

- `api/v1/` — HTTP routers (thin controllers)
- `services/` — business logic
- `repositories/` — DB queries
- `models/` — SQLAlchemy ORM
- `schemas/` — Pydantic DTOs
- `ai/` — embeddings, FAISS, RAG, prompts
- `ocr/` — Tesseract pipeline
- `tasks/` — Celery workers

## 4. Cross-Cutting Concerns

- **Auth:** JWT (access 60min, refresh 7d), bcrypt cost ≥ 12
- **RBAC:** FastAPI dependency that reads `role` claim from access token
- **Audit:** every privileged action writes to `activity_logs` (SEC-04)
- **Errors:** centralised `AppException` with `code`, `message`, `hint`
- **Logging:** loguru with daily rotation
- **CORS:** locked to known frontend origins via env var

## 5. Performance Targets (from Final Report)

- API endpoints (cases, docs): p95 ≤ 200ms (DB queries)
- Dashboard pages: p95 ≤ 2s
- AI Chat: ≤ 5s cached, ≤ 15s uncached
- 100 concurrent users at error rate ≤ 1%
