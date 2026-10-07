import json
import os
from datetime import datetime
from pathlib import Path
from time import sleep
from uuid import uuid4
from typing import Any, cast

from ua_generator.user_agent import UserAgent
from ua_generator import generate as ua_generate

from camoufox.async_api import AsyncCamoufox

from ecoindex.best_practices import (
    BestPracticesContext,
    BestPracticesEngine,
    BestPracticesReport,
    DomMetrics,
)
from ecoindex.compute import compute_ecoindex
from ecoindex.exceptions.scraper import EcoindexScraperStatusException
from ecoindex.models.compute import PageMetrics, Result, ScreenShot, WindowSize
from ecoindex.models.scraper import (
    DomainMetrics,
    MimetypeAggregation,
    RequestItem,
    Requests,
    get_domain_from_url,
)
from ecoindex.utils.screenshots import convert_screenshot_to_webp, set_screenshot_rights
from typing_extensions import deprecated

DOM_METRICS_SCRIPT = """
() => {
  const scripts = Array.from(document.scripts);
  const inlineJs = scripts.filter((s) => !s.src).length;
  const styles = Array.from(document.querySelectorAll("style")).filter(
    (el) => !(el instanceof SVGStyleElement)
  );
  const printStyles =
    document.querySelectorAll("link[rel=stylesheet][media~=print]").length +
    document.querySelectorAll("style[media~=print]").length;
  return {
    inline_js: inlineJs,
    inline_css: styles.length,
    print_stylesheet: printStyles,
  };
}
"""


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
        best_practices: bool | Path = False,
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
        self.best_practices_enabled = best_practices is not False
        self.best_practices_config_path: Path | None = (
            best_practices if isinstance(best_practices, Path) else None
        )
        self.dom_metrics = DomMetrics()
        self._best_practices_report: BestPracticesReport | None = None

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

    async def get_requests_by_domain(self) -> dict[str, DomainMetrics]:
        return self.all_requests.domain_aggregation

    async def get_best_practices(self) -> BestPracticesReport:
        if not self.best_practices_enabled:
            raise RuntimeError(
                "Best practices analysis is disabled. "
                "Initialize EcoindexScraper with best_practices=True "
                "or a Path to a YAML config."
            )
        if self._best_practices_report is None:
            raise RuntimeError(
                "Best practices report is not available yet. "
                "Call get_page_analysis() or scrap_page() first."
            )
        return self._best_practices_report

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
            if self.best_practices_enabled:
                self.dom_metrics = await self.get_dom_metrics()
            await self.page.close()
            await self.context.close()
            await browser.close()

        await self.get_requests_from_har_file()
        if self.best_practices_enabled:
            self._best_practices_report = self._run_best_practices()

        return PageMetrics(
            size=self.all_requests.total_size / 1000,
            nodes=total_nodes,
            requests=self.all_requests.total_count,
        )

    def _run_best_practices(self) -> BestPracticesReport:
        engine = BestPracticesEngine(self.best_practices_config_path)
        context = BestPracticesContext(
            requests=self.all_requests,
            dom=self.dom_metrics,
        )
        return engine.run(context)

    async def get_dom_metrics(self) -> DomMetrics:
        raw = await self.page.evaluate(DOM_METRICS_SCRIPT)
        return DomMetrics.model_validate(raw)

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
            domain_aggregation = self.all_requests.domain_aggregation.copy()

            for entry in trace["log"]["entries"]:
                url = entry["request"]["url"]
                domain = get_domain_from_url(url)
                mime_type = entry["response"]["content"]["mimeType"]
                category = await MimetypeAggregation.get_category_of_resource(mime_type)
                aggregation[category]["total_count"] += 1
                size = self.get_request_size(entry)
                aggregation[category]["total_size"] += size
                if domain not in domain_aggregation:
                    domain_aggregation[domain] = DomainMetrics()
                domain_aggregation[domain].total_count += 1
                domain_aggregation[domain].total_size += size
                self.all_requests.total_count += 1
                self.all_requests.total_size += size

                request_headers = {
                    h["name"].lower(): h["value"]
                    for h in entry.get("request", {}).get("headers", [])
                    if "name" in h and "value" in h
                }
                response_headers = {
                    h["name"].lower(): h["value"]
                    for h in entry.get("response", {}).get("headers", [])
                    if "name" in h and "value" in h
                }
                cookie_header = request_headers.get("cookie", "")

                self.all_requests.items.append(
                    RequestItem(
                        url=url,
                        domain=domain,
                        mime_type=mime_type,
                        status=entry["response"]["status"],
                        size=size,
                        category=category,
                        http_version=entry.get("response", {}).get("httpVersion"),
                        content_encoding=response_headers.get("content-encoding"),
                        cache_control=response_headers.get("cache-control"),
                        expires=response_headers.get("expires"),
                        response_date=response_headers.get("date"),
                        cookie_header_size=len(cookie_header),
                    )
                )
            self.all_requests.aggregation = MimetypeAggregation(**aggregation)
            self.all_requests.domain_aggregation = domain_aggregation
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
