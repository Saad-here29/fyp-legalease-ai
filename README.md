# LegalEase AI

**AI-Powered Online Lawyer Management and Legal Assistance Platform**

A unified web platform for the Pakistani legal sector that combines case management, AI-powered legal assistance, document analysis, semantic legal research, and a practice environment for law students — all behind role-based access control.

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

## Project Structure

```
LegalEase-AI/
├── frontend/          # React 19 + Vite + TailwindCSS web app
├── backend/           # FastAPI (Python) backend with PostgreSQL + FAISS
├── ai-services/       # Standalone AI utilities (corpus builder, evaluators)
├── docs/              # Architecture, API, and deployment documentation
├── testing/           # Cross-cutting test resources (load, security, fixtures)
├── scripts/           # Setup, seed, and build scripts
├── assets/            # Brand assets and illustrations
├── Documents and Reports/   # FYP report, diagrams, and proposals
└── Claude.md          # Engineering instruction document
```

---

## Tech Stack

**Frontend:** React 19 · Vite · TailwindCSS · ShadCN/UI · Framer Motion · Zustand · React Query · Axios

**Backend:** Python 3.11+ · FastAPI · SQLAlchemy · Pydantic · Alembic

**Database:** PostgreSQL · FAISS (vector store) · Redis (Celery broker)

**AI:** OpenAI Chat Completions · Sentence Transformers (multilingual) · Tesseract OCR

**Auth:** JWT (PyJWT) · bcrypt (cost ≥ 12) · Role-Based Access Control

**Testing:** pytest · React Testing Library · k6 · Locust · OWASP ZAP

---

## Modules

1. **Case Management** — Full lifecycle, hearings, deadlines, timeline, RBAC
2. **AI Legal Chat Assistant** — RAG-based bilingual (English/Urdu) Q&A with citations
3. **Document Analysis** — AI summarisation, clause identification, risk flagging
4. **AI Legal Research** — Semantic search over Pakistani statutes and judgments
5. **Practice Simulator** — Interactive scenarios for law students
6. **Contract Drafting & Compliance** — Templates, clause suggestions, version diff
7. **OCR & Scanned-Document** — Tesseract OCR pipeline for legal documents
8. **Security, RBAC & Notifications** — JWT, audit logs, in-app + email alerts
9. **Unified Dashboard** — Role-specific responsive dashboards

---

## Quickstart

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then edit .env with your secrets
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env          # then edit .env with API URL
npm run dev
```

### Celery worker (OCR + notifications)

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

---

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Database Schema](docs/database-schema.md)
- [Development Guide](docs/development-guide.md)
- [Deployment](docs/deployment.md)
