"""FastAPI application. Swagger UI: /docs, ReDoc: /redoc."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.auth import ensure_root_admin, require_login
from app.db import SessionLocal, init_db
from app.routers import auth, config, items, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_root_admin(db)
    yield


app = FastAPI(
    title="Template API",
    description=(
        "Minimal FastAPI backend with PostgreSQL and pgvector. When login is "
        "switched on, log in with POST /api/auth/login and use the token with "
        "the Authorize button (Authorization: Bearer <token>)."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Open endpoints: health, config and auth (login checks its own switch).
app.include_router(config.router)
app.include_router(auth.router)
app.include_router(users.router)

# One router per resource. /new-resource adds more here. Routers included
# with require_login need a Bearer token when login is switched on.
app.include_router(items.router, dependencies=[Depends(require_login)])


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
