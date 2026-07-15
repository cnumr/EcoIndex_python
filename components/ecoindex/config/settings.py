from typing import Literal
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DbEngine = Literal["sqlite", "mysql", "postgres"]


def build_database_url(
    *,
    engine: DbEngine = "sqlite",
    host: str = "localhost",
    port: int | None = None,
    user: str = "ecoindex",
    password: str = "ecoindex",
    name: str = "ecoindex",
) -> str:
    if engine == "sqlite":
        return "sqlite+aiosqlite:///db.sqlite3"

    credentials = f"{quote_plus(user)}:{quote_plus(password)}"

    if engine == "mysql":
        db_port = port or 3306
        return (
            f"mysql+aiomysql://{credentials}@{host}:{db_port}/{name}?charset=utf8mb4"
        )

    db_port = port or 5432
    return f"postgresql+asyncpg://{credentials}@{host}:{db_port}/{name}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    API_KEYS_BATCH: list[
        dict[str, str]
    ] = []  # formated as [{"key": "xxx", "name": "xxx", "description": "xxx", "source": "ecoindex.fr"}]
    CORS_ALLOWED_CREDENTIALS: bool = True
    CORS_ALLOWED_HEADERS: list = ["*"]
    CORS_ALLOWED_METHODS: list = ["*"]
    CORS_ALLOWED_ORIGINS: list = ["*"]
    DAILY_LIMIT_PER_HOST: int = 0
    DATABASE_URL: str = ""
    DB_ENGINE: DbEngine = "sqlite"
    DB_HOST: str = "localhost"
    DB_PORT: int | None = None
    DB_USER: str = "ecoindex"
    DB_PASSWORD: str = "ecoindex"
    DB_NAME: str = "ecoindex"
    DEBUG: bool = False
    DOCKER_CONTAINER: bool = False
    ENABLE_SCREENSHOT: bool = False
    EXCLUDED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    FRONTEND_BASE_URL: str = "https://www.ecoindex.fr"
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0
    REDIS_CACHE_HOST: str = "localhost"
    RQ_FAILURE_TTL: int = 86400
    RQ_JOB_TIMEOUT: int = 600
    RQ_RESULT_TTL: int = 86400
    RQ_WORKERS: int = 3
    SCREENSHOT_FILESYSTEM_PATH: str = "./screenshots"
    SCREENSHOT_STORAGE_TYPE: str = "filesystem"
    SCREENSHOT_S3_ACCESS_KEY_ID: str = ""
    SCREENSHOT_S3_BUCKET: str = ""
    SCREENSHOT_S3_ENDPOINT_URL: str = ""
    SCREENSHOT_S3_FORCE_PATH_STYLE: bool = True
    SCREENSHOT_S3_PREFIX: str = "screenshots"
    SCREENSHOT_S3_REGION: str = "us-east-1"
    SCREENSHOT_S3_SECRET_ACCESS_KEY: str = ""
    SCREENSHOTS_GID: int | None = None
    SCREENSHOTS_UID: int | None = None
    TZ: str = "Europe/Paris"
    WAIT_AFTER_SCROLL: int = 3
    WAIT_BEFORE_SCROLL: int = 3

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        if not self.DATABASE_URL:
            self.DATABASE_URL = build_database_url(
                engine=self.DB_ENGINE,
                host=self.DB_HOST,
                port=self.DB_PORT,
                user=self.DB_USER,
                password=self.DB_PASSWORD,
                name=self.DB_NAME,
            )
        return self
