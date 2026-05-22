from asyncio import run
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator

from ecoindex.models.compute import Result, WindowSize
from ecoindex.scraper.scrap import EcoindexScraper


def run_page_analysis(
    url: str,
    window_size: WindowSize,
    wait_after_scroll: int = 3,
    wait_before_scroll: int = 3,
    logger=None,
) -> tuple[Result, bool]:
    """Run the page analysis and return the result and a boolean indicating if the analysis was successful"""
    scraper = EcoindexScraper(
        url=str(url),
        window_size=window_size,
        wait_after_scroll=wait_after_scroll,
        wait_before_scroll=wait_before_scroll,
        page_load_timeout=20,
        logger=logger,
    )
    try:
        return (run(scraper.get_page_analysis()), True)
    except Exception as e:
        if logger:
            logger.error(f"{url} -- {e.msg if hasattr(e, 'msg') else e}")

        return (
            Result(
                url=url,
                water=0,
                width=window_size.width,
                height=window_size.height,
                size=0,
                nodes=0,
                requests=0,
            ),
            False,
        )


def bulk_analysis(
    max_workers,
    urls,
    window_sizes,
    wait_after_scroll: int = 0,
    wait_before_scroll: int = 0,
    logger=None,
) -> Generator[tuple[Result, bool], None, None]:
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_analysis = {}

        for url in urls:
            for window_size in window_sizes:
                future_to_analysis[
                    executor.submit(
                        run_page_analysis,
                        url,
                        window_size,
                        wait_after_scroll,
                        wait_before_scroll,
                        logger,
                    )
                ] = (
                    url,
                    window_size,
                    wait_after_scroll,
                    wait_before_scroll,
                    logger,
                )

        for future in as_completed(future_to_analysis):
            yield future.result()
