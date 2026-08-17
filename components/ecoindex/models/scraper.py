from urllib.parse import urlparse, urlunparse
from uuid import UUID

from pydantic import BaseModel, Field


def get_domain_from_url(url: str) -> str:
    return urlparse(url).netloc


def strip_query_params(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", parsed.fragment)
    )


class RequestItem(BaseModel):
    category: str
    domain: str
    mime_type: str
    size: float
    status: int
    url: str


class RequestDetail(BaseModel):
    id: UUID | None = None
    category: str
    domain: str
    status: int
    url: str
    size: float

    @classmethod
    def from_request_item(cls, item: RequestItem) -> "RequestDetail":
        return cls(
            category=item.category,
            domain=item.domain,
            status=item.status,
            url=item.url,
            size=item.size,
        )


class MimetypeMetrics(BaseModel):
    total_count: int = 0
    total_size: float = 0


class DomainMetrics(BaseModel):
    total_count: int = 0
    total_size: float = 0


class MimetypeAggregation(BaseModel):
    audio: MimetypeMetrics = MimetypeMetrics()
    css: MimetypeMetrics = MimetypeMetrics()
    font: MimetypeMetrics = MimetypeMetrics()
    html: MimetypeMetrics = MimetypeMetrics()
    image: MimetypeMetrics = MimetypeMetrics()
    javascript: MimetypeMetrics = MimetypeMetrics()
    other: MimetypeMetrics = MimetypeMetrics()
    video: MimetypeMetrics = MimetypeMetrics()

    @classmethod
    async def get_category_of_resource(cls, mimetype: str) -> str:
        mimetypes = [type for type in cls.model_fields.keys()]

        for type in mimetypes:
            if type in mimetype:
                return type

        return "other"


class Requests(BaseModel):
    aggregation: MimetypeAggregation = MimetypeAggregation()
    domain_aggregation: dict[str, DomainMetrics] = {}
    items: list[RequestItem] = []
    total_count: int = 0
    total_size: float = 0


class RequestsDetailResponse(BaseModel):
    by_category: MimetypeAggregation = Field(default_factory=MimetypeAggregation)
    by_domain: dict[str, DomainMetrics] = Field(default_factory=dict)
    items: list[RequestDetail] = Field(default_factory=list)


def aggregate_request_details(items: list[RequestDetail]) -> RequestsDetailResponse:
    aggregation = MimetypeAggregation().model_dump()
    by_domain: dict[str, DomainMetrics] = {}

    for item in items:
        category = item.category if item.category in aggregation else "other"
        aggregation[category]["total_count"] += 1
        aggregation[category]["total_size"] += item.size
        if item.domain not in by_domain:
            by_domain[item.domain] = DomainMetrics()
        by_domain[item.domain].total_count += 1
        by_domain[item.domain].total_size += item.size

    return RequestsDetailResponse(
        by_category=MimetypeAggregation(**aggregation),
        by_domain=by_domain,
        items=items,
    )
