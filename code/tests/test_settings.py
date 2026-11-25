"""Unit tests for reading settings from the environment (no database)."""

import pytest

from app.settings import get_settings


def test_defaults(monkeypatch):
    for name in ("APP_ENV", "AUTH_ENABLED", "USER_MANAGEMENT_ENABLED", "SESSION_TTL_MINUTES",
                 "ADMIN_EMAIL", "ADMIN_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    settings = get_settings()
    assert settings.app_env == "local"
    assert settings.config_editable is True
    assert settings.auth_enabled is False
    assert settings.user_management_enabled is False
    assert settings.session_ttl_minutes == 60
    assert settings.admin_email == "admin@example.com"
    assert settings.admin_password == ""


@pytest.mark.parametrize(
    ("app_env", "editable"),
    [("local", True), ("test", True), ("TEST", True), ("staging", False), ("production", False)],
)
def test_config_is_editable_only_in_local_and_test(monkeypatch, app_env, editable):
    monkeypatch.setenv("APP_ENV", app_env)
    assert get_settings().config_editable is editable


@pytest.mark.parametrize(
    ("value", "expected"),
    [("true", True), ("1", True), ("YES", True), ("false", False), ("0", False), ("", False)],
)
def test_boolean_flags(monkeypatch, value, expected):
    monkeypatch.setenv("AUTH_ENABLED", value)
    assert get_settings().auth_enabled is expected


@pytest.mark.parametrize(("value", "expected"), [("15", 15), ("0", 1), ("-5", 1), ("abc", 60)])
def test_session_ttl(monkeypatch, value, expected):
    monkeypatch.setenv("SESSION_TTL_MINUTES", value)
    assert get_settings().session_ttl_minutes == expected


def test_admin_email_is_normalized(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "  Root@Example.COM ")
    assert get_settings().admin_email == "root@example.com"
