from pydantic import BaseModel, Field

from ecoindex.models.scraper import Requests


class DomMetrics(BaseModel):
    inline_js: int = 0
    inline_css: int = 0
    print_stylesheet: int = 0


class BestPracticesContext(BaseModel):
    requests: Requests = Field(default_factory=Requests)
    dom: DomMetrics = Field(default_factory=DomMetrics)
