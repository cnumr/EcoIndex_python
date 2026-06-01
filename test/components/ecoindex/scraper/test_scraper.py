import json
from unittest.mock import MagicMock

import pytest
from ecoindex.exceptions.scraper import EcoindexScraperStatusException
from ecoindex.models import ScreenShot, WindowSize
from ecoindex.scraper import EcoindexScraper


def test_scraper_init():
    url = "https://www.example.com"
    scraper = EcoindexScraper(url=url)  # type: ignore
    assert scraper.url == url
    assert scraper.window_size == WindowSize(width=1920, height=1080)
    assert scraper.wait_before_scroll == 1
    assert scraper.wait_after_scroll == 1
    assert scraper.screenshot is None
    assert scraper.screenshot_uid is None
    assert scraper.screenshot_gid is None
    assert scraper.page_load_timeout == 20


def test_scraper_init_with_options():
    url = "https://www.example.com"
    window_size = WindowSize(width=800, height=600)
    wait_before_scroll = 2
    wait_after_scroll = 2
    screenshot_uid = 123
    screenshot_gid = 456
    page_load_timeout = 30
    screenshot_id = "123"
    screenshot_folder = "/tmp/screenshots"

    scraper = EcoindexScraper(
        url=url,  # type: ignore
        window_size=window_size,
        wait_before_scroll=wait_before_scroll,
        wait_after_scroll=wait_after_scroll,
        screenshot=ScreenShot(id=screenshot_id, folder=screenshot_folder),
        screenshot_uid=screenshot_uid,
        screenshot_gid=screenshot_gid,
        page_load_timeout=page_load_timeout,
    )

    assert scraper.url == url
    assert scraper.window_size == window_size
    assert scraper.wait_before_scroll == wait_before_scroll
    assert scraper.wait_after_scroll == wait_after_scroll
    assert scraper.screenshot.get_png() == f"{screenshot_folder}/{screenshot_id}.png"  # type: ignore
    assert scraper.screenshot.get_webp() == f"{screenshot_folder}/{screenshot_id}.webp"  # type: ignore
    assert scraper.screenshot_gid == screenshot_gid
    assert scraper.page_load_timeout == page_load_timeout


def test_get_request_size():
    mock_stripped_har_entry = (
        {
            "request": {
                "url": "https://www.ecoindex.fr/",
            },
            "response": {
                "status": 200,
                "headers": [
                    {"name": "content-length", "value": "7347"},
                ],
                "content": {
                    "mimeType": "text/html",
                },
                "_transferSize": 7772,
            },
        },
        {
            "request": {
                "url": "https://www.ecoindex.fr/",
            },
            "response": {
                "status": 200,
                "headers": [
                    {"name": "content-length", "value": "7347"},
                ],
                "content": {
                    "mimeType": "text/html",
                },
                "_transferSize": -1,
            },
        },
        {
            "request": {
                "url": "https://www.ecoindex.fr/",
            },
            "response": {
                "status": 206,
                "headers": [
                    {"name": "Content-Length", "value": "7347"},
                ],
                "content": {
                    "mimeType": "text/html",
                },
                "_transferSize": -1,
            },
        },
    )
    url = "https://www.example.com"
    window_size = WindowSize(width=800, height=600)
    wait_before_scroll = 2
    wait_after_scroll = 2
    screenshot_uid = 123
    screenshot_gid = 456
    page_load_timeout = 30
    screenshot_id = "123"
    screenshot_folder = "/tmp/screenshots"

    scraper = EcoindexScraper(
        url=url,  # type: ignore
        window_size=window_size,
        wait_before_scroll=wait_before_scroll,
        wait_after_scroll=wait_after_scroll,
        screenshot=ScreenShot(id=screenshot_id, folder=screenshot_folder),
        screenshot_uid=screenshot_uid,
        screenshot_gid=screenshot_gid,
        page_load_timeout=page_load_timeout,
    )
    assert scraper.get_request_size(mock_stripped_har_entry[0]) == 7772
    assert scraper.get_request_size(mock_stripped_har_entry[1]) == len(
        json.dumps(mock_stripped_har_entry[1]["response"]).encode("utf-8")
    )
    assert scraper.get_request_size(mock_stripped_har_entry[2]) == len(
        json.dumps(mock_stripped_har_entry[2]["response"]).encode("utf-8")
    )


def _mock_page_response(
    *, status: int, headers: dict[str, str], status_text: str = ""
) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.headers = headers
    response.status_text = status_text
    return response


@pytest.mark.asyncio
async def test_check_page_response():
    url = "https://www.example.com"
    window_size = WindowSize(width=800, height=600)
    wait_before_scroll = 2
    wait_after_scroll = 2
    screenshot_uid = 123
    screenshot_gid = 456
    page_load_timeout = 30
    screenshot_id = "123"
    screenshot_folder = "/tmp/screenshots"

    scraper = EcoindexScraper(
        url=url,  # type: ignore
        window_size=window_size,
        wait_before_scroll=wait_before_scroll,
        wait_after_scroll=wait_after_scroll,
        screenshot=ScreenShot(id=screenshot_id, folder=screenshot_folder),
        screenshot_uid=screenshot_uid,
        screenshot_gid=screenshot_gid,
        page_load_timeout=page_load_timeout,
    )

    with pytest.raises(TypeError) as type_error:
        await scraper.check_page_response(
            _mock_page_response(
                status=200, headers={"content-type": "audio/mpeg"}
            )
        )
    assert type_error.value.args[0] == {
        "mimetype": "audio/mpeg",
        "message": (
            "This resource is not a standard page with mimeType 'text/html'"
        ),
    }

    with pytest.raises(EcoindexScraperStatusException) as status_error:
        await scraper.check_page_response(
            _mock_page_response(
                status=404,
                headers={"content-type": "text/html"},
                status_text="Not Found",
            )
        )
    assert status_error.value.url == url
    assert status_error.value.status == 404
    assert status_error.value.message == "Not Found"

    assert (
        await scraper.check_page_response(
            _mock_page_response(
                status=200, headers={"content-type": "text/html"}
            )
        )
        is None
    )
