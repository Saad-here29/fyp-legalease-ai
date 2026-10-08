# LegalEase demo start (kb-v2 C5): one command for the backend and the frontend.
#
#   powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1          # everything on
#   powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Safe    # fallback: all four flags off
#
# 1. Frees ports 8000 and 5173 (stops whatever listens there: an old backend or frontend).
# 2. Opens the backend (port 8000) and the frontend (port 5173) in two new PowerShell windows,
#    with KB_V2, JUDGMENTS_V2, REASONING_V2 and SCRAPED_V2 set (all "true", or all "false" with -Safe)
#    and the Hugging Face offline variables. Each window stays open so you can read its log.
# 3. Waits for http://127.0.0.1:8000/health, prints it, and says if any flag isn't as expected.
#
# It runs the project's own backend\venv (create it with scripts\setup.ps1; -Python to change).

param(
    [switch]$Safe,
    [string]$Worktree = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Python = (Join-Path $Worktree "backend\venv\Scripts\python.exe"),
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [int]$WaitSeconds = 120
)

$ErrorActionPreference = "Stop"
$backend = Join-Path $Worktree "backend"
$frontend = Join-Path $Worktree "frontend"
if (-not (Test-Path $Python)) { throw "Python not found: $Python (pass -Python <path to python.exe>)" }
if (-not (Test-Path (Join-Path $backend "app\main.py"))) { throw "Not a LegalEase worktree: $Worktree" }

# ---- 1. free the ports ------------------------------------------------------
foreach ($port in @($BackendPort, $FrontendPort)) {
    $pids = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
              Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($procId in $pids) {
        if ($procId -and $procId -ne 0) {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            Write-Host "Port ${port}: stopping $($p.ProcessName) (PID $procId)"
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 1

# ---- 2. start both ------------------------------------------------------------
$flag = if ($Safe) { "false" } else { "true" }
$mode = if ($Safe) { "SAFE (all four flags off: the fallback)" } else { "FULL (KB_V2, JUDGMENTS_V2, REASONING_V2, SCRAPED_V2 on)" }
$backendCmd = @"
`$Host.UI.RawUI.WindowTitle = 'LegalEase backend :$BackendPort ($flag)'
Set-Location '$backend'
`$env:KB_V2 = '$flag'; `$env:JUDGMENTS_V2 = '$flag'; `$env:REASONING_V2 = '$flag'; `$env:SCRAPED_V2 = '$flag'
`$env:HF_HUB_OFFLINE = '1'; `$env:TRANSFORMERS_OFFLINE = '1'; `$env:PYTHONIOENCODING = 'utf-8'
& '$Python' -m uvicorn app.main:app --port $BackendPort
"@
$frontendCmd = @"
`$Host.UI.RawUI.WindowTitle = 'LegalEase frontend :$FrontendPort'
Set-Location '$frontend'
npm run dev -- --port $FrontendPort --strictPort
"@
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCmd)
Start-Process powershell -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd)
Write-Host ""
Write-Host "Starting LegalEase in $mode mode"
Write-Host "  Frontend:  http://localhost:$FrontendPort"
Write-Host "  Backend:   http://127.0.0.1:$BackendPort/health"
Write-Host "  API docs:  http://127.0.0.1:$BackendPort/docs"
Write-Host ""

# ---- 3. check -----------------------------------------------------------------
$health = $null
$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    try { $health = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 3; break }
    catch { Start-Sleep -Seconds 2 }
}
if (-not $health) {
    Write-Host "The backend did not answer /health within $WaitSeconds s. Look at its window for the error." -ForegroundColor Red
    exit 1
}
Write-Host "/health:"
$health | ConvertTo-Json -Depth 3 | Write-Host
$expected = -not $Safe
$wrong = @()
foreach ($name in @("kb_v2", "judgments_v2", "reasoning_v2", "scraped_v2")) {
    if ($health.$name -ne $expected) { $wrong += "$name is $($health.$name)" }
}
if ($wrong.Count) {
    Write-Host ("NOT AS EXPECTED: " + ($wrong -join "; ")) -ForegroundColor Yellow
} else {
    Write-Host ("All four flags are " + $(if ($expected) { "ON" } else { "OFF (safe mode)" }) + ".") -ForegroundColor Green
}
if (-not $Safe) {
    if (-not $health.judgment_chunks) { Write-Host "Note: the judgments index is empty or missing (judgment_chunks = $($health.judgment_chunks))." -ForegroundColor Yellow }
    if (-not $health.scraped_chunks) { Write-Host "Note: the scraped index is empty or missing (scraped_chunks = $($health.scraped_chunks))." -ForegroundColor Yellow }
}
$fe = $null
foreach ($i in 1..15) {
    try { $fe = Invoke-WebRequest -Uri "http://localhost:$FrontendPort" -UseBasicParsing -TimeoutSec 3; break }
    catch { Start-Sleep -Seconds 2 }
}
if ($fe) { Write-Host "Frontend is up: http://localhost:$FrontendPort" -ForegroundColor Green }
else { Write-Host "The frontend did not answer yet; look at its window (npm run dev)." -ForegroundColor Yellow }
