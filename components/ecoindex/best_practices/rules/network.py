from ecoindex.best_practices.context import BestPracticesContext
from ecoindex.best_practices.har_utils import (
    has_valid_cache_headers,
    is_compressible_resource,
    is_css_resource,
    is_font_resource,
    is_gif_resource,
    is_http1,
    is_http_redirect,
    is_resource_compressed,
    is_static_resource,
    official_social_network,
)
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


@register("stylesheets_number")
def check_stylesheets_number(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    urls: list[str] = []
    seen: set[str] = set()
    for item in context.requests.items:
        if not is_css_resource(item):
            continue
        if item.url in seen:
            continue
        seen.add(item.url)
        urls.append(item.url)
    return CheckOutcome(
        value=float(len(urls)),
        details=urls,
        message=f"{len(urls)} stylesheet(s)",
    )


@register("standard_typefaces")
def check_standard_typefaces(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    fonts = [item.url for item in context.requests.items if is_font_resource(item)]
    return CheckOutcome(
        value=float(len(fonts)),
        details=fonts,
        message=f"{len(fonts)} downloaded font(s)",
    )


@register("social_network_button")
def check_social_network_button(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    networks: list[str] = []
    seen: set[str] = set()
    for item in context.requests.items:
        name = official_social_network(item.url)
        if not name or name in seen:
            continue
        seen.add(name)
        networks.append(name)
    return CheckOutcome(
        value=float(len(networks)),
        details=networks,
        message=(
            f"{len(networks)} official social network button(s)"
            if networks
            else "No official social network button detected"
        ),
    )


@register("animated_gifs")
def check_animated_gifs(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    gifs = [item.url for item in context.requests.items if is_gif_resource(item)]
    return CheckOutcome(
        value=float(len(gifs)),
        details=gifs,
        message=f"{len(gifs)} GIF file(s)",
    )


@register("http_errors")
def check_http_errors(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    errors = [
        f"{item.status} {item.url}"
        for item in context.requests.items
        if item.status >= 400
    ]
    return CheckOutcome(
        value=float(len(errors)),
        details=errors,
        message=f"{len(errors)} HTTP error response(s)",
    )


@register("http_redirects")
def check_http_redirects(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    redirects = [
        f"{item.status} {item.url}"
        for item in context.requests.items
        if is_http_redirect(item.status)
    ]
    return CheckOutcome(
        value=float(len(redirects)),
        details=redirects,
        message=f"{len(redirects)} HTTP redirect(s)",
    )


@register("http2")
def check_http2(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    http1 = [
        f"{item.http_version or 'unknown'} {item.url}"
        for item in context.requests.items
        if is_http1(item)
    ]
    total = len(context.requests.items)
    return CheckOutcome(
        value=float(len(http1)),
        details=http1,
        message=f"{len(http1)}/{total} request(s) using HTTP/1",
    )


@register("cache_headers")
def check_cache_headers(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    static_items = [item for item in context.requests.items if is_static_resource(item)]
    without_cache = [
        item.url for item in static_items if not has_valid_cache_headers(item)
    ]
    with_cache = len(static_items) - len(without_cache)
    return CheckOutcome(
        value=float(len(without_cache)),
        details=without_cache,
        message=(
            f"{with_cache}/{len(static_items)} static resource(s) with cache headers"
        ),
    )


@register("http_compression")
def check_http_compression(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    uncompressed = [
        item.url
        for item in context.requests.items
        if is_compressible_resource(item) and not is_resource_compressed(item)
    ]
    return CheckOutcome(
        value=float(len(uncompressed)),
        details=uncompressed,
        message=f"{len(uncompressed)} compressible resource(s) without compression",
    )


@register("no_cookie_static")
def check_no_cookie_static(
    context: BestPracticesContext, rule: RuleDefinition
) -> CheckOutcome:
    domains: list[str] = []
    seen: set[str] = set()
    for item in context.requests.items:
        if not is_static_resource(item) or item.cookie_header_size <= 0:
            continue
        if item.domain in seen:
            continue
        seen.add(item.domain)
        domains.append(item.domain)
    return CheckOutcome(
        value=float(len(domains)),
        details=domains,
        message=(
            f"{len(domains)} domain(s) serving static resources with cookies"
            if domains
            else "No cookie sent with static resources"
        ),
    )
