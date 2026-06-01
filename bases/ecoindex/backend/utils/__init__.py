import re
from json import loads
from uuid import UUID, uuid4

from ecoindex.config.settings import Settings
from ecoindex.database.exceptions.quota import QuotaExceededException
from ecoindex.database.repositories.ecoindex import (
    get_count_daily_request_per_host,
    get_latest_result,
)
from ecoindex.models.api import ExceptionResponse
from ecoindex.models.sort import Sort
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession


async def format_exception_response(exception: Exception) -> ExceptionResponse:
    return ExceptionResponse(
        exception=type(exception).__name__,
        args=[arg for arg in exception.args if arg] if exception.args else [],
        message=exception.msg if hasattr(exception, "msg") else None,  # type: ignore
    )


async def new_uuid() -> UUID:
    val = uuid4()
    while val.hex[0] == "0":
        val = uuid4()
    return val


async def get_status_code(items: list, total: int) -> int:
    if not items:
        return status.HTTP_404_NOT_FOUND

    if total > len(items):
        return status.HTTP_206_PARTIAL_CONTENT

    return status.HTTP_200_OK


async def get_sort_parameters(query_params: list[str], model: BaseModel) -> list[Sort]:
    validation_error = []
    result = []

    for query_param in query_params:
        pattern = re.compile(r"^\w+:(asc|desc)$")

        if not re.fullmatch(pattern, query_param):
            validation_error.append(
                {
                    "loc": ["query", "sort", query_param],
                    "message": "this parameter does not respect the sort format",
                    "type": "value_error.sort",
                }
            )
            continue

        sort_params = query_param.split(":")

        if sort_params[0] not in model.__fields__:
            validation_error.append(
                {
                    "loc": ["query", "sort", sort_params[0]],
                    "message": "this parameter does not exist",
                    "type": "value_error.sort",
                }
            )
            continue

        result.append(Sort(clause=sort_params[0], sort=sort_params[1]))  # type: ignore

    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation_error
        )

    return result


async def check_quota(
    session: AsyncSession,
    host: str,
) -> int | None:
    if not Settings().DAILY_LIMIT_PER_HOST:
        return None

    count_daily_request_per_host = await get_count_daily_request_per_host(
        session=session, host=host
    )

    if count_daily_request_per_host >= Settings().DAILY_LIMIT_PER_HOST:
        latest_result = await get_latest_result(session=session, host=host)
        raise QuotaExceededException(
            limit=Settings().DAILY_LIMIT_PER_HOST,
            host=host,
            latest_result=loads(latest_result.model_dump_json() or "{}"),  # type: ignore
        )

    return Settings().DAILY_LIMIT_PER_HOST - count_daily_request_per_host
