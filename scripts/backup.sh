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

DATABASE="${1:-${POSTGRES_DB:-project_cost_hub}}"
USER_NAME="${POSTGRES_USER:-project_cost}"
OUT_DIR="${2:-$ROOT/backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="project_cost_hub_${STAMP}.backup"
TMP="/tmp/${FILE}"

docker compose exec -T postgres pg_dump -U "$USER_NAME" -d "$DATABASE" -Fc -f "$TMP"
docker compose cp "postgres:${TMP}" "${OUT_DIR}/${FILE}"
echo "BACKUP_OK ${OUT_DIR}/${FILE}"
