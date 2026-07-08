from unittest.mock import MagicMock, patch

import pytest

from ecoindex.config.sentry import (
    INTERNAL_SERVER_ERROR_STATUS,
    capture_internal_error,
    capture_task_failure,
    get_sentry_environment,
    init_sentry,
)


@pytest.fixture
def sentry_settings(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://example@sentry.io/1")


def test_get_sentry_environment_defaults_to_production(sentry_settings, monkeypatch):
    monkeypatch.delenv("DEBUG", raising=False)
    from ecoindex.config.settings import Settings

    Settings.model_config["env_file"] = None
    assert get_sentry_environment() == "production"


def test_get_sentry_environment_uses_debug(sentry_settings, monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    from ecoindex.config.settings import Settings

    Settings.model_config["env_file"] = None
    assert get_sentry_environment() == "development"


def test_get_sentry_environment_uses_explicit_value(sentry_settings, monkeypatch):
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "staging")
    from ecoindex.config.settings import Settings

    Settings.model_config["env_file"] = None
    assert get_sentry_environment() == "staging"


@patch("ecoindex.config.sentry.sentry_sdk.init")
def test_init_sentry_registers_fastapi_and_rq_integrations(mock_init, sentry_settings):
    init_sentry(with_fastapi=True, with_rq=True, release="ecoindex-api@1.0.0")

    mock_init.assert_called_once()
    kwargs = mock_init.call_args.kwargs
    assert kwargs["dsn"] == "https://example@sentry.io/1"
    assert kwargs["release"] == "ecoindex-api@1.0.0"
    assert len(kwargs["integrations"]) == 3


@patch("ecoindex.config.sentry.sentry_sdk.init")
def test_init_sentry_skipped_without_dsn(mock_init, monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)

    init_sentry(with_fastapi=True)

    mock_init.assert_not_called()


@patch("ecoindex.config.sentry.sentry_sdk.capture_exception")
@patch("ecoindex.config.sentry.sentry_sdk.push_scope")
def test_capture_internal_error_reports_500_errors(
    mock_push_scope, mock_capture_exception, sentry_settings
):
    scope = MagicMock()
    mock_push_scope.return_value.__enter__.return_value = scope
    error = RuntimeError("boom")

    capture_internal_error(
        error,
        status_code=INTERNAL_SERVER_ERROR_STATUS,
        context={"path": "/v1/ecoindexes"},
    )

    scope.set_extra.assert_called_once_with("path", "/v1/ecoindexes")
    mock_capture_exception.assert_called_once_with(error)


@patch("ecoindex.config.sentry.sentry_sdk.capture_exception")
def test_capture_internal_error_ignores_non_500_errors(
    mock_capture_exception, sentry_settings
):
    capture_internal_error(ValueError("expected"), status_code=429)

    mock_capture_exception.assert_not_called()


@patch("ecoindex.config.sentry.sentry_sdk.capture_exception")
@patch("ecoindex.config.sentry.sentry_sdk.push_scope")
def test_capture_task_failure_adds_task_context(
    mock_push_scope, mock_capture_exception, sentry_settings
):
    scope = MagicMock()
    mock_push_scope.return_value.__enter__.return_value = scope
    error = RuntimeError("worker failed")

    capture_task_failure(
        error,
        status_code=500,
        url="https://example.com",
        task_id="abc-123",
        task_name="ecoindex_task",
    )

    scope.set_extra.assert_any_call("url", "https://example.com")
    scope.set_extra.assert_any_call("task_id", "abc-123")
    scope.set_extra.assert_any_call("task_name", "ecoindex_task")
    mock_capture_exception.assert_called_once_with(error)
