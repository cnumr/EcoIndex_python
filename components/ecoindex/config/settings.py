from pydantic_settings import BaseSettings, SettingsConfigDict


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
    DATABASE_URL: str = "sqlite+aiosqlite:///db.sqlite3"
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
    SCREENSHOT_S3_REGION: str = "garage"
    SCREENSHOT_S3_SECRET_ACCESS_KEY: str = ""
    SCREENSHOTS_GID: int | None = None
    SCREENSHOTS_UID: int | None = None
    TZ: str = "Europe/Paris"
    WAIT_AFTER_SCROLL: int = 3
    WAIT_BEFORE_SCROLL: int = 3
