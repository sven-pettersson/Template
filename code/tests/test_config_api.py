"""Feature switches: editable in local/test only, environment rules elsewhere."""

import pytest


def test_defaults(db_client):
    body = db_client.get("/api/config").json()
    assert body == {
        "app_env": "local",
        "editable": True,
        "auth_enabled": False,
        "user_management_enabled": False,
        "session_ttl_minutes": 60,
    }


@pytest.mark.parametrize("app_env", ["local", "test"])
def test_put_saves_switches_in_local_and_test(db_client, monkeypatch, app_env):
    monkeypatch.setenv("APP_ENV", app_env)
    response = db_client.put(
        "/api/config", json={"auth_enabled": True, "user_management_enabled": True}
    )
    assert response.status_code == 200
    assert response.json()["auth_enabled"] is True
    assert response.json()["user_management_enabled"] is True
    # Saved value wins over the environment (AUTH_ENABLED is unset = false).
    assert db_client.get("/api/config").json()["auth_enabled"] is True
    # ...and actually protects the API.
    assert db_client.get("/api/items").status_code == 401


def test_saved_off_overrides_env_on(db_client, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    db_client.put("/api/config", json={"auth_enabled": False, "user_management_enabled": False})
    assert db_client.get("/api/config").json()["auth_enabled"] is False
    assert db_client.get("/api/items").status_code == 200


@pytest.mark.parametrize("app_env", ["staging", "production"])
def test_put_is_404_in_staging_and_production(db_client, monkeypatch, app_env):
    monkeypatch.setenv("APP_ENV", app_env)
    response = db_client.put(
        "/api/config", json={"auth_enabled": True, "user_management_enabled": False}
    )
    assert response.status_code == 404
    assert db_client.get("/api/config").json()["editable"] is False


def test_production_ignores_saved_values(db_client, monkeypatch):
    db_client.put("/api/config", json={"auth_enabled": True, "user_management_enabled": True})
    monkeypatch.setenv("APP_ENV", "production")
    body = db_client.get("/api/config").json()
    assert body["auth_enabled"] is False
    assert body["user_management_enabled"] is False

    monkeypatch.setenv("AUTH_ENABLED", "true")
    assert db_client.get("/api/config").json()["auth_enabled"] is True


def test_user_management_requires_auth(db_client):
    response = db_client.put(
        "/api/config", json={"auth_enabled": False, "user_management_enabled": True}
    )
    assert response.status_code == 422


def test_user_management_env_without_auth_is_off(db_client, monkeypatch):
    monkeypatch.setenv("USER_MANAGEMENT_ENABLED", "true")
    assert db_client.get("/api/config").json()["user_management_enabled"] is False
