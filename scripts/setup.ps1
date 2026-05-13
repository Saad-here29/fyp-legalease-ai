# LegalEase AI — first-time setup for Windows (PowerShell)
# Run from the project root: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> LegalEase AI setup" -ForegroundColor Cyan

# Backend
Write-Host "`n[1/3] Setting up backend..." -ForegroundColor Yellow
Push-Location backend
if (-not (Test-Path .venv)) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "  Created backend/.env from .env.example — please edit secrets" -ForegroundColor Green
}
Pop-Location

# Frontend
Write-Host "`n[2/3] Setting up frontend..." -ForegroundColor Yellow
Push-Location frontend
npm install
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "  Created frontend/.env from .env.example" -ForegroundColor Green
}
Pop-Location

# Infrastructure
Write-Host "`n[3/3] Starting Postgres + Redis (docker-compose)..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "`n==> Setup complete!" -ForegroundColor Green
Write-Host "Backend:  cd backend && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload"
Write-Host "Frontend: cd frontend && npm run dev"
Write-Host "Worker:   cd backend && celery -A app.tasks.celery_app worker --loglevel=info --pool=solo"
