import pytest
from ecoindex.scraper import EcoindexScraper


@pytest.mark.asyncio
async def test_get_best_practices_requires_enabled() -> None:
    scraper = EcoindexScraper(url="https://www.example.com")
    with pytest.raises(RuntimeError, match="disabled"):
        await scraper.get_best_practices()


@pytest.mark.asyncio
async def test_get_best_practices_requires_analysis_first() -> None:
    scraper = EcoindexScraper(url="https://www.example.com", best_practices=True)
    with pytest.raises(RuntimeError, match="not available yet"):
        await scraper.get_best_practices()


def test_scraper_best_practices_init_with_path(tmp_path) -> None:
    config = tmp_path / "rules.yaml"
    config.write_text("version: 1\nrules: []\n")
    scraper = EcoindexScraper(
        url="https://www.example.com",
        best_practices=config,
    )
    assert scraper.best_practices_enabled is True
    assert scraper.best_practices_config_path == config
