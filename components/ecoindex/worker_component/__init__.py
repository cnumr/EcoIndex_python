from json import loads
from typing import Any

from ecoindex.config.settings import Settings
from ecoindex.models.enums import TaskStatus
from ecoindex.models.tasks import QueueTaskResult
from redis import Redis
from rq import Queue, Retry
from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq.registry import StartedJobRegistry

ECOINDEX_QUEUE_NAME = "ecoindex"
ECOINDEX_BATCH_QUEUE_NAME = "ecoindex_batch"

_settings = Settings()


def get_redis_connection() -> Redis:
    return Redis(host=_settings.REDIS_CACHE_HOST, port=6379, db=0)


redis_connection: Redis = get_redis_connection()

ecoindex_queue: Queue = Queue(
    ECOINDEX_QUEUE_NAME,
    connection=redis_connection,
    default_result_ttl=_settings.RQ_RESULT_TTL,
)
ecoindex_batch_queue: Queue = Queue(
    ECOINDEX_BATCH_QUEUE_NAME,
    connection=redis_connection,
    default_result_ttl=_settings.RQ_RESULT_TTL,
)

_queues_by_name: dict[str, Queue] = {
    ECOINDEX_QUEUE_NAME: ecoindex_queue,
    ECOINDEX_BATCH_QUEUE_NAME: ecoindex_batch_queue,
}


def get_retry_policy() -> Retry:
    return Retry(max=5, interval=[5, 10, 20, 40, 80])


def get_queue_for_job(job: Job) -> Queue:
    return _queues_by_name.get(job.origin, ecoindex_queue)


def get_tasks_in_progress(queue: Queue) -> int:
    return StartedJobRegistry(queue.name, connection=queue.connection).count


def fetch_job(job_id: str) -> Job:
    return Job.fetch(job_id, connection=redis_connection)


def map_job_status_to_task_status(job: Job) -> TaskStatus:
    status = job.get_status()
    if status == "finished":
        return TaskStatus.SUCCESS
    if status == "failed":
        return TaskStatus.FAILURE
    return TaskStatus.PENDING


def get_queue_position(job: Job, queue: Queue) -> int | None:
    if job.get_status() != "queued":
        return None
    return queue.get_job_position(job)


def parse_job_result(job: Job) -> QueueTaskResult | Any | None:
    if job.get_status() == "finished":
        result = job.result
        if isinstance(result, str):
            return QueueTaskResult(**loads(result))
        return result
    if job.get_status() == "failed":
        return job.exc_info
    return None


def cancel_job(job_id: str) -> None:
    from rq.command import send_stop_job_command

    job = fetch_job(job_id)
    status = job.get_status()
    if status == "queued":
        job.cancel()
    elif status == "started":
        send_stop_job_command(redis_connection, job.id)


__all__ = [
    "ECOINDEX_BATCH_QUEUE_NAME",
    "ECOINDEX_QUEUE_NAME",
    "NoSuchJobError",
    "cancel_job",
    "ecoindex_batch_queue",
    "ecoindex_queue",
    "fetch_job",
    "get_queue_for_job",
    "get_queue_position",
    "get_retry_policy",
    "get_tasks_in_progress",
    "map_job_status_to_task_status",
    "parse_job_result",
    "redis_connection",
]
