import pytest

from ecoindex.config.settings import Settings, build_database_url


@pytest.fixture(autouse=True)
def disable_env_file(monkeypatch):
    monkeypatch.chdir("/tmp")
    Settings.model_config["env_file"] = None


def test_build_database_url_sqlite():
    assert build_database_url() == "sqlite+aiosqlite:///db.sqlite3"


def test_build_database_url_mysql():
    assert (
        build_database_url(
            engine="mysql",
            host="db-mysql",
            user="ecoindex",
            password="secret",
            name="ecoindex",
        )
        == "mysql+aiomysql://ecoindex:secret@db-mysql:3306/ecoindex?charset=utf8mb4"
    )


def test_build_database_url_postgres():
    assert (
        build_database_url(
            engine="postgres",
            host="db-postgres",
            port=5432,
            user="ecoindex",
            password="secret",
            name="ecoindex",
        )
        == "postgresql+asyncpg://ecoindex:secret@db-postgres:5432/ecoindex"
    )


def test_build_database_url_encodes_special_characters():
    assert (
        build_database_url(
            engine="postgres",
            password="p@ss#word",
        )
        == "postgresql+asyncpg://ecoindex:p%40ss%23word@localhost:5432/ecoindex"
    )


def test_settings_uses_db_engine_when_database_url_is_not_set(monkeypatch):
    monkeypatch.setenv("DB_ENGINE", "postgres")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")

    settings = Settings()

    assert settings.DATABASE_URL == (
        "postgresql+asyncpg://ecoindex:ecoindex@localhost:5432/ecoindex"
    )


def test_settings_keeps_explicit_database_url(monkeypatch):
    monkeypatch.setenv("DB_ENGINE", "postgres")
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+aiomysql://custom:custom@db:3306/custom?charset=utf8mb4",
    )

    settings = Settings()

    assert settings.DATABASE_URL == (
        "mysql+aiomysql://custom:custom@db:3306/custom?charset=utf8mb4"
    )
