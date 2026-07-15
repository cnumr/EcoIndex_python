#!/usr/bin/env bash
set -euo pipefail

API_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$API_DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

DB_ENGINE="${DB_ENGINE:-mysql}"

case "$DB_ENGINE" in
  mysql)
    export DB_ENGINE
    export DB_HOST="${DB_HOST:-db-mysql}"
    export DB_PORT="${DB_PORT:-3306}"
    docker compose --profile mysql up "$@"
    ;;
  postgres)
    export DB_ENGINE
    export DB_HOST="${DB_HOST:-db-postgres}"
    export DB_PORT="${DB_PORT:-5432}"
    docker compose --profile postgres up "$@"
    ;;
  sqlite)
    echo "DB_ENGINE=sqlite is not supported in Docker Compose. Use mysql or postgres." >&2
    exit 1
    ;;
  *)
    echo "Unknown DB_ENGINE: $DB_ENGINE" >&2
    exit 1
    ;;
esac
