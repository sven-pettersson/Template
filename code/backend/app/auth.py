"""Authentication dependencies and session helpers.

Clients send `Authorization: Bearer <token>`. The token is random and only its
sha256 hash is stored in the sessions table, together with expires_at (TTL from
SESSION_TTL_MINUTES).
"""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.features import get_features
from app.models import User, UserSession
from app.security import hash_password, hash_token, new_token, verify_password
from app.settings import get_settings

bearer = HTTPBearer(auto_error=False, description="Session token from POST /api/auth/login")


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_session(db: Session, user: User) -> tuple[str, datetime]:
    """Store a new session for user and return (token, expires_at)."""
    token = new_token()
    expires_at = datetime.now(UTC) + timedelta(minutes=get_settings().session_ttl_minutes)
    db.add(UserSession(token_hash=hash_token(token), user_id=user.id, expires_at=expires_at))
    db.commit()
    return token, expires_at


def find_session(db: Session, token: str) -> UserSession | None:
    """The valid session for token. Expired sessions are deleted and give None."""
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if session is None:
        return None
    if session.expires_at <= datetime.now(UTC):
        db.delete(session)
        db.commit()
        return None
    return session


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> UserSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    session = find_session(db, credentials.credentials)
    if session is None:
        raise _unauthorized("Invalid or expired token")
    return session


def current_user(
    session: UserSession = Depends(current_session), db: Session = Depends(get_db)
) -> User:
    user = db.get(User, session.user_id)
    if user is None:
        raise _unauthorized("Invalid or expired token")
    return user


def require_auth_feature(db: Session = Depends(get_db)) -> None:
    """404 when login/sessions are switched off."""
    if not get_features(db).auth_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Login is not enabled")


def require_login(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Protects a router: open when login is off, otherwise a valid token is required."""
    if not get_features(db).auth_enabled:
        return None
    return current_user(current_session(credentials, db), db)


def require_user_management(db: Session = Depends(get_db)) -> None:
    """404 when user management is switched off."""
    if not get_features(db).user_management_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User management is not enabled")


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin rights required")
    return user


def ensure_root_admin(db: Session) -> User | None:
    """Create or update the root admin from ADMIN_EMAIL and ADMIN_PASSWORD.

    Does nothing when ADMIN_PASSWORD is empty. If the password in the
    environment has changed, the stored hash is updated.
    """
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        return None
    user = db.scalar(select(User).where(User.email == settings.admin_email))
    if user is None:
        user = User(email=settings.admin_email, password_hash=hash_password(settings.admin_password))
        db.add(user)
    elif not verify_password(settings.admin_password, user.password_hash):
        user.password_hash = hash_password(settings.admin_password)
    user.is_admin = True
    user.is_root = True
    # If ADMIN_EMAIL changed, the previous root admin becomes an ordinary admin.
    for other in db.scalars(select(User).where(User.is_root, User.email != settings.admin_email)):
        other.is_root = False
    db.commit()
    db.refresh(user)
    return user
