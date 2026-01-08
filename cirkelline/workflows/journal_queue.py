"""
Journal Queue Management
========================
Functions for managing the journal workflow queue.
Handles adding jobs, processing, and tracking status.
"""

import os
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from cirkelline.config import logger


def get_engine():
    """Get SQLAlchemy engine for queue operations."""
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline")
    return create_engine(db_url)


def add_to_queue(user_id: str, target_date: str, priority: int = 0) -> bool:
    """
    Add a single journal job to the queue.

    Args:
        user_id: User ID to create journal for
        target_date: Date string (YYYY-MM-DD)
        priority: Higher = processed first (default 0, daily jobs use 10)

    Returns:
        True if added, False if already exists
    """
    engine = get_engine()

    with Session(engine) as session:
        try:
            query = """
                INSERT INTO ai.journal_queue (user_id, target_date, priority)
                VALUES (:user_id, :target_date, :priority)
                ON CONFLICT (user_id, target_date) DO NOTHING
                RETURNING id
            """
            result = session.execute(text(query), {
                "user_id": user_id,
                "target_date": target_date,
                "priority": priority
            })
            session.commit()

            row = result.fetchone()
            if row:
                logger.info(f"Added to journal queue: user={user_id}, date={target_date}")
                return True
            else:
                logger.debug(f"Already in queue: user={user_id}, date={target_date}")
                return False
        except Exception as e:
            logger.error(f"Failed to add to queue: {e}")
            session.rollback()
            return False


def get_user_gap_days(user_id: str) -> List[str]:
    """
    Find all days with activity but no journal for a user.

    Returns:
        List of date strings (YYYY-MM-DD) that need journals
    """
    engine = get_engine()

    with Session(engine) as session:
        # Get user registration date
        user_query = """
            SELECT created_at FROM users WHERE CAST(id AS varchar) = :user_id
        """
        user_result = session.execute(text(user_query), {"user_id": user_id})
        user_row = user_result.fetchone()

        if not user_row:
            return []

        registered_at = user_row[0]
        start_date = registered_at.date() if hasattr(registered_at, 'date') else registered_at

        # Get days with activity
        activity_query = """
            SELECT DISTINCT DATE(to_timestamp(created_at)) as activity_date
            FROM ai.agno_sessions
            WHERE user_id = :user_id
        """
        activity_result = session.execute(text(activity_query), {"user_id": user_id})
        activity_dates = {row[0].isoformat() for row in activity_result.fetchall() if row[0]}

        # Get days with journals
        journal_query = """
            SELECT journal_date FROM ai.user_journals WHERE user_id = :user_id
        """
        journal_result = session.execute(text(journal_query), {"user_id": user_id})
        journal_dates = {row[0].isoformat() for row in journal_result.fetchall() if row[0]}

        # Find gaps (activity but no journal)
        gap_dates = activity_dates - journal_dates

        # Filter to only dates from registration onwards and before today
        today = date.today().isoformat()
        valid_gaps = [d for d in gap_dates if d >= start_date.isoformat() and d < today]

        return sorted(valid_gaps)


def add_user_gaps_to_queue(user_id: str, priority: int = 0) -> int:
    """
    Find all gap days for a user and add them to the queue.

    Returns:
        Number of jobs added
    """
    gap_days = get_user_gap_days(user_id)
    added = 0

    for day in gap_days:
        if add_to_queue(user_id, day, priority):
            added += 1

    logger.info(f"Added {added} gap days to queue for user {user_id}")
    return added


def get_all_users_with_gaps() -> List[Dict[str, Any]]:
    """
    Get all users who have gap days (activity without journals).
    Excludes anonymous users (user_id starting with 'anon-').

    Returns:
        List of {user_id, email, gap_count}
    """
    engine = get_engine()

    with Session(engine) as session:
        query = """
            WITH activity_days AS (
                SELECT
                    user_id,
                    DATE(to_timestamp(created_at)) as activity_date
                FROM ai.agno_sessions
                WHERE user_id NOT LIKE 'anon-%'
                GROUP BY user_id, DATE(to_timestamp(created_at))
            ),
            journal_days AS (
                SELECT user_id, journal_date
                FROM ai.user_journals
            ),
            gaps AS (
                SELECT
                    a.user_id,
                    COUNT(*) as gap_count
                FROM activity_days a
                LEFT JOIN journal_days j ON a.user_id = j.user_id AND a.activity_date = j.journal_date
                WHERE j.journal_date IS NULL
                  AND a.activity_date < CURRENT_DATE
                GROUP BY a.user_id
            )
            SELECT g.user_id, u.email, g.gap_count
            FROM gaps g
            LEFT JOIN users u ON g.user_id = u.id::text
            WHERE g.gap_count > 0
            ORDER BY g.gap_count DESC
        """
        result = session.execute(text(query))

        return [
            {"user_id": row[0], "email": row[1], "gap_count": row[2]}
            for row in result.fetchall()
        ]


def add_all_gaps_to_queue(priority: int = 0) -> Dict[str, int]:
    """
    Find all gap days for all users and add them to the queue.

    Returns:
        Dict with total_users, total_jobs_added
    """
    users_with_gaps = get_all_users_with_gaps()
    total_added = 0

    for user in users_with_gaps:
        added = add_user_gaps_to_queue(user["user_id"], priority)
        total_added += added

    logger.info(f"Added {total_added} total gap days for {len(users_with_gaps)} users")
    return {
        "total_users": len(users_with_gaps),
        "total_jobs_added": total_added
    }


def get_next_pending() -> Optional[Dict[str, Any]]:
    """
    Get the next pending job from the queue.
    Orders by priority (high first), then created_at (oldest first).

    Returns:
        Job dict or None if queue is empty
    """
    engine = get_engine()

    with Session(engine) as session:
        query = """
            SELECT id, user_id, target_date, priority, created_at
            FROM ai.journal_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """
        result = session.execute(text(query))
        row = result.fetchone()

        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "target_date": row[2].isoformat() if row[2] else None,
                "priority": row[3],
                "created_at": row[4].isoformat() if row[4] else None
            }
        return None


def mark_processing(job_id: int) -> bool:
    """Mark a job as processing."""
    engine = get_engine()

    with Session(engine) as session:
        try:
            query = """
                UPDATE ai.journal_queue
                SET status = 'processing'
                WHERE id = :job_id
            """
            session.execute(text(query), {"job_id": job_id})
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as processing: {e}")
            session.rollback()
            return False


def mark_completed(job_id: int) -> bool:
    """Mark a job as completed."""
    engine = get_engine()

    with Session(engine) as session:
        try:
            query = """
                UPDATE ai.journal_queue
                SET status = 'completed', processed_at = NOW()
                WHERE id = :job_id
            """
            session.execute(text(query), {"job_id": job_id})
            session.commit()
            logger.info(f"Journal queue job {job_id} completed")
            return True
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as completed: {e}")
            session.rollback()
            return False


def mark_failed(job_id: int, error_message: str) -> bool:
    """Mark a job as failed with an error message."""
    engine = get_engine()

    with Session(engine) as session:
        try:
            query = """
                UPDATE ai.journal_queue
                SET status = 'failed', error_message = :error, processed_at = NOW()
                WHERE id = :job_id
            """
            session.execute(text(query), {"job_id": job_id, "error": error_message})
            session.commit()
            logger.error(f"Journal queue job {job_id} failed: {error_message}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
            session.rollback()
            return False


def get_queue_stats() -> Dict[str, int]:
    """
    Get queue statistics by status.

    Returns:
        Dict with counts: pending, processing, completed, failed, total
    """
    engine = get_engine()

    with Session(engine) as session:
        query = """
            SELECT status, COUNT(*) as count
            FROM ai.journal_queue
            GROUP BY status
        """
        result = session.execute(text(query))

        stats = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        for row in result.fetchall():
            if row[0] in stats:
                stats[row[0]] = row[1]

        stats["total"] = sum(stats.values())
        return stats


def get_recent_queue_items(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent queue items for display.

    Returns:
        List of queue items with user email
    """
    engine = get_engine()

    with Session(engine) as session:
        query = """
            SELECT
                q.id, q.user_id, u.email, q.target_date,
                q.status, q.priority, q.error_message,
                q.created_at, q.processed_at
            FROM ai.journal_queue q
            LEFT JOIN users u ON q.user_id = u.id::text
            ORDER BY
                CASE q.status
                    WHEN 'processing' THEN 1
                    WHEN 'pending' THEN 2
                    ELSE 3
                END,
                q.created_at DESC
            LIMIT :limit
        """
        result = session.execute(text(query), {"limit": limit})

        return [
            {
                "id": row[0],
                "user_id": row[1],
                "email": row[2],
                "target_date": row[3].isoformat() if row[3] else None,
                "status": row[4],
                "priority": row[5],
                "error_message": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "processed_at": row[8].isoformat() if row[8] else None
            }
            for row in result.fetchall()
        ]


def get_users_with_activity_no_journal(target_date: str) -> List[str]:
    """
    Get list of user IDs who have activity on target_date but no journal.
    Used by daily scheduler.

    Args:
        target_date: Date string (YYYY-MM-DD)

    Returns:
        List of user IDs
    """
    engine = get_engine()

    with Session(engine) as session:
        # Convert date to timestamp range
        from datetime import datetime
        parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        start_of_day = datetime.combine(parsed_date, datetime.min.time())
        end_of_day = datetime.combine(parsed_date, datetime.max.time())
        start_ts = int(start_of_day.timestamp())
        end_ts = int(end_of_day.timestamp())

        query = """
            SELECT DISTINCT s.user_id
            FROM ai.agno_sessions s
            LEFT JOIN ai.user_journals j
                ON s.user_id = j.user_id AND j.journal_date = :target_date
            WHERE s.created_at >= :start_ts
              AND s.created_at <= :end_ts
              AND j.id IS NULL
              AND s.user_id IS NOT NULL
              AND s.user_id NOT LIKE 'anon-%'
        """
        result = session.execute(text(query), {
            "target_date": target_date,
            "start_ts": start_ts,
            "end_ts": end_ts
        })

        return [row[0] for row in result.fetchall()]


def clear_completed_jobs(days_old: int = 7) -> int:
    """
    Clean up completed jobs older than specified days.

    Returns:
        Number of jobs deleted
    """
    engine = get_engine()

    with Session(engine) as session:
        try:
            query = """
                DELETE FROM ai.journal_queue
                WHERE status = 'completed'
                  AND processed_at < NOW() - INTERVAL ':days days'
                RETURNING id
            """
            result = session.execute(text(query.replace(':days', str(days_old))))
            deleted = len(result.fetchall())
            session.commit()
            logger.info(f"Cleaned up {deleted} completed journal queue jobs")
            return deleted
        except Exception as e:
            logger.error(f"Failed to clean up queue: {e}")
            session.rollback()
            return 0


def retry_failed_jobs() -> int:
    """
    Reset failed jobs back to pending for retry.

    Returns:
        Number of jobs reset
    """
    engine = get_engine()

    with Session(engine) as session:
        try:
            query = """
                UPDATE ai.journal_queue
                SET status = 'pending', error_message = NULL
                WHERE status = 'failed'
                RETURNING id
            """
            result = session.execute(text(query))
            reset = len(result.fetchall())
            session.commit()
            logger.info(f"Reset {reset} failed jobs to pending")
            return reset
        except Exception as e:
            logger.error(f"Failed to retry failed jobs: {e}")
            session.rollback()
            return 0


logger.info("✅ Journal queue module loaded")
