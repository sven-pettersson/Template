"""Runtime settings read from the environment.

get_settings() reads os.environ on every call, so tests can change values
with monkeypatch.setenv without reloading modules.
"""

import os
from dataclasses import dataclass

EDITABLE_ENVS = frozenset({"local", "test"})
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in TRUE_VALUES


def env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        value = int(os.getenv(name, ""))
    except ValueError:
        return default
    return max(value, minimum)


@dataclass(frozen=True)
class Settings:
    app_env: str
    auth_enabled: bool
    user_management_enabled: bool
    session_ttl_minutes: int
    admin_email: str
    admin_password: str

    @property
    def config_editable(self) -> bool:
        """The config page and PUT /api/config exist only in local and test."""
        return self.app_env in EDITABLE_ENVS


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "local").strip().lower() or "local",
        auth_enabled=env_bool("AUTH_ENABLED"),
        user_management_enabled=env_bool("USER_MANAGEMENT_ENABLED"),
        session_ttl_minutes=env_int("SESSION_TTL_MINUTES", 60),
        admin_email=os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower(),
        admin_password=os.getenv("ADMIN_PASSWORD", ""),
    )
