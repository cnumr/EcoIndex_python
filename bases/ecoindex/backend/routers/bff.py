from typing import Annotated

from ecoindex.backend.models.dependencies_parameters.bff import BffDepParameters
from ecoindex.backend.services.ecoindex import get_badge, get_latest_result_by_url
from ecoindex.config.settings import Settings
from ecoindex.database.engine import get_session
from ecoindex.database.models import EcoindexSearchResults
from ecoindex.models import example_file_not_found
from ecoindex.models.enums import BadgeTheme
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter(
    prefix="/{version}/ecoindexes",
    tags=["BFF"],
    deprecated=True,
    include_in_schema=False,
)


@router.get(
    name="Get latest results",
    path="/latest",
    response_model=EcoindexSearchResults,
    response_description="Get latest results for a given url",
    deprecated=True,
    include_in_schema=False,
)
async def get_latest_results(
    response: Response,
    parameters: BffDepParameters,
    session: AsyncSession = Depends(get_session),
) -> EcoindexSearchResults:
    """
    **Deprecated.** Use the Ecoindex BFF service instead.

    This returns the latest results for a given url. This feature is used by the Ecoindex
    browser extension. By default, the results are cached for 7 days.

    If the url is not found in the database, the response status code will be 404.
    """
    latest_result = await get_latest_result_by_url(
        session=session,
        url=parameters.url,
        refresh=parameters.refresh,
        version=parameters.version,
    )

    if latest_result.count == 0:
        response.status_code = status.HTTP_404_NOT_FOUND

    return latest_result


@router.get(
    name="Get badge",
    path="/latest/badge",
    response_description="Badge of the given url from [CDN V1](https://www.jsdelivr.com/package/gh/cnumr/ecoindex_badge)",
    responses={status.HTTP_404_NOT_FOUND: example_file_not_found},
    deprecated=True,
    include_in_schema=False,
)
async def get_badge_enpoint(
    parameters: BffDepParameters,
    theme: Annotated[
        BadgeTheme, Query(description="Theme of the badge")
    ] = BadgeTheme.light,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """
    **Deprecated.** Use the Ecoindex BFF service instead.

    This returns the SVG badge of the given url. This feature is used by the Ecoindex
    badge. By default, the results are cached for 7 days.

    If the url is not found in the database, it will return a badge with the grade `?`.
    """
    return Response(
        content=await get_badge(
            session=session,
            url=parameters.url,
            refresh=parameters.refresh,
            version=parameters.version,
            theme=theme.value,
        ),
        media_type="image/svg+xml",
    )


@router.get(
    name="Get latest results redirect",
    path="/latest/redirect",
    response_description="Redirect to the latest results for a given url",
    deprecated=True,
    include_in_schema=False,
)
async def get_latest_result_redirect(
    parameters: BffDepParameters,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """
    **Deprecated.** Use the Ecoindex BFF service instead.

    This redirects to the latest results on the frontend website for the given url.
    This feature is used by the Ecoindex browser extension and badge.

    If the url is not found in the database, the response status code will be 404.
    """
    latest_result = await get_latest_result_by_url(
        session=session,
        url=parameters.url,
        refresh=parameters.refresh,
        version=parameters.version,
    )

    if latest_result.count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis found for {parameters.url}",
        )

    return RedirectResponse(
        url=f"{Settings().FRONTEND_BASE_URL}/resultat/?id={latest_result.latest_result.id}"  # type: ignore
    )
