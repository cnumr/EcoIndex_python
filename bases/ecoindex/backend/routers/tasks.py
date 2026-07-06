from typing import Annotated
from urllib.parse import urlparse, urlunparse

import idna
import requests
from ecoindex.backend.dependencies.validation import validate_api_key_batch
from ecoindex.backend.models.dependencies_parameters.id import IdParameter
from ecoindex.backend.utils import check_quota
from ecoindex.config.settings import Settings
from ecoindex.database.engine import get_session
from ecoindex.database.models import ApiEcoindexes
from ecoindex.models import WebPage
from ecoindex.models.enums import TaskStatus
from ecoindex.models.response_examples import (
    example_daily_limit_response,
    example_host_unreachable,
)
from ecoindex.models.tasks import QueueTaskApi, QueueTaskApiBatch
from ecoindex.scraper.scrap import EcoindexScraper
from ecoindex.worker.tasks import ecoindex_batch_import_task, ecoindex_task
from ecoindex.worker_component import (
    NoSuchJobError,
    cancel_job,
    ecoindex_batch_queue,
    ecoindex_queue,
    fetch_job,
    get_queue_for_job,
    get_queue_position,
    get_retry_policy,
    get_tasks_in_progress,
    map_job_status_to_task_status,
    parse_job_result,
)
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.params import Body
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter(prefix="/v1/tasks/ecoindexes", tags=["Tasks"])


def convert_url_to_punycode(url: str) -> str:
    """
    Convert an URL with emoji domain (or any Unicode domain) to Punycode.
    This makes the URL compatible with requests library.

    Args:
        url: The URL string that may contain Unicode characters in the domain

    Returns:
        The URL with the domain converted to Punycode
    """
    parsed = urlparse(url)

    # Extract the hostname (netloc may contain port, so we need to handle that)
    hostname = parsed.hostname
    if not hostname:
        return url

    try:
        # Convert the hostname to Punycode
        hostname_punycode = idna.encode(hostname).decode("ascii")

        # Reconstruct the netloc with the converted hostname
        if parsed.port:
            netloc = f"{hostname_punycode}:{parsed.port}"
        else:
            netloc = hostname_punycode

        # Reconstruct the URL with the converted hostname
        return urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))
    except (idna.IDNAError, UnicodeError):
        # If conversion fails, return the original URL
        return url


def _enqueue_settings(*, with_retry: bool = True) -> dict:
    settings = Settings()
    enqueue_settings = {
        "result_ttl": settings.RQ_RESULT_TTL,
        "failure_ttl": settings.RQ_FAILURE_TTL,
        "job_timeout": settings.RQ_JOB_TIMEOUT,
    }
    if with_retry:
        enqueue_settings["retry"] = get_retry_policy()
    return enqueue_settings


@router.post(
    name="Add new ecoindex analysis task to the waiting queue",
    path="/",
    response_description="Identifier of the task that has been created in queue",
    responses={
        status.HTTP_201_CREATED: {"model": str},
        status.HTTP_403_FORBIDDEN: {"model": str},
        status.HTTP_429_TOO_MANY_REQUESTS: example_daily_limit_response,
        521: example_host_unreachable,
    },
    description="This submits a ecoindex analysis task to the engine",
    status_code=status.HTTP_201_CREATED,
)
async def add_ecoindex_analysis_task(
    response: Response,
    web_page: Annotated[
        WebPage,
        Body(
            default=...,
            title="Web page to analyze defined by its url and its screen resolution",
            example=WebPage(url="https://www.ecoindex.fr",
                            width=1920, height=1080),
        ),
    ],
    custom_headers: Annotated[
        dict[str, str],
        Body(
            description="Custom headers to add to the request",
            example={"X-My-Custom-Header": "MyValue"},
        ),
    ] = {},
    session: AsyncSession = Depends(get_session),
) -> str:
    if Settings().DAILY_LIMIT_PER_HOST:
        remaining_quota = await check_quota(
            session=session, host=web_page.get_url_host()
        )

        if remaining_quota:
            response.headers["X-Remaining-Daily-Requests"] = str(
                remaining_quota - 1)

    if (
        Settings().EXCLUDED_HOSTS
        and web_page.get_url_host() in Settings().EXCLUDED_HOSTS
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This host is excluded from the analysis",
        )

    ua = EcoindexScraper.get_user_agent()
    headers = {**custom_headers, **ua.headers.get()}

    # Convert URL to Punycode to handle emoji domains and other Unicode domains
    url_for_request = convert_url_to_punycode(str(web_page.url))

    try:
        r = requests.head(
            url=url_for_request,
            timeout=5,
            headers=headers,
        )
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=e.response.status_code
            if e.response
            else status.HTTP_400_BAD_REQUEST,
            detail=f"The URL {web_page.url} is unreachable. Are you really sure of this url? 🤔 ({e.response.status_code if e.response else ''})",
        )

    job = ecoindex_queue.enqueue(
        ecoindex_task,
        url=str(web_page.url),
        width=web_page.width,
        height=web_page.height,
        custom_headers=headers,
        **_enqueue_settings(),
    )

    return job.id


@router.get(
    name="Get ecoindex analysis task by id",
    path="/{id}",
    responses={
        status.HTTP_200_OK: {"model": QueueTaskApi},
        status.HTTP_425_TOO_EARLY: {"model": QueueTaskApi},
    },
    response_description="Get one ecoindex task result by its id",
    description="This returns an ecoindex given by its unique identifier",
)
async def get_ecoindex_analysis_task_by_id(
    response: Response,
    id: IdParameter,
) -> QueueTaskApi:
    try:
        job = fetch_job(str(id))
    except NoSuchJobError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc

    queue = get_queue_for_job(job)
    task_status = map_job_status_to_task_status(job)
    result = parse_job_result(job)

    task_response = QueueTaskApi(
        id=job.id,
        status=task_status,
        queue_position=get_queue_position(job, queue),
        tasks_in_progress=get_tasks_in_progress(queue),
    )

    if task_status == TaskStatus.PENDING:
        response.status_code = status.HTTP_425_TOO_EARLY

        return task_response

    if task_status == TaskStatus.SUCCESS:
        task_response.ecoindex_result = result

    if task_status == TaskStatus.FAILURE:
        task_response.task_error = result

    response.status_code = status.HTTP_200_OK

    return task_response


@router.delete(
    name="Abort ecoindex analysis by id",
    path="/{id}",
    response_description="Abort one ecoindex task by its id if it is still waiting",
    description="This aborts one ecoindex task by its id if it is still waiting",
)
async def delete_ecoindex_analysis_task_by_id(
    id: IdParameter,
) -> None:
    try:
        cancel_job(str(id))
    except NoSuchJobError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc


@router.post(
    name="Save ecoindex analysis from external source in batch mode",
    path="/batch",
    response_description="Identifier of the task that has been created in queue",
    responses={
        status.HTTP_201_CREATED: {"model": str},
        status.HTTP_403_FORBIDDEN: {"model": str},
    },
    description="This save ecoindex analysis from external source in batch mode. Limited to 100 entries at a time",
    status_code=status.HTTP_201_CREATED,
)
async def add_ecoindex_analysis_task_batch(
    results: Annotated[
        ApiEcoindexes,
        Body(
            default=...,
            title="List of ecoindex analysis results to save",
            example=[],
            min_length=1,
            max_length=100,
        ),
    ],
    batch_key: str = Depends(validate_api_key_batch),
):
    job = ecoindex_batch_queue.enqueue(
        ecoindex_batch_import_task,
        results=[result.model_dump() for result in results],
        source=batch_key["source"],  # type: ignore
        **_enqueue_settings(with_retry=False),
    )

    return job.id


@router.get(
    name="Get ecoindex analysis batch task by id",
    path="/batch/{id}",
    responses={
        status.HTTP_200_OK: {"model": QueueTaskApiBatch},
        status.HTTP_425_TOO_EARLY: {"model": QueueTaskApiBatch},
    },
    response_description="Get one ecoindex batch task result by its id",
    description="This returns an ecoindex batch task result given by its unique identifier",
)
async def get_ecoindex_analysis_batch_task_by_id(
    response: Response,
    id: IdParameter,
    _: str = Depends(validate_api_key_batch),
) -> QueueTaskApiBatch:
    try:
        job = fetch_job(str(id))
    except NoSuchJobError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc

    task_status = map_job_status_to_task_status(job)

    task_response = QueueTaskApiBatch(
        id=job.id,
        status=task_status,
    )

    if task_status == TaskStatus.PENDING:
        response.status_code = status.HTTP_425_TOO_EARLY

    return task_response
