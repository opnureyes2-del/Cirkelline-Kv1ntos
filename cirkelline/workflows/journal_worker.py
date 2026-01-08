"""
Journal Background Worker
=========================
Background worker that processes the journal queue.
Runs continuously, picking up pending jobs and executing them sequentially.
"""

import asyncio
from typing import Optional
from cirkelline.config import logger
from cirkelline.workflows.journal_queue import (
    get_next_pending,
    mark_processing,
    mark_completed,
    mark_failed,
    get_queue_stats,
)
from cirkelline.workflows.daily_journal import run_daily_journal


# Worker configuration
WORKER_INTERVAL_SECONDS = 30  # Time between processing jobs
WORKER_IDLE_INTERVAL = 60    # Time to wait when queue is empty
WORKER_ENABLED = True        # Global flag to enable/disable worker


class JournalWorker:
    """
    Background worker for processing journal queue.

    Runs in a loop:
    1. Check for pending jobs
    2. If found, process one job
    3. Wait WORKER_INTERVAL_SECONDS before next job
    4. If queue empty, wait WORKER_IDLE_INTERVAL
    """

    def __init__(self):
        self.running = False
        self.current_job_id: Optional[int] = None
        self.jobs_processed = 0
        self.jobs_failed = 0

    async def start(self):
        """Start the background worker."""
        if not WORKER_ENABLED:
            logger.info("Journal worker is disabled")
            return

        self.running = True
        logger.info("Journal background worker started")

        while self.running:
            try:
                await self._process_next()
            except Exception as e:
                logger.error(f"Journal worker error: {e}")
                await asyncio.sleep(WORKER_INTERVAL_SECONDS)

    async def stop(self):
        """Stop the background worker gracefully."""
        logger.info("Stopping journal background worker...")
        self.running = False

    async def _process_next(self):
        """Process the next pending job in the queue."""
        job = get_next_pending()

        if not job:
            # Queue is empty, wait longer
            await asyncio.sleep(WORKER_IDLE_INTERVAL)
            return

        job_id = job["id"]
        user_id = job["user_id"]
        target_date = job["target_date"]

        self.current_job_id = job_id
        logger.info(f"Processing journal job {job_id}: user={user_id}, date={target_date}")

        # Mark as processing
        mark_processing(job_id)

        try:
            # Run the daily journal workflow
            result = await run_daily_journal(
                user_id=user_id,
                target_date=target_date
            )

            if result.get("success"):
                mark_completed(job_id)
                self.jobs_processed += 1
                logger.info(f"Journal job {job_id} completed successfully")
            else:
                error = result.get("error", "Unknown error")
                mark_failed(job_id, error)
                self.jobs_failed += 1
                logger.error(f"Journal job {job_id} failed: {error}")

        except Exception as e:
            mark_failed(job_id, str(e))
            self.jobs_failed += 1
            logger.error(f"Journal job {job_id} exception: {e}")

        finally:
            self.current_job_id = None

        # Wait before processing next job (rate limiting)
        await asyncio.sleep(WORKER_INTERVAL_SECONDS)

    def get_status(self) -> dict:
        """Get current worker status."""
        stats = get_queue_stats()
        return {
            "running": self.running,
            "current_job_id": self.current_job_id,
            "jobs_processed": self.jobs_processed,
            "jobs_failed": self.jobs_failed,
            "queue_stats": stats
        }


# Global worker instance
_worker: Optional[JournalWorker] = None


async def start_journal_worker():
    """Start the global journal worker."""
    global _worker
    if _worker is None:
        _worker = JournalWorker()
    asyncio.create_task(_worker.start())
    logger.info("Journal worker task created")


async def stop_journal_worker():
    """Stop the global journal worker."""
    global _worker
    if _worker:
        await _worker.stop()
        _worker = None


def get_worker_status() -> dict:
    """Get the current worker status."""
    global _worker
    if _worker:
        return _worker.get_status()
    return {
        "running": False,
        "current_job_id": None,
        "jobs_processed": 0,
        "jobs_failed": 0,
        "queue_stats": get_queue_stats()
    }


logger.info("✅ Journal worker module loaded")
