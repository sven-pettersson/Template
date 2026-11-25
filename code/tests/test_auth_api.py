"""Login, sessions and protection of the API with Authorization: Bearer."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.auth import ensure_root_admin
from app.models import User, UserSession
from app.security import verify_password


def test_login_is_404_when_auth_is_off(db_client, make_user):
    make_user("a@example.com")
    response = db_client.post("/api/auth/login", json={"email": "a@example.com", "password": "secret123"})
    assert response.status_code == 404


def test_items_are_open_when_auth_is_off(db_client):
    assert db_client.get("/api/items").status_code == 200


def test_login_returns_bearer_token_with_ttl(db_client, db_session, make_user, auth_on, monkeypatch):
    monkeypatch.setenv("SESSION_TTL_MINUTES", "15")
    make_user("a@example.com")
    before = datetime.now(UTC)
    response = db_client.post("/api/auth/login", json={"email": "A@Example.com ", "password": "secret123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    expires_at = datetime.fromisoformat(body["expires_at"])
    assert before + timedelta(minutes=14) < expires_at <= datetime.now(UTC) + timedelta(minutes=15)
    # Only the hash is stored, never the token itself.
    stored = db_session.scalars(select(UserSession.token_hash)).all()
    assert len(stored) == 1 and body["access_token"] not in stored


@pytest.mark.parametrize(
    ("email", "password"),
    [("a@example.com", "wrong-password"), ("nobody@example.com", "secret123")],
    ids=["wrong-password", "unknown-email"],
)
def test_login_rejects_bad_credentials(db_client, make_user, auth_on, email, password):
    make_user("a@example.com")
    response = db_client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong email or password"


def test_me_returns_the_logged_in_user(db_client, make_user, login, auth_on):
    make_user("a@example.com")
    response = db_client.get("/api/auth/me", headers=login("a@example.com"))
    assert response.status_code == 200
    assert response.json()["email"] == "a@example.com"
    assert response.json()["is_admin"] is False


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Token abc"}, {"Authorization": "Bearer not-a-real-token"}],
    ids=["missing", "wrong-prefix", "unknown-token"],
)
def test_me_requires_a_valid_bearer_token(db_client, auth_on, headers):
    response = db_client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_session_is_rejected_and_deleted(db_client, db_session, make_user, login, auth_on):
    make_user("a@example.com")
    headers = login("a@example.com")
    session = db_session.scalar(select(UserSession))
    session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    assert db_client.get("/api/auth/me", headers=headers).status_code == 401
    assert db_session.scalar(select(UserSession)) is None


def test_logout_invalidates_the_token(db_client, make_user, login, auth_on):
    make_user("a@example.com")
    headers = login("a@example.com")
    assert db_client.post("/api/auth/logout", headers=headers).status_code == 204
    assert db_client.get("/api/auth/me", headers=headers).status_code == 401


def test_items_require_token_when_auth_is_on(db_client, make_user, login, auth_on):
    assert db_client.get("/api/items").status_code == 401
    make_user("a@example.com")
    assert db_client.get("/api/items", headers=login("a@example.com")).status_code == 200


def test_health_and_config_stay_open_when_auth_is_on(db_client, auth_on):
    assert db_client.get("/api/health").status_code == 200
    assert db_client.get("/api/config").status_code == 200


def test_ensure_root_admin_creates_and_updates(db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "Root@Example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "first-password")
    root = ensure_root_admin(db_session)
    assert root.email == "root@example.com"
    assert root.is_admin and root.is_root
    assert verify_password("first-password", root.password_hash)

    monkeypatch.setenv("ADMIN_PASSWORD", "second-password")
    again = ensure_root_admin(db_session)
    assert again.id == root.id
    assert verify_password("second-password", again.password_hash)
    assert len(db_session.scalars(select(User)).all()) == 1


def test_ensure_root_admin_moves_root_when_email_changes(db_session, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "first-password")
    monkeypatch.setenv("ADMIN_EMAIL", "old@example.com")
    old = ensure_root_admin(db_session)
    monkeypatch.setenv("ADMIN_EMAIL", "new@example.com")
    ensure_root_admin(db_session)
    db_session.refresh(old)
    assert old.is_root is False
    assert old.is_admin is True


def test_ensure_root_admin_does_nothing_without_password(db_session):
    assert ensure_root_admin(db_session) is None
    assert db_session.scalars(select(User)).all() == []


def test_root_admin_can_log_in(db_client, db_session, auth_on, monkeypatch):
    monkeypatch.setenv("ADMIN_PASSWORD", "root-password")
    ensure_root_admin(db_session)
    response = db_client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "root-password"}
    )
    assert response.status_code == 200
