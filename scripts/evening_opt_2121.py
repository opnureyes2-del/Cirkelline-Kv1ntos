#!/usr/bin/env python3
"""
CIRKELLINE EVENING OPTIMIZATION ROUTINE
=======================================
Kører dagligt kl. 21:21

5-Step Evening Optimization:
1. Session cleanup
2. Memory pre-optimization
3. Metrics aggregation
4. Prepare next day
5. Generate evening rapport

Brug:
    python scripts/evening_opt_2121.py [--dry-run] [--verbose]

Cron:
    21 21 * * * /path/to/python /path/to/scripts/evening_opt_2121.py >> /var/log/ckc/evening_opt.log 2>&1
"""

import argparse
import asyncio
import gc
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
EVENING_REPORTS_DIR = CKC_DIR / "evening-reports"
PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = CKC_DIR / "cache"
SESSION_DIR = CKC_DIR / "sessions"

# Cleanup settings
SESSION_MAX_AGE_HOURS = 24
CACHE_MAX_AGE_HOURS = 12
TEMP_FILES_MAX_AGE_HOURS = 6

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
class EveningOptReport:
    """Komplet evening optimization rapport."""
    timestamp: str
    date: str
    steps_completed: int
    total_steps: int
    success: bool
    duration_seconds: float
    sessions_cleaned: int
    cache_cleared_mb: float
    memory_freed_mb: float
    steps: List[Dict[str, Any]] = field(default_factory=list)
    next_day_prep: Dict[str, Any] = field(default_factory=dict)


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


def get_file_age_hours(path: Path) -> float:
    """Get file age in hours."""
    try:
        mtime = path.stat().st_mtime
        age_seconds = datetime.now().timestamp() - mtime
        return age_seconds / 3600
    except Exception:
        return 0


def get_dir_size_mb(path: Path) -> float:
    """Get directory size in MB."""
    try:
        total = 0
        for p in path.rglob('*'):
            if p.is_file():
                total += p.stat().st_size
        return total / (1024 * 1024)
    except Exception:
        return 0


# ==============================================================================
# STEP 1: SESSION CLEANUP
# ==============================================================================

async def step_session_cleanup(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 1: Session cleanup.

    Rydder gamle session filer og midlertidige data.
    """
    start = datetime.now()
    step_name = "Session Cleanup"
    details = {}
    sessions_cleaned = 0
    bytes_freed = 0

    try:
        # Clean old session files
        if SESSION_DIR.exists():
            for session_file in SESSION_DIR.glob('*.json'):
                age = get_file_age_hours(session_file)
                if age > SESSION_MAX_AGE_HOURS:
                    if not dry_run:
                        size = session_file.stat().st_size
                        session_file.unlink()
                        bytes_freed += size
                    sessions_cleaned += 1
                    if verbose:
                        print_info(f"Cleaned: {session_file.name} ({age:.1f}h old)")

        details['sessions_cleaned'] = sessions_cleaned
        details['bytes_freed'] = bytes_freed

        # Clean Python __pycache__
        pycache_cleaned = 0
        for pycache in PROJECT_ROOT.rglob('__pycache__'):
            if pycache.is_dir():
                try:
                    for pyc in pycache.glob('*.pyc'):
                        age = get_file_age_hours(pyc)
                        if age > 48:  # 2 days old
                            if not dry_run:
                                size = pyc.stat().st_size
                                pyc.unlink()
                                bytes_freed += size
                            pycache_cleaned += 1
                except Exception:
                    pass

        details['pycache_cleaned'] = pycache_cleaned

        if verbose:
            print_info(f"Sessions cleaned: {sessions_cleaned}")
            print_info(f"Pycache cleaned: {pycache_cleaned}")
            print_info(f"Bytes freed: {bytes_freed / 1024:.1f} KB")

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Cleaned {sessions_cleaned} sessions, {pycache_cleaned} pycache files",
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
# STEP 2: MEMORY PRE-OPTIMIZATION
# ==============================================================================

async def step_memory_preopt(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 2: Memory pre-optimization.

    Forbereder memory til nattens 03:33 sorting.
    """
    start = datetime.now()
    step_name = "Memory Pre-Optimization"
    details = {}

    try:
        # Get current memory stats
        try:
            import psutil
            mem_before = psutil.virtual_memory()
            details['memory_before_percent'] = mem_before.percent
            details['memory_before_available_gb'] = round(mem_before.available / (1024**3), 2)
        except ImportError:
            details['psutil'] = 'not installed'

        # Force garbage collection
        if not dry_run:
            gc.collect()
            gc.collect()  # Run twice for thorough cleanup
            if verbose:
                print_info("Garbage collection completed")
        else:
            if verbose:
                print_info("Garbage collection: skipped (dry-run)")

        # Get memory stats after
        try:
            import psutil
            mem_after = psutil.virtual_memory()
            details['memory_after_percent'] = mem_after.percent
            details['memory_after_available_gb'] = round(mem_after.available / (1024**3), 2)

            freed = mem_after.available - mem_before.available
            details['memory_freed_mb'] = round(freed / (1024**2), 2)

            if verbose:
                print_info(f"Memory before: {mem_before.percent}%")
                print_info(f"Memory after: {mem_after.percent}%")
                print_info(f"Freed: {details['memory_freed_mb']} MB")
        except ImportError:
            pass

        # Check for memory leaks indicators
        try:
            import psutil
            current_process = psutil.Process()
            details['current_process_mb'] = round(current_process.memory_info().rss / (1024**2), 2)
            if verbose:
                print_info(f"Current process: {details['current_process_mb']} MB")
        except ImportError:
            pass

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Memory optimized: {details.get('memory_freed_mb', 0)} MB freed",
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
# STEP 3: METRICS AGGREGATION
# ==============================================================================

async def step_metrics_aggregation(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 3: Metrics aggregation.

    Samler dagens metrics og statistikker.
    """
    start = datetime.now()
    step_name = "Metrics Aggregation"
    details = {}

    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # Check morning sync
        morning_sync_path = CKC_DIR / "morning-reports" / f"morning-sync-{today}.json"
        if morning_sync_path.exists():
            details['morning_sync'] = 'completed'
            if verbose:
                print_info("Morning sync: completed")
        else:
            details['morning_sync'] = 'not found'
            if verbose:
                print_warning("Morning sync: not found")

        # Check sorting report
        sorting_path = CKC_DIR / f"sorting-report-{today}.json"
        if sorting_path.exists():
            with open(sorting_path, 'r') as f:
                sorting_data = json.load(f)
            details['sorting_completed'] = sorting_data.get('success', False)
            if verbose:
                print_info(f"Sorting: {'completed' if details['sorting_completed'] else 'failed'}")
        else:
            details['sorting_completed'] = None
            if verbose:
                print_info("Sorting: not run today")

        # Git activity
        try:
            result = subprocess.run(
                ['git', '-C', str(PROJECT_ROOT), 'log', '--oneline', '--since=midnight'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                commits = [l for l in result.stdout.strip().split('\n') if l]
                details['commits_today'] = len(commits)
                if verbose:
                    print_info(f"Commits today: {len(commits)}")
        except Exception:
            pass

        # File changes
        try:
            result = subprocess.run(
                ['git', '-C', str(PROJECT_ROOT), 'diff', '--stat', '--cached'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                staged = len([l for l in result.stdout.strip().split('\n') if l])
                details['staged_changes'] = staged
        except Exception:
            pass

        # Aggregate
        details['aggregation_date'] = today
        details['aggregation_time'] = datetime.now().strftime("%H:%M")

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Metrics aggregated for {today}",
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
# STEP 4: PREPARE NEXT DAY
# ==============================================================================

async def step_prepare_next_day(dry_run: bool = False, verbose: bool = False) -> StepResult:
    """
    Step 4: Prepare next day.

    Forbereder system til næste dags 03:33 sorting.
    """
    start = datetime.now()
    step_name = "Prepare Next Day"
    details = {}

    try:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        details['preparing_for'] = tomorrow

        # Ensure CKC directories exist
        if not dry_run:
            CKC_DIR.mkdir(exist_ok=True)
            EVENING_REPORTS_DIR.mkdir(exist_ok=True)
            (CKC_DIR / "morning-reports").mkdir(exist_ok=True)

            if verbose:
                print_info("CKC directories verified")
        else:
            if verbose:
                print_info("Directory check: skipped (dry-run)")

        # Check disk space for next day
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            details['free_disk_gb'] = round(free_gb, 1)

            if free_gb < 10:
                details['disk_warning'] = True
                if verbose:
                    print_warning(f"Low disk space: {free_gb:.1f} GB free")
            else:
                if verbose:
                    print_info(f"Disk space OK: {free_gb:.1f} GB free")
        except Exception:
            pass

        # Verify cron jobs
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                cron_lines = result.stdout.strip().split('\n')
                sorting_cron = any('sorting_0333' in l for l in cron_lines)
                morning_cron = any('morning_sync' in l for l in cron_lines)
                evening_cron = any('evening_opt' in l for l in cron_lines)

                details['cron_sorting'] = sorting_cron
                details['cron_morning'] = morning_cron
                details['cron_evening'] = evening_cron

                if verbose:
                    print_info(f"Cron 03:33: {'✓' if sorting_cron else '✗'}")
                    print_info(f"Cron 09:00: {'✓' if morning_cron else '✗'}")
                    print_info(f"Cron 21:21: {'✓' if evening_cron else '✗'}")
        except Exception:
            details['cron_check'] = 'error'

        # Save next day prep file
        if not dry_run:
            prep_file = CKC_DIR / "next_day_prep.json"
            with open(prep_file, 'w') as f:
                json.dump({
                    'prepared_at': datetime.now().isoformat(),
                    'preparing_for': tomorrow,
                    'disk_ok': details.get('free_disk_gb', 0) >= 10,
                    'cron_sorting': details.get('cron_sorting', False),
                    'cron_morning': details.get('cron_morning', False),
                    'cron_evening': details.get('cron_evening', False)
                }, f, indent=2)

            if verbose:
                print_info(f"Prep file saved: {prep_file}")

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Prepared for {tomorrow}",
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
# STEP 5: GENERATE EVENING RAPPORT
# ==============================================================================

async def step_generate_report(
    all_results: List[StepResult],
    dry_run: bool = False,
    verbose: bool = False
) -> StepResult:
    """
    Step 5: Generer evening rapport.

    Samler alle resultater i en komplet rapport.
    """
    start = datetime.now()
    step_name = "Generate Evening Report"
    details = {}

    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # Extract metrics from results
        sessions_cleaned = 0
        cache_cleared = 0
        memory_freed = 0
        next_day_prep = {}

        for result in all_results:
            if result.step_name == "Session Cleanup":
                sessions_cleaned = result.details.get('sessions_cleaned', 0)
            elif result.step_name == "Memory Pre-Optimization":
                memory_freed = result.details.get('memory_freed_mb', 0)
            elif result.step_name == "Prepare Next Day":
                next_day_prep = result.details

        # Build report
        report = EveningOptReport(
            timestamp=now.isoformat(),
            date=today,
            steps_completed=sum(1 for r in all_results if r.success),
            total_steps=len(all_results) + 1,
            success=all(r.success for r in all_results),
            duration_seconds=sum(r.duration_ms for r in all_results) / 1000,
            sessions_cleaned=sessions_cleaned,
            cache_cleared_mb=cache_cleared,
            memory_freed_mb=memory_freed,
            steps=[{
                'name': r.step_name,
                'success': r.success,
                'duration_ms': r.duration_ms,
                'message': r.message
            } for r in all_results],
            next_day_prep=next_day_prep
        )

        # Save report
        if not dry_run:
            EVENING_REPORTS_DIR.mkdir(exist_ok=True)
            report_path = EVENING_REPORTS_DIR / f"evening-opt-{today}.json"

            with open(report_path, 'w') as f:
                json.dump({
                    'timestamp': report.timestamp,
                    'date': report.date,
                    'steps_completed': report.steps_completed,
                    'total_steps': report.total_steps,
                    'success': report.success,
                    'duration_seconds': report.duration_seconds,
                    'sessions_cleaned': report.sessions_cleaned,
                    'cache_cleared_mb': report.cache_cleared_mb,
                    'memory_freed_mb': report.memory_freed_mb,
                    'steps': report.steps,
                    'next_day_prep': report.next_day_prep
                }, f, indent=2)

            details['report_path'] = str(report_path)
            if verbose:
                print_success(f"Report saved: {report_path}")
        else:
            details['report_path'] = 'dry-run (skipped)'
            if verbose:
                print_info("Report save: skipped (dry-run)")

        duration = (datetime.now() - start).total_seconds() * 1000

        return StepResult(
            step_name=step_name,
            success=True,
            duration_ms=duration,
            message=f"Evening report generated for {today}",
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

async def run_evening_optimization(dry_run: bool = False, verbose: bool = False) -> EveningOptReport:
    """
    Kør komplet evening optimization routine.

    Args:
        dry_run: Hvis True, udfører ingen ændringer
        verbose: Hvis True, printer detaljeret output

    Returns:
        EveningOptReport med alle resultater
    """
    start_time = datetime.now()

    print_header(f"CIRKELLINE EVENING OPTIMIZATION - {start_time.strftime('%Y-%m-%d %H:%M')}")

    if dry_run:
        print(f"{Colors.YELLOW}DRY-RUN MODE - Ingen ændringer udføres{Colors.ENDC}\n")

    results: List[StepResult] = []
    total_steps = 5

    # Step 1: Session cleanup
    print_step(1, total_steps, "Session Cleanup")
    result = await step_session_cleanup(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 2: Memory pre-optimization
    print_step(2, total_steps, "Memory Pre-Optimization")
    result = await step_memory_preopt(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 3: Metrics aggregation
    print_step(3, total_steps, "Metrics Aggregation")
    result = await step_metrics_aggregation(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 4: Prepare next day
    print_step(4, total_steps, "Prepare Next Day")
    result = await step_prepare_next_day(dry_run, verbose)
    results.append(result)
    if result.success:
        print_success(result.message)
    else:
        print_error(result.message)

    # Step 5: Generate report
    print_step(5, total_steps, "Generate Evening Report")
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

    # Extract key metrics
    sessions_cleaned = 0
    memory_freed = 0
    for r in results:
        if r.step_name == "Session Cleanup":
            sessions_cleaned = r.details.get('sessions_cleaned', 0)
        elif r.step_name == "Memory Pre-Optimization":
            memory_freed = r.details.get('memory_freed_mb', 0)

    print_header("EVENING OPTIMIZATION COMPLETE")

    status_color = Colors.GREEN if all_success else Colors.RED
    print(f"  Status:          {status_color}{'SUCCESS' if all_success else 'FAILED'}{Colors.ENDC}")
    print(f"  Steps:           {steps_success}/{total_steps}")
    print(f"  Duration:        {duration:.2f} seconds")
    print(f"  Sessions:        {sessions_cleaned} cleaned")
    print(f"  Memory freed:    {memory_freed} MB")
    print(f"  Ready for 03:33: {'Yes' if all_success else 'Check logs'}")
    print()

    # Build final report
    return EveningOptReport(
        timestamp=end_time.isoformat(),
        date=end_time.strftime("%Y-%m-%d"),
        steps_completed=steps_success,
        total_steps=total_steps,
        success=all_success,
        duration_seconds=duration,
        sessions_cleaned=sessions_cleaned,
        cache_cleared_mb=0,
        memory_freed_mb=memory_freed,
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
        description="Cirkelline Evening Optimization - Daglig 21:21 optimering"
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
        report = asyncio.run(run_evening_optimization(
            dry_run=args.dry_run,
            verbose=args.verbose
        ))

        # Exit code baseret på success
        sys.exit(0 if report.success else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Evening optimization afbrudt af bruger{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal fejl: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
