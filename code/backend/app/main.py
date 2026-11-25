"""FastAPI application. Swagger UI: /docs, ReDoc: /redoc."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routers import items


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Template API",
    description="Minimal FastAPI backend with PostgreSQL and pgvector.",
    version="0.1.0",
    lifespan=lifespan,
)

# One router per resource. /new-resource adds more here.
app.include_router(items.router)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
