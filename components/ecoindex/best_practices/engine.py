from pathlib import Path

from yaml import safe_load

from ecoindex.best_practices.context import BestPracticesContext
from ecoindex.best_practices.models import (
    BestPracticesReport,
    RuleDefinition,
    RuleResult,
    RuleStatus,
    RulesConfig,
    Thresholds,
)
from ecoindex.best_practices.registry import get_checker

# Ensure checkers are registered when the engine is used.
from ecoindex.best_practices import rules as _rules  # noqa: F401

DEFAULT_RULES_PATH = Path(__file__).parent / "default_rules.yaml"


def load_rules_config(path: Path | None = None) -> RulesConfig:
    config_path = path or DEFAULT_RULES_PATH
    with open(config_path) as fp:
        raw = safe_load(fp) or {}
    return RulesConfig.model_validate(raw)


def evaluate_status(
    value: float,
    thresholds: Thresholds,
    *,
    higher_is_worse: bool = True,
) -> RuleStatus:
    """Evaluate a measured value against RWEB-style maximum thresholds.

    When ``higher_is_worse`` is True (count metrics), ``fail`` / ``warn`` are
    maximum acceptable values: status is fail when ``value > fail``, warn when
    ``value > warn``. This matches RWEB ``maxValue`` ("less than or equal to").
    """
    warn = thresholds.warn
    fail = thresholds.fail

    if higher_is_worse:
        if fail is not None and value > fail:
            return RuleStatus.fail
        if warn is not None and value > warn:
            return RuleStatus.warn
        return RuleStatus.ok

    if fail is not None and value < fail:
        return RuleStatus.fail
    if warn is not None and value < warn:
        return RuleStatus.warn
    return RuleStatus.ok


def run_rule(context: BestPracticesContext, rule: RuleDefinition) -> RuleResult:
    checker = get_checker(rule.checker)
    outcome = checker(context, rule)
    status = evaluate_status(
        outcome.value,
        rule.thresholds,
        higher_is_worse=rule.higher_is_worse,
    )
    message = outcome.message or f"{rule.id}={outcome.value}"
    return RuleResult(
        id=rule.id,
        category=rule.category,
        title=rule.title,
        description=rule.description,
        rweb_id=rule.rweb_id,
        url=rule.url,
        status=status,
        value=outcome.value,
        thresholds=rule.thresholds,
        message=message,
        details=outcome.details,
    )


class BestPracticesEngine:
    def __init__(self, config: RulesConfig | Path | None = None):
        if isinstance(config, RulesConfig):
            self.config = config
        elif isinstance(config, Path):
            self.config = load_rules_config(config)
        else:
            self.config = load_rules_config(None)

    def run(self, context: BestPracticesContext) -> BestPracticesReport:
        results: list[RuleResult] = []
        for rule in self.config.rules:
            if not rule.enabled:
                continue
            results.append(run_rule(context, rule))
        return BestPracticesReport(results=results)
