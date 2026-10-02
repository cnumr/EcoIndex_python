from datetime import date
from typing import cast
from uuid import UUID

from ecoindex.database.helper import date_filter
from ecoindex.database.models import (
    ApiEcoindex,
    ApiEcoindexBestPractice,
    ApiEcoindexBestPracticeResult,
    ApiEcoindexRequest,
    BestPracticeResultItem,
    BestPracticesAnalysisResponse,
)
from ecoindex.models import Result
from ecoindex.models.enums import Version
from ecoindex.models.sort import Sort
from sqlalchemy import func, text
from sqlalchemy.sql.expression import asc, desc
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_count_analysis_db(
    session: AsyncSession,
    version: Version = Version.v1,
    host: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> int:
    statement = select(func.count()).select_from(ApiEcoindex).where(
        ApiEcoindex.version == version.get_version_number()
    )

    if host:
        statement = statement.where(ApiEcoindex.host == host)

    statement = date_filter(statement=statement, date_from=date_from, date_to=date_to)

    result = await session.exec(statement)

    return cast(int, result.one())


async def get_rank_analysis_db(
    session: AsyncSession, ecoindex: Result, version: Version = Version.v1
) -> int | None:
    statement = (
        "SELECT ranking FROM ("
        "SELECT *, ROW_NUMBER() OVER (ORDER BY score DESC) ranking "
        "FROM apiecoindex "
        f"WHERE version={version.get_version_number()} "
        "ORDER BY score DESC) t "
        f"WHERE score <= {ecoindex.score} "
        "LIMIT 1;"
    )

    result = await session.exec(text(statement))  # type: ignore

    return result.scalar_one_or_none()


async def get_ecoindex_result_list_db(
    session: AsyncSession,
    version: Version = Version.v1,
    host: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 50,
    sort_params: list[Sort] = [],
) -> list[ApiEcoindex]:
    statement = (
        select(ApiEcoindex)
        .where(ApiEcoindex.version == version.get_version_number())
        .offset((page - 1) * size)
        .limit(size)
    )

    if host:
        statement = statement.where(ApiEcoindex.host == host)
    statement = date_filter(statement=statement, date_from=date_from, date_to=date_to)

    for sort in sort_params:
        if sort.sort == "asc":
            sort_parameter = asc(sort.clause)  # type: ignore
        elif sort.sort == "desc":
            sort_parameter = desc(sort.clause)

        statement = statement.order_by(sort_parameter)  # type: ignore

    ecoindexes = await session.exec(statement)

    return [ecoindex for ecoindex in ecoindexes.all()]


async def get_ecoindex_result_by_id_db(
    session: AsyncSession, id: UUID, version: Version = Version.v1
) -> ApiEcoindex | None:
    statement = (
        select(ApiEcoindex)
        .where(ApiEcoindex.id == id)
        .where(ApiEcoindex.version == version.get_version_number())
    )

    ecoindex = await session.exec(statement)

    return ecoindex.one_or_none()


async def get_requests_by_analysis_id_db(
    session: AsyncSession, analysis_id: UUID
) -> list[ApiEcoindexRequest]:
    statement = select(ApiEcoindexRequest).where(
        ApiEcoindexRequest.analysis_id == analysis_id
    )
    result = await session.exec(statement)

    return list(result.all())


async def get_best_practice_results_by_analysis_id_db(
    session: AsyncSession, analysis_id: UUID
) -> BestPracticesAnalysisResponse | None:
    statement = (
        select(ApiEcoindexBestPracticeResult, ApiEcoindexBestPractice)
        .join(
            ApiEcoindexBestPractice,
            ApiEcoindexBestPractice.id
            == ApiEcoindexBestPracticeResult.best_practice_id,
        )
        .where(ApiEcoindexBestPracticeResult.analysis_id == analysis_id)
    )
    result = await session.exec(statement)
    rows = list(result.all())
    if not rows:
        return None

    items: list[BestPracticeResultItem] = []
    ok_count = warn_count = fail_count = 0
    for result_row, practice in rows:
        items.append(
            BestPracticeResultItem(
                id=result_row.id,
                rule_id=practice.rule_id,
                rweb_id=practice.rweb_id,
                category=practice.category,
                title=practice.title,
                description=practice.description,
                url=practice.url,
                status=result_row.status,
                value=result_row.value,
                threshold_warn=result_row.threshold_warn,
                threshold_fail=result_row.threshold_fail,
                message=result_row.message,
                details=list(result_row.details or []),
            )
        )
        if result_row.status == "ok":
            ok_count += 1
        elif result_row.status == "warn":
            warn_count += 1
        elif result_row.status == "fail":
            fail_count += 1

    return BestPracticesAnalysisResponse(
        results=items,
        ok_count=ok_count,
        warn_count=warn_count,
        fail_count=fail_count,
    )


async def get_count_daily_request_per_host(session: AsyncSession, host: str) -> int:
    statement = select(ApiEcoindex).where(
        func.date(ApiEcoindex.date) == date.today(), ApiEcoindex.host == host
    )

    results = await session.exec(statement)

    return len(results.all())


async def get_latest_result(session: AsyncSession, host: str) -> ApiEcoindex | None:
    statement = (
        select(ApiEcoindex)
        .where(ApiEcoindex.host == host)
        .order_by(text("date desc"))
        .limit(1)
    )

    result = await session.exec(statement)

    return result.one_or_none()
