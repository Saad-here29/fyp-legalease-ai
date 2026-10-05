# LegalEase AI

**AI-powered legal assistance and practice management for the Pakistani legal sector.**

A web platform with five working parts:

- case management;
- an AI legal chat assistant grounded in Pakistani statutes (English and
  Urdu);
- semantic legal research;
- document analysis;
- contract drafting with a compliance check.

All of it sits behind role-based access for lawyers, clients and students.

> Final Year Project — Department of Software Engineering, NUCES (FAST) Islamabad — Session 2022-2026

---

## Team

| Member | Roll No. | Lead Role |
|--------|----------|-----------|
| Saadullah | 22I-8795 | Frontend / UX |
| Ali Mehmood Khan | 22I-2547 | Backend / AI |
| Muhammad Uzair Siddique | 22I-6181 | Platform / Data |

**Supervisor:** Ms. Fatima Gillani
**Co-Supervisor:** Mr. Farrukh Bashir

---

## What's built

| Module | What it does |
|---|---|
| Authentication | Signup with an emailed 6-digit code, login, password reset, lockout after 5 failed logins; sign-out revokes every token |
| Case management | Five-state case lifecycle, client linking by email, documents, activity timeline |
| AI legal chat | Answers from about 900 Pakistani statutes with `[n]` citations and a short answer; refuses out-of-scope questions; English and Urdu |
| Legal research | Semantic search over the same library, AI analysis of a passage, save to a case |
| Document analysis | Text extraction (PDF, DOCX, TXT), AI summary, clauses and risks, entities from a fine-tuned legal NER model |
| Contract drafting | NDA, employment and service agreements, version history, required-clause and unfilled-placeholder checks |
| Dashboards | One each for lawyers, clients and students |

**Not built:** the Practice Simulator and Notifications.

The search library holds **statutes only**, with no court judgments.

---

## Tech stack

| Area | Stack |
|---|---|
| **Frontend** | React 19, Vite 5, Tailwind CSS (design system v1: `docs/STYLE_GUIDE.md`), React Router 6, TanStack Query 5, Zustand 5, Axios |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, PyJWT, bcrypt |
| **Database** | PostgreSQL (Supabase in development) |
| **AI** | Groq `openai/gpt-oss-120b` (OpenAI and Gemini as optional fallbacks), `sentence-transformers` multilingual MiniLM embeddings, FAISS, a fine-tuned DistilBERT legal NER model (PyTorch, CPU) |
| **Documents** | PyMuPDF, PyPDF2, python-docx; Tesseract and Poppler optional, for scanned files |
| **Testing** | pytest (213 backend tests), ruff, ESLint |

---

## Repository layout

```
backend/       FastAPI app, Alembic migrations, tests          → backend/README.md
frontend/      React app (design system v1)                     → frontend/README.md
ai-services/   corpus/index builder, NER training notebook      → ai-services/README.md
scripts/       data cleaning, retrieval evaluation, setup       → scripts/README.md
data/          statute corpus and evaluation data (not in git)  → data/README.md
docs/          architecture, API, schema, design, retrieval, reports → docs/README.md
PROJECT_CONTEXT.md   project status, decisions and known gaps
DEMO_BRIEF.md        what to show and say in the demo
```

---

## Setup

### Prerequisites

- **Software:** Python **3.11**, Node.js **20+**, Git.
- **Database:** a PostgreSQL database URL, such as a Supabase project.
- **API key:** a **Groq** key (free at console.groq.com). It powers chat,
  research analysis, document summaries and contract drafting.
- **Large files that aren't in git (ask the team):**
  - **the search index**, `backend/storage/faiss/legal_corpus.faiss` and
    `legal_corpus_meta.json` (it can be rebuilt; see `ai-services/README.md`);
  - **the legal NER model**, `backend/storage/models/legal_ner/` (without it,
    set `NER_ENABLED=false`; document analysis then runs without entities);
  - **the raw data** under `data/` (needed only to rebuild the index).
- **Optional:** Tesseract OCR and Poppler, for scanned PDFs and images.

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt   # runtime + tests/lint; production: requirements.txt
copy .env.example .env                # then fill in DATABASE_URL, SECRET_KEY, GROQ_API_KEY
alembic upgrade head
```

`requirements.txt` installs **PyTorch from the CPU index**
(`--extra-index-url https://download.pytorch.org/whl/cpu`). The app runs its
models on the CPU, and the default Linux build would add about 2.5 GB of
CUDA libraries.

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env    # VITE_API_BASE_URL defaults to http://localhost:8000/api/v1
```

---

## Running

Start each server **in its own terminal window**, and leave both open:

```powershell
# Window 1 — backend (http://localhost:8000)
cd backend
venv\Scripts\activate
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
uvicorn app.main:app --port 8000

# Window 2 — frontend (http://localhost:5173)
cd frontend
npm run dev
```

- `HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE` stop the cached embedding model
  from checking huggingface.co at startup. That check can hang. Leave them
  off the first time, so the model downloads once.
- API docs are at `http://localhost:8000/docs` when `APP_ENV=development`.
- Signup codes are emailed only when the `SMTP_*` settings are filled in.
  Otherwise they appear in the backend window as
  `[DEV OTP] email -> code`.

---

## Tests and checks

```powershell
cd backend
pytest                    # 213 tests, offline (no AI calls)
ruff check app

cd ..\frontend
npm run lint
npm run build
```

---

## Documentation

`docs/README.md` indexes everything. Start with:

- `docs/architecture.md`
- `docs/api-reference.md`
- `docs/database-schema.md`
- `docs/development-guide.md`
- `docs/STYLE_GUIDE.md`
- `docs/retrieval_redesign.md`
