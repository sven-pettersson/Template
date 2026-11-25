"""Login, logout and the current user. Exists only when login is switched on."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import (
    authenticate,
    create_session,
    current_session,
    current_user,
    require_auth_feature,
)
from app.db import get_db
from app.models import User, UserSession
from app.schemas import LoginRequest, TokenResponse, UserRead

router = APIRouter(
    prefix="/api/auth", tags=["auth"], dependencies=[Depends(require_auth_feature)]
)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, payload.email, payload.password)
    if user is None:
        # Same message for unknown email and wrong password.
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Wrong email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_at = create_session(db, user)
    return TokenResponse(access_token=token, expires_at=expires_at)


@router.post("/logout", status_code=204)
def logout(session: UserSession = Depends(current_session), db: Session = Depends(get_db)):
    db.delete(session)
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(current_user)):
    return user
