#!/usr/bin/env python3
"""GT Setup Script — cross-platform (macOS, Linux, Windows)

Usage:
    python setup.py          # Full setup: deps + database + seed data
    python setup.py --seed   # Re-seed database only (resets all data)
    python setup.py --check  # Check prerequisites only
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
if os.name == "nt":
    os.system("")  # enable ANSI on Windows


def info(msg: str) -> None:
    print(f"{CYAN}→{RESET} {msg}")


def ok(msg: str) -> None:
    print(f"{GREEN}✓{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{YELLOW}!{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}✗{RESET} {msg}")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def find_python() -> str:
    for name in ["python3", "python"]:
        path = shutil.which(name)
        if path:
            result = run([path, "--version"], check=False)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                major, minor = map(int, version.split(".")[:2])
                if major >= 3 and minor >= 12:
                    return path
    return ""


def find_node() -> str:
    path = shutil.which("node")
    if path:
        result = run([path, "--version"], check=False)
        if result.returncode == 0:
            version = result.stdout.strip().lstrip("v")
            major = int(version.split(".")[0])
            if major >= 18:
                return path
    return ""


def find_npm() -> str:
    return shutil.which("npm") or ""


def find_docker() -> str:
    path = shutil.which("docker")
    if path:
        result = run([path, "info"], check=False)
        if result.returncode == 0:
            return path
    return ""


def check_prerequisites() -> dict[str, str]:
    info("Checking prerequisites...")
    tools = {}

    py = find_python()
    if py:
        ver = run([py, "--version"]).stdout.strip()
        ok(f"Python: {ver} ({py})")
        tools["python"] = py
    else:
        fail("Python 3.12+ not found — install from https://python.org")

    node = find_node()
    if node:
        ver = run([node, "--version"]).stdout.strip()
        ok(f"Node.js: {ver} ({node})")
        tools["node"] = node
    else:
        fail("Node.js 18+ not found — install from https://nodejs.org")

    npm = find_npm()
    if npm:
        ver = run([npm, "--version"]).stdout.strip()
        ok(f"npm: {ver}")
        tools["npm"] = npm
    else:
        fail("npm not found")

    docker = find_docker()
    if docker:
        ok(f"Docker: running ({docker})")
        tools["docker"] = docker
    else:
        warn("Docker not running — you'll need PostgreSQL and Redis running manually")

    print()
    return tools


def setup_docker(docker: str) -> None:
    info("Starting Docker services (PostgreSQL, Redis, Mailpit)...")
    result = run(["docker", "compose", "up", "-d"], cwd=ROOT, check=False)
    if result.returncode != 0:
        warn("docker compose failed — trying 'docker-compose'...")
        result = run(["docker-compose", "up", "-d"], cwd=ROOT, check=False)
        if result.returncode != 0:
            fail("Could not start Docker services. Start PostgreSQL and Redis manually.")
            return

    info("Waiting for PostgreSQL to be ready...")
    for _ in range(30):
        check = run(
            ["docker", "exec", "duct-tape-postgres", "pg_isready", "-U", "duct_tape"],
            check=False,
        )
        if check.returncode == 0:
            break
        import time
        time.sleep(1)
    else:
        warn("PostgreSQL may not be ready yet — continuing anyway")

    ok("Docker services running")


def setup_backend(python: str) -> None:
    info("Installing backend dependencies...")
    run([python, "-m", "pip", "install", "-e", ".[dev]"], cwd=BACKEND)
    ok("Backend dependencies installed")

    env_file = BACKEND / ".env"
    if not env_file.exists():
        info("Creating .env from .env.example...")
        shutil.copy(BACKEND / ".env.example", env_file)
        ok(".env created")
    else:
        ok(".env already exists")


def setup_frontend(npm: str) -> None:
    info("Installing frontend dependencies...")
    run([npm, "install"], cwd=FRONTEND)
    ok("Frontend dependencies installed")


def seed_database(python: str) -> None:
    info("Seeding database with demo data...")
    result = run([python, "seed.py"], cwd=BACKEND, check=False)
    if result.returncode != 0:
        fail("Seed failed:")
        print(result.stderr)
        return
    print(result.stdout)
    ok("Database seeded")


def create_test_db(docker: str) -> None:
    info("Creating test database...")
    result = run(
        ["docker", "exec", "duct-tape-postgres", "psql", "-U", "duct_tape", "-c",
         "CREATE DATABASE duct_tape_test OWNER duct_tape;"],
        check=False,
    )
    if result.returncode == 0:
        ok("Test database created")
    elif "already exists" in (result.stderr or ""):
        ok("Test database already exists")
    else:
        warn("Could not create test database — tests may fail")


def print_next_steps() -> None:
    print()
    print(f"{CYAN}{'=' * 50}{RESET}")
    print(f"{GREEN}Setup complete!{RESET}")
    print(f"{CYAN}{'=' * 50}{RESET}")
    print()
    print("Start the app:")
    print()
    if os.name == "nt":
        print(f"  {YELLOW}# Terminal 1 — Backend{RESET}")
        print(f"  cd backend && python -m uvicorn app.main:app --reload --port 8000")
        print()
        print(f"  {YELLOW}# Terminal 2 — Frontend{RESET}")
        print(f"  cd frontend && npm run dev")
    else:
        print(f"  {YELLOW}# Terminal 1 — Backend{RESET}")
        print(f"  cd backend && uvicorn app.main:app --reload --port 8000")
        print()
        print(f"  {YELLOW}# Terminal 2 — Frontend{RESET}")
        print(f"  cd frontend && npm run dev")
    print()
    print(f"Open {CYAN}http://localhost:5173{RESET}")
    print()
    print("Demo accounts:")
    print(f"  Admin:  {GREEN}admin@gt.dev{RESET} / admin123")
    print(f"  Crew:   {GREEN}kenji@gt.dev{RESET} / crew123")
    print()
    print(f"Reseed anytime:  {YELLOW}cd backend && python3 seed.py{RESET}")
    print(f"API docs:        {CYAN}http://localhost:8000/api/docs{RESET}")
    print(f"Email inbox:     {CYAN}http://localhost:8025{RESET} (Mailpit)")
    print()


def main() -> None:
    print()
    print(f"{CYAN}GT — Crew Management Setup{RESET}")
    print()

    args = sys.argv[1:]

    tools = check_prerequisites()

    if "--check" in args:
        return

    if not tools.get("python"):
        fail("Cannot continue without Python 3.12+")
        sys.exit(1)

    if "--seed" in args:
        seed_database(tools["python"])
        return

    if not tools.get("npm"):
        fail("Cannot continue without Node.js/npm")
        sys.exit(1)

    if tools.get("docker"):
        setup_docker(tools["docker"])
        create_test_db(tools["docker"])

    setup_backend(tools["python"])
    setup_frontend(tools["npm"])
    seed_database(tools["python"])
    print_next_steps()


if __name__ == "__main__":
    main()
