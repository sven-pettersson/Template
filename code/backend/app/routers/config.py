"""Feature switches. Reading is always open; changing exists only in local and test."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.features import get_features, set_features
from app.schemas import ConfigRead, ConfigUpdate
from app.settings import get_settings

router = APIRouter(prefix="/api/config", tags=["config"])


def _read(db: Session) -> ConfigRead:
    settings = get_settings()
    features = get_features(db)
    return ConfigRead(
        app_env=settings.app_env,
        editable=settings.config_editable,
        auth_enabled=features.auth_enabled,
        user_management_enabled=features.user_management_enabled,
        session_ttl_minutes=settings.session_ttl_minutes,
    )


@router.get("", response_model=ConfigRead)
def read_config(db: Session = Depends(get_db)):
    return _read(db)


@router.put("", response_model=ConfigRead)
def update_config(payload: ConfigUpdate, db: Session = Depends(get_db)):
    if not get_settings().config_editable:
        # Behave as if the endpoint does not exist in staging and production.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    set_features(db, payload.auth_enabled, payload.user_management_enabled)
    return _read(db)
