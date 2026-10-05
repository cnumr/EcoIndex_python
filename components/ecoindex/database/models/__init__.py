from uuid import UUID, uuid4

from ecoindex.models.compute import Result
from ecoindex.models.scraper import RequestDetail
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, Text, UniqueConstraint
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


class ApiEcoindex(SQLModel, Result, table=True):  # type: ignore
    id: UUID | None = SQLField(
        default=None,
        description="Analysis ID of type `UUID`",
        primary_key=True,
        index=True,
    )
    host: str = SQLField(
        default=...,
        title="Web page host",
        description="Host name of the web page",
        index=True,
    )
    version: int = SQLField(
        default=1,
        title="API version",
        description="Version number of the API used to run the test",
    )
    initial_ranking: int | None = SQLField(
        default=...,
        title="Analysis rank",
        description=(
            "This is the initial rank of the analysis. "
            "This is an indicator of the ranking at the "
            "time of the analysis for a given version."
        ),
    )
    initial_total_results: int | None = SQLField(
        default=...,
        title="Total number of analysis",
        description=(
            "This is the initial total number of analysis. "
            "This is an indicator of the total number of analysis "
            "at the time of the analysis for a given version."
        ),
    )
    source: str | None = SQLField(
        default="ecoindex.fr",
        title="Source of the analysis",
        description="Source of the analysis",
    )


class ApiEcoindexRequest(SQLModel, table=True):
    id: UUID = SQLField(
        default_factory=uuid4,
        primary_key=True,
        description="Request detail ID of type `UUID`",
    )
    analysis_id: UUID = SQLField(
        default=...,
        foreign_key="apiecoindex.id",
        index=True,
        description="ID of the related ecoindex analysis",
    )
    category: str = SQLField(
        default=...,
        title="Request category",
        description="Category of the resource (html, css, javascript, image, ...)",
    )
    domain: str = SQLField(
        default=...,
        title="Request domain",
        description="Domain that served the resource",
    )
    status: int = SQLField(
        default=...,
        title="HTTP status",
        description="HTTP status code of the resource response",
    )
    url: str = SQLField(
        default=...,
        sa_column=Column(Text(), nullable=False),
        title="Request URL",
        description="URL of the resource without query parameters",
    )
    size: float = SQLField(
        default=...,
        title="Request size",
        description="Transfer size of the resource in bytes",
    )


class ApiEcoindexBestPractice(SQLModel, table=True):
    __tablename__ = "apiecoindexbestpractices"
    __table_args__ = (
        UniqueConstraint("rule_id", name="uq_apiecoindexbestpractices_rule_id"),
    )

    id: UUID = SQLField(
        default_factory=uuid4,
        primary_key=True,
        description="Best practice ID of type `UUID`",
    )
    rule_id: str = SQLField(
        default=...,
        index=True,
        title="Rule ID",
        description="Stable rule identifier from the YAML config (e.g. http_requests)",
    )
    rweb_id: str | None = SQLField(
        default=None,
        title="RWEB ID",
        description="Official RWEB reference (e.g. RWEB_0047)",
    )
    category: str = SQLField(
        default=...,
        title="Category",
        description="RWEB tier / category (network, user-device, ...)",
    )
    title: str = SQLField(
        default=...,
        title="Title",
        description="Official best practice title",
    )
    description: str = SQLField(
        default="",
        sa_column=Column(Text(), nullable=False, server_default=""),
        title="Description",
        description="Best practice description",
    )
    url: str | None = SQLField(
        default=None,
        sa_column=Column(Text(), nullable=True),
        title="RWEB URL",
        description="URL of the official RWEB fiche",
    )
    enabled: bool = SQLField(
        default=True,
        title="Enabled",
        description="Whether the rule is currently enabled in the catalog",
    )
    threshold_warn: float | None = SQLField(
        default=None,
        title="Warn threshold",
        description="Current warn threshold from the YAML config",
    )
    threshold_fail: float | None = SQLField(
        default=None,
        title="Fail threshold",
        description="Current fail threshold from the YAML config (RWEB maxValue)",
    )
    higher_is_worse: bool = SQLField(
        default=True,
        title="Higher is worse",
        description="Whether higher measured values are worse for this rule",
    )


class ApiEcoindexBestPracticeResult(SQLModel, table=True):
    __tablename__ = "apiecoindexbestpracticeresults"
    __table_args__ = (
        UniqueConstraint(
            "analysis_id",
            "best_practice_id",
            name="uq_apiecoindexbestpracticeresults_analysis_practice",
        ),
    )

    id: UUID = SQLField(
        default_factory=uuid4,
        primary_key=True,
        description="Best practice result ID of type `UUID`",
    )
    analysis_id: UUID = SQLField(
        default=...,
        foreign_key="apiecoindex.id",
        index=True,
        description="ID of the related ecoindex analysis",
    )
    best_practice_id: UUID = SQLField(
        default=...,
        foreign_key="apiecoindexbestpractices.id",
        index=True,
        description="ID of the related best practice definition",
    )
    status: str = SQLField(
        default=...,
        title="Status",
        description="Evaluation status: ok, warn or fail",
    )
    value: float = SQLField(
        default=...,
        title="Measured value",
        description="Measured value used for the rule evaluation",
    )
    threshold_warn: float | None = SQLField(
        default=None,
        title="Warn threshold snapshot",
        description="Warn threshold at analysis time",
    )
    threshold_fail: float | None = SQLField(
        default=None,
        title="Fail threshold snapshot",
        description="Fail threshold at analysis time",
    )
    message: str = SQLField(
        default=...,
        sa_column=Column(Text(), nullable=False),
        title="Message",
        description="Human-readable evaluation message",
    )
    details: list[str] = SQLField(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
        title="Details",
        description="Optional list of detail strings (URLs, domains, ...)",
    )


class BestPracticeResultItem(BaseModel):
    id: UUID | None = None
    rule_id: str
    rweb_id: str | None = None
    category: str
    title: str
    description: str = ""
    url: str | None = None
    status: str
    value: float
    threshold_warn: float | None = None
    threshold_fail: float | None = None
    message: str
    details: list[str] = Field(default_factory=list)


class BestPracticesAnalysisResponse(BaseModel):
    results: list[BestPracticeResultItem] = Field(default_factory=list)
    ok_count: int = 0
    warn_count: int = 0
    fail_count: int = 0


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
