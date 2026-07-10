from os import getcwd
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from ecoindex.config.settings import Settings
from ecoindex.models import ScreenShot

TEMPORARY_SCREENSHOT_ROOT = "/tmp/ecoindex-screenshots"


def get_screenshot_storage_type() -> str:
    return Settings().SCREENSHOT_STORAGE_TYPE.lower()


def is_s3_screenshot_storage() -> bool:
    return get_screenshot_storage_type() == "s3"


def _get_root_path(path: str) -> Path:
    root_path = Path(path).expanduser()
    if root_path.is_absolute():
        return root_path
    return Path(getcwd()) / root_path


def _get_s3_client():
    settings = Settings()
    if not settings.SCREENSHOT_S3_BUCKET:
        raise RuntimeError("SCREENSHOT_S3_BUCKET must be configured when using S3 storage.")

    if not settings.SCREENSHOT_S3_ENDPOINT_URL:
        raise RuntimeError(
            "SCREENSHOT_S3_ENDPOINT_URL must be configured when using S3 storage."
        )

    if not settings.SCREENSHOT_S3_ACCESS_KEY_ID:
        raise RuntimeError(
            "SCREENSHOT_S3_ACCESS_KEY_ID must be configured when using S3 storage."
        )

    if not settings.SCREENSHOT_S3_SECRET_ACCESS_KEY:
        raise RuntimeError(
            "SCREENSHOT_S3_SECRET_ACCESS_KEY must be configured when using S3 storage."
        )

    return boto3.client(
        "s3",
        endpoint_url=settings.SCREENSHOT_S3_ENDPOINT_URL,
        region_name=settings.SCREENSHOT_S3_REGION,
        aws_access_key_id=settings.SCREENSHOT_S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.SCREENSHOT_S3_SECRET_ACCESS_KEY,
        config=Config(
            s3={
                "addressing_style": (
                    "path" if settings.SCREENSHOT_S3_FORCE_PATH_STYLE else "auto"
                )
            }
        ),
    )


def get_screenshot_local_folder(version: str) -> str:
    if is_s3_screenshot_storage():
        return str(Path(TEMPORARY_SCREENSHOT_ROOT) / version)

    settings = Settings()
    return str(_get_root_path(settings.SCREENSHOT_FILESYSTEM_PATH) / version)


def get_screenshot_local_path(version: str, screenshot_id: str) -> str:
    return str(Path(get_screenshot_local_folder(version)) / f"{screenshot_id}.webp")


def get_screenshot_object_key(version: str, screenshot_id: str) -> str:
    settings = Settings()
    prefix = settings.SCREENSHOT_S3_PREFIX.strip("/")
    filename = f"{version}/{screenshot_id}.webp"
    return f"{prefix}/{filename}" if prefix else filename


def persist_screenshot(screenshot: ScreenShot, version: str) -> None:
    if not is_s3_screenshot_storage():
        return

    settings = Settings()
    screenshot_path = Path(screenshot.get_webp())
    client = _get_s3_client()
    bucket = settings.SCREENSHOT_S3_BUCKET
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        client.create_bucket(Bucket=bucket)

    client.upload_file(
        str(screenshot_path),
        bucket,
        get_screenshot_object_key(version=version, screenshot_id=screenshot.id),
        ExtraArgs={"ContentType": "image/webp"},
    )
    screenshot_path.unlink(missing_ok=True)


def screenshot_exists(version: str, screenshot_id: str) -> bool:
    if not is_s3_screenshot_storage():
        return Path(get_screenshot_local_path(version, screenshot_id)).is_file()

    settings = Settings()
    try:
        _get_s3_client().head_object(
            Bucket=settings.SCREENSHOT_S3_BUCKET,
            Key=get_screenshot_object_key(version=version, screenshot_id=screenshot_id),
        )
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def read_screenshot(version: str, screenshot_id: str) -> bytes:
    if not is_s3_screenshot_storage():
        return Path(get_screenshot_local_path(version, screenshot_id)).read_bytes()

    settings = Settings()
    response = _get_s3_client().get_object(
        Bucket=settings.SCREENSHOT_S3_BUCKET,
        Key=get_screenshot_object_key(version=version, screenshot_id=screenshot_id),
    )
    return response["Body"].read()
