# Ecoindex Scraper

[![Validate project quality](https://github.com/cnumr/ecoindex_python_fullstack/actions/workflows/quality_check.yml/badge.svg?branch=main)](https://github.com/cnumr/ecoindex_python_fullstack/actions/workflows/quality_check.yml)

![PyPI - Version](https://img.shields.io/pypi/v/ecoindex-scraper?logo=pypi)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ecoindex-scraper?style=social&logo=pypi)

This module provides a simple interface to get the [Ecoindex](http://www.ecoindex.fr) of a given webpage using module [ecoindex-compute](https://pypi.org/project/ecoindex-compute/)

## Requirements

- Python ^3.10 with [pip](https://pip.pypa.io/en/stable/installation/)
- [Camoufox](https://camoufox.com/python/installation/) for the browser binary

## Install

```shell
pip install ecoindex_scraper
python -m camoufox fetch
```

If you need to convert the screenshot to webp with the `generate_screenshot` method, you need to install the Pillow dependency.

```shell
pip install ecoindex_scraper[webp] # OR directly pillow
```

## Use

### Get a page analysis

You can run a page analysis by calling the function `get_page_analysis()`:

```python
(function) get_page_analysis: (url: AnyHttpUrl, window_size: WindowSize | None = WindowSize(width=1920, height=1080), wait_before_scroll: int | None = 1, wait_after_scroll: int | None = 1) -> Coroutine[Any, Any, Result]
```

Example:

```python
import asyncio
from pprint import pprint

from ecoindex.scraper import EcoindexScraper

pprint(
    asyncio.run(
        EcoindexScraper(url="http://ecoindex.fr").get_page_analysis()
    )
)
```

Result example:

```python
Result(width=1920, height=1080, url=AnyHttpUrl('http://ecoindex.fr', ), size=549.253, nodes=52, requests=12, grade='A', score=90.0, ges=1.2, water=1.8, ecoindex_version='5.0.0', date=datetime.datetime(2022, 9, 12, 10, 54, 46, 773443), page_type=None)
```

> **Default behaviour:** By default, the page analysis simulates:
>
> - Window size of **1920x1080** pixels (can be set with parameter `window_size`)
> - Wait for **1 second when page is loaded** (can be set with parameter `wait_before_scroll`)
> - Scroll to the bottom of the page (if it is possible)
> - Wait for **1 second after** having scrolled to the bottom of the page (can be set with parameter `wait_after_scroll`)

### Get a page analysis and generate a screenshot

It is possible to generate a screenshot of the analyzed page by adding a `ScreenShot` property to the `EcoindexScraper` object.
You have to define an id (can be a string, but it is recommended to use a unique id) and a path to the screenshot file (if the folder does not exist, it will be created).

```python
import asyncio
from pprint import pprint
from uuid import uuid1

from ecoindex.models import ScreenShot
from ecoindex.scrap import EcoindexScraper

pprint(
    asyncio.run(
        EcoindexScraper(
            url="http://www.ecoindex.fr/",
            screenshot=ScreenShot(id=str(uuid1()), folder="./screenshots"),
        )
        .get_page_analysis()
    )
)
```

## Async analysis

You can also run the analysis asynchronously:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from ecoindex.scrap import EcoindexScraper

def run_page_analysis(url):
    return asyncio.run(
        EcoindexScraper(url=url)
        .get_page_analysis()
    )


with ThreadPoolExecutor(max_workers=8) as executor:
    future_to_analysis = {}

    url = "https://www.ecoindex.fr"

    for i in range(10):
        future_to_analysis[
            executor.submit(
                run_page_analysis,
                url,
            )
        ] = (url)

    for future in as_completed(future_to_analysis):
        try:
            print(future.result())
        except Exception as e:
            print(e)
```
## Get requests details from an analysis

You can get the details of the requests made by the page by calling the function `get_all_requests()` and also get the aggregation of requests by category by calling the function `get_requests_by_category()`:

```python
import asyncio
from pprint import pprint

from ecoindex.scraper import EcoindexScraper

scraper = EcoindexScraper(url="http://www.ecoindex.fr")

result = asyncio.run(scraper.get_page_analysis())
all_requests = asyncio.run(scraper.get_all_requests())
requests_by_category = asyncio.run(scraper.get_requests_by_category())

pprint([request.model_dump() for request in all_requests])
# [{'category': 'html',
#   'mime_type': 'text/html; charset=iso-8859-1',
#   'size': 475.0,
#   'status': 301,
#   'url': 'http://www.ecoindex.fr/'},
#  {'category': 'html',
#   'mime_type': 'text/html',
#   'size': 7772.0,
#   'status': 200,
#   'url': 'https://www.ecoindex.fr/'},
#  {'category': 'css',
#   'mime_type': 'text/css',
#   'size': 9631.0,
#   'status': 200,
#   'url': 'https://www.ecoindex.fr/css/bundle.min.d38033feecefa0352173204171412aec01f58eee728df0ac5c917a396ca0bc14.css'},
#  {'category': 'javascript',
#   'mime_type': 'application/javascript',
#   'size': 9823.0,
#   'status': 200,
#   'url': 'https://www.ecoindex.fr/fr/js/bundle.8781a9ae8d87b4ebaa689167fc17b7d71193cf514eb8bb40aac9bf4548e14533.js'},
#  {'category': 'other',
#   'mime_type': 'x-unknown',
#   'size': 892.0,
#   'status': 200,
#   'url': 'https://www.ecoindex.fr/images/logo-neutral-it.webp'},
#  {'category': 'image',
#   'mime_type': 'image/svg+xml',
#   'size': 3298.0,
#   'status': 200,
#   'url': 'https://www.ecoindex.fr/images/logo-greenit.svg'}]

pprint(requests_by_category.model_dump())
# {'css': {'total_count': 1, 'total_size': 9631.0},
#  'font': {'total_count': 0, 'total_size': 0.0},
#  'html': {'total_count': 2, 'total_size': 8247.0},
#  'image': {'total_count': 1, 'total_size': 3298.0},
#  'javascript': {'total_count': 1, 'total_size': 9823.0},
#  'other': {'total_count': 1, 'total_size': 892.0},
#  'video': {'total_count': 0, 'total_size': 0.0}}
```
