from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from ecoindex.backend.routers.ecoindex import get_ecoindex_analysis_requests_by_id
from ecoindex.models.enums import Version
from ecoindex.models.scraper import RequestDetail, RequestsDetailResponse
from fastapi import HTTPException, Response, status


@pytest.mark.asyncio
async def test_get_requests_returns_204_when_analysis_exists_without_rows(
    monkeypatch,
):
    monkeypatch.setattr(
        "ecoindex.backend.routers.ecoindex.get_ecoindex_result_by_id_db",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        "ecoindex.backend.routers.ecoindex.get_requests_by_analysis_id_db",
        AsyncMock(return_value=[]),
    )

    result = await get_ecoindex_analysis_requests_by_id(
        id=uuid4(),
        version=Version.v1,
        session=AsyncMock(),
    )

    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_204_NO_CONTENT
    assert not result.body


@pytest.mark.asyncio
async def test_get_requests_raises_404_when_analysis_is_missing(monkeypatch):
    analysis_id = uuid4()
    monkeypatch.setattr(
        "ecoindex.backend.routers.ecoindex.get_ecoindex_result_by_id_db",
        AsyncMock(return_value=None),
    )
    get_requests = AsyncMock()
    monkeypatch.setattr(
        "ecoindex.backend.routers.ecoindex.get_requests_by_analysis_id_db",
        get_requests,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_ecoindex_analysis_requests_by_id(
            id=analysis_id,
            version=Version.v1,
            session=AsyncMock(),
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(analysis_id) in str(exc_info.value.detail)
    get_requests.assert_not_called()


@pytest.mark.asyncio
async def test_get_requests_returns_payload_when_rows_exist(monkeypatch):
    analysis_id = uuid4()
    monkeypatch.setattr(
        "ecoindex.backend.routers.ecoindex.get_ecoindex_result_by_id_db",
        AsyncMock(return_value=object()),
    )
    monkeypatch.setattr(
        "ecoindex.backend.routers.ecoindex.get_requests_by_analysis_id_db",
        AsyncMock(
            return_value=[
                RequestDetail(
                    category="html",
                    domain="www.ecoindex.fr",
                    status=200,
                    url="https://www.ecoindex.fr/",
                    size=1000,
                )
            ]
        ),
    )

    result = await get_ecoindex_analysis_requests_by_id(
        id=analysis_id,
        version=Version.v1,
        session=AsyncMock(),
    )

    assert isinstance(result, RequestsDetailResponse)
    assert len(result.items) == 1
    assert result.items[0].domain == "www.ecoindex.fr"
