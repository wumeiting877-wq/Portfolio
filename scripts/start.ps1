$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required. Start Docker Desktop first."
}

$envExample = Join-Path $root ".env.example"
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
}

docker compose up -d --build

$deadline = (Get-Date).AddMinutes(3)
do {
    Start-Sleep -Seconds 3
    $health = docker compose ps --format json | ConvertFrom-Json
    $backend = @($health) | Where-Object { $_.Service -eq "backend" }
    if ($backend -and ($backend.Health -eq "healthy" -or $backend.State -eq "running")) {
        try {
            $ok = Invoke-RestMethod -Uri "http://127.0.0.1:8010/health" -TimeoutSec 5
            if ($ok.status -eq "ok") { break }
        } catch {
            # keep waiting
        }
    }
} while ((Get-Date) -lt $deadline)

Write-Output "Frontend: http://localhost:5173"
Write-Output "Backend:  http://localhost:8010/health"
Write-Output "DB check: http://localhost:8010/health/db"
