#!/usr/bin/env python3
"""
CIRKELLINE MORNING SYNC ROUTINE
===============================
Kører dagligt kl. 09:00

5-Step Morning Sync:
1. Check sorting rapport fra natten
2. Verificer system health
3. Saml metrics oversigt
4. Opdater sync status
5. Generer morning rapport

Brug:
    python scripts/morning_sync_0900.py [--dry-run] [--verbose]

Cron:
    0 9 * * * /path/to/python /path/to/scripts/morning_sync_0900.py >> /var/log/ckc/morning_sync.log 2>&1
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# ==============================================================================
# KONFIGURATION
# ==============================================================================

# Paths
CKC_DIR = Path.home() / ".ckc"
SORTING_REPORTS_DIR = CKC_DIR
MORNING_REPORTS_DIR = CKC_DIR / "morning-reports"
LOG_DIR = Path("/var/log/ckc")
PROJECT_ROOT = Path(__file__).parent.parent

# Health check
BACKEND_URL = "http://localhost:7777"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
CONFIG_ENDPOINT = f"{BACKEND_URL}/config"

# Thresholds
MEMORY_WARNING_MB = 1024  # 1GB
DISK_WARNING_PERCENT = 80

# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class StepResult:
    """Resultat af et enkelt step."""
    step_name: str
    success: bool
    duration_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MorningSyncReport:
    """Komplet morning sync rapport."""
    timestamp: str
    date: str
    steps_completed: int
    total_steps: int
    success: bool
    duration_seconds: float
    sorting_report_found: bool
    system_healthy: bool
    warnings: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

class Colors:
    """ANSI farve koder."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print formatted header."""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}\n")


def print_step(step_num: int, total: int, name: str) -> None:
    """Print step header."""
    print(f"{Colors.BLUE}[{step_num}/{total}] {name}{Colors.ENDC}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"  {Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"  {Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"  {Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"  {Colors.CYAN}→ {text}{Colors.ENDC}")


# ==============================================================================
# STEP 1: CHECK SORTING RAPPORT
# ==============================================================================

async def step_check_sorting_report(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 1: Check sorting rapport fra natten.

    Finder og analyserer sorting rapport fra 03:33.
    """
    start = datetime.now()
    step_name = "Check Sorting Report"
    details = {}
    warnings = []

    try:
        # Find dagens sorting rapport
        today = datetime.now().strftime("%Y-%m-%d")
        report_path = SORTING_REPORTS_DIR / f"sorting-report-{today}.json"

        if verbose:
            print_info(f"Looking for: {report_path}")

        if report_path.exists():
            with open(report_path, 'r') as f:
                sorting_data = json.load(f)

            details['report_found'] = True
            details['report_path'] = str(report_path)
            details['sorting_success'] = sorting_data.get('success', False)
            details['sorting_steps'] = sorting_data.get('steps_completed', 0)
            details['sorting_duration'] = sorting_data.get('duration_seconds', 0)

            if not sorting_data.get('success', False):
                warnings.append("Sorting rapport viser fejl")

            if verbose:
                print_info(f"Steps: {details['sorting_steps']}/5")
                print_info(f"Duration: {details['sorting_duration']:.2f}s")

            message = f"Sorting rapport fundet: {details['sorting_steps']}/5 steps, {'SUCCESS' if details['sorting_success'] else 'FAILED'}"
        else:
            details['report_found'] = False
            details['report_path'] = str(report_path)
            warnings.append(f"Ingen sorting rapport fundet for {today}")
            message = f"Ingen sorting rapport for {today}"

            if verbose:
                print_warning(message)

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=message,
            details={**details, 'warnings': warnings}
        )

    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StepResult(
            step_name=step_name,
            success=False,
            duration_ms=duration,
            message=f"Fejl: {str(e)}",
            details={'error': str(e)}
        )


# ==============================================================================
# STEP 2: VERIFICER SYSTEM HEALTH
# ==============================================================================

async def step_verify_health(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 2: Verificer system health.

    Checker backend health endpoint og system resources.
    """
    start = datetime.now()
    step_name = "Verify System Health"
    details = {}
    warnings = []

    try:
        # Check backend health
        backend_healthy = False
        try:
            if not dry_run:
                import urllib.request
                with urllib.request.urlopen(HEALTH_ENDPOINT, timeout=5) as response:
                    if response.status == 200:
                        backend_healthy = True
                        details['backend_status'] = 'healthy'
                        if verbose:
                            print_success("Backend: healthy")
            else:
                backend_healthy = True
                details['backend_status'] = 'dry-run (skipped)'
                if verbose:
                    print_info("Backend check: skipped (dry-run)")
        except Exception as e:
            details['backend_status'] = f'unreachable: {str(e)}'
            warnings.append("Backend ikke tilgængelig")
            if verbose:
                print_warning(f"Backend: {str(e)}")

        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            disk_percent = (used / total) * 100
            details['disk_usage_percent'] = round(disk_percent, 1)
            details['disk_free_gb'] = round(free / (1024**3), 1)

            if disk_percent > DISK_WARNING_PERCENT:
                warnings.append(f"Disk usage høj: {disk_percent:.1f}%")
                if verbose:
                    print_warning(f"Disk: {disk_percent:.1f}% brugt")
            else:
                if verbose:
                    print_success(f"Disk: {disk_percent:.1f}% brugt, {details['disk_free_gb']:.1f}GB fri")
        except Exception as e:
            details['disk_error'] = str(e)

        # Check memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            details['memory_used_percent'] = memory.percent
            details['memory_available_gb'] = round(memory.available / (1024**3), 1)

            if memory.percent > 80:
                warnings.append(f"Memory usage høj: {memory.percent}%")
                if verbose:
                    print_warning(f"Memory: {memory.percent}% brugt")
            else:
                if verbose:
                    print_success(f"Memory: {memory.percent}% brugt, {details['memory_available_gb']:.1f}GB fri")
        except ImportError:
            details['memory_status'] = 'psutil not installed'
            if verbose:
                print_info("Memory check: psutil not installed")
        except Exception as e:
            details['memory_error'] = str(e)

        # Check Docker containers
        try:
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}: {{.Status}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                containers = result.stdout.strip().split('\n')
                running = [c for c in containers if c and 'Up' in c]
                details['docker_containers'] = len(running)
                if verbose:
                    print_success(f"Docker: {len(running)} containers running")
            else:
                details['docker_status'] = 'error'
        except Exception as e:
            details['docker_error'] = str(e)
            if verbose:
                print_info(f"Docker check: {str(e)}")

        system_healthy = backend_healthy and len(warnings) == 0
        details['overall_healthy'] = system_healthy

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"System {'healthy' if system_healthy else 'has warnings'}: {len(warnings)} warnings",
            details={**details, 'warnings': warnings}
        )

    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StepResult(
            step_name=step_name,
            success=False,
            duration_ms=duration,
            message=f"Fejl: {str(e)}",
            details={'error': str(e)}
        )


# ==============================================================================
# STEP 3: SAML METRICS
# ==============================================================================

async def step_collect_metrics(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 3: Saml metrics oversigt.

    Samler system metrics og status information.
    """
    start = datetime.now()
    step_name = "Collect Metrics"
    details = {}

    try:
        # Git status
        try:
            result = subprocess.run(
                ['git', '-C', str(PROJECT_ROOT), 'status', '--short'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                changes = [l for l in result.stdout.strip().split('\n') if l]
                details['git_uncommitted'] = len(changes)
                if verbose:
                    print_info(f"Git: {len(changes)} uncommitted changes")
            else:
                details['git_status'] = 'error'
        except Exception as e:
            details['git_error'] = str(e)

        # Get latest commit
        try:
            result = subprocess.run(
                ['git', '-C', str(PROJECT_ROOT), 'log', '--oneline', '-1'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                details['latest_commit'] = result.stdout.strip()
                if verbose:
                    print_info(f"Latest: {details['latest_commit'][:50]}")
        except Exception as e:
            details['git_log_error'] = str(e)

        # Count test files
        try:
            test_dir = PROJECT_ROOT / 'tests'
            if test_dir.exists():
                test_files = list(test_dir.glob('test_*.py'))
                details['test_files'] = len(test_files)
                if verbose:
                    print_info(f"Test files: {len(test_files)}")
        except Exception as e:
            details['test_count_error'] = str(e)

        # Check SYNKRONISERING folder
        try:
            sync_dir = PROJECT_ROOT / 'my_admin_workspace' / 'SYNKRONISERING'
            if sync_dir.exists():
                sync_files = list(sync_dir.glob('*.md'))
                details['sync_docs'] = len(sync_files)
                if verbose:
                    print_info(f"Sync docs: {len(sync_files)}")
        except Exception as e:
            details['sync_error'] = str(e)

        # System uptime
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_hours = uptime_seconds / 3600
                details['system_uptime_hours'] = round(uptime_hours, 1)
                if verbose:
                    print_info(f"Uptime: {uptime_hours:.1f} hours")
        except Exception:
            pass

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Metrics collected: {len(details)} data points",
            details=details
        )

    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StepResult(
            step_name=step_name,
            success=False,
            duration_ms=duration,
            message=f"Fejl: {str(e)}",
            details={'error': str(e)}
        )


# ==============================================================================
# STEP 4: UPDATE SYNC STATUS
# ==============================================================================

async def step_update_sync_status(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 4: Opdater sync status.

    Logger morning sync til system.
    """
    start = datetime.now()
    step_name = "Update Sync Status"
    details = {}

    try:
        now = datetime.now()
        details['sync_time'] = now.strftime("%Y-%m-%d %H:%M")
        details['sync_date'] = now.strftime("%Y-%m-%d")

        # Ensure CKC dir exists
        if not dry_run:
            CKC_DIR.mkdir(exist_ok=True)

            # Update last sync file
            last_sync_file = CKC_DIR / "last_morning_sync.json"
            sync_data = {
                "timestamp": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M"),
                "success": True
            }
            with open(last_sync_file, 'w') as f:
                json.dump(sync_data, f, indent=2)

            details['sync_file'] = str(last_sync_file)
            if verbose:
                print_success(f"Sync status saved: {last_sync_file}")
        else:
            details['sync_file'] = 'dry-run (skipped)'
            if verbose:
                print_info("Sync status update: skipped (dry-run)")

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Sync status updated: {details['sync_time']}",
            details=details
        )

    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StepResult(
            step_name=step_name,
            success=False,
            duration_ms=duration,
            message=f"Fejl: {str(e)}",
            details={'error': str(e)}
        )


# ==============================================================================
# STEP 5: GENERER MORNING RAPPORT
# ==============================================================================

async def step_generate_report(
    all_results: List[StepResult],
    dry_run: bool = False,
    verbose: bool = False
) -> StepResult:
    """
    Step 5: Generer morning rapport.

    Samler alle resultater i en komplet rapport.
    """
    start = datetime.now()
    step_name = "Generate Morning Report"
    details = {}

    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # Collect all warnings
        all_warnings = []
        for result in all_results:
            if 'warnings' in result.details:
                all_warnings.extend(result.details['warnings'])

        # Collect metrics from step 3
        metrics = {}
        for result in all_results:
            if result.step_name == "Collect Metrics":
                metrics = result.details
                break

        # Check if sorting report was found
        sorting_found = False
        for result in all_results:
            if result.step_name == "Check Sorting Report":
                sorting_found = result.details.get('report_found', False)
                break

        # Check system health
        system_healthy = True
        for result in all_results:
            if result.step_name == "Verify System Health":
                system_healthy = result.details.get('overall_healthy', False)
                break

        # Build report
        report = MorningSyncReport(
            timestamp=now.isoformat(),
            date=today,
            steps_completed=sum(1 for r in all_results if r.success),
            total_steps=len(all_results) + 1,  # +1 for this step
            success=all(r.success for r in all_results),
            duration_seconds=sum(r.duration_ms for r in all_results) / 1000,
            sorting_report_found=sorting_found,
            system_healthy=system_healthy,
            warnings=all_warnings,
            steps=[{
                'name': r.step_name,
                'success': r.success,
                'duration_ms': r.duration_ms,
                'message': r.message
            } for r in all_results],
            metrics=metrics
        )

        # Save report
        if not dry_run:
            MORNING_REPORTS_DIR.mkdir(exist_ok=True)
            report_path = MORNING_REPORTS_DIR / f"morning-sync-{today}.json"

            with open(report_path, 'w') as f:
                json.dump({
                    'timestamp': report.timestamp,
                    'date': report.date,
                    'steps_completed': report.steps_completed,
                    'total_steps': report.total_steps,
                    'success': report.success,
                    'duration_seconds': report.duration_seconds,
                    'sorting_report_found': report.sorting_report_found,
                    'system_healthy': report.system_healthy,
                    'warnings': report.warnings,
                    'steps': report.steps,
                    'metrics': report.metrics
                }, f, indent=2)

            details['report_path'] = str(report_path)
            if verbose:
                print_success(f"Report saved: {report_path}")
        else:
            details['report_path'] = 'dry-run (skipped)'
            if verbose:
                print_info("Report save: skipped (dry-run)")

        details['total_warnings'] = len(all_warnings)
        details['all_steps_success'] = all(r.success for r in all_results)

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Morning report generated: {len(all_warnings)} warnings",
            details=details
        )

    except Exception as e:
        duration = (datetime.now() - start).total_seconds() * 1000
        return StepResult(
            step_name=step_name,
            success=False,
            duration_ms=duration,
            message=f"Fejl: {str(e)}",
            details={'error': str(e)}
        )


# ==============================================================================
# MAIN ROUTINE
# ==============================================================================

async def run_morning_sync(dry_run: bool = False, verbose: bool = False) -> MorningSyncReport:
    """
    Kør komplet morning sync routine.

    Args:
        dry_run: Hvis True, udfører ingen ændringer
        verbose: Hvis True, printer detaljeret output

    Returns:
        MorningSyncReport med alle resultater
    """
    start_time = datetime.now()

    print_header(f"CIRKELLINE MORNING SYNC - {start_time.strftime('%Y-%m-%d %H:%M')}")

    if dry_run:
        print(f"{Colors.YELLOW}DRY-RUN MODE - Ingen ændringer udføres{Colors.ENDC}\n")

    results: List[StepResult] = []
    total_steps = 5

    # Step 1: Check sorting report
    print_step(1, total_steps, "Check Sorting Report")
    result = await step_check_sorting_report(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 2: Verify system health
    print_step(2, total_steps, "Verify System Health")
    result = await step_verify_health(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 3: Collect metrics
    print_step(3, total_steps, "Collect Metrics")
    result = await step_collect_metrics(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 4: Update sync status
    print_step(4, total_steps, "Update Sync Status")
    result = await step_update_sync_status(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 5: Generate report
    print_step(5, total_steps, "Generate Morning Report")
    result = await step_generate_report(results, dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    steps_success = sum(1 for r in results if r.success)
    all_success = all(r.success for r in results)

    # Collect all warnings
    all_warnings = []
    for r in results:
        if 'warnings' in r.details:
            all_warnings.extend(r.details['warnings'])

    print_header("MORNING SYNC COMPLETE")

    status_color = Colors.GREEN if all_success else Colors.YELLOW
    print(f"  Status:    {status_color}{'SUCCESS' if all_success else 'COMPLETED WITH WARNINGS'}{Colors.ENDC}")
    print(f"  Steps:     {steps_success}/{total_steps}")
    print(f"  Duration:  {duration:.2f} seconds")
    print(f"  Warnings:  {len(all_warnings)}")

    if all_warnings:
        print(f"\n  {Colors.YELLOW}Warnings:{Colors.ENDC}")
        for w in all_warnings:
            print(f"    - {w}")

    print()

    # Build final report
    return MorningSyncReport(
        timestamp=end_time.isoformat(),
        date=end_time.strftime("%Y-%m-%d"),
        steps_completed=steps_success,
        total_steps=total_steps,
        success=all_success,
        duration_seconds=duration,
        sorting_report_found=any(
            r.details.get('report_found', False)
            for r in results
            if r.step_name == "Check Sorting Report"
        ),
        system_healthy=any(
            r.details.get('overall_healthy', False)
            for r in results
            if r.step_name == "Verify System Health"
        ),
        warnings=all_warnings,
        steps=[{
            'name': r.step_name,
            'success': r.success,
            'duration_ms': r.duration_ms,
            'message': r.message
        } for r in results]
    )


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Cirkelline Morning Sync Routine - Daglig 09:00 sync"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Kør uden at lave ændringer'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Vis detaljeret output'
    )

    args = parser.parse_args()

    try:
        report = asyncio.run(run_morning_sync(
            dry_run=args.dry_run,
            verbose=args.verbose
        ))

        # Exit code baseret på success
        sys.exit(0 if report.success else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Morning sync afbrudt af bruger{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal fejl: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
