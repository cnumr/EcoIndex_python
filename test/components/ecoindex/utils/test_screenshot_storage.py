from pathlib import Path

from ecoindex.models import ScreenShot
from ecoindex.screenshot_storage import (
    get_screenshot_local_folder,
    get_screenshot_object_key,
    persist_screenshot,
    read_screenshot,
    screenshot_exists,
)


def test_get_screenshot_local_folder_for_filesystem(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_STORAGE_TYPE", "filesystem")
    monkeypatch.setenv("SCREENSHOT_FILESYSTEM_PATH", "./custom-screenshots")

    folder = get_screenshot_local_folder(version="v1")

    assert folder.endswith("/custom-screenshots/v1")


def test_get_screenshot_local_folder_for_s3(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_STORAGE_TYPE", "s3")

    folder = get_screenshot_local_folder(version="v1")

    assert folder == "/tmp/ecoindex-screenshots/v1"


def test_get_screenshot_object_key(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_S3_PREFIX", "nested/prefix")

    assert (
        get_screenshot_object_key(version="v1", screenshot_id="screen-id")
        == "nested/prefix/v1/screen-id.webp"
    )


def test_persist_screenshot_uploads_to_s3(monkeypatch, tmp_path):
    uploads = []

    class FakeS3Client:
        def upload_file(self, filename, bucket, key, ExtraArgs):
            uploads.append((filename, bucket, key, ExtraArgs))

    monkeypatch.setenv("SCREENSHOT_STORAGE_TYPE", "s3")
    monkeypatch.setenv("SCREENSHOT_S3_BUCKET", "ecoindex-screenshots")
    monkeypatch.setenv("SCREENSHOT_S3_PREFIX", "screenshots")
    monkeypatch.setenv("SCREENSHOT_S3_ENDPOINT_URL", "http://garage:3900")
    monkeypatch.setenv("SCREENSHOT_S3_ACCESS_KEY_ID", "access-key")
    monkeypatch.setenv("SCREENSHOT_S3_SECRET_ACCESS_KEY", "secret-key")
    monkeypatch.setattr(
        "ecoindex.screenshot_storage.storage._get_s3_client",
        lambda: FakeS3Client(),
    )

    screenshot = ScreenShot(id="screen-id", folder=str(tmp_path))
    screenshot_path = Path(screenshot.get_webp())
    screenshot_path.write_bytes(b"image-bytes")

    persist_screenshot(screenshot=screenshot, version="v1")

    assert uploads == [
        (
            str(screenshot_path),
            "ecoindex-screenshots",
            "screenshots/v1/screen-id.webp",
            {"ContentType": "image/webp"},
        )
    ]
    assert screenshot_path.exists() is False


def test_screenshot_exists_for_filesystem(monkeypatch, tmp_path):
    monkeypatch.setenv("SCREENSHOT_STORAGE_TYPE", "filesystem")
    monkeypatch.setenv("SCREENSHOT_FILESYSTEM_PATH", str(tmp_path))

    screenshot_path = tmp_path / "v1" / "screen-id.webp"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_path.write_bytes(b"content")

    assert screenshot_exists(version="v1", screenshot_id="screen-id") is True


def test_read_screenshot_for_filesystem(monkeypatch, tmp_path):
    monkeypatch.setenv("SCREENSHOT_STORAGE_TYPE", "filesystem")
    monkeypatch.setenv("SCREENSHOT_FILESYSTEM_PATH", str(tmp_path))

    screenshot_path = tmp_path / "v1" / "screen-id.webp"
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_path.write_bytes(b"content")

    assert read_screenshot(version="v1", screenshot_id="screen-id") == b"content"
