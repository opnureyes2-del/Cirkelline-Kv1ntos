"""
Cirkelline Calendar Tools
=========================
AI tools for calendar management using our standalone calendar system.
These tools use the same database as the UI - ONE unified system.

All operations go to local database FIRST, with optional Google sync.
This ensures AI and UI always see the same data.

v1.3.4: Created to replace AGNO GoogleCalendarTools
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import uuid4
from agno.tools import Toolkit
from sqlalchemy import text
from zoneinfo import ZoneInfo

from cirkelline.config import logger
from cirkelline.database import engine


class CirkellineCalendarTools(Toolkit):
    """
    Calendar management tools for Cirkelline AI.

    Uses the same standalone calendar database as the UI panel.
    Supports optional Google Calendar sync (write-through).
    """

    def __init__(self):
        super().__init__(name="calendar_tools")
        self.register(self.list_calendar_events)
        self.register(self.create_calendar_event)
        self.register(self.update_calendar_event)
        self.register(self.delete_calendar_event)
        self.register(self.get_calendars)
        logger.info("✅ CirkellineCalendarTools loaded (v1.3.4 - unified system)")

    def _get_user_timezone(self, user_id: str) -> str:
        """Get the user's timezone from their preferences. Defaults to UTC."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT preferences->>'timezone' as tz FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                row = result.fetchone()
                if row and row.tz:
                    return row.tz
        except Exception as e:
            logger.warning(f"Could not get user timezone: {e}")
        return "UTC"

    def _get_or_create_default_calendar(self, user_id: str) -> str:
        """Get or create the user's default calendar. Returns calendar_id."""
        with engine.connect() as conn:
            # Check for existing default calendar
            result = conn.execute(
                text("SELECT id FROM calendars WHERE user_id = :user_id AND is_default = true"),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if row:
                return str(row.id)

            # Create default calendar
            result = conn.execute(
                text("""
                    INSERT INTO calendars (user_id, name, color, is_default, source)
                    VALUES (:user_id, 'My Calendar', '#8E0B83', true, 'local')
                    RETURNING id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()
            conn.commit()
            logger.info(f"Created default calendar for user {user_id}")
            return str(row.id)

    def get_calendars(self, user_id: str) -> str:
        """
        Get all calendars for a user.

        Args:
            user_id: The user's ID

        Returns:
            List of calendars with their names, colors, and visibility status.
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, name, color, is_default, is_visible, source
                        FROM calendars
                        WHERE user_id = :user_id
                        ORDER BY is_default DESC, name ASC
                    """),
                    {"user_id": user_id}
                )

                calendars = []
                for row in result:
                    calendars.append({
                        "id": str(row.id),
                        "name": row.name,
                        "color": row.color,
                        "is_default": row.is_default,
                        "is_visible": row.is_visible,
                        "source": row.source
                    })

                if not calendars:
                    # Create default calendar if none exist
                    cal_id = self._get_or_create_default_calendar(user_id)
                    return f"Created default calendar (ID: {cal_id}). User has 1 calendar."

                result_lines = [f"User has {len(calendars)} calendar(s):"]
                for cal in calendars:
                    default = " (default)" if cal["is_default"] else ""
                    visible = " [hidden]" if not cal["is_visible"] else ""
                    result_lines.append(f"- {cal['name']}{default}{visible} (ID: {cal['id']})")

                return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error getting calendars: {e}")
            return f"Error getting calendars: {e}"

    def list_calendar_events(
        self,
        user_id: str,
        days_ahead: int = 7,
        days_behind: int = 0,
        calendar_id: Optional[str] = None
    ) -> str:
        """
        List upcoming calendar events for a user.

        Args:
            user_id: The user's ID
            days_ahead: How many days into the future to look (default: 7)
            days_behind: How many days into the past to look (default: 0)
            calendar_id: Optional specific calendar to filter by

        Returns:
            Formatted list of events with dates, times, and details.
            Use this to check what's scheduled, find conflicts, or review the calendar.
        """
        try:
            time_min = datetime.now(timezone.utc) - timedelta(days=days_behind)
            time_max = datetime.now(timezone.utc) + timedelta(days=days_ahead)

            with engine.connect() as conn:
                query = """
                    SELECT e.id, e.title, e.description, e.location,
                           e.start_time, e.end_time, e.all_day,
                           c.name as calendar_name, c.color as calendar_color
                    FROM calendar_events e
                    JOIN calendars c ON e.calendar_id = c.id
                    WHERE e.user_id = :user_id
                    AND c.is_visible = true
                    AND e.start_time <= :time_max
                    AND e.end_time >= :time_min
                """
                params = {
                    "user_id": user_id,
                    "time_min": time_min,
                    "time_max": time_max
                }

                if calendar_id:
                    query += " AND e.calendar_id = :calendar_id"
                    params["calendar_id"] = calendar_id

                query += " ORDER BY e.start_time ASC LIMIT 50"

                result = conn.execute(text(query), params)

                events = []
                for row in result:
                    events.append({
                        "id": str(row.id),
                        "title": row.title,
                        "description": row.description,
                        "location": row.location,
                        "start": row.start_time,
                        "end": row.end_time,
                        "all_day": row.all_day,
                        "calendar": row.calendar_name
                    })

                if not events:
                    return f"No events found in the next {days_ahead} days."

                result_lines = [f"Found {len(events)} event(s):"]
                for evt in events:
                    if evt["all_day"]:
                        time_str = evt["start"].strftime("%Y-%m-%d") + " (All day)"
                    else:
                        time_str = evt["start"].strftime("%Y-%m-%d %H:%M") + " - " + evt["end"].strftime("%H:%M")

                    line = f"- {evt['title']} | {time_str}"
                    if evt["location"]:
                        line += f" | {evt['location']}"
                    line += f" (ID: {evt['id']})"
                    result_lines.append(line)

                return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return f"Error listing events: {e}"

    def create_calendar_event(
        self,
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: bool = False,
        calendar_id: Optional[str] = None
    ) -> str:
        """
        Create a new calendar event.

        Args:
            user_id: The user's ID
            title: Event title/name
            start_time: Start time in ISO format (e.g., "2025-12-20T14:00:00")
            end_time: End time in ISO format (e.g., "2025-12-20T15:00:00")
            description: Optional event description
            location: Optional event location
            all_day: Whether this is an all-day event (default: False)
            calendar_id: Optional calendar ID (uses default if not provided)

        Returns:
            Confirmation with event details and ID.
            The event is created in the local database and optionally synced to Google.
        """
        try:
            # Get user's timezone for proper time interpretation
            user_tz_str = self._get_user_timezone(user_id)
            try:
                user_tz = ZoneInfo(user_tz_str)
            except Exception:
                user_tz = ZoneInfo("UTC")
                logger.warning(f"Invalid timezone '{user_tz_str}', defaulting to UTC")

            # Log the arguments for debugging
            logger.info(f"📅 create_calendar_event called: title='{title}', start='{start_time}', end='{end_time}', all_day={all_day}, user_tz={user_tz_str}")

            # Parse times - if no timezone in string, assume user's local timezone
            try:
                # Parse the datetime string
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

                # If the datetime is naive (no timezone), assume it's in the user's local time
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=user_tz)
                    logger.info(f"📅 Interpreted start time as {user_tz_str}: {start_dt.isoformat()}")
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=user_tz)
                    logger.info(f"📅 Interpreted end time as {user_tz_str}: {end_dt.isoformat()}")

                # Convert to UTC for storage
                start_dt = start_dt.astimezone(timezone.utc)
                end_dt = end_dt.astimezone(timezone.utc)
                logger.info(f"📅 Converted to UTC: start={start_dt.isoformat()}, end={end_dt.isoformat()}")

            except ValueError as e:
                return f"Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SS. Error: {e}"

            if end_dt <= start_dt:
                return "Error: End time must be after start time."

            # Get or create calendar
            if not calendar_id:
                calendar_id = self._get_or_create_default_calendar(user_id)

            with engine.connect() as conn:
                # Verify calendar ownership
                check = conn.execute(
                    text("SELECT id FROM calendars WHERE id = :id AND user_id = :user_id"),
                    {"id": calendar_id, "user_id": user_id}
                )
                if not check.fetchone():
                    return "Error: Calendar not found or doesn't belong to user."

                # Create event
                result = conn.execute(
                    text("""
                        INSERT INTO calendar_events
                        (calendar_id, user_id, title, description, location, start_time, end_time, all_day, source, sync_status)
                        VALUES (:calendar_id, :user_id, :title, :description, :location, :start_time, :end_time, :all_day, 'local', 'local')
                        RETURNING id, title, start_time, end_time
                    """),
                    {
                        "calendar_id": calendar_id,
                        "user_id": user_id,
                        "title": title,
                        "description": description,
                        "location": location,
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "all_day": all_day
                    }
                )

                row = result.fetchone()
                conn.commit()

                # Try to sync to Google (if connected)
                sync_msg = self._try_google_sync(user_id, str(row.id), "create", {
                    "title": title,
                    "description": description,
                    "location": location,
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "all_day": all_day
                })

                logger.info(f"✅ AI created calendar event '{title}' for user {user_id}")

                time_str = start_dt.strftime("%Y-%m-%d %H:%M") if not all_day else start_dt.strftime("%Y-%m-%d") + " (All day)"
                response = f"✅ Created event: {title}\n📅 {time_str}\nID: {row.id}"
                if location:
                    response += f"\n📍 {location}"
                if sync_msg:
                    response += f"\n{sync_msg}"

                return response

        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return f"Error creating event: {e}"

    def update_calendar_event(
        self,
        user_id: str,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: Optional[bool] = None
    ) -> str:
        """
        Update an existing calendar event.

        Args:
            user_id: The user's ID
            event_id: The event ID to update
            title: New title (optional)
            start_time: New start time in ISO format (optional)
            end_time: New end time in ISO format (optional)
            description: New description (optional)
            location: New location (optional)
            all_day: Whether this is an all-day event (optional)

        Returns:
            Confirmation of the update.
            Only provided fields are updated; others remain unchanged.
        """
        try:
            with engine.connect() as conn:
                # Verify ownership
                check = conn.execute(
                    text("SELECT id, external_id, start_time, end_time, all_day FROM calendar_events WHERE id = :id AND user_id = :user_id"),
                    {"id": event_id, "user_id": user_id}
                )
                existing = check.fetchone()
                if not existing:
                    return "Error: Event not found or doesn't belong to user."

                # Build update query
                updates = []
                params = {"id": event_id, "user_id": user_id}

                if title is not None:
                    updates.append("title = :title")
                    params["title"] = title
                if description is not None:
                    updates.append("description = :description")
                    params["description"] = description
                if location is not None:
                    updates.append("location = :location")
                    params["location"] = location
                if start_time is not None:
                    try:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        updates.append("start_time = :start_time")
                        params["start_time"] = start_dt
                    except ValueError:
                        return "Invalid start_time format. Use ISO format."
                if end_time is not None:
                    try:
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        updates.append("end_time = :end_time")
                        params["end_time"] = end_dt
                    except ValueError:
                        return "Invalid end_time format. Use ISO format."
                if all_day is not None:
                    updates.append("all_day = :all_day")
                    params["all_day"] = all_day

                if not updates:
                    return "No updates provided."

                updates.append("updated_at = NOW()")

                query = f"UPDATE calendar_events SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id RETURNING title"
                result = conn.execute(text(query), params)
                row = result.fetchone()
                conn.commit()

                # Try to sync to Google (if connected and event has external_id)
                sync_msg = ""
                if existing.external_id:
                    sync_msg = self._try_google_sync(user_id, event_id, "update", params)

                logger.info(f"✅ AI updated calendar event {event_id} for user {user_id}")

                response = f"✅ Updated event: {row.title}"
                if sync_msg:
                    response += f"\n{sync_msg}"
                return response

        except Exception as e:
            logger.error(f"Error updating calendar event: {e}")
            return f"Error updating event: {e}"

    def delete_calendar_event(self, user_id: str, event_id: str) -> str:
        """
        Delete a calendar event.

        Args:
            user_id: The user's ID
            event_id: The event ID to delete

        Returns:
            Confirmation of deletion.
            If synced to Google, also deletes from Google Calendar.
        """
        try:
            with engine.connect() as conn:
                # Check ownership and get external_id
                check = conn.execute(
                    text("SELECT id, title, external_id FROM calendar_events WHERE id = :id AND user_id = :user_id"),
                    {"id": event_id, "user_id": user_id}
                )
                existing = check.fetchone()
                if not existing:
                    return "Error: Event not found or doesn't belong to user."

                title = existing.title
                external_id = existing.external_id

                # Delete event
                conn.execute(
                    text("DELETE FROM calendar_events WHERE id = :id AND user_id = :user_id"),
                    {"id": event_id, "user_id": user_id}
                )
                conn.commit()

                # Try to sync delete to Google
                sync_msg = ""
                if external_id:
                    sync_msg = self._try_google_sync(user_id, event_id, "delete", {"external_id": external_id})

                logger.info(f"✅ AI deleted calendar event '{title}' for user {user_id}")

                response = f"✅ Deleted event: {title}"
                if sync_msg:
                    response += f"\n{sync_msg}"
                return response

        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            return f"Error deleting event: {e}"

    def _try_google_sync(self, user_id: str, event_id: str, action: str, data: dict) -> str:
        """Try to sync with Google Calendar if connected. Returns status message."""
        try:
            from cirkelline.integrations.google.google_oauth import get_user_google_credentials
            import asyncio

            # Get Google credentials
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                google_creds = loop.run_until_complete(get_user_google_credentials(user_id))
            finally:
                loop.close()

            if not google_creds:
                return ""  # Not connected, no message needed

            from googleapiclient.discovery import build
            service = build('calendar', 'v3', credentials=google_creds)

            if action == "create":
                event = {
                    'summary': data['title'],
                    'description': data.get('description', ''),
                    'location': data.get('location', ''),
                    'start': {'dateTime': data['start_time'].isoformat()} if not data.get('all_day') else {'date': data['start_time'].strftime('%Y-%m-%d')},
                    'end': {'dateTime': data['end_time'].isoformat()} if not data.get('all_day') else {'date': data['end_time'].strftime('%Y-%m-%d')}
                }
                created = service.events().insert(calendarId='primary', body=event).execute()

                # Update local event with Google ID
                with engine.connect() as conn:
                    conn.execute(
                        text("UPDATE calendar_events SET external_id = :ext_id, sync_status = 'synced', source = 'google' WHERE id = :id"),
                        {"ext_id": created['id'], "id": event_id}
                    )
                    conn.commit()
                return "📤 Synced to Google Calendar"

            elif action == "update":
                external_id = data.get("external_id")
                if not external_id:
                    # Get external_id from database
                    with engine.connect() as conn:
                        result = conn.execute(
                            text("SELECT external_id FROM calendar_events WHERE id = :id"),
                            {"id": event_id}
                        )
                        row = result.fetchone()
                        if row:
                            external_id = row.external_id

                if external_id:
                    # Get current event, update it
                    event = service.events().get(calendarId='primary', eventId=external_id).execute()
                    if 'title' in data:
                        event['summary'] = data['title']
                    if 'description' in data:
                        event['description'] = data['description']
                    if 'location' in data:
                        event['location'] = data['location']
                    if 'start_time' in data:
                        event['start'] = {'dateTime': data['start_time'].isoformat()}
                    if 'end_time' in data:
                        event['end'] = {'dateTime': data['end_time'].isoformat()}

                    service.events().update(calendarId='primary', eventId=external_id, body=event).execute()
                    return "📤 Synced to Google Calendar"

            elif action == "delete":
                external_id = data.get("external_id")
                if external_id:
                    service.events().delete(calendarId='primary', eventId=external_id).execute()
                    return "📤 Deleted from Google Calendar"

            return ""

        except Exception as e:
            logger.warning(f"Google sync failed (non-critical): {e}")
            return ""  # Don't report sync failures to user


# Create singleton instance
calendar_tools = CirkellineCalendarTools()

logger.info("✅ Calendar tools module loaded (v1.3.4 - unified system)")
