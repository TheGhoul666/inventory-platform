# Stops what .\run_local.ps1 started.
$root = $PSScriptRoot
$pidFile = Join-Path $root ".local_run_pids"

if (-not (Test-Path $pidFile)) {
    Write-Host "Nothing tracked as running (no .local_run_pids file)." -ForegroundColor Yellow
    exit 0
}

Get-Content $pidFile | ForEach-Object {
    try {
        Stop-Process -Id $_ -Force -ErrorAction Stop
        Write-Host "stopped PID $_"
    } catch {
        Write-Host "PID $_ already gone"
    }
}
Remove-Item $pidFile
