from datetime import date
from typing import Any, cast

from ecoindex.database.helper import date_filter
from ecoindex.database.models import ApiEcoindex
from ecoindex.models.enums import Version
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_host_list_db(
    session: AsyncSession,
    version: Version = Version.v1,
    host: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 50,
) -> list[str]:
    statement = (
        select(ApiEcoindex.host)
        .where(ApiEcoindex.version == version.get_version_number())
        .offset(size * (page - 1))
        .limit(size)
    )

    if host:
        statement = statement.filter(cast(Any, ApiEcoindex.host).like(f"%{host}%"))

    statement = date_filter(statement=statement, date_from=date_from, date_to=date_to)

    statement = statement.group_by(ApiEcoindex.host).order_by(ApiEcoindex.host)

    hosts = await session.exec(statement=statement)

    return [str(host) for host in hosts.all()]


async def get_count_hosts_db(
    session: AsyncSession,
    version: Version = Version.v1,
    name: str | None = None,
    q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    group_by_host: bool = True,
) -> int:
    statement = select(ApiEcoindex.host).where(
        ApiEcoindex.version == version.get_version_number()
    )

    if name:
        statement = statement.where(ApiEcoindex.host == name)

    if q:
        statement = statement.where(cast(Any, ApiEcoindex.host).like(f"%{q}%"))

    statement = date_filter(statement=statement, date_from=date_from, date_to=date_to)

    if group_by_host:
        statement = statement.group_by(ApiEcoindex.host)
        count_statement = select(func.count()).select_from(statement.subquery())
    else:
        count_statement = select(func.count()).select_from(ApiEcoindex).where(
            ApiEcoindex.version == version.get_version_number()
        )
        if name:
            count_statement = count_statement.where(ApiEcoindex.host == name)
        if q:
            count_statement = count_statement.where(
                cast(Any, ApiEcoindex.host).like(f"%{q}%")
            )
        count_statement = date_filter(
            statement=count_statement, date_from=date_from, date_to=date_to
        )

    result = await session.exec(count_statement)

    return cast(int, result.one())
