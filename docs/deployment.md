# Deployment Guide

LegalEase AI has not been deployed to production yet. This page lists what a
deployment needs, based on how the app runs today.

## Components

| Component | What to run | Notes |
|---|---|---|
| Frontend | `npm run build`, then serve `frontend/dist/` as static files (Nginx, Vercel, Netlify) | Set `VITE_API_BASE_URL` at build time. Production builds have no source maps |
| Backend | `uvicorn app.main:app` behind a reverse proxy with TLS | Loads the embedding model (about 470 MB) and the NER model (about 520 MB), so allow at least 2 GB of RAM (an estimate; not measured under load). Set `APP_ENV=production` (secure cookies on, API docs off) |
| Database | Managed PostgreSQL (the team uses Supabase) | Run `alembic upgrade head`. Choose a region close to the users: with Singapore, each query takes 0.2–0.4 s from Pakistan |
| Search index | `backend/storage/faiss/` (FAISS file + metadata JSON) | Built offline (`ai-services/README.md`) and copied to the server |
| NER model | `backend/storage/models/legal_ner/` | Or set `NER_ENABLED=false` |
| Uploads | `UPLOAD_DIR` on persistent disk | Files are stored under generated names. Back the folder up alongside the database |
| AI provider | Groq API key | The free tier allows 200k tokens a day for everything. Use a paid tier for real use |
| Email | `SMTP_*` settings | Without them, signup and reset codes only appear in the server log |
| OCR | Tesseract with English + Urdu data, `TESSERACT_CMD` | Needed for scanned PDFs and images (no Poppler) |

Install the backend with `pip install -r requirements.txt`. It pulls the
CPU-only PyTorch build.

## Before a public deployment

- [ ] `SECRET_KEY`: a long random value, never the example one.
- [ ] `APP_ENV=production` and `CORS_ORIGINS` set to the real frontend URL.
- [ ] SMTP configured, so signup codes reach users.
- [ ] A paid Groq tier, or a plan for the daily token limit.
- [ ] Database region close to the users.
- [ ] HTTPS everywhere (the auth cookies are `Secure` outside development).
- [ ] Backups for the database and `UPLOAD_DIR`.
