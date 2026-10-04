# Folder Structure

What each folder holds and why. Updated October 2026 to match the
repository. Folders marked *(not in git)* are git-ignored. They are needed
at run time but too large or private to commit.

## Root

```
.
├── backend/              FastAPI app, migrations, tests            (backend/README.md)
├── frontend/             React 19 + Vite app                       (frontend/README.md)
├── ai-services/          search-index builder, NER training notebook (ai-services/README.md)
├── scripts/              corpus cleaning, retrieval evaluation, setup (scripts/README.md)
├── data/                 raw + processed corpus and eval data — only README.md in git (data/README.md)
├── docs/                 project documentation                      (docs/README.md)
├── README.md             overview, setup, how to run
├── PROJECT_CONTEXT.md    status, decisions, known gaps
├── DEMO_BRIEF.md         demo script and talking points
├── .editorconfig, .gitignore
```

## backend/

```
backend/
├── app/
│   ├── main.py            app factory: routers, CORS, error handlers, API docs (development only)
│   ├── api/v1/            routers: auth, cases, chat, research, documents, contracts
│   ├── services/          business rules, role checks, audit, AI orchestration
│   ├── ai/                embeddings + FAISS, LLM client, query rewrite, section lookup,
│   │                      citation checker, legal NER, summary sections, contract templates
│   ├── models/            SQLAlchemy ORM (14 tables)
│   ├── schemas/           Pydantic request/response models
│   ├── repositories/      user repository (auth)
│   ├── middlewares/       current-user dependency, audit helpers
│   ├── core/              settings, security (bcrypt/JWT), cookies, exceptions, logging
│   ├── db/                engine, sessions, base, column types
│   ├── utils/             email, email-domain validation, placeholder scan
│   └── tests/             pytest suite (unit/ + top-level HTTP tests)
├── alembic/versions/      database migrations
├── requirements.txt       runtime dependencies (CPU PyTorch index)
├── requirements-dev.txt   + tests, lint, scripts
├── storage/               (not in git) faiss/ index + metadata, models/legal_ner/
├── uploads/               (not in git) uploaded files, stored under generated names
└── logs/                  (not in git) daily log files
```

## frontend/

```
frontend/
├── index.html, vite.config.js, tailwind.config.js (design system v1 tokens)
├── public/favicon.svg
└── src/
    ├── main.jsx, App.jsx, index.css (ds- component classes)
    ├── routes/            AppRouter (all routes + 404), ProtectedRoute (role check)
    ├── api/               Axios client (cookies, refresh on 401), endpoint paths
    ├── store/             Zustand auth store
    ├── constants/         routes, roles, dashboardRouteFor, enums mirrored from the backend
    ├── lib/               Markdown renderer for AI output, citation helpers, formatting
    ├── layouts/           AuthShell (sign-in / sign-up pages)
    ├── components/
    │   ├── layout/        AppShell (sidebar, header, mobile drawer)
    │   └── common/        Wordmark, ArchPattern, NotFoundPage
    └── features/          one folder per feature: auth, landing, dashboard,
                           case-management, chatbot, legal-research,
                           document-analysis, contract-drafting
```

Ten placeholder folders that held only a `.gitkeep` were removed on
2026-10-04:
- `assets`, `pages`, `services`, `styles`, `utils`;
- `components/forms`, `components/ui`;
- the unbuilt `features/notifications`, `features/ocr`,
  `features/practice-simulator`.

## ai-services/

```
ai-services/
├── corpus_builder/build_corpus.py   chunks + embeds the statute corpus, writes the FAISS index
└── ner_training/                    Colab notebook for the legal NER model (trained_model/ not in git)
```

## scripts/

- `clean_statute_corpus.py`: cleans and merges the raw statute data into
  `data/processed/`.
- `eval_research_retrieval.py`: runs the 78 lawyer questions against a
  running backend.
- `setup.ps1`: one-time Windows setup (venv, dependencies, `.env` files).

## docs/

- **Technical:** architecture, api-reference, database-schema,
  development-guide, deployment, folder-structure (this page), TEST_PLAN.
- **Design:** STYLE_GUIDE, plus `design_reference/` (the design-system PDF;
  page images not in git).
- **AI and data:** ner_training_results, corpus_statute_list,
  retrieval_redesign, retrieval_gold_set_draft, retrieval_statute_chunking.
- **Demo:** demo_examples and `demo/` (a recorded real-document run).
- **Reports:** `reports/`, the FYP proposal, mid and final reports, and
  design diagrams.

`docs/README.md` is the index.
