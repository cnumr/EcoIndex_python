import pytest
from ecoindex.models.scraper import (
    MimetypeAggregation,
    RequestDetail,
    RequestItem,
    aggregate_request_details,
    strip_query_params,
)


@pytest.mark.asyncio
async def test_get_category_of_resource_video() -> None:
    mime_type = "video/mp4"
    assert await MimetypeAggregation.get_category_of_resource(mime_type) == "video"


@pytest.mark.asyncio
async def test_get_category_of_resource_image() -> None:
    mime_type = "image/png"
    assert await MimetypeAggregation.get_category_of_resource(mime_type) == "image"


@pytest.mark.asyncio
async def test_get_category_of_resource_font() -> None:
    mime_type = "font/woff2"
    assert await MimetypeAggregation.get_category_of_resource(mime_type) == "font"


@pytest.mark.asyncio
async def test_get_category_of_resource_css() -> None:
    mime_type = "text/css"
    assert await MimetypeAggregation.get_category_of_resource(mime_type) == "css"


@pytest.mark.asyncio
async def test_get_category_of_resource_javascript() -> None:
    mime_type = "application/javascript"
    assert await MimetypeAggregation.get_category_of_resource(mime_type) == "javascript"


@pytest.mark.asyncio
async def test_get_category_of_resource_other() -> None:
    mime_type = "application/pdf"
    assert await MimetypeAggregation.get_category_of_resource(mime_type) == "other"


def test_strip_query_params() -> None:
    assert (
        strip_query_params("https://cdn.example.com/app.js?token=secret&v=1")
        == "https://cdn.example.com/app.js"
    )
    assert (
        strip_query_params("https://www.ecoindex.fr/path?foo=bar#section")
        == "https://www.ecoindex.fr/path#section"
    )
    assert strip_query_params("https://www.ecoindex.fr/") == "https://www.ecoindex.fr/"


def test_request_detail_from_request_item() -> None:
    item = RequestItem(
        category="javascript",
        domain="cdn.example.com",
        mime_type="application/javascript",
        size=1024,
        status=200,
        url="https://cdn.example.com/app.js?token=secret",
    )
    detail = RequestDetail.from_request_item(item)
    assert detail.category == "javascript"
    assert detail.domain == "cdn.example.com"
    assert detail.status == 200
    assert detail.url == item.url
    assert detail.size == 1024
    assert detail.id is None


def test_aggregate_request_details() -> None:
    items = [
        RequestDetail(
            category="html",
            domain="www.ecoindex.fr",
            status=200,
            url="https://www.ecoindex.fr/",
            size=1000,
        ),
        RequestDetail(
            category="css",
            domain="cdn.ecoindex.fr",
            status=200,
            url="https://cdn.ecoindex.fr/bundle.css",
            size=500,
        ),
        RequestDetail(
            category="javascript",
            domain="cdn.ecoindex.fr",
            status=200,
            url="https://cdn.ecoindex.fr/app.js",
            size=1500,
        ),
    ]
    response = aggregate_request_details(items)

    assert response.by_category.html.total_count == 1
    assert response.by_category.html.total_size == 1000
    assert response.by_category.css.total_count == 1
    assert response.by_category.css.total_size == 500
    assert response.by_category.javascript.total_count == 1
    assert response.by_category.javascript.total_size == 1500
    assert response.by_category.image.total_count == 0
    assert response.by_domain["www.ecoindex.fr"].total_count == 1
    assert response.by_domain["www.ecoindex.fr"].total_size == 1000
    assert response.by_domain["cdn.ecoindex.fr"].total_count == 2
    assert response.by_domain["cdn.ecoindex.fr"].total_size == 2000
    assert response.items == items


if __name__ == "__main__":
    pytest.main()
