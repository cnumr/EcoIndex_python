#!/usr/bin/env bash
set -euo pipefail

API_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$API_DIR/../.." && pwd)"

if [ -f "$API_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$API_DIR/.env"
  set +a
fi

cd "$ROOT"
uv run python projects/ecoindex_api/scripts/init_rustfs_bucket.py
