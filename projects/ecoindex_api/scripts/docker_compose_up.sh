#!/usr/bin/env bash
set -euo pipefail

API_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$API_DIR"

DB_ENGINE_OVERRIDE="${DB_ENGINE-}"
DB_HOST_OVERRIDE="${DB_HOST-}"
DB_PORT_OVERRIDE="${DB_PORT-}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

if [ -n "$DB_ENGINE_OVERRIDE" ]; then
  DB_ENGINE="$DB_ENGINE_OVERRIDE"
fi
if [ -n "$DB_HOST_OVERRIDE" ]; then
  DB_HOST="$DB_HOST_OVERRIDE"
fi
if [ -n "$DB_PORT_OVERRIDE" ]; then
  DB_PORT="$DB_PORT_OVERRIDE"
fi

DB_ENGINE="${DB_ENGINE:-mysql}"

check_dev_port_conflict() {
  local port="$1"
  local container="$2"
  local label="$3"

  if docker inspect "$container" --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
    echo "Port $port is already used by local dev container '$container' ($label)." >&2
    echo "Stop the local dev stack first: task api:stop-dev" >&2
    exit 1
  fi
}

check_dev_port_conflict 9000 ecoindex-dev-rustfs "RustFS"
check_dev_port_conflict 6379 ecoindex-dev-valkey "Valkey"

case "$DB_ENGINE" in
  mysql)
    check_dev_port_conflict "${DB_PORT:-3306}" ecoindex-dev-mysql "MySQL"
    export DB_ENGINE
    export DB_HOST="${DB_HOST:-db-mysql}"
    export DB_PORT="${DB_PORT:-3306}"
    docker compose --profile mysql up --remove-orphans "$@"
    ;;
  postgres)
    check_dev_port_conflict "${DB_PORT:-5432}" ecoindex-dev-postgres "PostgreSQL"
    export DB_ENGINE
    export DB_HOST="${DB_HOST:-db-postgres}"
    export DB_PORT="${DB_PORT:-5432}"
    docker compose --profile postgres up --remove-orphans "$@"
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
