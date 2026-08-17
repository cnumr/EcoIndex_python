from uuid import uuid4

import pytest
from ecoindex.database.models import ApiEcoindexRequest
from ecoindex.database.repositories.ecoindex import (
    get_count_analysis_db,
    get_requests_by_analysis_id_db,
)
from ecoindex.database.repositories.host import get_count_hosts_db
from ecoindex.database.repositories.worker import save_ecoindex_result_db
from ecoindex.models import Result
from ecoindex.models.enums import Version
from ecoindex.models.scraper import RequestDetail


class FakeResult:
    def __init__(self, value: int):
        self.value = value

    def one(self) -> int:
        return self.value


class FakeListResult:
    def __init__(self, value: list):
        self.value = value

    def all(self) -> list:
        return self.value


class FakeSession:
    def __init__(self, value: int = 1, rows: list | None = None):
        self.value = value
        self.rows = rows if rows is not None else []
        self.statement = None
        self.added: list = []
        self.committed = False
        self.refreshed = None
        self.closed = False

    async def exec(self, statement):
        self.statement = statement
        if self.rows:
            return FakeListResult(self.rows)
        return FakeResult(self.value)

    def add(self, obj) -> None:
        self.added.append(obj)

    def add_all(self, objs) -> None:
        self.added.extend(objs)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj) -> None:
        self.refreshed = obj

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_get_count_analysis_db_parameterizes_host():
    session = FakeSession()
    host = "vivalya-reseau.com'"

    count = await get_count_analysis_db(
        session=session,
        version=Version.v1,
        host=host,
    )

    assert count == 1
    assert session.statement is not None
    compiled = session.statement.compile()
    assert compiled.params["host_1"] == host
    assert "vivalya-reseau.com''" not in str(compiled)


@pytest.mark.asyncio
async def test_get_count_hosts_db_parameterizes_exact_name():
    session = FakeSession()
    host = "vivalya-reseau.com'"

    count = await get_count_hosts_db(
        session=session,
        version=Version.v1,
        name=host,
        group_by_host=False,
    )

    assert count == 1
    assert session.statement is not None
    compiled = session.statement.compile()
    assert compiled.params["host_1"] == host
    assert "vivalya-reseau.com''" not in str(compiled)


@pytest.mark.asyncio
async def test_get_requests_by_analysis_id_db_parameterizes_id():
    analysis_id = uuid4()
    rows = [
        ApiEcoindexRequest(
            analysis_id=analysis_id,
            category="html",
            domain="www.ecoindex.fr",
            status=200,
            url="https://www.ecoindex.fr/",
            size=1000,
        )
    ]
    session = FakeSession(rows=rows)

    result = await get_requests_by_analysis_id_db(
        session=session,
        analysis_id=analysis_id,
    )

    assert result == rows
    assert session.statement is not None
    compiled = session.statement.compile()
    assert compiled.params["analysis_id_1"] == analysis_id


@pytest.mark.asyncio
async def test_save_ecoindex_result_db_persists_stripped_request_urls(monkeypatch):
    analysis_id = uuid4()
    session = FakeSession()

    async def fake_rank(*_args, **_kwargs):
        return 1

    async def fake_count(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(
        "ecoindex.database.repositories.worker.get_rank_analysis_db",
        fake_rank,
    )
    monkeypatch.setattr(
        "ecoindex.database.repositories.worker.get_count_analysis_db",
        fake_count,
    )

    await save_ecoindex_result_db(
        session=session,
        id=analysis_id,
        ecoindex_result=Result(
            size=119,
            nodes=45,
            requests=2,
            url="https://www.ecoindex.fr",
            width=1920,
            height=1080,
            grade="A",
            score=89,
            ges=1.22,
            water=1.89,
        ),
        requests=[
            RequestDetail(
                category="javascript",
                domain="cdn.example.com",
                status=200,
                url="https://cdn.example.com/app.js?token=secret&v=2",
                size=1024,
            )
        ],
    )

    assert session.committed is True
    assert session.closed is True
    request_rows = [
        item for item in session.added if isinstance(item, ApiEcoindexRequest)
    ]
    assert len(request_rows) == 1
    assert request_rows[0].analysis_id == analysis_id
    assert request_rows[0].url == "https://cdn.example.com/app.js"
    assert request_rows[0].domain == "cdn.example.com"
    assert request_rows[0].category == "javascript"
