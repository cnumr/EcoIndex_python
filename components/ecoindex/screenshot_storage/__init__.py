from ecoindex.screenshot_storage.storage import (
    get_screenshot_local_folder,
    get_screenshot_local_path,
    get_screenshot_object_key,
    is_s3_screenshot_storage,
    persist_screenshot,
    read_screenshot,
    screenshot_exists,
)

__all__ = [
    "get_screenshot_local_folder",
    "get_screenshot_local_path",
    "get_screenshot_object_key",
    "is_s3_screenshot_storage",
    "persist_screenshot",
    "read_screenshot",
    "screenshot_exists",
]
