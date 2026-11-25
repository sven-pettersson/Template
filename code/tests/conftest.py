"""pytest setup for code/tests.

The API tests need the backend dependencies (code/backend/requirements-dev.txt).
Without them those tests are not collected, so the standalone tests (receipt
calculator, stack.py) still run with a plain pytest install.
"""

import importlib.util

BACKEND_DEPS = all(
    importlib.util.find_spec(name) is not None for name in ("fastapi", "sqlalchemy", "pgvector")
)

if BACKEND_DEPS:
    from api_fixtures import *  # noqa: F401,F403  (registers the fixtures)
else:
    collect_ignore_glob = ["test_*_api.py"]


def pytest_report_header(config):
    if not BACKEND_DEPS:
        return (
            "API tests not collected: install code/backend/requirements-dev.txt "
            "or run /stack-test"
        )
    return None
