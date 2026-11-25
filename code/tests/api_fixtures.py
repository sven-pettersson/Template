"""Fixtures for the API tests (loaded by conftest.py when backend deps exist).

`client` runs without a database. `db_client` (and `db_session`) need
PostgreSQL via DATABASE_URL and are skipped when it is not reachable. Every
database test runs inside a transaction that is rolled back.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import engine, get_db, init_db
from app.main import app
from app.models import User
from app.security import hash_password

FEATURE_ENV = (
    "APP_ENV",
    "AUTH_ENABLED",
    "USER_MANAGEMENT_ENABLED",
    "SESSION_TTL_MINUTES",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
)


@pytest.fixture(autouse=True)
def clean_feature_env(monkeypatch):
    """Tests start from the defaults: APP_ENV=local, login and users off."""
    for name in FEATURE_ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def client():
    # No `with` block: the lifespan (init_db) is not run, so no database is needed.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    try:
        init_db()
        connection = engine.connect()
    except OperationalError:
        pytest.skip("PostgreSQL is not reachable via DATABASE_URL")

    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    session.execute(text("DELETE FROM sessions"))
    session.execute(text("DELETE FROM users"))
    session.execute(text("DELETE FROM app_settings"))
    session.execute(text("DELETE FROM items"))
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db_client(client, db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield client


@pytest.fixture
def auth_on(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")


@pytest.fixture
def users_on(monkeypatch, auth_on):
    monkeypatch.setenv("USER_MANAGEMENT_ENABLED", "true")


@pytest.fixture
def make_user(db_session):
    """make_user(email, password="secret123", is_admin=False) -> User"""

    def _make(email: str, password: str = "secret123", is_admin: bool = False) -> User:
        user = User(email=email, password_hash=hash_password(password), is_admin=is_admin)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def login(client):
    """login(email, password="secret123") -> {"Authorization": "Bearer <token>"}"""

    def _login(email: str, password: str = "secret123") -> dict[str, str]:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login
