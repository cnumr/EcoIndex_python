from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.rq import RqIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from ecoindex.config.settings import Settings

INTERNAL_SERVER_ERROR_STATUS = 500


def _is_sentry_enabled() -> bool:
    return bool(Settings().SENTRY_DSN)


def get_sentry_environment() -> str:
    settings = Settings()
    if settings.SENTRY_ENVIRONMENT:
        return settings.SENTRY_ENVIRONMENT
    return "development" if settings.DEBUG else "production"


def init_sentry(
    *,
    with_fastapi: bool = False,
    with_rq: bool = False,
    release: str | None = None,
) -> None:
    settings = Settings()
    if not settings.SENTRY_DSN:
        return

    integrations = []
    if with_fastapi:
        integrations.extend(
            [
                StarletteIntegration(),
                FastApiIntegration(),
            ]
        )
    if with_rq:
        integrations.append(RqIntegration())

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=integrations,
        environment=get_sentry_environment(),
        release=release,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    )


def capture_internal_error(
    exception: BaseException,
    *,
    status_code: int = INTERNAL_SERVER_ERROR_STATUS,
    context: dict[str, Any] | None = None,
) -> None:
    if not _is_sentry_enabled():
        return
    if status_code != INTERNAL_SERVER_ERROR_STATUS:
        return

    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def capture_task_failure(
    exception: BaseException,
    *,
    status_code: int,
    url: str | None = None,
    task_id: str | None = None,
    task_name: str | None = None,
) -> None:
    context: dict[str, Any] = {}
    if url is not None:
        context["url"] = url
    if task_id is not None:
        context["task_id"] = task_id
    if task_name is not None:
        context["task_name"] = task_name

    capture_internal_error(exception, status_code=status_code, context=context)
