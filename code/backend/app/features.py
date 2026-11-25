"""Feature switches: login/sessions and user management.

In local and test, values saved from the config page (table app_settings)
override the environment. In staging and production only the environment
(AUTH_ENABLED, USER_MANAGEMENT_ENABLED) counts.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import AppSetting
from app.settings import get_settings

AUTH_KEY = "auth_enabled"
USER_MANAGEMENT_KEY = "user_management_enabled"


@dataclass(frozen=True)
class Features:
    auth_enabled: bool
    user_management_enabled: bool


def get_features(db: Session) -> Features:
    settings = get_settings()
    auth = settings.auth_enabled
    users = settings.user_management_enabled
    if settings.config_editable:
        saved = {row.key: row.value == "true" for row in db.query(AppSetting).all()}
        auth = saved.get(AUTH_KEY, auth)
        users = saved.get(USER_MANAGEMENT_KEY, users)
    # User management without login makes no sense: treat it as off.
    return Features(auth_enabled=auth, user_management_enabled=auth and users)


def set_features(db: Session, auth_enabled: bool, user_management_enabled: bool) -> None:
    for key, value in ((AUTH_KEY, auth_enabled), (USER_MANAGEMENT_KEY, user_management_enabled)):
        db.merge(AppSetting(key=key, value="true" if value else "false"))
    db.commit()
