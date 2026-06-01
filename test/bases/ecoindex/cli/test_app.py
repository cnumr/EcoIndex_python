from os import remove

from ecoindex.cli.app import app
from typer.testing import CliRunner

runner = CliRunner()


def test_analyze_no_args() -> None:
    result = runner.invoke(app=app, args=["analyze"])
    assert result.exit_code == 1
    assert "🔥 You must provide an url..." in result.stdout


def test_analyze_not_valid_url() -> None:
    invalid_url = "url"
    result = runner.invoke(app=app, args=["analyze", "--url", invalid_url])
    assert result.exit_code == 1
    assert (
        "Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='url', input_type=str]"
        in result.stdout
    )


def test_analyze_one_invalid_url() -> None:
    valid_url = "https://www.test.com"
    invalid_url = "dummy"
    result = runner.invoke(
        app=app, args=["analyze", "--url", valid_url, "--url", invalid_url], input="n\n"
    )
    assert result.exit_code == 1
    assert (
        "Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='dummy', input_type=str]"
        in result.stdout
    )


def test_analyze_one_valid_url() -> None:
    domain = "www.test.com"
    valid_url = f"https://{domain}"
    result = runner.invoke(app=app, args=["analyze", "--url", valid_url], input="n\n")
    assert "There are 1 url(s), do you want to process?" in result.stdout
    assert result.exit_code == 1
    assert f"{domain}.csv" in result.stdout
    remove(f"/tmp/ecoindex-cli/input/{domain}.csv")


def test_analyze_string_window_size() -> None:
    invalid_window_size = "window"
    result = runner.invoke(
        app=app, args=["analyze", "--window-size", invalid_window_size]
    )
    assert result.exit_code == 1
    assert (
        f"🔥 `{invalid_window_size}` is not a valid window size. Must be of type `1920,1080`"
        in result.stdout
    )


def test_analyze_one_invalid_window_size() -> None:
    valid_window_size = "1920,1080"
    invalid_window_size = "1920,height"
    result = runner.invoke(
        app=app,
        args=[
            "analyze",
            "--window-size",
            valid_window_size,
            "--window-size",
            invalid_window_size,
        ],
    )
    assert result.exit_code == 1
    assert (
        f"🔥 `{invalid_window_size}` is not a valid window size. Must be of type `1920,1080`"
        in result.stdout
    )


def test_analyze_abort_recursive() -> None:
    result = runner.invoke(app=app, args=["analyze", "--recursive"], input="n\n")
    assert (
        "You are about to perform a recursive website scraping. This can take a long time. Are you sure to want to proceed?"
        in result.stdout
    )
    assert result.exit_code == 1


def test_analyze_abort_sitemap() -> None:
    domain = "www.test.com"
    valid_url = f"https://{domain}/sitemap.xml"
    result = runner.invoke(
        app=app, args=["analyze", "--sitemap", valid_url], input="n\n"
    )
    assert (
        "You are about to read urls from a website sitemap. This can take a long time. Are you sure to want to proceed?"
        in result.stdout
    )
    assert result.exit_code == 1


def test_invalid_sitemap() -> None:
    domain = "www.test.com"
    invalid_sitemap = f"https://{domain}"
    result = runner.invoke(
        app=app, args=["analyze", "--sitemap", invalid_sitemap], input="y\n"
    )
    assert (
        "You are about to read urls from a website sitemap. This can take a long time. Are you sure to want to proceed?"
        in result.stdout
    )
    assert "Aborted" not in result.stdout
    assert "The provided url is not a valid sitemap url" in result.stdout
    assert result.exit_code == 1


def test_no_interaction() -> None:
    result = runner.invoke(app=app, args=["analyze", "--recursive", "--no-interaction"])
    assert "[Y/n]" not in result.stdout
    assert result.exit_code == 1


def test_unauthorized_export_format() -> None:
    result = runner.invoke(app=app, args=["analyze", "--export-format", "txt"])
    assert result.exit_code == 2
    assert "'txt' is not one of 'csv', 'json'." in result.stderr
