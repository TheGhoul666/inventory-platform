# Run transport-ai locally without Docker (SQLite instead of Postgres).
# Starts backend + frontend in the background, seeds demo data, opens the dashboard.
# Stop with: .\stop_local.ps1
#
# ponytail: SQLite here, not the spec's Postgres — fine for a UI demo, but
# gtfs_loader only speaks Postgres (ד.3 names it explicitly), so real GTFS
# ingestion still needs `docker compose up` or a real $env:DATABASE_URL.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backend = Join-Path $root "app\backend"
$frontend = Join-Path $root "app\frontend"
$pidFile = Join-Path $root ".local_run_pids"

if (Test-Path $pidFile) {
    Write-Host "Already running (or a previous run didn't clean up). Run .\stop_local.ps1 first." -ForegroundColor Yellow
    exit 1
}

if (-not $env:DATABASE_URL) {
    $dbPath = (Join-Path $backend "demo.db") -replace '\\', '/'
    $env:DATABASE_URL = "sqlite:///$dbPath"
}
Write-Host "Using DATABASE_URL=$env:DATABASE_URL"

Push-Location $backend
pip install -q -r requirements.txt
python -c "import seed; seed.seed()"
$backendProc = Start-Process python -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000" -PassThru -WindowStyle Hidden
Pop-Location

Push-Location $frontend
# --bind 127.0.0.1: http.server's default bind triggers a hostname/IDNA crash on this machine
$frontendProc = Start-Process python -ArgumentList "-m", "http.server", "5173", "--bind", "127.0.0.1" -PassThru -WindowStyle Hidden
Pop-Location

"$($backendProc.Id)`n$($frontendProc.Id)" | Set-Content $pidFile

Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5173/index.html"

Write-Host ""
Write-Host "Backend:   http://127.0.0.1:8000/docs"
Write-Host "Dashboard: http://127.0.0.1:5173"
Write-Host "Stop with: .\stop_local.ps1"
