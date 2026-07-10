"""Create the screenshot bucket in S3-compatible storage if it does not exist."""

from __future__ import annotations

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from ecoindex.config.settings import Settings


def ensure_screenshot_bucket() -> str:
    settings = Settings()
    if not settings.SCREENSHOT_S3_BUCKET:
        raise RuntimeError("SCREENSHOT_S3_BUCKET must be configured when using S3 storage.")

    client = boto3.client(
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

    bucket = settings.SCREENSHOT_S3_BUCKET
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        client.create_bucket(Bucket=bucket)

    return bucket


def main() -> None:
    print(ensure_screenshot_bucket())


if __name__ == "__main__":
    main()
