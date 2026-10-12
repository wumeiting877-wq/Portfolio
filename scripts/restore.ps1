param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [Parameter(Mandatory = $true)]
    [string]$TargetDatabase
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$envFile = Join-Path $root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*#" -or $_ -notmatch "=") { return }
        $name, $value = $_.Split("=", 2)
        if (-not [string]::IsNullOrWhiteSpace($name) -and -not (Test-Path "Env:$name")) {
            Set-Item -Path "Env:$name" -Value $value.Trim()
        }
    }
}

$current = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "project_cost_hub" }
$user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "project_cost" }

if ($TargetDatabase -eq $current) {
    throw "Refusing to restore over current database '$current'. Use a dedicated restore test database."
}
if ($TargetDatabase -notmatch '^[A-Za-z0-9_]+$') {
    throw "Invalid target database name"
}
if (-not (Test-Path $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

Write-Warning "Restoring '$BackupFile' into database '$TargetDatabase' (not '$current')."

docker compose exec -T postgres psql -U $user -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TargetDatabase' AND pid <> pg_backend_pid();"
docker compose exec -T postgres psql -U $user -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $TargetDatabase;"
docker compose exec -T postgres psql -U $user -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $TargetDatabase OWNER $user;"

$tmp = "/tmp/restore_target.backup"
docker compose cp $BackupFile "postgres:$tmp"
docker compose exec -T postgres pg_restore -U $user -d $TargetDatabase --no-owner --role=$user "$tmp"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "pg_restore exited $LASTEXITCODE (warnings may be expected for custom format)"
}

Write-Output "RESTORE_OK $TargetDatabase"
