from ecoindex.best_practices.context import BestPracticesContext
from ecoindex.best_practices.models import CheckOutcome, RuleDefinition
from ecoindex.best_practices.registry import register


@register("http_requests")
def check_http_requests(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    value = float(context.requests.total_count)
    return CheckOutcome(
        value=value,
        message=f"{int(value)} HTTP request(s)",
    )


@register("domains_number")
def check_domains_number(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    domains = sorted(context.requests.domain_aggregation.keys())
    return CheckOutcome(
        value=float(len(domains)),
        details=domains,
        message=f"{len(domains)} distinct domain(s)",
    )
