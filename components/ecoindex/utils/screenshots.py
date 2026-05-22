import os

from ecoindex.models import ScreenShot

try:
    from PIL import Image

    _pillow_available = True
except ImportError:
    _pillow_available = False


async def convert_screenshot_to_webp(screenshot: ScreenShot) -> None:
    if not _pillow_available:
        raise ImportError("Pillow is required for WebP conversion. Install it with: pip install ecoindex-scraper[webp]")
    image = Image.open(rf"{screenshot.get_png()}")
    width, height = image.size
    ratio = 800 / height if width > height else 600 / width

    image.convert("RGB").resize(size=(int(width * ratio), int(height * ratio))).save(
        rf"{screenshot.get_webp()}",
        format="webp",
    )
    os.unlink(screenshot.get_png())


async def set_screenshot_rights(
    screenshot: ScreenShot,
    uid: int | None = None,
    gid: int | None = None,
) -> None:
    if uid and gid:
        os.chown(path=screenshot.get_webp(), uid=uid, gid=gid)
