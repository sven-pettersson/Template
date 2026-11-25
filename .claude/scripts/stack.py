"""Helper for the stack skills (/stack, /stack-test, /diagnose ...). Stdlib only.

Usage (from anywhere inside the repo):
    python .claude/scripts/stack.py env            effective configuration
    python .claude/scripts/stack.py ports [--write] check host ports, --write fixes .env
    python .claude/scripts/stack.py wait [--timeout N]  wait for db healthy + /api/health
    python .claude/scripts/stack.py urls           print the URLs
    python .claude/scripts/stack.py network        compose network name
    python .claude/scripts/stack.py test [pytest args]  pytest in a container on the network
    python .claude/scripts/stack.py build-frontend  build the frontend build stage
    python .claude/scripts/stack.py diagnose       status, health and logs as markdown
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULTS = {
    "POSTGRES_USER": "app",
    "POSTGRES_PASSWORD": "app",
    "POSTGRES_DB": "app",
    "EMBEDDING_DIM": "3",
    "DB_PORT": "5432",
    "BACKEND_PORT": "8000",
    "FRONTEND_PORT": "3000",
}
PORT_KEYS = ("DB_PORT", "BACKEND_PORT", "FRONTEND_PORT")
COMPOSE_FILE = "docker-compose.yml"
NAME_RE = re.compile(r"^name:\s*['\"]?([A-Za-z0-9_-]+)", re.M)
PUBLISHED_RE = re.compile(r":(\d+)->")
PYTHON_IMAGE = "python:3.14-slim"


# ---------- configuration ----------

def find_root(start=None):
    """Directory holding docker-compose.yml, searching upwards from start."""
    path = Path(start or os.getcwd()).resolve()
    for candidate in (path, *path.parents):
        if (candidate / COMPOSE_FILE).is_file():
            return candidate
    raise SystemExit(f"Hittar ingen {COMPOSE_FILE} uppåt från {path}")


def parse_env(text):
    """Parse KEY=VALUE lines like docker compose does (comments and blanks ignored)."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def project_name(root):
    """`name:` from the compose file, otherwise the directory name (as compose does)."""
    text = (Path(root) / COMPOSE_FILE).read_text(encoding="utf-8")
    match = NAME_RE.search(text)
    if match:
        return match.group(1).lower()
    return re.sub(r"[^a-z0-9_-]", "", Path(root).name.lower())


def effective_config(root, environ=None):
    """Defaults < .env < shell environment (same precedence as docker compose)."""
    environ = os.environ if environ is None else environ
    config = dict(DEFAULTS)
    env_file = Path(root) / ".env"
    if env_file.is_file():
        config.update(parse_env(env_file.read_text(encoding="utf-8")))
    for key in DEFAULTS:
        if environ.get(key):
            config[key] = environ[key]
    return config


def update_env_file(path, updates):
    """Set keys in a .env file, keeping other lines and comments. Creates the file."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    remaining = dict(updates)
    for index, line in enumerate(lines):
        key = line.split("=", 1)[0].strip()
        if "=" in line and not line.lstrip().startswith("#") and key in remaining:
            lines[index] = f"{key}={remaining.pop(key)}"
    lines += [f"{key}={value}" for key, value in remaining.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- docker helpers ----------

def run(args, cwd=None, check=False, capture=True):
    result = subprocess.run(
        args, cwd=cwd, capture_output=capture, text=True, encoding="utf-8", errors="replace"
    )
    if check and result.returncode != 0:
        raise SystemExit(result.stderr or f"{args[0]} misslyckades")
    return result


def published_ports(project=None):
    """Host ports published by running containers (only `project`'s if given)."""
    args = ["docker", "ps", "--format", "{{.Ports}}"]
    if project:
        args[2:2] = ["--filter", f"label=com.docker.compose.project={project}"]
    result = run(args)
    return {int(p) for p in PUBLISHED_RE.findall(result.stdout)}


def own_published_ports(project):
    """Host ports already published by this compose project's containers."""
    return published_ports(project)


def port_is_free(port, docker_ports=None):
    """False if another container publishes the port, something answers on it,
    or it cannot be bound. (On Windows a bind can succeed even though Docker
    Desktop already forwards the port, hence the other checks.)"""
    if docker_ports is not None and port in docker_ports:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


def port_checker(project):
    """is_free(port) that also knows which ports other containers publish."""
    others = published_ports() - published_ports(project)
    return lambda port: port_is_free(port, others)


def next_free_port(start, is_free, taken=()):
    """First port >= start that is free and not already chosen."""
    port = start
    while port < 65535:
        if port not in taken and is_free(port):
            return port
        port += 1
    raise SystemExit(f"Ingen ledig port från {start}")


def plan_ports(config, own_ports, is_free):
    """Return {key: (current, suggested_or_None)} for every port key."""
    plan, chosen = {}, set()
    for key in PORT_KEYS:
        current = int(config[key])
        if current in own_ports or (current not in chosen and is_free(current)):
            plan[key] = (current, None)
            chosen.add(current)
        else:
            suggestion = next_free_port(current + 10000 if current < 55535 else 1024,
                                        is_free, chosen)
            plan[key] = (current, suggestion)
            chosen.add(suggestion)
    return plan


def compose_services(root):
    """List of dicts from `docker compose ps -a --format json`."""
    result = run(["docker", "compose", "ps", "-a", "--format", "json"], cwd=root)
    services = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        services.extend(data if isinstance(data, list) else [data])
    return services


def http_get(url, timeout=3):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, ""
    except (urllib.error.URLError, OSError) as error:
        return None, str(error)


def host_path(path):
    """Absolute path in a form docker accepts for bind mounts (C:/... on Windows)."""
    return Path(path).resolve().as_posix()


# ---------- commands ----------

def cmd_env(root, _args):
    config = effective_config(root)
    print(f"PROJECT={project_name(root)}")
    print(f"NETWORK={project_name(root)}_default")
    for key, value in config.items():
        print(f"{key}={value}")


def cmd_ports(root, args):
    config = effective_config(root)
    project = project_name(root)
    plan = plan_ports(config, own_published_ports(project), port_checker(project))
    changes = {k: s for k, (_, s) in plan.items() if s is not None}
    for key, (current, suggestion) in plan.items():
        state = "ledig" if suggestion is None else f"UPPTAGEN -> förslag {suggestion}"
        print(f"{key}={current}  {state}")
    if not changes:
        print("OK: alla portar är lediga (eller används redan av det här projektet).")
        return 0
    overridden = [k for k in changes if os.environ.get(k)]
    if overridden:
        print("Obs: satta i skalets miljö och går före .env: " + ", ".join(overridden))
    if "--write" in args:
        update_env_file(Path(root) / ".env", {k: str(v) for k, v in changes.items()})
        print("Skrev nya portar till .env")
        return 0
    return 1


def cmd_urls(root, _args):
    config = effective_config(root)
    print(f"Frontend: http://localhost:{config['FRONTEND_PORT']}")
    print(f"Swagger:  http://localhost:{config['BACKEND_PORT']}/docs")
    print(f"ReDoc:    http://localhost:{config['BACKEND_PORT']}/redoc")
    print(f"Databas:  localhost:{config['DB_PORT']} ({config['POSTGRES_USER']}/{config['POSTGRES_DB']})")


def cmd_wait(root, args):
    timeout = int(args[args.index("--timeout") + 1]) if "--timeout" in args else 120
    config = effective_config(root)
    url = f"http://localhost:{config['BACKEND_PORT']}/api/health"
    deadline = time.monotonic() + timeout
    db_state = api_state = "okänd"
    while time.monotonic() < deadline:
        services = {s.get("Service"): s for s in compose_services(root)}
        db = services.get("db", {})
        db_state = db.get("Health") or db.get("State") or "saknas"
        status, _ = http_get(url)
        api_state = str(status)
        if db_state == "healthy" and status == 200:
            print(f"OK: db healthy, {url} svarar 200")
            return 0
        exited = [name for name, s in services.items() if s.get("State") == "exited"]
        if exited:
            print(f"FEL: tjänster har avslutats: {', '.join(exited)}. Kör /diagnose.")
            return 1
        time.sleep(2)
    print(f"TIMEOUT efter {timeout}s: db={db_state}, api={api_state}. Kör /diagnose.")
    return 1


def cmd_network(root, _args):
    print(f"{project_name(root)}_default")


def cmd_test(root, args):
    config = effective_config(root)
    network = f"{project_name(root)}_default"
    url = (f"postgresql+psycopg://{config['POSTGRES_USER']}:{config['POSTGRES_PASSWORD']}"
           f"@db:5432/{config['POSTGRES_DB']}")
    has_network = run(["docker", "network", "inspect", network]).returncode == 0
    if not has_network:
        print(f"Obs: nätverket {network} finns inte – databastesterna hoppas över. "
              "Starta stacken med /stack up först.")
    command = [
        "docker", "run", "--rm",
        *(["--network", network] if has_network else []),
        "-v", f"{host_path(root)}:/repo:ro",
        "-v", f"{project_name(root)}_pipcache:/root/.cache/pip",
        "-w", "/repo",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", f"DATABASE_URL={url}",
        "-e", f"EMBEDDING_DIM={config['EMBEDDING_DIM']}",
        PYTHON_IMAGE, "sh", "-c",
        "pip install -q --root-user-action=ignore --disable-pip-version-check "
        "-r code/backend/requirements-dev.txt && pytest -p no:cacheprovider -rs "
        + " ".join(args),
    ]
    env = dict(os.environ, MSYS_NO_PATHCONV="1")
    return subprocess.run(command, env=env).returncode


def cmd_build_frontend(root, _args):
    return subprocess.run(
        ["docker", "build", "--target", "build", "-q", str(Path(root) / "code" / "frontend")]
    ).returncode


def cmd_diagnose(root, _args):
    config = effective_config(root)
    project = project_name(root)
    print(f"# Diagnos för compose-projektet `{project}`\n")
    services = compose_services(root)
    if not services:
        print("Inga containrar finns för projektet. Stacken är inte startad (/stack up).\n")
    else:
        print("| Tjänst | State | Health | Status | Portar |")
        print("|---|---|---|---|---|")
        for s in services:
            ports = sorted({str(p["PublishedPort"]) for p in s.get("Publishers") or []
                            if p.get("PublishedPort")})
            print(f"| {s.get('Service')} | {s.get('State')} | {s.get('Health') or '-'} | "
                  f"{s.get('Status')} | {', '.join(ports) or '-'} |")
        print()

    print("## Portar\n")
    plan = plan_ports(config, own_published_ports(project), port_checker(project))
    for key, (current, suggestion) in plan.items():
        print(f"- {key}={current}: " + ("ok" if suggestion is None
                                        else f"upptagen av något annat (ledig: {suggestion})"))
    print()

    print("## Hälsokontroller\n")
    for name, url in (("backend", f"http://localhost:{config['BACKEND_PORT']}/api/health"),
                      ("frontend->backend", f"http://localhost:{config['FRONTEND_PORT']}/api/health")):
        status, body = http_get(url)
        print(f"- {name} `{url}`: {status if status else 'ingen kontakt'} {body[:120]}")
    print()

    for s in services:
        problem = s.get("State") != "running" or s.get("Health") == "unhealthy"
        lines = "80" if problem else "20"
        result = run(["docker", "compose", "logs", "--no-color", "--tail", lines,
                      s.get("Service")], cwd=root)
        log = (result.stdout + result.stderr).strip()
        if problem or re.search(r"Traceback|ERROR|error|FATAL|emerg", log):
            print(f"## Loggar: {s.get('Service')} (senaste {lines} rader)\n")
            print("```\n" + log + "\n```\n")
    return 0


COMMANDS = {
    "env": cmd_env,
    "ports": cmd_ports,
    "urls": cmd_urls,
    "wait": cmd_wait,
    "network": cmd_network,
    "test": cmd_test,
    "build-frontend": cmd_build_frontend,
    "diagnose": cmd_diagnose,
}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    root = find_root()
    return COMMANDS[argv[0]](root, argv[1:]) or 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
