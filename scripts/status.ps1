$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

docker compose ps
Write-Output ""
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8010/health" -TimeoutSec 5
    Write-Output "health: $($health.status)"
} catch {
    Write-Output "health: unavailable"
}
try {
    $db = Invoke-RestMethod -Uri "http://127.0.0.1:8010/health/db" -TimeoutSec 5
    Write-Output "health/db: $($db.status)"
} catch {
    Write-Output "health/db: unavailable"
}
