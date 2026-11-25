"""Request and response models used by the API (and shown in Swagger)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db import EMBEDDING_DIM


def _check_dim(value: list[float] | None) -> list[float] | None:
    if value is not None and len(value) != EMBEDDING_DIM:
        raise ValueError(
            f"embedding must have {EMBEDDING_DIM} values, got {len(value)}"
        )
    if value is not None and not any(value):
        # Cosine distance is undefined for a zero vector.
        raise ValueError("embedding must not be all zeros")
    return value


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    embedding: list[float] | None = Field(
        default=None, description=f"Optional vector with {EMBEDDING_DIM} values"
    )

    _validate_embedding = field_validator("embedding")(_check_dim)


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    embedding: list[float] | None

    @field_validator("embedding", mode="before")
    @classmethod
    def _to_list(cls, value):
        # pgvector returns a numpy array; convert it to a plain list.
        return None if value is None else [float(x) for x in value]


class SearchRequest(BaseModel):
    embedding: list[float] = Field(
        description=f"Query vector with {EMBEDDING_DIM} values"
    )
    limit: int = Field(default=5, ge=1, le=100)

    _validate_embedding = field_validator("embedding")(_check_dim)


class SearchResult(ItemRead):
    distance: float = Field(description="Cosine distance, 0 = same direction")


# ---------- auth, users and config ----------

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class LoginRequest(BaseModel):
    email: str = Field(max_length=254, examples=["admin@example.com"])
    password: str = Field(max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserCreate(BaseModel):
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN, examples=["user@example.com"])
    password: str = Field(min_length=8, max_length=200)
    is_admin: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_admin: bool
    is_root: bool
    created_at: datetime


class ConfigRead(BaseModel):
    app_env: str
    editable: bool = Field(description="True only in local and test: the config page exists")
    auth_enabled: bool
    user_management_enabled: bool
    session_ttl_minutes: int


class ConfigUpdate(BaseModel):
    auth_enabled: bool
    user_management_enabled: bool

    @model_validator(mode="after")
    def _users_need_auth(self):
        if self.user_management_enabled and not self.auth_enabled:
            raise ValueError("user management requires login to be enabled")
        return self
