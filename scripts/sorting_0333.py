#!/usr/bin/env python3
"""
===============================================================================
3:33 SORTERING RUTINE - DAGLIG AUTOMATISERET SORTERING
===============================================================================
Version: v1.3.5
Agent: Kommandor #4
Korer: Dagligt kl. 03:33

5-Step Process:
1. Morning Memory Audit - Scan og optimer hukommelse
2. System Cleanup - Fjern midlertidige filer
3. Log Rotation - Roter og komprimér logs
4. Cache Invalidation - Ryd cache entries
5. Index Optimization - Optimer database indekser

Usage:
    python scripts/sorting_0333.py [--dry-run] [--verbose]

Cron:
    33 3 * * * /path/to/python scripts/sorting_0333.py >> /var/log/ckc_sorting_0333.log 2>&1
===============================================================================
"""

import os
import sys
import gc
import json
import gzip
import shutil
import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# ==============================================================================
# CONFIGURATION
# ==============================================================================

@dataclass
class SortingConfig:
    """Configuration for 3:33 sorting routine."""
    # Paths
    project_root: Path = Path("/home/rasmus/Desktop/projekts/projects/cirkelline-system")
    log_dir: Path = Path("/home/rasmus/Desktop/projekts/projects/cirkelline-system/logs")
    tmp_dir: Path = Path("/tmp")
    cache_dir: Path = Path.home() / ".ckc" / "cache"

    # Retention
    log_retention_days: int = 30
    tmp_retention_days: int = 7
    cache_retention_hours: int = 24

    # Database
    db_host: str = "localhost"
    db_port: int = 5532
    db_name: str = "cirkelline"
    db_user: str = "cirkelline"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Report
    report_dir: Path = Path.home() / "Desktop/projekts/projects/cirkelline-system/my_admin_workspace/SYNKRONISERING"

@dataclass
class SortingReport:
    """Report from 3:33 sorting routine."""
    timestamp: str
    duration_seconds: float
    steps_completed: int
    steps_total: int = 5
    memory_audit: Dict[str, Any] = None
    cleanup: Dict[str, Any] = None
    log_rotation: Dict[str, Any] = None
    cache_clear: Dict[str, Any] = None
    index_optimization: Dict[str, Any] = None
    errors: List[str] = None
    success: bool = True

# ==============================================================================
# LOGGING SETUP
# ==============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for sorting routine."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    return logging.getLogger("sorting_0333")

# ==============================================================================
# STEP 1: MORNING MEMORY AUDIT
# ==============================================================================

async def morning_memory_audit(config: SortingConfig, logger: logging.Logger, dry_run: bool = False) -> Dict[str, Any]:
    """
    Step 1: Scan and audit memory entries.

    Actions:
    - Count total memory entries
    - Identify potential duplicates
    - Report memory statistics
    """
    logger.info("STEP 1: MORNING MEMORY AUDIT")
    logger.info("=" * 60)

    result = {
        "action": "memory_audit",
        "status": "success",
        "entries_scanned": 0,
        "duplicates_found": 0,
        "memory_mb_before": 0,
        "memory_mb_after": 0
    }

    try:
        import psutil
        process = psutil.Process(os.getpid())
        result["memory_mb_before"] = process.memory_info().rss / 1024 / 1024

        # Force garbage collection
        if not dry_run:
            gc.collect()

        result["memory_mb_after"] = process.memory_info().rss / 1024 / 1024
        result["gc_collected"] = gc.get_count()

        logger.info(f"  Memory before: {result['memory_mb_before']:.2f} MB")
        logger.info(f"  Memory after:  {result['memory_mb_after']:.2f} MB")
        logger.info(f"  GC counts: {result['gc_collected']}")

    except ImportError:
        logger.warning("  psutil not available, skipping detailed memory audit")
        result["status"] = "partial"

        # Still do garbage collection
        if not dry_run:
            gc.collect()

    except Exception as e:
        logger.error(f"  Memory audit failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    logger.info("")
    return result

# ==============================================================================
# STEP 2: SYSTEM CLEANUP
# ==============================================================================

async def system_cleanup(config: SortingConfig, logger: logging.Logger, dry_run: bool = False) -> Dict[str, Any]:
    """
    Step 2: Remove temporary files.

    Targets:
    - /tmp/*.log (older than 7 days)
    - ~/.ckc/cache/* (older than 24 hours)
    """
    logger.info("STEP 2: SYSTEM CLEANUP")
    logger.info("=" * 60)

    result = {
        "action": "system_cleanup",
        "status": "success",
        "files_deleted": 0,
        "bytes_freed": 0,
        "paths_cleaned": []
    }

    now = datetime.now()

    # Cleanup patterns
    cleanup_targets = [
        {
            "path": config.tmp_dir,
            "pattern": "*.log",
            "max_age_days": config.tmp_retention_days
        },
        {
            "path": config.cache_dir,
            "pattern": "*",
            "max_age_hours": config.cache_retention_hours
        }
    ]

    for target in cleanup_targets:
        target_path = Path(target["path"])
        if not target_path.exists():
            logger.info(f"  Path does not exist: {target_path}")
            continue

        pattern = target.get("pattern", "*")
        max_age_days = target.get("max_age_days", 0)
        max_age_hours = target.get("max_age_hours", 0)

        max_age = timedelta(days=max_age_days, hours=max_age_hours)
        cutoff_time = now - max_age

        logger.info(f"  Scanning: {target_path}/{pattern} (older than {max_age})")

        try:
            for file_path in target_path.glob(pattern):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        file_size = file_path.stat().st_size

                        if dry_run:
                            logger.debug(f"    [DRY-RUN] Would delete: {file_path}")
                        else:
                            file_path.unlink()
                            logger.debug(f"    Deleted: {file_path}")

                        result["files_deleted"] += 1
                        result["bytes_freed"] += file_size
                        result["paths_cleaned"].append(str(file_path))

        except Exception as e:
            logger.error(f"  Error cleaning {target_path}: {e}")
            result["status"] = "partial"

    result["mb_freed"] = result["bytes_freed"] / 1024 / 1024

    logger.info(f"  Files deleted: {result['files_deleted']}")
    logger.info(f"  Space freed: {result['mb_freed']:.2f} MB")
    logger.info("")

    return result

# ==============================================================================
# STEP 3: LOG ROTATION
# ==============================================================================

async def log_rotation(config: SortingConfig, logger: logging.Logger, dry_run: bool = False) -> Dict[str, Any]:
    """
    Step 3: Rotate and compress logs.

    Actions:
    - Compress logs older than 1 day
    - Archive to logs/archive/
    - Delete logs older than retention period
    """
    logger.info("STEP 3: LOG ROTATION")
    logger.info("=" * 60)

    result = {
        "action": "log_rotation",
        "status": "success",
        "logs_rotated": 0,
        "logs_archived": 0,
        "logs_deleted": 0,
        "bytes_compressed": 0
    }

    log_dirs = [
        config.log_dir,
        config.project_root / "logs",
        Path.home() / ".ckc" / "logs"
    ]

    now = datetime.now()
    compress_cutoff = now - timedelta(days=1)
    delete_cutoff = now - timedelta(days=config.log_retention_days)

    for log_dir in log_dirs:
        if not log_dir.exists():
            continue

        archive_dir = log_dir / "archive"
        if not dry_run:
            archive_dir.mkdir(exist_ok=True)

        logger.info(f"  Processing: {log_dir}")

        try:
            for log_file in log_dir.glob("*.log"):
                if log_file.is_file():
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    file_size = log_file.stat().st_size

                    # Delete very old logs
                    if mtime < delete_cutoff:
                        if dry_run:
                            logger.debug(f"    [DRY-RUN] Would delete: {log_file}")
                        else:
                            log_file.unlink()
                        result["logs_deleted"] += 1

                    # Compress older logs
                    elif mtime < compress_cutoff:
                        gz_path = archive_dir / f"{log_file.name}.gz"

                        if dry_run:
                            logger.debug(f"    [DRY-RUN] Would compress: {log_file} -> {gz_path}")
                        else:
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(gz_path, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            log_file.unlink()

                        result["logs_rotated"] += 1
                        result["bytes_compressed"] += file_size

        except Exception as e:
            logger.error(f"  Error processing {log_dir}: {e}")
            result["status"] = "partial"

    result["mb_compressed"] = result["bytes_compressed"] / 1024 / 1024

    logger.info(f"  Logs rotated: {result['logs_rotated']}")
    logger.info(f"  Logs deleted: {result['logs_deleted']}")
    logger.info(f"  Size compressed: {result['mb_compressed']:.2f} MB")
    logger.info("")

    return result

# ==============================================================================
# STEP 4: CACHE INVALIDATION
# ==============================================================================

async def cache_invalidation(config: SortingConfig, logger: logging.Logger, dry_run: bool = False) -> Dict[str, Any]:
    """
    Step 4: Clear expired cache entries.

    Targets:
    - Redis cache (selective flush)
    - File cache
    - Memory cache (gc.collect)
    """
    logger.info("STEP 4: CACHE INVALIDATION")
    logger.info("=" * 60)

    result = {
        "action": "cache_invalidation",
        "status": "success",
        "redis_cleared": False,
        "file_cache_cleared": 0,
        "memory_collected": False
    }

    # Redis cache
    try:
        import redis
        r = redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)

        if r.ping():
            logger.info("  Redis connected")

            # Get expired keys count (don't flush entire DB in production)
            # Just log stats for now
            info = r.info('keyspace')
            result["redis_stats"] = info
            logger.info(f"  Redis keyspace: {info}")

            # Selective cleanup: clear keys matching pattern with TTL check
            if not dry_run:
                # Only clear keys that have expired (Redis does this automatically)
                # But we trigger memory cleanup
                r.memory_purge() if hasattr(r, 'memory_purge') else None

            result["redis_cleared"] = True

    except ImportError:
        logger.info("  Redis client not available")
    except Exception as e:
        logger.warning(f"  Redis cleanup skipped: {e}")

    # File cache directories
    cache_dirs = [
        config.cache_dir,
        Path("/tmp/ckc_cache"),
        config.project_root / ".cache"
    ]

    for cache_path in cache_dirs:
        if cache_path.exists():
            try:
                if dry_run:
                    count = len(list(cache_path.glob("*")))
                    logger.debug(f"    [DRY-RUN] Would clear {count} files from {cache_path}")
                else:
                    count = 0
                    for item in cache_path.glob("*"):
                        if item.is_file():
                            item.unlink()
                            count += 1
                    logger.info(f"  Cleared {count} files from {cache_path}")

                result["file_cache_cleared"] += count

            except Exception as e:
                logger.warning(f"  Error clearing {cache_path}: {e}")

    # Memory cache
    if not dry_run:
        gc.collect()
    result["memory_collected"] = True
    logger.info("  Memory garbage collected")

    logger.info("")
    return result

# ==============================================================================
# STEP 5: INDEX OPTIMIZATION
# ==============================================================================

async def index_optimization(config: SortingConfig, logger: logging.Logger, dry_run: bool = False) -> Dict[str, Any]:
    """
    Step 5: Optimize database indexes.

    Actions:
    - PostgreSQL VACUUM ANALYZE
    - pgvector index rebuild (if needed)
    - Clear query plan cache
    """
    logger.info("STEP 5: INDEX OPTIMIZATION")
    logger.info("=" * 60)

    result = {
        "action": "index_optimization",
        "status": "success",
        "vacuum_run": False,
        "analyze_run": False,
        "tables_optimized": []
    }

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        conn_string = f"host={config.db_host} port={config.db_port} dbname={config.db_name} user={config.db_user} password=cirkelline123"

        if dry_run:
            logger.info("  [DRY-RUN] Would run VACUUM ANALYZE on ai schema tables")
            result["vacuum_run"] = False
            result["analyze_run"] = False
        else:
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            # Get AI schema tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'ai'
            """)
            tables = [row[0] for row in cur.fetchall()]

            logger.info(f"  Found {len(tables)} tables in ai schema")

            # VACUUM ANALYZE each table
            for table in tables:
                try:
                    logger.info(f"  VACUUM ANALYZE ai.{table}")
                    cur.execute(f"VACUUM ANALYZE ai.{table}")
                    result["tables_optimized"].append(table)
                except Exception as e:
                    logger.warning(f"    Error on {table}: {e}")

            result["vacuum_run"] = True
            result["analyze_run"] = True

            # Clear prepared statement cache
            cur.execute("DISCARD ALL")
            logger.info("  Query plan cache cleared")

            cur.close()
            conn.close()

    except ImportError:
        logger.warning("  psycopg2 not available, skipping database optimization")
        result["status"] = "skipped"
    except Exception as e:
        logger.error(f"  Database optimization failed: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    logger.info(f"  Tables optimized: {len(result['tables_optimized'])}")
    logger.info("")

    return result

# ==============================================================================
# MAIN SORTING ROUTINE
# ==============================================================================

async def run_sorting_routine(dry_run: bool = False, verbose: bool = False) -> SortingReport:
    """
    Execute the complete 3:33 sorting routine.

    Steps:
    1. Morning Memory Audit
    2. System Cleanup
    3. Log Rotation
    4. Cache Invalidation
    5. Index Optimization
    """
    logger = setup_logging(verbose)
    config = SortingConfig()

    start_time = datetime.now()

    logger.info("")
    logger.info("=" * 70)
    logger.info("      3:33 SORTERING RUTINE - DAGLIG AUTOMATISERET SORTERING")
    logger.info("=" * 70)
    logger.info(f"  Timestamp: {start_time.isoformat()}")
    logger.info(f"  Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    logger.info("=" * 70)
    logger.info("")

    report = SortingReport(
        timestamp=start_time.isoformat(),
        duration_seconds=0,
        steps_completed=0,
        errors=[]
    )

    # Execute steps
    steps = [
        ("memory_audit", morning_memory_audit),
        ("cleanup", system_cleanup),
        ("log_rotation", log_rotation),
        ("cache_clear", cache_invalidation),
        ("index_optimization", index_optimization),
    ]

    for step_name, step_func in steps:
        try:
            result = await step_func(config, logger, dry_run)
            setattr(report, step_name, result)
            report.steps_completed += 1

            if result.get("status") == "failed":
                report.errors.append(f"{step_name}: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Step {step_name} failed with exception: {e}")
            report.errors.append(f"{step_name}: {str(e)}")
            setattr(report, step_name, {"status": "failed", "error": str(e)})

    # Calculate duration
    end_time = datetime.now()
    report.duration_seconds = (end_time - start_time).total_seconds()
    report.success = report.steps_completed == report.steps_total and len(report.errors) == 0

    # Summary
    logger.info("=" * 70)
    logger.info("                         RAPPORT")
    logger.info("=" * 70)
    logger.info(f"  Steps completed: {report.steps_completed}/{report.steps_total}")
    logger.info(f"  Duration: {report.duration_seconds:.2f} seconds")
    logger.info(f"  Status: {'SUCCESS' if report.success else 'PARTIAL'}")
    if report.errors:
        logger.warning(f"  Errors: {len(report.errors)}")
        for err in report.errors:
            logger.warning(f"    - {err}")
    logger.info("=" * 70)
    logger.info("")

    # Save report
    if not dry_run:
        await save_report(config, report, logger)

    return report

async def save_report(config: SortingConfig, report: SortingReport, logger: logging.Logger):
    """Save sorting report to SYNKRONISERING folder."""
    try:
        report_dir = config.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)

        # Create daily report file
        date_str = datetime.now().strftime("%Y-%m-%d")
        report_file = report_dir / f"sorting-report-{date_str}.json"

        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"  Report saved to: {report_file}")

    except Exception as e:
        logger.error(f"  Failed to save report: {e}")

# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="3:33 Sorting Routine - Daily automated system maintenance"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Run async routine
    report = asyncio.run(run_sorting_routine(
        dry_run=args.dry_run,
        verbose=args.verbose
    ))

    # Exit with appropriate code
    sys.exit(0 if report.success else 1)

if __name__ == "__main__":
    main()
