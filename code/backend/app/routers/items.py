"""Endpoints for items: CRUD-light plus vector search."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemRead, SearchRequest, SearchResult

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=list[ItemRead])
def list_items(db: Session = Depends(get_db)):
    return db.scalars(select(Item).order_by(Item.id)).all()


@router.post("", response_model=ItemRead, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/search", response_model=list[SearchResult])
def search_items(payload: SearchRequest, db: Session = Depends(get_db)):
    """Return the items closest to the query vector (cosine distance)."""
    distance = Item.embedding.cosine_distance(payload.embedding).label("distance")
    rows = db.execute(
        select(Item, distance)
        .where(Item.embedding.is_not(None))
        .order_by(distance)
        .limit(payload.limit)
    ).all()
    return [
        SearchResult.model_validate(
            {**ItemRead.model_validate(item).model_dump(), "distance": dist}
        )
        for item, dist in rows
    ]
