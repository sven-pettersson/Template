"""User management (admins only, only when the switch is on)."""

import pytest


@pytest.fixture
def admin_headers(make_user, login):
    make_user("admin@example.com", is_admin=True)
    return login("admin@example.com")


def test_admin_creates_lists_and_deletes(db_client, users_on, admin_headers):
    created = db_client.post(
        "/api/users",
        json={"email": " New@Example.com", "password": "password1"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "new@example.com"
    assert body["is_admin"] is False
    assert "password" not in body and "password_hash" not in body

    emails = [u["email"] for u in db_client.get("/api/users", headers=admin_headers).json()]
    assert emails == ["admin@example.com", "new@example.com"]

    assert db_client.delete(f"/api/users/{body['id']}", headers=admin_headers).status_code == 204
    assert db_client.delete(f"/api/users/{body['id']}", headers=admin_headers).status_code == 404


def test_new_user_can_log_in(db_client, users_on, admin_headers, login):
    db_client.post(
        "/api/users", json={"email": "u@example.com", "password": "password1"}, headers=admin_headers
    )
    assert "Authorization" in login("u@example.com", "password1")


def test_non_admin_gets_403(db_client, users_on, make_user, login):
    make_user("user@example.com")
    assert db_client.get("/api/users", headers=login("user@example.com")).status_code == 403


def test_requires_token(db_client, users_on):
    assert db_client.get("/api/users").status_code == 401


def test_404_when_user_management_is_off(db_client, auth_on, admin_headers):
    assert db_client.get("/api/users", headers=admin_headers).status_code == 404


def test_duplicate_email_gives_409(db_client, users_on, admin_headers):
    payload = {"email": "dup@example.com", "password": "password1"}
    assert db_client.post("/api/users", json=payload, headers=admin_headers).status_code == 201
    payload["email"] = "DUP@example.com"
    assert db_client.post("/api/users", json=payload, headers=admin_headers).status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": "password1"},
        {"email": "a@b", "password": "password1"},
        {"email": "", "password": "password1"},
        {"email": "ok@example.com", "password": "short"},
        {"email": "ok@example.com"},
    ],
    ids=["no-at", "no-dot", "empty-email", "short-password", "missing-password"],
)
def test_invalid_payload_gives_422(db_client, users_on, admin_headers, payload):
    assert db_client.post("/api/users", json=payload, headers=admin_headers).status_code == 422


def test_cannot_delete_root_admin(db_client, db_session, users_on, admin_headers, monkeypatch):
    from app.auth import ensure_root_admin

    monkeypatch.setenv("ADMIN_EMAIL", "root@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "root-password")
    root = ensure_root_admin(db_session)
    response = db_client.delete(f"/api/users/{root.id}", headers=admin_headers)
    assert response.status_code == 400


def test_cannot_delete_yourself(db_client, users_on, admin_headers):
    me = db_client.get("/api/auth/me", headers=admin_headers).json()
    assert db_client.delete(f"/api/users/{me['id']}", headers=admin_headers).status_code == 400
