"""Database connection, session handling and schema setup."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://app:app@localhost:5432/app"
)
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "3"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Enable pgvector and create missing tables."""
    # Import models so they are registered on Base.metadata.
    from app import models  # noqa: F401

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields one session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
