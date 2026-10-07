"""Helpers inspired by GreenIT-Analysis HAR resource classification."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from ecoindex.models.scraper import RequestItem

HTTP_REDIRECT_CODES = frozenset({301, 302, 303, 307})
HTTP_COMPRESSION_TOKENS = frozenset(
    {"br", "compress", "deflate", "gzip", "pack200-gzip"}
)

_STATIC_CATEGORIES = frozenset(
    {"image", "javascript", "font", "css", "audio", "video"}
)
_COMPRESSIBLE_CATEGORIES = frozenset({"css", "javascript", "html", "font"})

_FONT_MIME_RE = re.compile(
    r"(font/|application/(?:x-)?font-|application/vnd\.ms-fontobject|"
    r"application/font-sfnt)",
    re.I,
)
_COMPRESSIBLE_MIME_RE = re.compile(
    r"^(text/|application/(?:javascript|x-javascript|json|xml|xhtml\+xml|"
    r"ld\+json|rss\+xml|atom\+xml|manifest\+json)|image/svg\+xml|"
    r"font/(?:eot|opentype))",
    re.I,
)
_STATIC_MIME_RE = re.compile(
    r"^(image/|audio/|video/|text/css|text/javascript|application/javascript|"
    r"application/x-javascript|font/|application/(?:x-)?font-|"
    r"application/vnd\.ms-fontobject|application/pdf|application/octet-stream|"
    r"application/zip|application/x-shockwave-flash|application/manifest\+json)",
    re.I,
)

_SOCIAL_PATTERNS: list[tuple[str, str]] = [
    ("platform.twitter.com/widgets.js", "twitter"),
    ("platform.linkedin.com/in.js", "linkedin"),
    ("assets.pinterest.com/js/pinit.js", "pinterest"),
    ("platform-api.sharethis.com/js/sharethis.js", "sharethis"),
    ("s7.addthis.com/js/300/addthis_widget.js", "addthis"),
    ("static.addtoany.com/menu/page.js", "addtoany"),
]


def header_map(headers: list[dict] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    if not headers:
        return result
    for header in headers:
        name = header.get("name")
        value = header.get("value")
        if name is None or value is None:
            continue
        result[str(name).lower()] = str(value)
    return result


def is_font_resource(item: RequestItem) -> bool:
    if item.category == "font" or _FONT_MIME_RE.search(item.mime_type or ""):
        return item.size > 0
    mime = (item.mime_type or "").split(";")[0].strip().lower()
    if mime in {"", "text/plain", "application/octet-stream"}:
        path = urlparse(item.url).path.lower()
        if path.endswith((".woff", ".woff2", ".ttf", ".otf", ".eot")):
            return item.size > 0
        if ".woff?" in item.url.lower() or ".woff2?" in item.url.lower():
            return item.size > 0
    return False


def is_css_resource(item: RequestItem) -> bool:
    return item.category == "css" or "css" in (item.mime_type or "").lower()


def is_gif_resource(item: RequestItem) -> bool:
    mime = (item.mime_type or "").lower()
    if "gif" in mime:
        return True
    path = urlparse(item.url).path.lower()
    return path.endswith(".gif")


def is_static_resource(item: RequestItem) -> bool:
    if item.category in _STATIC_CATEGORIES:
        return True
    return bool(_STATIC_MIME_RE.search((item.mime_type or "").split(";")[0].strip()))


def is_compressible_resource(item: RequestItem) -> bool:
    if item.size <= 150:
        return False
    if item.category in _COMPRESSIBLE_CATEGORIES:
        return True
    return bool(
        _COMPRESSIBLE_MIME_RE.search((item.mime_type or "").split(";")[0].strip())
    )


def is_resource_compressed(item: RequestItem) -> bool:
    encoding = (item.content_encoding or "").lower().strip()
    if not encoding:
        return False
    # Content-Encoding can be a comma-separated list.
    tokens = {token.strip() for token in encoding.split(",")}
    return bool(tokens & HTTP_COMPRESSION_TOKENS)


def has_valid_cache_headers(item: RequestItem) -> bool:
    cache_control = item.cache_control or ""
    is_valid = False
    if cache_control and not re.search(
        r"(no-cache)|(no-store)|(max-age\s*=\s*0)", cache_control, re.I
    ):
        is_valid = True

    if item.expires:
        expires = _parse_http_date(item.expires)
        if expires is not None:
            now = _parse_http_date(item.response_date) or datetime.now(tz=expires.tzinfo)
            if expires < now:
                is_valid = False

    return is_valid


def _parse_http_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def is_http1(item: RequestItem) -> bool:
    version = (item.http_version or "").upper()
    return "HTTP/1" in version


def is_http_redirect(status: int) -> bool:
    return status in HTTP_REDIRECT_CODES


def official_social_network(url: str) -> str | None:
    lower = url.lower()
    host = (urlparse(url).hostname or "").lower()
    if host == "connect.facebook.net" and "sdk.js" in lower:
        return "facebook"
    for pattern, name in _SOCIAL_PATTERNS:
        if pattern in lower:
            return name
    return None
