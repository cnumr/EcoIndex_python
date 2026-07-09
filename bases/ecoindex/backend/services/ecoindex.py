import json

from ecoindex.backend.services.cache import cache
from ecoindex.database.models import EcoindexSearchResults
from ecoindex.database.repositories.ecoindex import get_ecoindex_result_list_db
from ecoindex.models.enums import Version
from ecoindex.models.sort import Sort
from pydantic import AnyHttpUrl
from requests import get
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_latest_result_by_url(
    session: AsyncSession, url: AnyHttpUrl, refresh: bool, version: Version
) -> EcoindexSearchResults:
    """
    Get the latest ecoindex result for a given url. This function will first try to find
    an exact match for the url path, and if it doesn't find any, it will return the latest
    result for the host.

    Results are cached for 1 week by default. If you want to force the refresh of the cache,
    set the refresh parameter to True.

    params:
        url: the url to search for
        refresh: if True, will force the refresh of the cache
        version: the version of the ecoindex to use

    returns:
        EcoindexSearchResults: the results for the given url
    """
    ecoindex_cache = cache.set_cache_key(key=f"ecoindex-{url.host}/{url.path}")
    cached_results = await ecoindex_cache.get()

    if not refresh and cached_results:
        return EcoindexSearchResults(**json.loads(cached_results))

    ecoindexes = await get_ecoindex_result_list_db(
        session=session,
        host=str(url.host),
        version=version,
        size=20,
        sort_params=[Sort(clause="date", sort="desc")],
    )

    if not ecoindexes:
        await ecoindex_cache.set(
            data=EcoindexSearchResults(count=0).model_dump_json()
        )

        return EcoindexSearchResults(count=0)

    exact_url_results = []
    host_results = []

    for ecoindex in ecoindexes:
        if ecoindex.get_url_path() == str(url.path):
            exact_url_results.append(ecoindex)
        else:
            host_results.append(ecoindex)

    results = EcoindexSearchResults(
        count=len(exact_url_results),
        latest_result=exact_url_results[0] if exact_url_results else None,
        older_results=exact_url_results[1:] if len(exact_url_results) > 1 else [],
        host_results=host_results,
    )

    await ecoindex_cache.set(
        data=results.model_dump_json(),
    )

    return results


async def get_badge(
    session: AsyncSession, url: AnyHttpUrl, refresh: bool, version: Version, theme: str
) -> str:
    """
    Get the badge for a given url. This function will use the method `get_latest_result_by_url`.
    If the url is not found, it will return the badge for the grade "unknown".

    This returns the badge that [are hosted on jsdelivr.net](https://cdn.jsdelivr.net/gh/cnumr/ecoindex_badge@1/assets/svg/).

    params:
        url: the url to search for
        refresh: if True, will force the refresh of the cache
        version: the version of the ecoindex to use
        theme: the theme of the badge to use (light or dark)

    returns:
        str: the badge image
    """
    results = await get_latest_result_by_url(
        session=session, url=url, refresh=refresh, version=version
    )

    grade = results.latest_result.grade if results.latest_result else "unknown"
    ecoindex_cache = cache.set_cache_key(key=f"badge-{grade}-{theme}")

    cached_badge = await ecoindex_cache.get()

    if cached_badge:
        return cached_badge

    base_url = f"https://cdn.jsdelivr.net/gh/cnumr/ecoindex_badge@1/assets/svg/{theme}/{grade}.svg"

    image = get(base_url).text

    await ecoindex_cache.set(data=image)

    return image
