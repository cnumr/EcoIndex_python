from ecoindex.models.api import HealthWorker, HealthWorkers
from ecoindex.worker_component import redis_connection
from redis.exceptions import ConnectionError as RedisConnectionError
from rq.worker import Worker


def is_worker_healthy() -> HealthWorkers:
    try:
        workers = []
        for worker in Worker.all(connection=redis_connection):
            workers.append(
                HealthWorker(
                    name=worker.name,
                    healthy=worker.state in ("busy", "idle"),
                )
            )
    except RedisConnectionError:
        return HealthWorkers(healthy=False, workers=[])

    return HealthWorkers(
        healthy=bool(workers) and all(w.healthy for w in workers),
        workers=workers,
    )
