# LegalEase AI

LegalEase AI is a web platform for the Pakistani legal sector. Lawyers manage
their cases and clients. Lawyers, clients and law students can:
- ask legal questions;
- search Pakistani law;
- have documents analysed;
- draft contracts.

AI answers are grounded in a knowledge base built from Pakistani laws at
section level and from court judgments. Each answer cites the passages it
used. The backend is FastAPI with PostgreSQL. The frontend is React. The
language model is reached through the Groq API.

> Final Year Project, Department of Software Engineering, NUCES (FAST) Islamabad, Session 2022–2026

---

## Modules

| Module | What it does |
|---|---|
| **Legal Research** | Semantic search over the knowledge base, filtered by category and jurisdiction. AI analysis of a passage. Results can be saved to a case. A Knowledge Base page lists every law, section and judgment held, with its source. |
| **AI Chat** | Answers in English or Urdu from retrieved passages, with `[n]` citations. A deterministic checker removes citation markers that point to no passage. It also flags sections, figures and legal consequences that the passages don't contain. Out-of-scope questions are declined. |
| **Document Analysis** | Text extraction from PDF, DOCX and TXT, with Tesseract OCR for scans and images. An AI summary with clauses and points to review. Entities come from a fine-tuned legal NER model. An optional reasoning view (issues, arguments, statutes cited) shows the quoted evidence for every item. |
| **Contract Drafting** | NDA, employment and service agreement templates, with version history and checks for required clauses and unfilled placeholders. |
| **Case Management** | A five-state case lifecycle, client linking by email, case documents, an activity timeline and hearing dates. |

Also built: sign-up with an emailed code, login with lockout after 5 failed
attempts, sign-out that revokes tokens, and role-based dashboards for lawyers,
clients and students. **Not built:** the Practice Simulator and Notifications.

## Architecture

```
 Browser ── React 19 + Vite (frontend/) ──HTTP/JSON, cookies──▶ FastAPI (backend/app)
                                                                  │
               ┌──────────────────────┬───────────────────────────┼──────────────────────┐
               ▼                      ▼                           ▼                      ▼
     PostgreSQL (Supabase)   Knowledge base on disk       Groq LLM API          Local models (CPU)
     users, cases, docs,     FAISS indexes + section      answers, summaries,   multilingual MiniLM
     chats, contracts,       records, judgments,          drafting, reasoning   embeddings; legal NER;
     audit log               scraped laws (storage/kb)                          Tesseract OCR
```

Each request flows from the routers (`api/v1`) to the services and repositories,
then to the database. AI features go through `ai/` and `kb/`: retrieval
(vector search plus BM25 keyword search), then the model call, then
deterministic checks on the model's output. For details, see
[docs/architecture/system-overview.md](docs/architecture/system-overview.md)
and [docs/knowledge_base_spec.md](docs/knowledge_base_spec.md).

## Knowledge base

These numbers were read from the index files in `backend/storage/kb/` on
2026-10-08. The four optional flags in the last column default to off. The
demo script turns them on.

| Index | Contents | Searchable chunks | Used when |
|---|---|---:|---|
| Core laws (`faiss_v2`) | 35 core Pakistani laws, 3,081 section records | 11,193 | `KB_V2` |
| All laws (`faiss_v2_all`) | The 35 core laws plus 223 more from the statute corpus: 258 laws, 9,401 section records | 43,610 | `KB_V2`, when present |
| Scraped laws (`faiss_scraped`) | 724 laws from the Pakistan Code and the Khyber Pakhtunkhwa Code, 22,455 section records (32 laws marked repealed) | 82,023 | `SCRAPED_V2` |
| Judgments (`faiss_judgments`) | 400 judgments, mostly the Supreme Court of Pakistan, by paragraph | 64,322 | `JUDGMENTS_V2` |
| Scraped judgments (`faiss_scraped_judgments`) | 18 Federal Shariat Court judgments | 10,416 | `SCRAPED_V2` |
| Original index (`storage/faiss/legal_corpus`) | The statute corpus as plain chunks (the fallback) | 53,739 | flags off |

`GET /health` reports which of these the running server is using.

## Repository layout

```
backend/
  app/
    api/v1/        HTTP routers: auth, cases, chat, research, documents, contracts, kb
    services/      business rules, role checks, AI orchestration (chat, research, cases, contracts)
    ai/            LLM client, embeddings, citation checker, document reasoning, NER, summaries
    kb/            knowledge base: records, catalog, indexes, hybrid search, judgments, query hints
    scraping/      law-update scraper: fetch, parse, stage, quarantine, update log
    models/        SQLAlchemy tables
    schemas/       Pydantic request and response models
    repositories/  data access for users
    middlewares/   current user, audit helpers
    core/          settings and feature flags, security, cookies, errors, logging
    db/            engine, sessions, column types
    utils/         email, placeholders
    tests/         pytest suite (unit/ and HTTP tests) with fixtures
  alembic/         database migrations
  storage/         (not in git) FAISS indexes, section records, judgments, models
frontend/src/
  features/        one folder per screen group: auth, dashboard, case-management, chatbot,
                   legal-research, knowledge-base, document-analysis, contract-drafting, landing
  components/, layouts/, routes/, api/, store/, lib/, constants/
scripts/           start_demo.ps1, setup.ps1, knowledge base builders (kb/), scraping jobs (scraping/), evaluations
ai-services/       original corpus builder and the NER training notebook
data/              raw and processed corpus (not in git; see data/README.md)
docs/              documentation; index in docs/README.md
```

## Setup

First-time setup, on Windows.


You need:
- Python 3.11 and Node.js 20+;
- a PostgreSQL URL (the team uses Supabase);
- a Groq API key;
- the large files that aren't in git: `backend/storage/` (indexes and the
  NER model). Ask the team for these.

Tesseract with English and Urdu data is optional. It's needed only for scanned
PDFs and images.

```powershell
cd backend
python -m venv venv; venv\Scripts\activate
pip install -r requirements-dev.txt     # PyTorch comes from the CPU index
copy .env.example .env                  # fill in DATABASE_URL, SECRET_KEY, GROQ_API_KEY
alembic upgrade head

cd ..\frontend
npm install
copy .env.example .env                  # VITE_API_BASE_URL defaults to http://localhost:8000/api/v1
```

`scripts/setup.ps1` does the venv, dependency and `.env` steps in one go. You still fill in `.env` and run the migration yourself. Day-to-day work is covered in
[docs/runbooks/development-guide.md](docs/runbooks/development-guide.md).

## Running it

To start the demo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1         # all four flags on
powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Safe   # fallback: all flags off
```

The script:
1. frees ports 8000 and 5173;
2. starts the backend and the frontend in their own windows;
3. waits for `/health` and prints it, so you can see that the flags are as
   expected.

The app is at http://localhost:5173. The API docs are at
http://127.0.0.1:8000/docs, in development mode. What to show and say is in
[docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md) and
[docs/runbooks/demo-brief.md](docs/runbooks/demo-brief.md).

## Tests

```powershell
cd backend
$env:HF_HUB_OFFLINE = "1"; $env:TRANSFORMERS_OFFLINE = "1"; $env:GROQ_API_KEY = ""
python -m pytest app/tests        # 679 tests, offline: no AI calls, an in-memory database
ruff check app

cd ..\frontend
npm run lint
npm run build
```

## Team

| Member | Roll No. | Lead role |
|---|---|---|
| Saadullah | 22I-8795 | Frontend / UX |
| Ali Mehmood Khan | 22I-2547 | Backend / AI |
| Muhammad Uzair Siddique | 22I-6181 | Platform / Data |

**Supervisor:** Ms. Fatima Gillani · **Co-supervisor:** Mr. Farrukh Bashir

## Screenshots

*Placeholder: screenshots of the dashboard, AI Chat, Document Analysis and the Knowledge Base page to be added.*
