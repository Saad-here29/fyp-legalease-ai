# Deployment Guide

Placeholder — populated in Phase 12 (Deployment Readiness).

## Target Architecture

- Frontend: static build served via Nginx or Vercel
- Backend: FastAPI behind Uvicorn workers + Nginx reverse proxy
- Database: managed PostgreSQL (e.g., Neon, Supabase, RDS)
- Redis: managed Redis or self-hosted
- File storage: S3-compatible bucket (signed URLs)
- Workers: Celery on a separate process pool
- TLS: required (SEC-02 — TLS 1.2+ with SSL Labs grade ≥ A)

## Pre-Demo Checklist

- [ ] OWASP ZAP scan: zero critical/high (SEC-05)
- [ ] All FR-xx acceptance criteria documented as passing tests
- [ ] Lighthouse score on landing + dashboards ≥ 90
- [ ] System Usability Scale ≥ 70 (USE-05)
- [ ] Sample dataset seeded (10 lawyers, 30 clients, 5 students, 20 cases)
- [ ] Legal corpus indexed with FAISS
- [ ] Demo script rehearsed end-to-end
