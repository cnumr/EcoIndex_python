from asyncio import run
from urllib.parse import urlparse
from uuid import UUID

from ecoindex.backend import get_api_version
from ecoindex.backend.utils import check_quota, format_exception_response
from ecoindex.config.settings import Settings
from ecoindex.database.engine import get_session
from ecoindex.database.exceptions.quota import QuotaExceededException
from ecoindex.database.models import ApiEcoindexBatchItem
from ecoindex.database.repositories.worker import save_ecoindex_result_db
from ecoindex.exceptions.scraper import EcoindexScraperStatusException
from ecoindex.exceptions.worker import (
    EcoindexContentTypeError,
    EcoindexHostUnreachable,
    EcoindexStatusError,
    EcoindexTimeout,
)
from ecoindex.models import ScreenShot, WindowSize
from ecoindex.models.enums import TaskStatus, Version
from ecoindex.models.scraper import RequestDetail
from ecoindex.models.tasks import QueueTaskError, QueueTaskResult
from ecoindex.monitoring import capture_task_failure, init_sentry
from ecoindex.scraper.scrap import EcoindexScraper
from ecoindex.screenshot_storage import (
    get_screenshot_local_folder,
    persist_screenshot,
)
from playwright._impl._errors import Error as WebDriverException
from rq import get_current_job

init_sentry(with_rq=True, release=get_api_version())


def _get_task_id() -> UUID:
    job = get_current_job()
    if job is None:
        raise RuntimeError("No RQ job context available")
    return UUID(job.id)


def ecoindex_task(
    url: str,
    width: int,
    height: int,
    custom_headers: dict[str, str],
    include_requests_detail: bool = False,
) -> str:
    queue_task_result = run(
        async_ecoindex_task(
            task_id=_get_task_id(),
            url=url,
            width=width,
            height=height,
            custom_headers=custom_headers,
            include_requests_detail=include_requests_detail,
        )
    )

    return queue_task_result.model_dump_json()


async def async_ecoindex_task(
    task_id: UUID,
    url: str,
    width: int,
    height: int,
    custom_headers: dict[str, str],
    include_requests_detail: bool = False,
) -> QueueTaskResult:
    try:
        settings = Settings()
        session_generator = get_session()
        session = await session_generator.__anext__()
        screenshot = (
            ScreenShot(
                id=str(task_id),
                folder=get_screenshot_local_folder(version=Version.v1.value),
            )
            if settings.ENABLE_SCREENSHOT
            else None
        )

        await check_quota(session=session, host=urlparse(url=url).netloc)

        scraper = EcoindexScraper(
            url=url,
            window_size=WindowSize(height=height, width=width),
            wait_after_scroll=settings.WAIT_AFTER_SCROLL,
            wait_before_scroll=settings.WAIT_BEFORE_SCROLL,
            screenshot=screenshot,
            screenshot_gid=settings.SCREENSHOTS_GID,
            screenshot_uid=settings.SCREENSHOTS_UID,
            custom_headers=custom_headers,
        )
        ecoindex = await scraper.get_page_analysis()
        request_details = (
            [
                RequestDetail.from_request_item(item)
                for item in await scraper.get_all_requests()
            ]
            if include_requests_detail
            else None
        )

        if screenshot:
            persist_screenshot(screenshot=screenshot, version=Version.v1.value)

        db_result = await save_ecoindex_result_db(
            session=session,
            id=task_id,
            ecoindex_result=ecoindex,
            requests=request_details,
        )

        return QueueTaskResult(status=TaskStatus.SUCCESS, detail=db_result)

    except QuotaExceededException as exc:
        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=url,  # type: ignore
                exception=QuotaExceededException.__name__,
                status_code=429,
                message=exc.message,
                detail=exc.__dict__,
            ),
        )

    except WebDriverException as exc:
        if exc.message and "ERR_NAME_NOT_RESOLVED" in exc.message:
            return QueueTaskResult(
                status=TaskStatus.FAILURE,
                error=QueueTaskError(
                    url=url,  # type: ignore
                    exception=EcoindexHostUnreachable.__name__,
                    status_code=502,
                    message=(
                        "This host is unreachable (error 502). "
                        "Are you really sure of this url? 🤔"
                    ),
                    detail=None,
                ),
            )

        if exc.message and "ERR_CONNECTION_TIMED_OUT" in exc.message:
            return QueueTaskResult(
                status=TaskStatus.FAILURE,
                error=QueueTaskError(
                    url=url,  # type: ignore
                    exception=EcoindexTimeout.__name__,
                    status_code=504,
                    message=(
                        "Timeout reached when requesting this url (error 504). "
                        "This is probably a temporary issue. 😥"
                    ),
                    detail=None,
                ),
            )

        capture_task_failure(
            exc,
            status_code=500,
            url=url,
            task_id=str(task_id),
            task_name="ecoindex_task",
        )
        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=url,  # type: ignore
                exception=type(exc).__name__,
                status_code=500,
                message=str(exc.message) if exc.message else "",
                detail=await format_exception_response(exception=exc),
            ),
        )

    except TypeError as exc:
        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=url,  # type: ignore
                exception=EcoindexContentTypeError.__name__,
                status_code=520,
                message=exc.args[0],
                detail={"mimetype": None},
            ),
        )

    except EcoindexScraperStatusException as exc:
        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=url,  # type: ignore
                status_code=521,
                exception=EcoindexStatusError.__name__,
                message=exc.message,
                detail={"status": exc.status},
            ),
        )


def ecoindex_batch_import_task(results: list[dict], source: str) -> str:
    queue_task_result = run(
        async_ecoindex_batch_import_task(
            results=[ApiEcoindexBatchItem.model_validate(result) for result in results],
            source=source,
        )
    )

    return queue_task_result.model_dump_json()


async def async_ecoindex_batch_import_task(
    results: list[ApiEcoindexBatchItem], source: str
) -> QueueTaskResult:
    try:
        session_generator = get_session()
        session = await session_generator.__anext__()

        for result in results:
            await save_ecoindex_result_db(
                session=session,
                id=result.id,  # type: ignore
                ecoindex_result=result,
                source=source,
                requests=result.request_details,
            )

        return QueueTaskResult(status=TaskStatus.SUCCESS)

    except Exception as exc:
        capture_task_failure(
            exc,
            status_code=500,
            task_name="ecoindex_batch_import_task",
        )
        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=None,  # type: ignore
                exception=type(exc).__name__,
                status_code=500,
                message=str(exc.message) if exc.message else "",  # type: ignore
                detail=await format_exception_response(exception=exc),
            ),
        )
