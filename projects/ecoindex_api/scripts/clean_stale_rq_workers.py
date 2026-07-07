"""Unregister stale RQ workers before starting new worker processes."""

from __future__ import annotations

import os
import time

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Worker
from rq.utils import utcparse
from rq.worker.base import BaseWorker

WORKER_NAME_PREFIX = "ecoindex-worker-"


def redis_url() -> str:
    return os.environ.get(
        "RQ_REDIS_URL",
        f"redis://{os.environ.get('REDIS_CACHE_HOST', 'localhost')}:6379/0",
    )


def worker_host_id() -> str:
    return os.environ.get("RQ_WORKER_HOST") or os.environ.get("HOSTNAME", "local")


def planned_worker_names() -> set[str]:
    worker_count = int(os.environ.get("RQ_WORKERS", "3"))
    host_id = worker_host_id()
    names = {f"{WORKER_NAME_PREFIX}{host_id}-{index}" for index in range(1, worker_count + 1)}
    # Legacy fixed names kept during transition from older deployments.
    names.update(f"{WORKER_NAME_PREFIX}{index}" for index in range(1, worker_count + 1))
    return names


def is_stale(worker: BaseWorker, max_age_seconds: int) -> bool:
    if worker.last_heartbeat is None:
        return True

    heartbeat = worker.last_heartbeat
    if isinstance(heartbeat, str):
        heartbeat = utcparse(heartbeat)

    return (time.time() - heartbeat.timestamp()) > max_age_seconds


def cleanup_stale_workers(connection: Redis, max_age_seconds: int) -> None:
    planned_names = planned_worker_names()

    for worker in Worker.all(connection=connection):
        if not worker.name.startswith(WORKER_NAME_PREFIX):
            continue

        if worker.name not in planned_names and not is_stale(worker, max_age_seconds):
            continue

        worker.register_death()


def main() -> None:
    max_age_seconds = int(os.environ.get("RQ_STALE_WORKER_SECONDS", "60"))

    try:
        connection = Redis.from_url(redis_url())
        cleanup_stale_workers(connection, max_age_seconds)
    except RedisConnectionError as exc:
        raise SystemExit(f"Redis is not reachable: {exc}") from exc


if __name__ == "__main__":
    main()
