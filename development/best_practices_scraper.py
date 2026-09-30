"""Manual smoke test for EcoIndex + RWEB best practices analysis.

Run from the repo root:

    uv run development/best_practices_scraper.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Prefer local polylith bricks over stale copies in site-packages.
_ROOT = Path(__file__).resolve().parents[1]
for _path in (_ROOT / "components", _ROOT / "bases", _ROOT / "development"):
    sys.path.insert(0, str(_path))

from ecoindex.scraper import EcoindexScraper

URL = "https://www.ecoindex.fr"
# Optional custom rules file; leave as None to use the default RWEB rules
RULES_PATH: Path | None = None


async def main() -> None:
    best_practices: bool | Path = RULES_PATH if RULES_PATH else True
    scraper = EcoindexScraper(url=URL, best_practices=best_practices)

    print(f"Analyzing {URL} ...")
    result = await scraper.get_page_analysis()
    report = await scraper.get_best_practices()

    print()
    print("=== EcoIndex ===")
    print(f"grade={result.grade} score={result.score}")
    print(
        f"nodes={result.nodes} size_kb={result.size:.1f} requests={result.requests}"
    )
    print()
    print(
        "=== Best practices "
        f"(ok={report.ok_count} warn={report.warn_count} fail={report.fail_count}) ==="
    )

    for rule in report.results:
        print()
        print(f"[{rule.status.value.upper()}] {rule.rweb_id} — {rule.title}")
        print(f"  category : {rule.category.value}")
        print(f"  value    : {rule.value}")
        print(f"  thresholds: warn={rule.thresholds.warn} fail={rule.thresholds.fail}")
        print(f"  message  : {rule.message}")
        if rule.details:
            print(f"  details  : {', '.join(rule.details[:5])}")
        print(f"  url      : {rule.url}")

    if report.fail_count:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
