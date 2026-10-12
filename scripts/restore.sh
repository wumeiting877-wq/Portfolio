#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BACKUP_FILE="${1:-}"
TARGET_DATABASE="${2:-}"
CURRENT="${POSTGRES_DB:-project_cost_hub}"
USER_NAME="${POSTGRES_USER:-project_cost}"

if [ -z "$BACKUP_FILE" ] || [ -z "$TARGET_DATABASE" ]; then
  echo "Usage: restore.sh <backup-file> <target-database>" >&2
  exit 1
fi
if [ "$TARGET_DATABASE" = "$CURRENT" ]; then
  echo "Refusing to restore over current database $CURRENT" >&2
  exit 1
fi

echo "WARNING: restoring $BACKUP_FILE into $TARGET_DATABASE"
docker compose exec -T postgres psql -U "$USER_NAME" -d postgres -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TARGET_DATABASE' AND pid <> pg_backend_pid();"
docker compose exec -T postgres psql -U "$USER_NAME" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $TARGET_DATABASE;"
docker compose exec -T postgres psql -U "$USER_NAME" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $TARGET_DATABASE OWNER $USER_NAME;"
docker compose cp "$BACKUP_FILE" postgres:/tmp/restore_target.backup
docker compose exec -T postgres pg_restore -U "$USER_NAME" -d "$TARGET_DATABASE" --no-owner --role="$USER_NAME" /tmp/restore_target.backup
echo "RESTORE_OK $TARGET_DATABASE"
