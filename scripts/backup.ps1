param(
    [string]$Database = "",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required"
}

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

if (-not $Database) {
    $Database = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "project_cost_hub" }
}
$user = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "project_cost" }
if (-not $OutputDir) {
    $OutputDir = Join-Path $root "backups"
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$fileName = "project_cost_hub_${stamp}.backup"
$dest = Join-Path $OutputDir $fileName
$tmp = "/tmp/$fileName"

docker compose exec -T postgres pg_dump -U $user -d $Database -Fc -f $tmp
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed" }
docker compose cp "postgres:$tmp" $dest
if (-not (Test-Path $dest)) { throw "backup file was not created" }

Write-Output "BACKUP_OK $dest"
