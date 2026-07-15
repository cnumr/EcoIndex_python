#!/usr/bin/env bash
set -euo pipefail

DB_ENGINE="${DB_ENGINE:-sqlite}"
DB_USER="${DB_USER:-ecoindex}"
DB_NAME="${DB_NAME:-ecoindex}"
DB_PASSWORD="${DB_PASSWORD:-ecoindex}"

case "$DB_ENGINE" in
  sqlite)
    exit 0
    ;;
  mysql)
    container="${ECOINDEX_DEV_DB_CONTAINER:-ecoindex-dev-mysql}"
    until docker exec "$container" mysqladmin ping -h 127.0.0.1 -u "$DB_USER" --password="$DB_PASSWORD" --silent >/dev/null 2>&1; do
      sleep 1
    done
    ;;
  postgres)
    container="${ECOINDEX_DEV_DB_CONTAINER:-ecoindex-dev-postgres}"
    until docker exec "$container" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
      sleep 1
    done
    ;;
  *)
    echo "Unsupported DB_ENGINE for local dev: $DB_ENGINE" >&2
    exit 1
    ;;
esac
