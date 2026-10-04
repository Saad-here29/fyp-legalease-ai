# LegalEase AI — first-time setup for Windows (PowerShell)
# Run from the project root: .\scripts\setup.ps1
#
# Needs Python 3.11 and Node.js 20+. It does not set up the database (use a
# PostgreSQL URL, e.g. Supabase, in backend/.env) or fetch the search index
# and NER model, which aren't in git (see README.md, "Setup").

$ErrorActionPreference = "Stop"

Write-Host "==> LegalEase AI setup" -ForegroundColor Cyan

# Backend
Write-Host "`n[1/2] Setting up backend..." -ForegroundColor Yellow
Push-Location backend
if (-not (Test-Path venv)) {
    python -m venv venv
}
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "  Created backend/.env from .env.example: set DATABASE_URL, SECRET_KEY and GROQ_API_KEY" -ForegroundColor Green
}
Pop-Location

# Frontend
Write-Host "`n[2/2] Setting up frontend..." -ForegroundColor Yellow
Push-Location frontend
npm install
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "  Created frontend/.env from .env.example" -ForegroundColor Green
}
Pop-Location

Write-Host "`n==> Setup complete." -ForegroundColor Green
Write-Host "Next: fill in backend/.env, then 'cd backend; venv\Scripts\alembic upgrade head'."
Write-Host "Run each server in its own window:"
Write-Host "  Backend:  cd backend; venv\Scripts\uvicorn app.main:app --port 8000"
Write-Host "  Frontend: cd frontend; npm run dev"
