"""Request and response models used by the API (and shown in Swagger)."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
