import json
import os
from datetime import datetime
from time import sleep
from uuid import uuid4
from typing import Any, cast

from ua_generator.user_agent import UserAgent
from ua_generator import generate as ua_generate

from camoufox.async_api import AsyncCamoufox

from ecoindex.compute import compute_ecoindex
from ecoindex.exceptions.scraper import EcoindexScraperStatusException
from ecoindex.models.compute import PageMetrics, Result, ScreenShot, WindowSize
from ecoindex.models.scraper import MimetypeAggregation, RequestItem, Requests
from ecoindex.utils.screenshots import convert_screenshot_to_webp, set_screenshot_rights
from typing_extensions import deprecated


class EcoindexScraper:
    def __init__(
        self,
        url: str,
        window_size: WindowSize = WindowSize(width=1920, height=1080),
        wait_before_scroll: float = 1,
        wait_after_scroll: float = 1,
        screenshot: ScreenShot | None = None,
        screenshot_uid: int | None = None,
        screenshot_gid: int | None = None,
        page_load_timeout: int = 20,
        headless: bool = True,
        basic_auth: str | None = None,
        cookies: list[dict[str, object]] = [],
        custom_headers: dict[str, str] = {},
        logger=None,
    ):
        self.url = url
        self.window_size = window_size
        self.wait_before_scroll = wait_before_scroll
        self.wait_after_scroll = wait_after_scroll
        self.screenshot = screenshot
        self.screenshot_uid = screenshot_uid
        self.screenshot_gid = screenshot_gid
        self.page_load_timeout = page_load_timeout
        self.all_requests = Requests()
        self.now = datetime.now()
        self.har_temp_file_path = (
            f"/tmp/ecoindex-{self.now.strftime('%Y-%m-%d-%H-%M-%S-%f')}-{uuid4()}.har"
        )
        self.headless = headless
        self.basic_auth = basic_auth
        self.cookies = cookies
        self.custom_headers = custom_headers
        self.logger = logger

    @staticmethod
    def get_user_agent() -> UserAgent:
        return ua_generate(
            device="desktop",
            browser="chrome",
            platform="linux",
        )

    @deprecated("This method is useless with new version of EcoindexScraper")
    def init_chromedriver(self):
        return self

    async def get_page_analysis(self) -> Result:
        page_metrics = await self.scrap_page()
        ecoindex = await compute_ecoindex(**page_metrics.model_dump())

        return Result(
            **ecoindex.model_dump(),
            **self.window_size.model_dump(),
            **page_metrics.model_dump(),
            date=self.now,
            url=self.url,
        )

    async def get_all_requests(self) -> list[RequestItem]:
        return self.all_requests.items

    async def get_requests_by_category(self) -> MimetypeAggregation:
        return self.all_requests.aggregation

    async def scrap_page(self) -> PageMetrics:
        async with AsyncCamoufox(
            headless=self.headless,
            window=(self.window_size.width, self.window_size.height),
        ) as browser_handle:
            browser = cast(Any, browser_handle)
            self.context = await browser.new_context(
                record_har_path=self.har_temp_file_path,
                ignore_https_errors=True,
                http_credentials={
                    "username": self.basic_auth.split(":")[0],
                    "password": self.basic_auth.split(":")[1],
                }
                if self.basic_auth
                else None,
                extra_http_headers=self.custom_headers,
            )
            await self.context.add_cookies(cast(Any, self.cookies))
            self.page = await self.context.new_page()
            response = await self.page.goto(self.url)
            await self.check_page_response(response)
            await self.page.wait_for_load_state()
            sleep(self.wait_before_scroll)
            await self.generate_screenshot()
            await self.page.keyboard.press("ArrowDown")
            await self.page.evaluate(
                "window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })"
            )
            sleep(self.wait_after_scroll)
            total_nodes = await self.get_nodes_count()
            await self.page.close()
            await self.context.close()
            await browser.close()

        await self.get_requests_from_har_file()

        return PageMetrics(
            size=self.all_requests.total_size / 1000,
            nodes=total_nodes,
            requests=self.all_requests.total_count,
        )

    async def generate_screenshot(self) -> None:
        if self.screenshot and self.screenshot.folder and self.screenshot.id:
            await self.page.screenshot(path=self.screenshot.get_png())
            try:
                await convert_screenshot_to_webp(self.screenshot)
            except ImportError:
                if self.logger:
                    self.logger.warning(
                        "WebP conversion skipped: Pillow library is not installed."
                    )
            await set_screenshot_rights(
                screenshot=self.screenshot,
                uid=self.screenshot_uid,
                gid=self.screenshot_gid,
            )

    async def get_requests_from_har_file(self):
        with open(self.har_temp_file_path, "r") as f:
            trace = json.load(f)
            aggregation = self.all_requests.aggregation.model_dump()

            for entry in trace["log"]["entries"]:
                url = entry["request"]["url"]
                mime_type = entry["response"]["content"]["mimeType"]
                category = await MimetypeAggregation.get_category_of_resource(mime_type)
                aggregation[category]["total_count"] += 1
                size = self.get_request_size(entry)
                aggregation[category]["total_size"] += size
                self.all_requests.total_count += 1
                self.all_requests.total_size += size
                self.all_requests.items.append(
                    RequestItem(
                        url=url,
                        mime_type=mime_type,
                        status=entry["response"]["status"],
                        size=size,
                        category=category,
                    )
                )
            self.all_requests.aggregation = MimetypeAggregation(**aggregation)
        os.remove(self.har_temp_file_path)

    async def get_nodes_count(self) -> int:
        nodes = await self.page.locator("*").all()
        svgs = await self.page.locator("//*[local-name()='svg']//*").all()

        return len(nodes) - len(svgs)

    def get_request_size(self, entry) -> int:
        if entry["response"]["_transferSize"] != -1:
            return entry["response"]["_transferSize"]
        else:
            return len(json.dumps(entry["response"]).encode("utf-8"))

    async def check_page_response(self, response) -> None:
        if response and response.status != 200:
            raise EcoindexScraperStatusException(
                url=self.url,
                status=response.status,
                message=response.status_text,
            )
        headers = response.headers
        content_type = next(
            (value for key, value in headers.items() if key.lower() == "content-type"),
            None,
        )
        if content_type and "text/html" not in content_type:
            raise TypeError(
                {
                    "mimetype": content_type,
                    "message": (
                        "This resource is not a standard page with mimeType 'text/html'"
                    ),
                }
            )
