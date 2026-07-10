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
