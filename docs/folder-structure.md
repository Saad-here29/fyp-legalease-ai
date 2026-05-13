# Folder Structure — Why Each Folder Exists

This document explains every top-level folder and the reasoning behind it.
A non-technical reader should be able to follow the structure end-to-end.

## Root

```
FYP Project/
├── frontend/                   # React 19 web app
├── backend/                    # FastAPI Python backend
├── ai-services/                # Standalone AI scripts (corpus builder, evaluators)
├── docs/                       # Architecture, API, schema, deployment docs
├── testing/                    # Cross-cutting test resources (load, security)
├── scripts/                    # One-shot setup/seed/build scripts
├── assets/                     # Brand assets, illustrations
├── Documents and Reports/      # FYP report, diagrams (read-only reference)
├── docker-compose.yml          # Local Postgres + Redis for development
├── .gitignore                  # Cross-stack ignore rules
├── .editorconfig               # Editor consistency across the team
├── Claude.md                   # Engineering instruction document
└── README.md                   # Project entry point
```

---

## frontend/

```
frontend/
├── public/                     # Static files served as-is (favicon, robots.txt)
├── src/
│   ├── api/                    # Axios client + endpoint constants
│   │   ├── client.js           #   Single configured Axios instance with JWT refresh
│   │   └── endpoints.js        #   Centralised endpoint paths
│   ├── animations/             # Framer Motion variants (fadeIn, stagger, etc.)
│   ├── assets/                 # Images, icons, illustrations imported by code
│   ├── components/
│   │   ├── ui/                 #   ShadCN base components (button, input, ...)
│   │   ├── common/             #   App-wide composite components
│   │   ├── layout/             #   Header, Footer, Sidebar
│   │   └── forms/              #   Form-specific composites
│   ├── constants/              # ROLES, ROUTES, STORAGE_KEYS — no hardcoded strings
│   ├── features/               # Feature-first modules (vertical slices)
│   │   ├── auth/               #   Login, signup, OTP, role selection
│   │   ├── dashboard/          #   Role-specific dashboard pages
│   │   ├── case-management/
│   │   ├── chatbot/
│   │   ├── legal-research/
│   │   ├── document-analysis/
│   │   ├── ocr/
│   │   ├── contract-drafting/
│   │   ├── practice-simulator/
│   │   └── notifications/
│   ├── hooks/                  # Custom React hooks (useAuth, useDebounce, ...)
│   ├── layouts/                # Page wrappers (DashboardLayout, AuthLayout)
│   ├── lib/                    # Pure utility libraries (cn helper for ShadCN)
│   ├── pages/                  # Top-level route components if not in features/
│   ├── routes/                 # AppRouter, ProtectedRoute
│   ├── services/               # Domain services that wrap API calls
│   ├── store/                  # Zustand stores (authStore, uiStore)
│   ├── styles/                 # Additional global CSS or theme overrides
│   ├── utils/                  # Helper functions
│   ├── App.jsx                 # Mounts the router
│   ├── main.jsx                # ReactDOM root + providers
│   └── index.css               # Tailwind layers + theme tokens
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── jsconfig.json               # Path aliases (@/ -> src/)
├── .env.example
├── .eslintrc.cjs
└── .prettierrc
```

**Why feature-first inside src/features?**
Each module (chatbot, cases, etc.) has its own page components, hooks, and
local state. Keeping them together (instead of scattering across pages/,
components/, hooks/) makes the codebase navigable as it grows and lets one
team member own one feature folder.

---

## backend/

```
backend/
├── app/
│   ├── api/v1/                 # HTTP routers (thin controllers)
│   ├── core/
│   │   ├── config.py           #   Settings via pydantic-settings
│   │   ├── security.py         #   JWT + bcrypt
│   │   ├── logging.py          #   loguru config
│   │   └── exceptions.py       #   AppException hierarchy with codes
│   ├── db/
│   │   ├── base.py             #   SQLAlchemy declarative base + TimestampMixin
│   │   └── session.py          #   Engine + get_db dependency
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic DTOs (request/response)
│   ├── repositories/           # Data access layer (DB queries)
│   ├── services/               # Business logic, state machines, audit writes
│   ├── ai/                     # Embeddings, FAISS, RAG pipeline, LLM client
│   │   └── prompts/            #   Versioned prompt templates
│   ├── ocr/                    # Tesseract integration
│   ├── middlewares/            # JWT auth dep, RBAC guard, audit middleware
│   ├── validators/             # Cross-field rules
│   ├── utils/                  # Helpers
│   ├── tasks/
│   │   └── celery_app.py       #   Celery app + autodiscover
│   ├── tests/
│   │   ├── conftest.py         #   pytest fixtures (TestClient, in-memory DB)
│   │   ├── unit/
│   │   ├── integration/
│   │   └── test_health.py      #   Smoke test
│   └── main.py                 # FastAPI app entrypoint
├── alembic/                    # DB migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── uploads/                    # Local file storage (dev only)
├── storage/faiss/              # FAISS index files (gitignored)
├── logs/                       # Rotated daily log files
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── .env.example
```

**Why repository pattern?**
Services should not write raw SQL. Repositories isolate query logic so
services stay focused on business rules and tests can mock the data layer.

**Why separate ai/ and ocr/ from services/?**
They are infrastructure concerns (external models, GPU/CPU-heavy work). Pulling
them out keeps services thin and lets us swap implementations (e.g. OpenAI →
local Llama) without touching business logic.

---

## ai-services/

```
ai-services/
├── corpus-builder/             # Builds the FAISS index from legal documents
└── data/                       # Pakistani legal corpus (raw + processed)
```

These are standalone scripts — they import from `backend/app/ai/` but run as
one-off jobs (not during request handling). Kept separate so the backend Docker
image stays slim and CI can rebuild the index on a schedule.

---

## docs/

```
docs/
├── architecture.md             # 3-layer architecture + cross-cutting concerns
├── folder-structure.md         # This file
├── api-reference.md            # OpenAPI overview + naming conventions
├── database-schema.md          # ER diagrams + table-by-table reference
├── development-guide.md        # Local setup, testing, conventions
└── deployment.md               # Production deploy steps
```

---

## testing/

```
testing/
├── load/                       # k6 / Locust scripts (PER-01, PER-04)
├── security/                   # OWASP ZAP configs (SEC-05)
└── fixtures/                   # Shared test data (sample PDFs, contracts)
```

---

## scripts/

```
scripts/
├── setup.sh / setup.ps1        # First-time dev setup
├── seed-db.py                  # Insert demo users, cases, scenarios
└── build-index.py              # Build the FAISS legal corpus index
```

---

## assets/

Brand assets (logo, illustrations, screenshots). Imported by frontend or used
for documentation.
