#!/bin/sh
set -e

RQ_WORKERS="${RQ_WORKERS:-3}"
REDIS_URL="${RQ_REDIS_URL:-redis://${REDIS_CACHE_HOST:-localhost}:6379/0}"
HOST_ID="${RQ_WORKER_HOST:-${HOSTNAME:-local}}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

export RQ_WORKERS RQ_REDIS_URL="$REDIS_URL" RQ_WORKER_HOST="$HOST_ID"

if [ "${USE_UV:-0}" = "1" ]; then
  uv run python "$SCRIPT_DIR/clean_stale_rq_workers.py"
else
  python "$SCRIPT_DIR/clean_stale_rq_workers.py"
fi

start_worker() {
  if [ "${USE_UV:-0}" = "1" ]; then
    uv run --package ecoindex_api --group worker rq worker "$@"
  else
    rq worker "$@"
  fi
}

i=1
while [ "$i" -le "$RQ_WORKERS" ]; do
  start_worker ecoindex ecoindex_batch \
    --url "$REDIS_URL" \
    --name "ecoindex-worker-${HOST_ID}-$i" &
  i=$((i + 1))
done

wait
