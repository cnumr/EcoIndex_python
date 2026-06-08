from asyncio import run
from os import getcwd
from urllib.parse import urlparse

from ecoindex.backend.utils import check_quota, format_exception_response
from ecoindex.config.settings import Settings
from ecoindex.database.engine import get_session
from ecoindex.database.exceptions.quota import QuotaExceededException
from ecoindex.database.models import ApiEcoindex
from ecoindex.database.repositories.worker import save_ecoindex_result_db
from ecoindex.exceptions.scraper import EcoindexScraperStatusException
from ecoindex.exceptions.worker import (
    EcoindexContentTypeError,
    EcoindexHostUnreachable,
    EcoindexStatusError,
    EcoindexTimeout,
)
from ecoindex.models import ScreenShot, WindowSize
from ecoindex.models.enums import TaskStatus
from ecoindex.models.tasks import QueueTaskError, QueueTaskResult
from ecoindex.scraper.scrap import EcoindexScraper
from ecoindex.worker_component import app
from sentry_sdk import init as sentry_init

if Settings().GLITCHTIP_DSN:
    sentry_init(Settings().GLITCHTIP_DSN)


@app.task(
    name="ecoindex.analysis",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 5},
    timezone=Settings().TZ,
    queue="ecoindex",
    dont_autoretry_for=[EcoindexScraperStatusException, TypeError],
)
def ecoindex_task(
    self, url: str, width: int, height: int, custom_headers: dict[str, str]
) -> str:
    queue_task_result = run(
        async_ecoindex_task(
            self, url=url, width=width, height=height, custom_headers=custom_headers
        )
    )

    return queue_task_result.model_dump_json()


async def async_ecoindex_task(
    self,
    url: str,
    width: int,
    height: int,
    custom_headers: dict[str, str],
) -> QueueTaskResult:
    try:
        session_generator = get_session()
        session = await session_generator.__anext__()

        await check_quota(session=session, host=urlparse(url=url).netloc)

        ecoindex = await EcoindexScraper(
            url=url,
            window_size=WindowSize(height=height, width=width),
            wait_after_scroll=Settings().WAIT_AFTER_SCROLL,
            wait_before_scroll=Settings().WAIT_BEFORE_SCROLL,
            screenshot=ScreenShot(
                id=str(self.request.id), folder=f"{getcwd()}/screenshots/v1"
            )
            if Settings().ENABLE_SCREENSHOT
            else None,
            screenshot_gid=Settings().SCREENSHOTS_GID,
            screenshot_uid=Settings().SCREENSHOTS_UID,
            custom_headers=custom_headers,
        ).get_page_analysis()

        db_result = await save_ecoindex_result_db(
            session=session,
            id=self.request.id,
            ecoindex_result=ecoindex,
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

    except Exception as exc:
        message = getattr(exc, "message", str(exc))

        if message and "ERR_NAME_NOT_RESOLVED" in message:
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

        if message and "ERR_CONNECTION_TIMED_OUT" in message:
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

        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=url,  # type: ignore
                exception=type(exc).__name__,
                status_code=500,
                message=message,
                detail=await format_exception_response(exception=exc),
            ),
        )


@app.task(
    name="ecoindex.batch_import",
    timezone=Settings().TZ,
    queue="ecoindex_batch",
    bind=True,
)
def ecoindex_batch_import_task(self, results: list[dict], source: str):
    queue_task_result = run(
        async_ecoindex_batch_import_task(
            results=[ApiEcoindex.model_validate(result) for result in results],
            source=source,
        )
    )

    return queue_task_result.model_dump_json()


async def async_ecoindex_batch_import_task(
    results: list[ApiEcoindex], source: str
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
            )

        return QueueTaskResult(status=TaskStatus.SUCCESS)

    except Exception as exc:
        return QueueTaskResult(
            status=TaskStatus.FAILURE,
            error=QueueTaskError(
                url=None,
                exception=type(exc).__name__,
                status_code=500,
                message=str(exc.message) if exc.message else "",  # type: ignore
                detail=await format_exception_response(exception=exc),
            ),
        )
