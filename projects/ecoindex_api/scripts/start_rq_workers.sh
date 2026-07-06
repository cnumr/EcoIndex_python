#!/bin/sh
set -e

RQ_WORKERS="${RQ_WORKERS:-3}"
REDIS_URL="${RQ_REDIS_URL:-redis://${REDIS_CACHE_HOST:-localhost}:6379/0}"

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
    --name "ecoindex-worker-$i" &
  i=$((i + 1))
done

wait
