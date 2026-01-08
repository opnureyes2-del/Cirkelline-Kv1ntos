#!/usr/bin/env python3
"""
CIRKELLINE SYSTEM KOORDINATOR v2.0.0
====================================
Central enhed der starter, overvåger og hjælper med hele Cirkelline økosystemet.

Brug:
    python system-koordinator.py start     # Start alle services
    python system-koordinator.py stop      # Stop alle services
    python system-koordinator.py status    # Vis status
    python system-koordinator.py test      # Kør tests
    python system-koordinator.py doctor    # Diagnosticer problemer
    python system-koordinator.py logs      # Vis aggregerede logs
    python system-koordinator.py env       # Valider environment
    python system-koordinator.py migrate   # Kør database migrations
    python system-koordinator.py help      # Vis hjælp

Forfatter: Claude Code / Rasmus
Version: 2.0.0
Updated: 2025-12-13 (FASE 0 Enhancement)
"""

import os
import sys
import subprocess
import socket
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# ============================================================================
# KONFIGURATION
# ============================================================================

PROJECTS_ROOT = Path("/home/rasmus/Desktop/projects")
VERSION = "2.0.0"


@dataclass
class ServiceConfig:
    """Konfiguration for en service"""
    name: str
    path: Path
    port: int
    start_cmd: List[str]
    health_endpoint: str = ""
    env_path: Optional[Path] = None
    docker_container: Optional[str] = None
    is_frontend: bool = False
    depends_on: List[str] = field(default_factory=list)
    tier: int = 1  # 1=Core, 2=Backend, 3=Frontend, 4=Support
    required: bool = True
    description: str = ""


# Complete service definitions - all 11 services
SERVICES: Dict[str, ServiceConfig] = {
    # =========================================================================
    # Tier 1: Core Infrastructure
    # =========================================================================
    "cirkelline-postgres": ServiceConfig(
        name="cirkelline-postgres",
        path=PROJECTS_ROOT / "cirkelline-system",
        port=5532,
        start_cmd=["docker", "start", "cirkelline-postgres"],
        docker_container="cirkelline-postgres",
        tier=1,
        description="PostgreSQL 17 database med pgvector"
    ),
    "redis": ServiceConfig(
        name="redis",
        path=PROJECTS_ROOT / "cirkelline-system",
        port=6380,
        start_cmd=["docker", "start", "cirkelline-redis"],
        docker_container="cirkelline-redis",
        tier=1,
        required=False,
        description="Redis cache (optional)"
    ),

    # =========================================================================
    # Tier 2: Backend Services
    # =========================================================================
    "cirkelline-backend": ServiceConfig(
        name="cirkelline-backend",
        path=PROJECTS_ROOT / "cirkelline-system",
        port=7777,
        start_cmd=["python", "my_os.py"],
        health_endpoint="http://localhost:7777/health",
        env_path=PROJECTS_ROOT / "cirkelline-env",
        depends_on=["cirkelline-postgres"],
        tier=2,
        description="Hovedplatform - AgentOS og API"
    ),
    "lib-admin-backend": ServiceConfig(
        name="lib-admin-backend",
        path=PROJECTS_ROOT / "lib-admin-main" / "backend",
        port=7779,
        start_cmd=["python", "main.py"],
        health_endpoint="http://localhost:7779/health",
        env_path=PROJECTS_ROOT / "lib-admin-main" / "backend" / "venv",
        depends_on=["cirkelline-postgres"],
        tier=2,
        description="CKC Admin HUB - HASA agenter"
    ),
    "cosmic-library": ServiceConfig(
        name="cosmic-library",
        path=PROJECTS_ROOT / "Cosmic-Library-main" / "backend",
        port=7778,
        start_cmd=["python", "main.py"],
        health_endpoint="http://localhost:7778/health",
        env_path=PROJECTS_ROOT / "Cosmic-Library-main" / "backend" / "venv",
        depends_on=["cirkelline-postgres"],
        tier=2,
        required=False,
        description="Training Academy - Knowledge Orchestrator"
    ),
    "commando-center": ServiceConfig(
        name="commando-center",
        path=PROJECTS_ROOT / "Commando-Center-main",
        port=8000,
        start_cmd=["python", "-m", "uvicorn", "main:app", "--port", "8000"],
        health_endpoint="http://localhost:8000/health",
        env_path=PROJECTS_ROOT / "Commando-Center-main" / "venv",
        depends_on=["cirkelline-backend"],
        tier=2,
        required=False,
        description="Meta-cognition og task execution"
    ),

    # =========================================================================
    # Tier 3: Frontend Services
    # =========================================================================
    "cirkelline-frontend": ServiceConfig(
        name="cirkelline-frontend",
        path=PROJECTS_ROOT / "cirkelline-system" / "cirkelline-ui",
        port=3000,
        start_cmd=["pnpm", "dev"],
        health_endpoint="http://localhost:3000",
        is_frontend=True,
        depends_on=["cirkelline-backend"],
        tier=3,
        description="Cirkelline Chat UI"
    ),
    "lib-admin-frontend": ServiceConfig(
        name="lib-admin-frontend",
        path=PROJECTS_ROOT / "lib-admin-main" / "frontend",
        port=3002,
        start_cmd=["pnpm", "dev"],
        health_endpoint="http://localhost:3002",
        is_frontend=True,
        depends_on=["lib-admin-backend"],
        tier=3,
        required=False,
        description="CKC Admin Dashboard UI"
    ),
    "consulting-frontend": ServiceConfig(
        name="consulting-frontend",
        path=PROJECTS_ROOT / "Cirkelline-Consulting-main" / "frontend",
        port=3001,
        start_cmd=["pnpm", "dev"],
        health_endpoint="http://localhost:3001",
        is_frontend=True,
        depends_on=["cirkelline-backend"],
        tier=3,
        required=False,
        description="Cirkelline Consulting website"
    ),

    # =========================================================================
    # Tier 4: Support Services
    # =========================================================================
    "ollama": ServiceConfig(
        name="ollama",
        path=Path("/usr/local"),
        port=11434,
        start_cmd=["ollama", "serve"],
        health_endpoint="http://localhost:11434/api/tags",
        tier=4,
        required=False,
        description="Local LLM inference (optional)"
    ),
    "chromadb": ServiceConfig(
        name="chromadb",
        path=PROJECTS_ROOT / "cirkelline-system",
        port=8001,
        start_cmd=["docker", "start", "chromadb"],
        docker_container="chromadb",
        tier=4,
        required=False,
        description="Vector database (optional)"
    ),
}

# Required environment variables per service
REQUIRED_ENV_VARS = {
    "cirkelline-backend": [
        "GOOGLE_API_KEY",
        "DATABASE_URL",
        "JWT_SECRET_KEY",
    ],
    "lib-admin-backend": [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
    ],
    "cosmic-library": [
        "DATABASE_URL",
    ],
}


class Status(Enum):
    RUNNING = "🟢"
    STOPPED = "🔴"
    STARTING = "🟡"
    ERROR = "❌"
    UNKNOWN = "⚪"
    OPTIONAL = "⚫"


# ============================================================================
# HJÆLPEFUNKTIONER
# ============================================================================

def print_banner():
    """Vis velkomstbanner"""
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║          CIRKELLINE SYSTEM KOORDINATOR v{VERSION}                    ║
║                                                                   ║
║  "Alt virker automatisk - spørg hvis du har brug for hjælp"      ║
╚═══════════════════════════════════════════════════════════════════╝
    """)


def check_port(port: int) -> bool:
    """Check om en port er i brug"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0


def check_docker_container(container_name: str) -> bool:
    """Check om en Docker container kører"""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "true"
    except Exception:
        return False


def check_health_endpoint(url: str, timeout: int = 5) -> Tuple[bool, Optional[dict]]:
    """Check om en health endpoint svarer og returner data"""
    try:
        import urllib.request
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                try:
                    data = json.loads(response.read().decode())
                    return True, data
                except Exception:
                    return True, None
            return False, None
    except Exception:
        return False, None


def get_service_status(service: ServiceConfig) -> Tuple[Status, Optional[dict]]:
    """Hent status for en service med health data"""
    if service.docker_container:
        if check_docker_container(service.docker_container):
            return Status.RUNNING, {"container": service.docker_container}
        if not service.required:
            return Status.OPTIONAL, None
        return Status.STOPPED, None

    if check_port(service.port):
        if service.health_endpoint:
            healthy, data = check_health_endpoint(service.health_endpoint)
            if healthy:
                return Status.RUNNING, data
            return Status.ERROR, {"error": "Health check failed"}
        return Status.RUNNING, None

    if not service.required:
        return Status.OPTIONAL, None
    return Status.STOPPED, None


def get_env_file(service_name: str) -> Optional[Path]:
    """Find .env fil for en service"""
    service = SERVICES.get(service_name)
    if not service:
        return None

    env_locations = [
        service.path / ".env",
        service.path / ".env.local",
        service.path.parent / ".env",
    ]

    for loc in env_locations:
        if loc.exists():
            return loc
    return None


def load_env_file(env_path: Path) -> Dict[str, str]:
    """Læs environment variables fra .env fil"""
    env_vars = {}
    if env_path and env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars


# ============================================================================
# KOMMANDOER
# ============================================================================

def cmd_status():
    """Vis status for alle services"""
    print("\n📊 SYSTEM STATUS\n")
    print("-" * 70)
    print(f"  {'Service':<25} {'Port':<8} {'Status':<10} {'Info'}")
    print("-" * 70)

    tier_names = {1: "Core Infrastructure", 2: "Backend Services", 3: "Frontend Services", 4: "Support Services"}
    current_tier = 0

    running_count = 0
    total_required = 0

    for name, service in sorted(SERVICES.items(), key=lambda x: (x[1].tier, x[0])):
        if service.tier != current_tier:
            current_tier = service.tier
            print(f"\n  --- {tier_names[current_tier]} ---")

        status, data = get_service_status(service)
        port_info = f":{service.port}" if service.port else ""

        info = ""
        if status == Status.RUNNING:
            running_count += 1
            if data and isinstance(data, dict):
                if "version" in data:
                    info = f"v{data['version']}"
                elif "status" in data:
                    info = data["status"]
        elif status == Status.OPTIONAL:
            info = "(optional)"
        elif status == Status.ERROR:
            info = "Health check failed!"

        if service.required:
            total_required += 1

        print(f"  {status.value} {service.name:<23} {port_info:<8} {info}")

    print("-" * 70)
    print(f"\n  Kørende: {running_count}/{total_required} (påkrævede services)")

    all_required_running = all(
        get_service_status(s)[0] == Status.RUNNING
        for s in SERVICES.values() if s.required
    )
    if all_required_running:
        print("\n✅ Alle påkrævede services kører!")
    else:
        print("\n⚠️  Nogle services er ikke klar. Kør 'python system-koordinator.py start'")


def cmd_start():
    """Start alle services i korrekt rækkefølge"""
    print("\n🚀 STARTER CIRKELLINE SYSTEM\n")

    started = []
    failed = []
    skipped = []

    # Sort by tier to start dependencies first
    sorted_services = sorted(SERVICES.items(), key=lambda x: x[1].tier)

    for name, service in sorted_services:
        status, _ = get_service_status(service)

        if status == Status.RUNNING:
            print(f"  ✓ {service.name} kører allerede")
            started.append(name)
            continue

        if not service.required and status == Status.OPTIONAL:
            print(f"  ○ {service.name} (optional - springer over)")
            skipped.append(name)
            continue

        # Check dependencies
        deps_ok = True
        for dep in service.depends_on:
            dep_status, _ = get_service_status(SERVICES[dep])
            if dep_status != Status.RUNNING:
                deps_ok = False
                print(f"  ⚠️  {service.name} afventer {dep}")
                break

        if not deps_ok:
            failed.append(name)
            continue

        print(f"  → Starter {service.name}...", end=" ", flush=True)

        try:
            if service.docker_container:
                # Check if container exists
                check_result = subprocess.run(
                    ["docker", "ps", "-a", "--filter", f"name={service.docker_container}", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True
                )
                if service.docker_container not in check_result.stdout:
                    print("CONTAINER IKKE FUNDET")
                    if service.required:
                        failed.append(name)
                    else:
                        skipped.append(name)
                    continue

                subprocess.run(
                    service.start_cmd,
                    capture_output=True,
                    check=True
                )
                time.sleep(2)
            else:
                # Start backend/frontend i baggrunden
                env = os.environ.copy()
                if service.env_path and service.env_path.exists():
                    env["VIRTUAL_ENV"] = str(service.env_path)
                    env["PATH"] = f"{service.env_path}/bin:" + env["PATH"]

                # Load .env file if exists
                env_file = get_env_file(name)
                if env_file:
                    env_vars = load_env_file(env_file)
                    env.update(env_vars)

                subprocess.Popen(
                    service.start_cmd,
                    cwd=service.path,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                time.sleep(3 if not service.is_frontend else 5)

            # Verificer at service kører
            new_status, _ = get_service_status(service)
            if new_status == Status.RUNNING:
                print("OK")
                started.append(name)
            else:
                print("FEJL")
                failed.append(name)

        except subprocess.CalledProcessError as e:
            print(f"FEJL: {e}")
            failed.append(name)
        except FileNotFoundError:
            print("KOMMANDO IKKE FUNDET")
            if service.required:
                failed.append(name)
            else:
                skipped.append(name)
        except Exception as e:
            print(f"FEJL: {e}")
            failed.append(name)

    print("\n" + "=" * 60)
    print(f"  Startet: {len(started)}")
    print(f"  Skippet: {len(skipped)}")
    if failed:
        print(f"  Fejlet: {', '.join(failed)}")
    print("=" * 60)

    if not failed or all(f in [s for s, cfg in SERVICES.items() if not cfg.required] for f in failed):
        print("\n✅ System klar! Åbn http://localhost:3000 i browseren.")
        print("   Brug 'python system-koordinator.py help' for vejledning.\n")


def cmd_stop():
    """Stop alle services"""
    print("\n🛑 STOPPER CIRKELLINE SYSTEM\n")

    # Stop in reverse tier order (frontends first, then backends, then core)
    sorted_services = sorted(SERVICES.items(), key=lambda x: -x[1].tier)

    for name, service in sorted_services:
        status, _ = get_service_status(service)

        if status in [Status.STOPPED, Status.OPTIONAL]:
            print(f"  ✓ {service.name} er allerede stoppet")
            continue

        print(f"  → Stopper {service.name}...", end=" ", flush=True)

        try:
            if service.docker_container:
                subprocess.run(
                    ["docker", "stop", service.docker_container],
                    capture_output=True
                )
            else:
                # Find og stop processen baseret på port
                subprocess.run(
                    ["fuser", "-k", f"{service.port}/tcp"],
                    capture_output=True,
                    stderr=subprocess.DEVNULL
                )
            print("OK")
        except Exception as e:
            print(f"FEJL: {e}")

    print("\n✅ System stoppet.\n")


def cmd_env():
    """Valider environment variables"""
    print("\n🔐 ENVIRONMENT VALIDERING\n")
    print("-" * 60)

    issues = []

    for service_name, required_vars in REQUIRED_ENV_VARS.items():
        service = SERVICES.get(service_name)
        if not service:
            continue

        print(f"\n  📁 {service_name}:")

        env_file = get_env_file(service_name)
        if env_file:
            env_vars = load_env_file(env_file)
            print(f"     Fil: {env_file}")

            for var in required_vars:
                if var in env_vars:
                    value = env_vars[var]
                    masked = value[:10] + "..." if len(value) > 13 else value
                    print(f"     ✓ {var}: {masked}")
                elif var in os.environ:
                    print(f"     ✓ {var}: (fra system env)")
                else:
                    print(f"     ✗ {var}: MANGLER!")
                    issues.append(f"{service_name}: {var} mangler")
        else:
            print(f"     ⚠️  Ingen .env fil fundet")
            issues.append(f"{service_name}: .env fil mangler")

    print("\n" + "-" * 60)
    if issues:
        print("\n❌ PROBLEMER FUNDET:\n")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✅ Alle påkrævede environment variables er sat!")


def cmd_migrate():
    """Kør database migrations"""
    print("\n🔄 DATABASE MIGRATIONS\n")

    # Check if database is running
    db_status, _ = get_service_status(SERVICES["cirkelline-postgres"])
    if db_status != Status.RUNNING:
        print("❌ Database kører ikke. Start den først med: python system-koordinator.py start")
        return

    migrations_found = False

    # Check cirkelline-system migrations
    alembic_dir = PROJECTS_ROOT / "cirkelline-system" / "migrations"
    if alembic_dir.exists():
        print("  📁 cirkelline-system migrations:")
        migrations_found = True

        # Check alembic
        alembic_ini = PROJECTS_ROOT / "cirkelline-system" / "alembic.ini"
        if alembic_ini.exists():
            result = subprocess.run(
                ["bash", "-c", f"""
                    cd {PROJECTS_ROOT / 'cirkelline-system'} &&
                    source {PROJECTS_ROOT / 'cirkelline-env'}/bin/activate &&
                    alembic current 2>&1
                """],
                capture_output=True,
                text=True
            )
            print(f"     Current: {result.stdout.strip()}")

            print("     Kører migrations...", end=" ")
            result = subprocess.run(
                ["bash", "-c", f"""
                    cd {PROJECTS_ROOT / 'cirkelline-system'} &&
                    source {PROJECTS_ROOT / 'cirkelline-env'}/bin/activate &&
                    alembic upgrade head 2>&1
                """],
                capture_output=True,
                text=True
            )
            if "FAILED" in result.stdout or result.returncode != 0:
                print("FEJL")
                print(f"     {result.stdout}")
            else:
                print("OK")
        else:
            print("     ⚠️  alembic.ini ikke fundet")

    # Check lib-admin migrations
    lib_admin_alembic = PROJECTS_ROOT / "lib-admin-main" / "backend" / "alembic.ini"
    if lib_admin_alembic.exists():
        print("\n  📁 lib-admin migrations:")
        migrations_found = True

        result = subprocess.run(
            ["bash", "-c", f"""
                cd {PROJECTS_ROOT / 'lib-admin-main' / 'backend'} &&
                source venv/bin/activate &&
                alembic current 2>&1
            """],
            capture_output=True,
            text=True
        )
        print(f"     Current: {result.stdout.strip()}")

    if not migrations_found:
        print("  ⚠️  Ingen Alembic migrations fundet")

    print("\n✅ Migration check komplet.\n")


def cmd_logs():
    """Vis aggregerede logs"""
    print("\n📋 SYSTEM LOGS\n")
    print("-" * 60)

    # Docker logs
    for name, service in SERVICES.items():
        if service.docker_container:
            status, _ = get_service_status(service)
            if status == Status.RUNNING:
                print(f"\n  === {service.name} (Docker) ===")
                result = subprocess.run(
                    ["docker", "logs", "--tail", "10", service.docker_container],
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    for line in result.stdout.strip().split("\n")[-10:]:
                        print(f"    {line[:80]}")
                if result.stderr:
                    for line in result.stderr.strip().split("\n")[-5:]:
                        print(f"    [ERR] {line[:70]}")

    # Check for log files
    log_locations = [
        PROJECTS_ROOT / "cirkelline-system" / "logs",
        PROJECTS_ROOT / "lib-admin-main" / "backend" / "logs",
    ]

    for log_dir in log_locations:
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                print(f"\n  === Log filer i {log_dir.name}/ ===")
                for log_file in log_files[-3:]:  # Last 3 log files
                    print(f"    • {log_file.name}")

    print("\n" + "-" * 60)
    print("Tip: Brug 'docker logs -f cirkelline-postgres' for live logs")


def cmd_test():
    """Kør tests for alle services"""
    print("\n🧪 KØRER TESTS\n")

    # lib-admin tests
    print("📁 lib-admin backend tests...")
    result = subprocess.run(
        ["bash", "-c", """
            cd /home/rasmus/Desktop/projects/lib-admin-main/backend &&
            source venv/bin/activate &&
            TESTING=true ENVIRONMENT=testing python -m pytest tests/ -v --tb=short -q 2>&1 | tail -30
        """],
        capture_output=True,
        text=True
    )
    print(result.stdout)

    if "passed" in result.stdout:
        # Extract count
        import re
        match = re.search(r"(\d+) passed", result.stdout)
        if match:
            print(f"✅ lib-admin tests OK! ({match.group(1)} tests)\n")
    else:
        print("❌ lib-admin tests fejlede\n")

    # cirkelline-system tests
    cirkelline_tests = PROJECTS_ROOT / "cirkelline-system" / "tests"
    if cirkelline_tests.exists():
        print("📁 cirkelline-system tests...")
        result = subprocess.run(
            ["bash", "-c", f"""
                cd {PROJECTS_ROOT / 'cirkelline-system'} &&
                source {PROJECTS_ROOT / 'cirkelline-env'}/bin/activate &&
                python -m pytest tests/ -v --tb=short -q 2>&1 | tail -20
            """],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if "passed" in result.stdout:
            print("✅ cirkelline-system tests OK!\n")


def cmd_doctor():
    """Diagnosticer og fiks problemer"""
    print("\n🔍 SYSTEM DIAGNOSTIK\n")

    issues = []
    fixes = []

    # Check Docker
    print("Checker Docker...", end=" ")
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True
        )
        if result.returncode == 0:
            print("OK")
        else:
            print("FEJL")
            issues.append("Docker daemon kører ikke")
            fixes.append("sudo systemctl start docker")
    except FileNotFoundError:
        print("MANGLER")
        issues.append("Docker er ikke installeret")

    # Check Python environments
    print("Checker Python environments...", end=" ")
    envs_ok = True
    for name, service in SERVICES.items():
        if service.env_path and not service.docker_container:
            python_path = service.env_path / "bin" / "python"
            if not python_path.exists():
                envs_ok = False
                issues.append(f"Python environment mangler: {service.env_path}")
                fixes.append(f"python3 -m venv {service.env_path}")
    print("OK" if envs_ok else "FEJL")

    # Check Node/pnpm
    print("Checker Node.js/pnpm...", end=" ")
    try:
        subprocess.run(["pnpm", "--version"], capture_output=True, check=True)
        print("OK")
    except Exception:
        print("FEJL")
        issues.append("pnpm ikke installeret")
        fixes.append("npm install -g pnpm")

    # Check porte
    print("Checker porte...", end=" ")
    blocked_ports = []
    for service in SERVICES.values():
        if service.port and check_port(service.port):
            status, _ = get_service_status(service)
            if status not in [Status.RUNNING, Status.OPTIONAL]:
                blocked_ports.append(service.port)
    if blocked_ports:
        print("KONFLIKT")
        issues.append(f"Porte i brug af andre processer: {blocked_ports}")
        for port in blocked_ports:
            fixes.append(f"fuser -k {port}/tcp")
    else:
        print("OK")

    # Check database connection
    print("Checker database forbindelse...", end=" ")
    db_status, _ = get_service_status(SERVICES["cirkelline-postgres"])
    if db_status == Status.RUNNING:
        result = subprocess.run(
            ["docker", "exec", "cirkelline-postgres", "psql", "-U", "cirkelline", "-c", "SELECT 1;"],
            capture_output=True
        )
        if result.returncode == 0:
            print("OK")
        else:
            print("FEJL")
            issues.append("Database forbindelse fejler")
    else:
        print("IKKE STARTET")
        issues.append("PostgreSQL container kører ikke")
        fixes.append("docker start cirkelline-postgres")

    # Check environment variables
    print("Checker environment variables...", end=" ")
    env_ok = True
    for service_name, required_vars in REQUIRED_ENV_VARS.items():
        env_file = get_env_file(service_name)
        if env_file:
            env_vars = load_env_file(env_file)
            for var in required_vars:
                if var not in env_vars and var not in os.environ:
                    env_ok = False
                    issues.append(f"{service_name}: {var} mangler")
    print("OK" if env_ok else "FEJL")

    # Opsummering
    print("\n" + "=" * 60)
    if issues:
        print("❌ PROBLEMER FUNDET:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")

        if fixes:
            print("\n🔧 FORESLÅEDE FIXES:\n")
            for fix in fixes:
                print(f"  $ {fix}")

            print("\n  Vil du køre disse fixes automatisk? (Kør manuelt for nu)")
    else:
        print("✅ Ingen problemer fundet!")
    print("=" * 60 + "\n")


def cmd_help():
    """Vis hjælp og brugervejledning"""
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    CIRKELLINE BRUGERVEJLEDNING                    ║
║                         Version {VERSION}                            ║
╚═══════════════════════════════════════════════════════════════════╝

🚀 HURTIG START
───────────────
  python system-koordinator.py start     # Start alt
  Åbn http://localhost:3000              # Chat med Cirkelline

📊 KOMMANDOER
─────────────
  start   - Start alle services (database, backend, frontend)
  stop    - Stop alle services
  status  - Vis hvad der kører (med health checks)
  test    - Kør automatiske tests
  doctor  - Find og diagnoticer problemer
  env     - Valider environment variables
  migrate - Kør database migrations
  logs    - Vis aggregerede logs
  help    - Denne vejledning

🔗 SERVICES (11 total)
──────────────────────
  Tier 1 - Core Infrastructure:
    :5532  PostgreSQL database
    :6380  Redis cache (optional)

  Tier 2 - Backend Services:
    :7777  Cirkelline Backend (hovedplatform)
    :7779  lib-admin Backend (CKC Admin)
    :7778  Cosmic Library (optional)
    :8000  Commando Center (optional)

  Tier 3 - Frontend Services:
    :3000  Cirkelline Chat UI
    :3002  Admin Dashboard (optional)
    :3001  Consulting website (optional)

  Tier 4 - Support Services:
    :11434 Ollama (optional)
    :8001  ChromaDB (optional)

💬 CHAT EKSEMPLER
─────────────────
  "Hej Cirkelline!"                     - Start en samtale
  "Søg efter AI nyheder"                - Quick search
  "Lav en dybdegående undersøgelse..."  - Deep research mode
  "Hvad ved du om mig?"                 - Se dine memories

📚 DOKUMENTATION
────────────────
  BASELINE-2025-12-12.md   - System status
  ROADMAP-2025-12-12.md    - Udviklingsplan
  CLAUDE.md                - AI assistent guide
  docs/                    - Detaljeret dokumentation

❓ BRUG FOR HJÆLP?
──────────────────
  1. Kør: python system-koordinator.py doctor
  2. Check logs: python system-koordinator.py logs
  3. Valider env: python system-koordinator.py env
  4. Kontakt: opnureyes2@gmail.com (Ivo) / opnureyes2@gmail.com (Rasmus)

""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Hovedfunktion"""
    print_banner()

    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower()

    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "test": cmd_test,
        "doctor": cmd_doctor,
        "env": cmd_env,
        "migrate": cmd_migrate,
        "logs": cmd_logs,
        "help": cmd_help,
        "--help": cmd_help,
        "-h": cmd_help,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Ukendt kommando: {command}")
        print("   Brug: python system-koordinator.py help")


if __name__ == "__main__":
    main()
