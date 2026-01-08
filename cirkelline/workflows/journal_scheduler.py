"""
Journal Scheduler
=================
APScheduler configuration for automated journal creation.
Runs daily at 1 AM to queue journals for users with activity the previous day.
"""

from datetime import date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from cirkelline.config import logger
from cirkelline.workflows.journal_queue import (
    add_to_queue,
    get_users_with_activity_no_journal,
)


# Scheduler configuration
SCHEDULER_HOUR = 1      # Run at 1 AM
SCHEDULER_MINUTE = 0
DAILY_JOB_PRIORITY = 10  # Higher priority than backfill jobs


# Global scheduler instance
scheduler = AsyncIOScheduler()


async def daily_journal_job():
    """
    Daily job that runs at 1 AM.
    Queues journal creation for all users who had activity yesterday but no journal.
    """
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    logger.info(f"Daily journal job starting for date: {yesterday}")

    try:
        # Find users with activity yesterday but no journal
        users_needing_journals = get_users_with_activity_no_journal(yesterday)

        if not users_needing_journals:
            logger.info(f"No users need journals for {yesterday}")
            return

        # Queue each user's journal with high priority
        queued_count = 0
        for user_id in users_needing_journals:
            if add_to_queue(user_id, yesterday, priority=DAILY_JOB_PRIORITY):
                queued_count += 1

        logger.info(f"Daily journal job: Queued {queued_count} journals for {yesterday}")

    except Exception as e:
        logger.error(f"Daily journal job failed: {e}")


def configure_scheduler():
    """Configure the scheduler with the daily journal job."""
    # Add daily job at 1:00 AM
    scheduler.add_job(
        daily_journal_job,
        trigger=CronTrigger(hour=SCHEDULER_HOUR, minute=SCHEDULER_MINUTE),
        id='daily_journal_job',
        name='Daily Journal Queue Job',
        replace_existing=True
    )
    logger.info(f"Scheduler configured: Daily journal job at {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d}")


def start_scheduler():
    """Start the scheduler."""
    if not scheduler.running:
        configure_scheduler()
        scheduler.start()
        logger.info("Journal scheduler started")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Journal scheduler stopped")


def get_scheduler_status() -> dict:
    """Get current scheduler status and job info."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {
        "running": scheduler.running,
        "jobs": jobs
    }


async def trigger_daily_job_now():
    """
    Manually trigger the daily journal job.
    Useful for testing or admin-initiated runs.
    """
    logger.info("Manual trigger: Running daily journal job now")
    await daily_journal_job()


logger.info("✅ Journal scheduler module loaded")
