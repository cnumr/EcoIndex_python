from ecoindex.backend.routers.tasks import convert_url_to_punycode
from ecoindex.models import WebPage


def test_convert_url_to_punycode_from_idna_url() -> None:
    assert convert_url_to_punycode("https://xn--3s8h30f.ws/") == "https://xn--3s8h30f.ws/"


def test_convert_url_to_punycode_from_unicode_domain() -> None:
    assert convert_url_to_punycode("https://🦊💻.ws/") == "https://xn--3s8h30f.ws/"


def test_convert_url_to_punycode_from_webpage_validation() -> None:
    web_page = WebPage(url="https://xn--3s8h30f.ws/")

    assert convert_url_to_punycode(web_page.url) == "https://xn--3s8h30f.ws/"
