from tempfile import NamedTemporaryFile
from typing import Set, cast
from urllib.parse import urlparse, urlunparse

from ecoindex.cli.crawl import EcoindexSpider
from ecoindex.cli.helper import replace_localhost_with_hostdocker
from ecoindex.cli.sitemap import EcoindexSitemapSpider
from ecoindex.models import WindowSize

from pydantic import AnyHttpUrl, TypeAdapter, validate_call
from pydantic.types import FilePath
from scrapy.crawler import CrawlerProcess

_any_http_url_adapter = TypeAdapter(AnyHttpUrl)


def _parse_any_http_url(url: str) -> AnyHttpUrl:
    return cast(AnyHttpUrl, _any_http_url_adapter.validate_python(url))


@validate_call
def validate_list_of_urls(urls: list[AnyHttpUrl]) -> Set[str]:
    result = set()

    for url in urls:
        splitted_url = str(url).split("?")
        result.add(splitted_url[0])

    return result


@validate_call
def get_urls_from_file(urls_file: FilePath) -> Set[str]:
    with open(urls_file) as fp:
        urls_from_file = set()

        for url in fp.readlines():
            url = url.strip()

            if url:
                urls_from_file.add(url)

    return validate_list_of_urls(urls_from_file)  # type: ignore


def get_urls_recursive(main_url: str) -> Set[str]:
    parsed_url = urlparse(main_url)
    host_infos = replace_localhost_with_hostdocker(parsed_url.netloc)
    netloc = host_infos.netloc
    domain = host_infos.domain
    main_url = f"{parsed_url.scheme}://{netloc}"
    process = CrawlerProcess()

    with NamedTemporaryFile(mode="w+t") as temp_file:
        process.crawl(
            crawler_or_spidercls=EcoindexSpider,
            allowed_domains=[domain],
            start_urls=[main_url],
            temp_file=temp_file,
        )
        process.start()
        temp_file.seek(0)
        urls = temp_file.readlines()
    return validate_list_of_urls(urls)  # type: ignore


def get_urls_from_sitemap(main_url: str) -> Set[str]:
    process = CrawlerProcess()
    if "sitemap" not in main_url or not main_url.endswith(".xml"):
        raise ValueError("The provided url is not a valid sitemap url")

    with NamedTemporaryFile(mode="w+t") as temp_file:
        process.crawl(
            crawler_or_spidercls=EcoindexSitemapSpider, 
            sitemap_urls=[main_url],
            temp_file=temp_file,
        )
        process.start()
        temp_file.seek(0)
        urls = list()
        str_urls = temp_file.readlines()
        for url in str_urls:
            urls.append(_parse_any_http_url(url))

    return validate_list_of_urls(urls)


@validate_call
def get_url_from_args(urls_arg: list[AnyHttpUrl]) -> set[AnyHttpUrl]:
    urls_from_args = set()
    for url in urls_arg:
        parsed_url = urlparse(str(url))
        host_infos = replace_localhost_with_hostdocker(parsed_url.netloc)
        url = _parse_any_http_url(
            urlunparse(
                (
                    parsed_url.scheme,
                    host_infos.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )
        )
        urls_from_args.add(url)

    return urls_from_args


def get_window_sizes_from_args(window_sizes: list[str]) -> list[WindowSize]:
    result = []
    errors = ""
    for window_size in window_sizes:
        try:
            width, height = window_size.split(",")
            result.append(WindowSize(width=int(width), height=int(height)))
        except ValueError:
            errors += f"🔥 `{window_size}` is not a valid window size. Must be of type `1920,1080`\n"

    if errors:
        raise ValueError(errors)

    return result


def get_file_prefix_input_file_logger_file(
    urls: list[AnyHttpUrl],
    urls_file: str | None = None,
    tmp_folder: str = "/tmp/ecoindex-cli",
) -> tuple[str, str, str]:
    """
    Returns file prefix, input file and logger file based on provided urls
    and provider method: If this is based on an existing csv file, we take
    the name of the file, else, we take the first provided url's domain
    """
    if urls_file:
        file_prefix = urls_file.split("/")[-1]
        input_file = urls_file
    else:
        first_url = str(next(iter(urls)))
        file_prefix = urlparse(first_url).netloc
        input_file = f"{tmp_folder}/input/{file_prefix}.csv"

    return (file_prefix, input_file, f"{tmp_folder}/logs/{file_prefix}.log")
