"""API tests for the FastAPI backend.

The health and validation tests run without a database. Tests that touch
PostgreSQL use DATABASE_URL and are skipped when no database is reachable.
Every database test runs inside a transaction that is rolled back, so no
data is left behind.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db import EMBEDDING_DIM, engine, get_db, init_db
from app.main import app


def vector(*values: float) -> list[float]:
    """Pad values with zeros up to EMBEDDING_DIM."""
    return list(values) + [0.0] * (EMBEDDING_DIM - len(values))


@pytest.fixture
def client():
    # No `with` block: the lifespan (init_db) is not run, so no database is needed.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def db_client(client):
    try:
        init_db()
        connection = engine.connect()
    except OperationalError:
        pytest.skip("PostgreSQL is not reachable via DATABASE_URL")

    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    session.execute(text("DELETE FROM items"))

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield client
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_swagger_docs_are_served(client):
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/api/health", "/api/items", "/api/items/search"} <= set(paths)


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "x", "embedding": [1.0] * (EMBEDDING_DIM + 1)},
        {"name": "x", "embedding": [0.0] * EMBEDDING_DIM},
    ],
    ids=["empty-name", "wrong-dim", "zero-vector"],
)
def test_create_item_rejects_invalid_payload(client, payload):
    assert client.post("/api/items", json=payload).status_code == 422


def test_search_rejects_wrong_dimension(client):
    response = client.post("/api/items/search", json={"embedding": [1.0] * (EMBEDDING_DIM + 1)})
    assert response.status_code == 422


def test_list_items_empty(db_client):
    response = db_client.get("/api/items")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_item(db_client):
    created = db_client.post(
        "/api/items",
        json={"name": "First", "description": "desc", "embedding": vector(1.0)},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "First"
    assert body["embedding"] == vector(1.0)

    items = db_client.get("/api/items").json()
    assert [item["name"] for item in items] == ["First"]


def test_create_item_without_embedding(db_client):
    created = db_client.post("/api/items", json={"name": "Plain"})
    assert created.status_code == 201
    assert created.json()["embedding"] is None


def test_search_returns_nearest_first(db_client):
    db_client.post("/api/items", json={"name": "near", "embedding": vector(1.0, 0.1)})
    db_client.post("/api/items", json={"name": "far", "embedding": vector(0.0, 1.0)})
    db_client.post("/api/items", json={"name": "no-vector"})

    response = db_client.post("/api/items/search", json={"embedding": vector(1.0), "limit": 5})
    assert response.status_code == 200
    results = response.json()
    assert [r["name"] for r in results] == ["near", "far"]
    assert results[0]["distance"] < results[1]["distance"]


def test_search_without_embeddings_returns_empty(db_client):
    db_client.post("/api/items", json={"name": "no-vector"})
    response = db_client.post("/api/items/search", json={"embedding": vector(1.0)})
    assert response.status_code == 200
    assert response.json() == []
