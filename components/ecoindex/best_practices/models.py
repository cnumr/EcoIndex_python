from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class RuleStatus(str, Enum):
    ok = "ok"
    warn = "warn"
    fail = "fail"


class RuleCategory(str, Enum):
    """RWEB `tiers` values used by the référentiel."""

    network = "network"
    user_device = "user-device"
    datacenter = "datacenter"


class Thresholds(BaseModel):
    """Maximum acceptable values (RWEB `maxValue` semantics: value must be <= fail)."""

    warn: float | None = None
    fail: float | None = None


class RuleDefinition(BaseModel):
    id: str
    enabled: bool = True
    checker: str
    category: RuleCategory
    title: str
    description: str = ""
    rweb_id: str | None = None
    url: HttpUrl | str | None = None
    thresholds: Thresholds = Field(default_factory=Thresholds)
    higher_is_worse: bool = True
    params: dict = Field(default_factory=dict)


class RulesConfig(BaseModel):
    version: int = 1
    rules: list[RuleDefinition] = Field(default_factory=list)


class RuleResult(BaseModel):
    id: str
    category: RuleCategory
    title: str
    description: str = ""
    rweb_id: str | None = None
    url: HttpUrl | str | None = None
    status: RuleStatus
    value: float
    thresholds: Thresholds
    message: str
    details: list[str] = Field(default_factory=list)


class BestPracticesReport(BaseModel):
    results: list[RuleResult] = Field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.status == RuleStatus.ok)

    @property
    def warn_count(self) -> int:
        return sum(1 for r in self.results if r.status == RuleStatus.warn)

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.status == RuleStatus.fail)

    def results_by_category(self) -> dict[RuleCategory, list[RuleResult]]:
        grouped: dict[RuleCategory, list[RuleResult]] = {}
        for result in self.results:
            grouped.setdefault(result.category, []).append(result)
        return grouped


class CheckOutcome(BaseModel):
    """Raw measurement returned by a checker before threshold evaluation."""

    value: float
    details: list[str] = Field(default_factory=list)
    message: str | None = None
