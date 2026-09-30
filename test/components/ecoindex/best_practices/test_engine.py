from pathlib import Path

import pytest
from ecoindex.best_practices import (
    BestPracticesContext,
    BestPracticesEngine,
    DomMetrics,
    RuleStatus,
    load_rules_config,
)
from ecoindex.best_practices.engine import evaluate_status
from ecoindex.best_practices.models import (
    RuleCategory,
    RuleDefinition,
    RulesConfig,
    Thresholds,
)
from ecoindex.best_practices.registry import get_checker, list_checkers
from ecoindex.best_practices.rules import dom, network  # noqa: F401
from ecoindex.models.scraper import DomainMetrics, RequestItem, Requests


def _request(
    url: str,
    *,
    status: int = 200,
    category: str = "other",
    mime_type: str = "application/octet-stream",
    size: float = 100,
) -> RequestItem:
    return RequestItem(
        url=url,
        domain=url.split("/")[2],
        mime_type=mime_type,
        status=status,
        size=size,
        category=category,
    )


def test_default_rules_config_loads() -> None:
    config = load_rules_config()
    assert config.version == 1
    assert len(config.rules) == 4
    assert {rule.checker for rule in config.rules} <= set(list_checkers())
    assert {rule.category for rule in config.rules} == {
        RuleCategory.network,
        RuleCategory.user_device,
    }
    assert all(rule.rweb_id and rule.rweb_id.startswith("RWEB_") for rule in config.rules)
    assert all(rule.url for rule in config.rules)
    assert all(rule.description for rule in config.rules)

    by_id = {rule.id: rule for rule in config.rules}
    assert by_id["http_requests"].thresholds.fail == 40
    assert by_id["http_requests"].thresholds.warn == 26
    assert by_id["domains_number"].thresholds.fail == 5
    assert by_id["externalize_css_js"].thresholds.fail == 2
    assert by_id["print_stylesheet"].higher_is_worse is False


def test_evaluate_status_higher_is_worse_uses_rweb_max_semantics() -> None:
    thresholds = Thresholds(warn=10, fail=20)
    assert evaluate_status(5, thresholds) == RuleStatus.ok
    assert evaluate_status(10, thresholds) == RuleStatus.ok
    assert evaluate_status(11, thresholds) == RuleStatus.warn
    assert evaluate_status(20, thresholds) == RuleStatus.warn
    assert evaluate_status(21, thresholds) == RuleStatus.fail


def test_evaluate_status_higher_is_better() -> None:
    thresholds = Thresholds(fail=1)
    assert evaluate_status(0, thresholds, higher_is_worse=False) == RuleStatus.fail
    assert evaluate_status(1, thresholds, higher_is_worse=False) == RuleStatus.ok


def test_network_checkers() -> None:
    requests = Requests(
        total_count=3,
        items=[
            _request("https://a.example/page", status=200, category="html"),
            _request("https://b.example/img.png", status=404, category="image"),
            _request("https://c.example/go", status=301, category="other"),
        ],
        domain_aggregation={
            "a.example": DomainMetrics(total_count=1, total_size=100),
            "b.example": DomainMetrics(total_count=1, total_size=100),
            "c.example": DomainMetrics(total_count=1, total_size=100),
        },
    )
    context = BestPracticesContext(requests=requests)
    rule = RuleDefinition(
        id="x",
        checker="http_requests",
        category=RuleCategory.network,
        title="t",
        thresholds=Thresholds(),
    )

    assert get_checker("http_requests")(context, rule).value == 3
    assert get_checker("domains_number")(context, rule).value == 3


def test_dom_checkers() -> None:
    context = BestPracticesContext(
        dom=DomMetrics(inline_js=2, inline_css=1, print_stylesheet=0)
    )
    rule = RuleDefinition(
        id="x",
        checker="externalize_css_js",
        category=RuleCategory.network,
        title="t",
        thresholds=Thresholds(),
    )
    assert get_checker("externalize_css_js")(context, rule).value == 3
    assert get_checker("print_stylesheet")(context, rule).value == 0


def test_engine_skips_disabled_rules_and_applies_thresholds() -> None:
    config = RulesConfig(
        rules=[
            RuleDefinition(
                id="http_requests",
                enabled=True,
                checker="http_requests",
                category=RuleCategory.network,
                title="HTTP requests",
                rweb_id="RWEB_0047",
                url="https://rweb.greenit.fr/en/fiches/RWEB_0047-limit-the-number-of-http-requests",
                thresholds=Thresholds(warn=2, fail=5),
            ),
            RuleDefinition(
                id="disabled_rule",
                enabled=False,
                checker="domains_number",
                category=RuleCategory.network,
                title="Disabled",
                thresholds=Thresholds(warn=1, fail=2),
            ),
            RuleDefinition(
                id="print_stylesheet",
                enabled=True,
                checker="print_stylesheet",
                category=RuleCategory.user_device,
                title="Print CSS",
                rweb_id="RWEB_0031",
                higher_is_worse=False,
                thresholds=Thresholds(fail=1),
            ),
        ]
    )
    context = BestPracticesContext(
        requests=Requests(total_count=3),
        dom=DomMetrics(print_stylesheet=0),
    )
    report = BestPracticesEngine(config).run(context)

    assert len(report.results) == 2
    by_id = {r.id: r for r in report.results}
    assert by_id["http_requests"].status == RuleStatus.warn
    assert by_id["http_requests"].rweb_id == "RWEB_0047"
    assert by_id["http_requests"].category == RuleCategory.network
    assert by_id["print_stylesheet"].status == RuleStatus.fail
    assert by_id["print_stylesheet"].category == RuleCategory.user_device
    assert report.warn_count == 1
    assert report.fail_count == 1
    assert report.ok_count == 0
    by_category = report.results_by_category()
    assert len(by_category[RuleCategory.network]) == 1
    assert len(by_category[RuleCategory.user_device]) == 1


def test_engine_loads_custom_yaml(tmp_path: Path) -> None:
    yaml_path = tmp_path / "rules.yaml"
    yaml_path.write_text(
        """
version: 1
rules:
  - id: http_requests
    enabled: true
    checker: http_requests
    category: network
    rweb_id: RWEB_0047
    url: https://rweb.greenit.fr/en/fiches/RWEB_0047-limit-the-number-of-http-requests
    title: Custom HTTP
    thresholds:
      warn: 1
      fail: 2
"""
    )
    report = BestPracticesEngine(yaml_path).run(
        BestPracticesContext(requests=Requests(total_count=3))
    )
    assert len(report.results) == 1
    assert report.results[0].title == "Custom HTTP"
    assert report.results[0].category == RuleCategory.network
    assert report.results[0].rweb_id == "RWEB_0047"
    assert report.results[0].status == RuleStatus.fail


def test_unknown_checker_raises() -> None:
    with pytest.raises(KeyError, match="Unknown best-practice checker"):
        get_checker("does_not_exist")
