#!/usr/bin/env python3
"""
Fix journal day numbers for all existing journals.

Each journal's "Day X" should be its sequential position among all user journals,
not days since registration.

Usage:
    python scripts/fix_journal_day_numbers.py [--dry-run]
"""

import sys
import re
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/home/eenvy/Desktop/cirkelline')

from sqlalchemy import text
from cirkelline.database import _shared_engine


def fix_journal_day_numbers(dry_run: bool = False):
    """Fix day numbers in all journal summaries."""

    print("=" * 60)
    print("JOURNAL DAY NUMBER FIX SCRIPT")
    print("=" * 60)

    if dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    else:
        print("MODE: LIVE (changes will be committed)")
    print()

    with _shared_engine.connect() as conn:
        # Get all users with journals
        users = conn.execute(text("""
            SELECT DISTINCT user_id FROM ai.user_journals ORDER BY user_id
        """)).fetchall()

        print(f"Found {len(users)} users with journals")
        print()

        total_fixed = 0

        for (user_id,) in users:
            print(f"\n--- User: {user_id} ---")

            # Get all journals for this user, ordered by date
            journals = conn.execute(text("""
                SELECT id, journal_date, summary
                FROM ai.user_journals
                WHERE user_id = :user_id
                ORDER BY journal_date ASC
            """), {"user_id": user_id}).fetchall()

            print(f"  Found {len(journals)} journals")

            for idx, (journal_id, journal_date, summary) in enumerate(journals):
                correct_day = idx + 1  # Day 1, Day 2, etc.

                # Parse current day number from summary
                # Format: "Day X - December 02, 2025"
                match = re.match(r'^Day (\d+) - (.+)$', summary.split('\n')[0])

                if match:
                    current_day = int(match.group(1))
                    date_part = match.group(2)

                    if current_day != correct_day:
                        print(f"  [{journal_date}] Day {current_day} -> Day {correct_day}")

                        # Fix the summary
                        new_first_line = f"Day {correct_day} - {date_part}"
                        lines = summary.split('\n')
                        lines[0] = new_first_line
                        new_summary = '\n'.join(lines)

                        if not dry_run:
                            conn.execute(text("""
                                UPDATE ai.user_journals
                                SET summary = :summary
                                WHERE id = :id
                            """), {"summary": new_summary, "id": journal_id})

                        total_fixed += 1
                    else:
                        print(f"  [{journal_date}] Day {current_day} - OK")
                else:
                    # No "Day X" format found, add it
                    print(f"  [{journal_date}] No day number found, adding Day {correct_day}")

                    # Try to parse just the date
                    first_line = summary.split('\n')[0]
                    try:
                        dt = datetime.strptime(str(journal_date), "%Y-%m-%d")
                        new_first_line = f"Day {correct_day} - {dt.strftime('%B %d, %Y')}"
                        lines = summary.split('\n')
                        lines[0] = new_first_line
                        new_summary = '\n'.join(lines)

                        if not dry_run:
                            conn.execute(text("""
                                UPDATE ai.user_journals
                                SET summary = :summary
                                WHERE id = :id
                            """), {"summary": new_summary, "id": journal_id})

                        total_fixed += 1
                    except Exception as e:
                        print(f"    ERROR: Could not fix - {e}")

        if not dry_run:
            conn.commit()
            print(f"\n{'=' * 60}")
            print(f"DONE! Fixed {total_fixed} journal entries.")
        else:
            print(f"\n{'=' * 60}")
            print(f"DRY RUN: Would fix {total_fixed} journal entries.")
            print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    fix_journal_day_numbers(dry_run=dry_run)
