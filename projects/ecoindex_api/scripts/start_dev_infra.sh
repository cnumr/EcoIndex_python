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

DB_ENGINE="${DB_ENGINE:-sqlite}"

ensure_container() {
  local lock_file="$1"
  local name="$2"
  local port="$3"
  shift 3

  (
    flock -x 200
    if docker inspect "$name" --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
      return 0
    fi

    if docker inspect "$name" >/dev/null 2>&1; then
      docker start "$name" >/dev/null
      return 0
    fi

    local port_owner
    port_owner="$(bash scripts/docker_container_on_port.sh "$port" 2>/dev/null || true)"
    if [ -n "$port_owner" ] && [ "$port_owner" != "$name" ]; then
      echo "Port $port is already used by container '$port_owner'." >&2
      echo "Stop it first, for example: docker rm -f $port_owner" >&2
      exit 1
    fi

    docker run -d --name "$name" "$@"
  ) 200>"$lock_file"
}

ensure_container \
  /tmp/ecoindex-dev-valkey.lock \
  ecoindex-dev-valkey \
  6379 \
  -p 6379:6379 \
  valkey/valkey:alpine

uv run python scripts/wait_valkey.py > /dev/null

ensure_container \
  /tmp/ecoindex-dev-rustfs.lock \
  ecoindex-dev-rustfs \
  9000 \
  -p 9000:9000 \
  -p 9001:9001 \
  -v ecoindex-dev-rustfs-data:/data \
  -e RUSTFS_ACCESS_KEY="${SCREENSHOT_S3_ACCESS_KEY_ID:-ecoindex-access-key}" \
  -e RUSTFS_SECRET_KEY="${SCREENSHOT_S3_SECRET_ACCESS_KEY:-ecoindex-secret-key-change-me}" \
  -e RUSTFS_CONSOLE_ENABLE=true \
  rustfs/rustfs:latest \
  /data

bash scripts/init_rustfs_bucket.sh

case "$DB_ENGINE" in
  mysql)
    ensure_container \
      /tmp/ecoindex-dev-mysql.lock \
      ecoindex-dev-mysql \
      "${DB_PORT:-3306}" \
      -p "${DB_PORT:-3306}:3306" \
      -e MYSQL_DATABASE="${DB_NAME:-ecoindex}" \
      -e MYSQL_USER="${DB_USER:-ecoindex}" \
      -e MYSQL_PASSWORD="${DB_PASSWORD:-ecoindex}" \
      -e MYSQL_ROOT_PASSWORD="${DB_PASSWORD:-ecoindex}" \
      -v ecoindex-dev-mysql-data:/var/lib/mysql \
      mysql:8
    ECOINDEX_DEV_DB_CONTAINER=ecoindex-dev-mysql bash scripts/wait_db.sh
    ;;
  postgres)
    ensure_container \
      /tmp/ecoindex-dev-postgres.lock \
      ecoindex-dev-postgres \
      "${DB_PORT:-5432}" \
      -p "${DB_PORT:-5432}:5432" \
      -e POSTGRES_DB="${DB_NAME:-ecoindex}" \
      -e POSTGRES_USER="${DB_USER:-ecoindex}" \
      -e POSTGRES_PASSWORD="${DB_PASSWORD:-ecoindex}" \
      -v ecoindex-dev-postgres-data:/var/lib/postgresql/data \
      postgres:16-alpine
    ECOINDEX_DEV_DB_CONTAINER=ecoindex-dev-postgres bash scripts/wait_db.sh
    ;;
  sqlite)
    ;;
  *)
    echo "Unsupported DB_ENGINE for local dev: $DB_ENGINE" >&2
    exit 1
    ;;
esac
