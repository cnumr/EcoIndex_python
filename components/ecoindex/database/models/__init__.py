from uuid import UUID, uuid4

from ecoindex.models.compute import Result
from ecoindex.models.scraper import RequestDetail
from pydantic import BaseModel
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class ApiEcoindex(SQLModel, Result, table=True):  # type: ignore
    id: UUID | None = Field(
        default=None,
        description="Analysis ID of type `UUID`",
        primary_key=True,
        index=True,
    )
    host: str = Field(
        default=...,
        title="Web page host",
        description="Host name of the web page",
        index=True,
    )
    version: int = Field(
        default=1,
        title="API version",
        description="Version number of the API used to run the test",
    )
    initial_ranking: int | None = Field(
        default=...,
        title="Analysis rank",
        description=(
            "This is the initial rank of the analysis. "
            "This is an indicator of the ranking at the "
            "time of the analysis for a given version."
        ),
    )
    initial_total_results: int | None = Field(
        default=...,
        title="Total number of analysis",
        description=(
            "This is the initial total number of analysis. "
            "This is an indicator of the total number of analysis "
            "at the time of the analysis for a given version."
        ),
    )
    source: str | None = Field(
        default="ecoindex.fr",
        title="Source of the analysis",
        description="Source of the analysis",
    )


class ApiEcoindexRequest(SQLModel, table=True):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Request detail ID of type `UUID`",
    )
    analysis_id: UUID = Field(
        default=...,
        foreign_key="apiecoindex.id",
        index=True,
        description="ID of the related ecoindex analysis",
    )
    category: str = Field(
        default=...,
        title="Request category",
        description="Category of the resource (html, css, javascript, image, ...)",
    )
    domain: str = Field(
        default=...,
        title="Request domain",
        description="Domain that served the resource",
    )
    status: int = Field(
        default=...,
        title="HTTP status",
        description="HTTP status code of the resource response",
    )
    url: str = Field(
        default=...,
        sa_column=Column(Text(), nullable=False),
        title="Request URL",
        description="URL of the resource without query parameters",
    )
    size: float = Field(
        default=...,
        title="Request size",
        description="Transfer size of the resource in bytes",
    )


class ApiEcoindexBatchItem(Result):
    id: UUID | None = None
    host: str
    version: int = 1
    initial_ranking: int | None = None
    initial_total_results: int | None = None
    source: str | None = None
    request_details: list[RequestDetail] | None = Field(
        default=None,
        title="Request details",
        description="Optional list of requests made by the page",
    )


ApiEcoindexes = list[ApiEcoindex]
ApiEcoindexBatchItems = list[ApiEcoindexBatchItem]


class PageApiEcoindexes(BaseModel):
    items: list[ApiEcoindex]
    total: int
    page: int
    size: int


class EcoindexSearchResults(BaseModel):
    count: int
    latest_result: ApiEcoindex | None = None
    older_results: list[ApiEcoindex] = []
    host_results: list[ApiEcoindex] = []
