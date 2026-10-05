from ecoindex.best_practices import BestPracticesReport, load_rules_config
from ecoindex.database.models import (
    ApiEcoindexBestPractice,
    ApiEcoindexBestPracticeResult,
)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def sync_best_practices_catalog(
    session: AsyncSession,
) -> dict[str, ApiEcoindexBestPractice]:
    """Upsert best practice definitions from the default YAML config."""
    config = load_rules_config()
    result = await session.exec(select(ApiEcoindexBestPractice))
    existing = {row.rule_id: row for row in result.all()}

    for rule in config.rules:
        url = str(rule.url) if rule.url is not None else None
        if rule.id in existing:
            practice = existing[rule.id]
            practice.rweb_id = rule.rweb_id
            practice.category = rule.category.value
            practice.title = rule.title
            practice.description = rule.description
            practice.url = url
            practice.enabled = rule.enabled
            practice.threshold_warn = rule.thresholds.warn
            practice.threshold_fail = rule.thresholds.fail
            practice.higher_is_worse = rule.higher_is_worse
            session.add(practice)
        else:
            practice = ApiEcoindexBestPractice(
                rule_id=rule.id,
                rweb_id=rule.rweb_id,
                category=rule.category.value,
                title=rule.title,
                description=rule.description,
                url=url,
                enabled=rule.enabled,
                threshold_warn=rule.thresholds.warn,
                threshold_fail=rule.thresholds.fail,
                higher_is_worse=rule.higher_is_worse,
            )
            session.add(practice)
            existing[rule.id] = practice

    await session.flush()
    return existing


def build_best_practice_result_rows(
    *,
    analysis_id,
    report: BestPracticesReport,
    catalog: dict[str, ApiEcoindexBestPractice],
) -> list[ApiEcoindexBestPracticeResult]:
    rows: list[ApiEcoindexBestPracticeResult] = []
    for rule_result in report.results:
        practice = catalog.get(rule_result.id)
        if practice is None or practice.id is None:
            continue
        rows.append(
            ApiEcoindexBestPracticeResult(
                analysis_id=analysis_id,
                best_practice_id=practice.id,
                status=rule_result.status.value,
                value=rule_result.value,
                threshold_warn=rule_result.thresholds.warn,
                threshold_fail=rule_result.thresholds.fail,
                message=rule_result.message,
                details=list(rule_result.details),
            )
        )
    return rows
