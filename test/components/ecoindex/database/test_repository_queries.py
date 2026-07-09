import pytest
from ecoindex.database.repositories.ecoindex import get_count_analysis_db
from ecoindex.database.repositories.host import get_count_hosts_db
from ecoindex.models.enums import Version


class FakeResult:
    def __init__(self, value: int):
        self.value = value

    def scalar_one(self) -> int:
        return self.value


class FakeSession:
    def __init__(self, value: int = 1):
        self.value = value
        self.statement = None

    async def exec(self, statement):
        self.statement = statement
        return FakeResult(self.value)


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
