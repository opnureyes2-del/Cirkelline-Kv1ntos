"""
Journal Search Tool
===================
Allows Cirkelline to search past journal entries.
Uses SQL-level filtering for efficient querying.

v1.0.0: Initial implementation
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text

from agno.tools import Toolkit
from cirkelline.config import logger
from cirkelline.database import _shared_engine


class JournalSearchTool(Toolkit):
    """Tool for searching user journal entries."""

    def __init__(self):
        super().__init__(name="journal_tools")
        self.register(self.search_journals)
        self.register(self.get_recent_journals)
        self.register(self.get_journal_by_date)

    def search_journals(
        self,
        user_id: str,
        topics: List[str] = None,
        date_range: str = "7d",
        limit: int = 10
    ) -> str:
        """
        Search journal entries by topics and/or date range.

        Args:
            user_id: The user's ID
            topics: Optional list of topic keywords to filter by
            date_range: Time range - "7d", "14d", "30d", "this_month", "last_month", "all"
            limit: Maximum entries to return (default 10)

        Returns:
            Formatted string of matching journal entries
        """
        try:
            # Calculate date filter
            start_date = self._parse_date_range(date_range)

            # Build query
            query_parts = ["SELECT journal_date, summary, topics, outcomes FROM ai.user_journals WHERE user_id = :user_id"]
            params = {"user_id": user_id, "limit": limit}

            if start_date:
                query_parts.append("AND journal_date >= :start_date")
                params["start_date"] = start_date

            # Add topic filtering if provided
            if topics:
                topic_conditions = []
                for i, topic in enumerate(topics):
                    param_name = f"topic_{i}"
                    topic_conditions.append(f"topics::text ILIKE :{param_name}")
                    params[param_name] = f"%{topic}%"
                query_parts.append(f"AND ({' OR '.join(topic_conditions)})")

            query_parts.append("ORDER BY journal_date DESC LIMIT :limit")
            query = " ".join(query_parts)

            with _shared_engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()

            if not rows:
                if topics:
                    return f"No journal entries found matching topics: {', '.join(topics)} in the last {date_range}"
                return f"No journal entries found in the last {date_range}"

            # Format results
            entries = []
            for row in rows:
                journal_date = row[0]
                summary = row[1]
                topics_list = row[2] or []
                outcomes = row[3] or []

                # Truncate summary if too long
                if len(summary) > 300:
                    summary = summary[:300] + "..."

                entry = f"**{journal_date.strftime('%B %d, %Y')}**"
                if topics_list:
                    entry += f" (Topics: {', '.join(topics_list[:5])})"
                entry += f"\n{summary}"
                entries.append(entry)

            logger.info(f"Journal search returned {len(rows)} entries for user")
            return "\n\n---\n\n".join(entries)

        except Exception as e:
            logger.error(f"Journal search failed: {e}")
            return f"Journal search error: {e}"

    def get_recent_journals(self, user_id: str, limit: int = 5) -> str:
        """
        Get the most recent journal entries for a user.

        Args:
            user_id: The user's ID
            limit: Number of entries (default 5)

        Returns:
            Formatted string of recent journal entries
        """
        try:
            with _shared_engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT journal_date, summary, topics, outcomes, message_count
                        FROM ai.user_journals
                        WHERE user_id = :user_id
                        ORDER BY journal_date DESC
                        LIMIT :limit
                    """),
                    {"user_id": user_id, "limit": limit}
                )
                rows = result.fetchall()

            if not rows:
                return "No journal entries found for this user."

            entries = []
            for row in rows:
                journal_date = row[0]
                summary = row[1]
                topics_list = row[2] or []
                outcomes = row[3] or []
                message_count = row[4] or 0

                entry = f"**{journal_date.strftime('%B %d, %Y')}** ({message_count} messages)"
                if topics_list:
                    entry += f"\nTopics: {', '.join(topics_list[:5])}"
                if outcomes:
                    entry += f"\nOutcomes: {', '.join(outcomes[:3])}"

                # Truncate summary
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                entry += f"\n{summary}"

                entries.append(entry)

            logger.info(f"Retrieved {len(rows)} recent journals for user")
            return "\n\n---\n\n".join(entries)

        except Exception as e:
            logger.error(f"Get recent journals failed: {e}")
            return f"Error: {e}"

    def get_journal_by_date(self, user_id: str, date_str: str) -> str:
        """
        Get journal entry for a specific date.

        Args:
            user_id: The user's ID
            date_str: Date in YYYY-MM-DD format

        Returns:
            The full journal entry for that date
        """
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            with _shared_engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT journal_date, summary, topics, outcomes, sessions_processed, message_count
                        FROM ai.user_journals
                        WHERE user_id = :user_id
                        AND journal_date = :target_date
                    """),
                    {"user_id": user_id, "target_date": target_date}
                )
                row = result.fetchone()

            if not row:
                return f"No journal entry found for {date_str}"

            journal_date = row[0]
            summary = row[1]
            topics_list = row[2] or []
            outcomes = row[3] or []
            session_count = len(row[4]) if row[4] else 0
            message_count = row[5] or 0

            # Format full entry
            lines = [
                f"# Journal: {journal_date.strftime('%B %d, %Y')}",
                "",
                f"**Sessions:** {session_count} | **Messages:** {message_count}",
                "",
            ]

            if topics_list:
                lines.append(f"**Topics:** {', '.join(topics_list)}")
                lines.append("")

            if outcomes:
                lines.append("**Key Outcomes:**")
                for outcome in outcomes:
                    lines.append(f"- {outcome}")
                lines.append("")

            lines.append("**Summary:**")
            lines.append(summary)

            logger.info(f"Retrieved journal for {date_str}")
            return "\n".join(lines)

        except ValueError:
            return f"Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-06)"
        except Exception as e:
            logger.error(f"Get journal by date failed: {e}")
            return f"Error: {e}"

    def _parse_date_range(self, date_range: str) -> Optional[datetime]:
        """Parse date range string to start date."""
        today = datetime.now().date()

        if date_range == "all":
            return None
        elif date_range == "7d":
            return today - timedelta(days=7)
        elif date_range == "14d":
            return today - timedelta(days=14)
        elif date_range == "30d":
            return today - timedelta(days=30)
        elif date_range == "this_month":
            return today.replace(day=1)
        elif date_range == "last_month":
            first_of_month = today.replace(day=1)
            last_month = first_of_month - timedelta(days=1)
            return last_month.replace(day=1)
        else:
            # Default to 7 days
            return today - timedelta(days=7)


logger.info("Journal search tool loaded (v1.0.0)")
