param(
    [string]$Backend = "http://127.0.0.1:8010"
)

$health = Invoke-RestMethod -Uri "$Backend/health"
if ($health.status -ne "ok") {
    throw "health check failed"
}

$db = Invoke-RestMethod -Uri "$Backend/health/db"
if ($db.status -ne "ok") {
    throw "database health check failed"
}

Write-Output "health: ok"
Write-Output "health/db: ok"
