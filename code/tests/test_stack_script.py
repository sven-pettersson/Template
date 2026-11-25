"""Tests for the pure helpers in .claude/scripts/stack.py (no Docker needed)."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / ".claude" / "scripts" / "stack.py"
spec = importlib.util.spec_from_file_location("stack", SCRIPT)
stack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stack)


@pytest.fixture
def root(tmp_path):
    (tmp_path / "docker-compose.yml").write_text("name: demo\nservices: {}\n", encoding="utf-8")
    return tmp_path


def test_parse_env_ignores_comments_and_strips_quotes():
    text = "# comment\n\nA=1\nB = 'two'\nC=\"three\"\nnot a line\nD=x=y\n"
    assert stack.parse_env(text) == {"A": "1", "B": "two", "C": "three", "D": "x=y"}


def test_project_name_from_name_key(root):
    assert stack.project_name(root) == "demo"


def test_project_name_falls_back_to_directory(tmp_path):
    folder = tmp_path / "My Project"
    folder.mkdir()
    (folder / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    assert stack.project_name(folder) == "myproject"


def test_effective_config_precedence(root):
    (root / ".env").write_text("DB_PORT=6000\nBACKEND_PORT=7000\n", encoding="utf-8")
    config = stack.effective_config(root, environ={"BACKEND_PORT": "9000"})
    assert config["DB_PORT"] == "6000"  # .env beats default
    assert config["BACKEND_PORT"] == "9000"  # shell beats .env
    assert config["FRONTEND_PORT"] == "3000"  # default


def test_find_root_searches_upwards(root):
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    assert stack.find_root(nested) == root.resolve()


def test_find_root_without_compose_file(tmp_path):
    with pytest.raises(SystemExit):
        stack.find_root(tmp_path)


def test_update_env_file_keeps_other_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# ports\nDB_PORT=5432\nPOSTGRES_USER=app\n", encoding="utf-8")
    stack.update_env_file(env, {"DB_PORT": "15432", "FRONTEND_PORT": "13000"})
    assert env.read_text(encoding="utf-8") == (
        "# ports\nDB_PORT=15432\nPOSTGRES_USER=app\nFRONTEND_PORT=13000\n"
    )


def test_update_env_file_creates_file(tmp_path):
    env = tmp_path / ".env"
    stack.update_env_file(env, {"DB_PORT": "1"})
    assert env.read_text(encoding="utf-8") == "DB_PORT=1\n"


def test_next_free_port_skips_busy_and_taken():
    busy = {100, 101}
    assert stack.next_free_port(100, lambda p: p not in busy, taken={102}) == 103


def test_plan_ports_keeps_free_and_own_ports():
    config = {"DB_PORT": "5432", "BACKEND_PORT": "8000", "FRONTEND_PORT": "3000"}
    busy = {5432, 8000}
    plan = stack.plan_ports(config, own_ports={8000}, is_free=lambda p: p not in busy)
    assert plan["DB_PORT"] == (5432, 15432)
    assert plan["BACKEND_PORT"] == (8000, None)  # used by this project itself
    assert plan["FRONTEND_PORT"] == (3000, None)


def test_plan_ports_never_suggests_the_same_port_twice():
    config = {"DB_PORT": "5000", "BACKEND_PORT": "5000", "FRONTEND_PORT": "3000"}
    plan = stack.plan_ports(config, own_ports=set(), is_free=lambda p: True)
    assert plan["DB_PORT"] == (5000, None)
    assert plan["BACKEND_PORT"] == (5000, 15000)


def test_port_is_free_respects_docker_ports():
    assert stack.port_is_free(1, docker_ports={1}) is False
