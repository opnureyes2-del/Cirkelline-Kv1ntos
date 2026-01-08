"""
Standalone Calendar Endpoints
==============================
CRUD operations for local calendars and events.
Supports standalone mode without external connections.
Includes Google Calendar sync (write-through + pull sync).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from cirkelline.config import logger
from cirkelline.database import engine
from cirkelline.integrations.google.google_oauth import get_user_google_credentials

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# GOOGLE CALENDAR HELPERS
# ═══════════════════════════════════════════════════════════════

async def get_google_calendar_service(user_id: str):
    """Get Google Calendar service if user is connected."""
    try:
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            return None
        from googleapiclient.discovery import build
        return build('calendar', 'v3', credentials=google_creds)
    except Exception as e:
        logger.warning(f"⚠️ Could not get Google Calendar service: {e}")
        return None


async def create_google_event(service, event_data: dict) -> Optional[str]:
    """Create event in Google Calendar. Returns Google event ID."""
    try:
        event = {
            'summary': event_data['title'],
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
            'start': {'dateTime': event_data['start_time'].isoformat()} if not event_data.get('all_day') else {'date': event_data['start_time'].strftime('%Y-%m-%d')},
            'end': {'dateTime': event_data['end_time'].isoformat()} if not event_data.get('all_day') else {'date': event_data['end_time'].strftime('%Y-%m-%d')}
        }
        created = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"✅ Created Google event: {created['id']}")
        return created['id']
    except Exception as e:
        logger.error(f"❌ Failed to create Google event: {e}")
        return None


async def update_google_event(service, google_event_id: str, event_data: dict) -> bool:
    """Update event in Google Calendar."""
    try:
        # Get existing event first
        event = service.events().get(calendarId='primary', eventId=google_event_id).execute()

        # Update fields
        if 'title' in event_data:
            event['summary'] = event_data['title']
        if 'description' in event_data:
            event['description'] = event_data['description']
        if 'location' in event_data:
            event['location'] = event_data['location']
        if 'start_time' in event_data:
            if event_data.get('all_day'):
                event['start'] = {'date': event_data['start_time'].strftime('%Y-%m-%d')}
            else:
                event['start'] = {'dateTime': event_data['start_time'].isoformat()}
        if 'end_time' in event_data:
            if event_data.get('all_day'):
                event['end'] = {'date': event_data['end_time'].strftime('%Y-%m-%d')}
            else:
                event['end'] = {'dateTime': event_data['end_time'].isoformat()}

        service.events().update(calendarId='primary', eventId=google_event_id, body=event).execute()
        logger.info(f"✅ Updated Google event: {google_event_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update Google event: {e}")
        return False


async def delete_google_event(service, google_event_id: str) -> bool:
    """Delete event from Google Calendar."""
    try:
        service.events().delete(calendarId='primary', eventId=google_event_id).execute()
        logger.info(f"✅ Deleted Google event: {google_event_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete Google event: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class CalendarCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(default="#8E0B83", pattern="^#[0-9A-Fa-f]{6}$")
    is_default: bool = False


class CalendarUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_default: Optional[bool] = None
    is_visible: Optional[bool] = None


class EventCreate(BaseModel):
    calendar_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class EventUpdate(BaseModel):
    calendar_id: Optional[UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_user_id(request: Request) -> str:
    """Extract user_id from JWT middleware."""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


# ═══════════════════════════════════════════════════════════════
# CALENDAR ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/calendar/calendars")
async def list_calendars(request: Request):
    """List all calendars for the current user."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, name, color, is_default, is_visible, source,
                           external_id, sync_enabled, last_synced_at, created_at, updated_at
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
                    "source": row.source,
                    "external_id": row.external_id,
                    "sync_enabled": row.sync_enabled,
                    "last_synced_at": row.last_synced_at.isoformat() if row.last_synced_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"calendars": calendars, "total": len(calendars)})

    except Exception as e:
        logger.error(f"❌ Error listing calendars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/calendar/calendars")
async def create_calendar(request: Request, data: CalendarCreate):
    """Create a new calendar."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # If this is set as default, unset other defaults first
            if data.is_default:
                conn.execute(
                    text("UPDATE calendars SET is_default = false WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )

            # Check if user has any calendars - if not, make this one default
            count_result = conn.execute(
                text("SELECT COUNT(*) FROM calendars WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            is_first_calendar = count_result.scalar() == 0

            result = conn.execute(
                text("""
                    INSERT INTO calendars (user_id, name, color, is_default, source)
                    VALUES (:user_id, :name, :color, :is_default, 'local')
                    RETURNING id, name, color, is_default, is_visible, source, created_at
                """),
                {
                    "user_id": user_id,
                    "name": data.name,
                    "color": data.color,
                    "is_default": data.is_default or is_first_calendar
                }
            )

            row = result.fetchone()
            conn.commit()

            logger.info(f"✅ Created calendar '{data.name}' for user {user_id}")

            return JSONResponse(
                status_code=201,
                content={
                    "id": str(row.id),
                    "name": row.name,
                    "color": row.color,
                    "is_default": row.is_default,
                    "is_visible": row.is_visible,
                    "source": row.source,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
            )

    except Exception as e:
        logger.error(f"❌ Error creating calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/calendar/calendars/{calendar_id}")
async def update_calendar(request: Request, calendar_id: UUID, data: CalendarUpdate):
    """Update a calendar."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Verify ownership
            check = conn.execute(
                text("SELECT id FROM calendars WHERE id = :id AND user_id = :user_id"),
                {"id": str(calendar_id), "user_id": user_id}
            )
            if not check.fetchone():
                raise HTTPException(status_code=404, detail="Calendar not found")

            # If setting as default, unset other defaults first
            if data.is_default:
                conn.execute(
                    text("UPDATE calendars SET is_default = false WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )

            # Build update query dynamically
            updates = []
            params = {"id": str(calendar_id), "user_id": user_id}

            if data.name is not None:
                updates.append("name = :name")
                params["name"] = data.name
            if data.color is not None:
                updates.append("color = :color")
                params["color"] = data.color
            if data.is_default is not None:
                updates.append("is_default = :is_default")
                params["is_default"] = data.is_default
            if data.is_visible is not None:
                updates.append("is_visible = :is_visible")
                params["is_visible"] = data.is_visible

            if updates:
                updates.append("updated_at = NOW()")
                query = f"UPDATE calendars SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id RETURNING *"
                result = conn.execute(text(query), params)
                row = result.fetchone()
                conn.commit()

                return JSONResponse(content={
                    "id": str(row.id),
                    "name": row.name,
                    "color": row.color,
                    "is_default": row.is_default,
                    "is_visible": row.is_visible,
                    "source": row.source,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"message": "No updates provided"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/calendar/calendars/{calendar_id}")
async def delete_calendar(request: Request, calendar_id: UUID):
    """Delete a calendar and all its events."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Verify ownership and delete
            result = conn.execute(
                text("DELETE FROM calendars WHERE id = :id AND user_id = :user_id RETURNING id"),
                {"id": str(calendar_id), "user_id": user_id}
            )

            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Calendar not found")

            conn.commit()
            logger.info(f"✅ Deleted calendar {calendar_id} for user {user_id}")

            return JSONResponse(content={"message": "Calendar deleted", "id": str(calendar_id)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# EVENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/calendar/events")
async def list_events(
    request: Request,
    calendar_id: Optional[UUID] = None,
    time_min: Optional[datetime] = None,
    time_max: Optional[datetime] = None,
    limit: int = 100
):
    """List events for the current user, optionally filtered by calendar and date range."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            query = """
                SELECT e.id, e.calendar_id, e.title, e.description, e.location,
                       e.start_time, e.end_time, e.all_day, e.recurrence_rule,
                       e.color, e.external_id, e.external_link, e.source, e.sync_status,
                       e.created_at, e.updated_at,
                       c.name as calendar_name, c.color as calendar_color
                FROM calendar_events e
                JOIN calendars c ON e.calendar_id = c.id
                WHERE e.user_id = :user_id AND c.is_visible = true
            """
            params = {"user_id": user_id, "limit": limit}

            if calendar_id:
                query += " AND e.calendar_id = :calendar_id"
                params["calendar_id"] = str(calendar_id)

            if time_min:
                query += " AND e.end_time >= :time_min"
                params["time_min"] = time_min

            if time_max:
                query += " AND e.start_time <= :time_max"
                params["time_max"] = time_max

            query += " ORDER BY e.start_time ASC LIMIT :limit"

            result = conn.execute(text(query), params)

            events = []
            for row in result:
                events.append({
                    "id": str(row.id),
                    "calendar_id": str(row.calendar_id),
                    "calendar_name": row.calendar_name,
                    "calendar_color": row.calendar_color,
                    "title": row.title,
                    "summary": row.title,  # Alias for compatibility
                    "description": row.description,
                    "location": row.location,
                    "start": row.start_time.isoformat() if row.start_time else None,
                    "end": row.end_time.isoformat() if row.end_time else None,
                    "start_time": row.start_time.isoformat() if row.start_time else None,
                    "end_time": row.end_time.isoformat() if row.end_time else None,
                    "all_day": row.all_day,
                    "recurrence_rule": row.recurrence_rule,
                    "color": row.color or row.calendar_color,
                    "external_id": row.external_id,
                    "external_link": row.external_link,
                    "source": row.source,
                    "sync_status": row.sync_status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"events": events, "total_count": len(events)})

    except Exception as e:
        logger.error(f"❌ Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/calendar/events/{event_id}")
async def get_event(request: Request, event_id: UUID):
    """Get a specific event by ID."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT e.*, c.name as calendar_name, c.color as calendar_color
                    FROM calendar_events e
                    JOIN calendars c ON e.calendar_id = c.id
                    WHERE e.id = :id AND e.user_id = :user_id
                """),
                {"id": str(event_id), "user_id": user_id}
            )

            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Event not found")

            return JSONResponse(content={
                "id": str(row.id),
                "calendar_id": str(row.calendar_id),
                "calendar_name": row.calendar_name,
                "calendar_color": row.calendar_color,
                "title": row.title,
                "summary": row.title,
                "description": row.description,
                "location": row.location,
                "start": row.start_time.isoformat() if row.start_time else None,
                "end": row.end_time.isoformat() if row.end_time else None,
                "all_day": row.all_day,
                "recurrence_rule": row.recurrence_rule,
                "color": row.color or row.calendar_color,
                "external_id": row.external_id,
                "external_link": row.external_link,
                "source": row.source,
                "sync_status": row.sync_status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/calendar/events")
async def create_event(request: Request, data: EventCreate):
    """Create a new event. If Google is connected, also creates in Google Calendar."""
    user_id = get_user_id(request)

    # Validate times
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    try:
        # Check if Google is connected for write-through
        google_service = await get_google_calendar_service(user_id)
        google_event_id = None
        sync_status = 'local'

        # If Google connected, create event there first
        if google_service:
            event_data = {
                'title': data.title,
                'description': data.description,
                'location': data.location,
                'start_time': data.start_time,
                'end_time': data.end_time,
                'all_day': data.all_day
            }
            google_event_id = await create_google_event(google_service, event_data)
            if google_event_id:
                sync_status = 'synced'

        with engine.connect() as conn:
            # Verify calendar ownership
            check = conn.execute(
                text("SELECT id FROM calendars WHERE id = :id AND user_id = :user_id"),
                {"id": str(data.calendar_id), "user_id": user_id}
            )
            if not check.fetchone():
                raise HTTPException(status_code=404, detail="Calendar not found")

            result = conn.execute(
                text("""
                    INSERT INTO calendar_events
                    (calendar_id, user_id, title, description, location, start_time, end_time, all_day, color, source, external_id, sync_status)
                    VALUES (:calendar_id, :user_id, :title, :description, :location, :start_time, :end_time, :all_day, :color, :source, :external_id, :sync_status)
                    RETURNING id, calendar_id, title, description, location, start_time, end_time, all_day, color, source, external_id, sync_status, created_at
                """),
                {
                    "calendar_id": str(data.calendar_id),
                    "user_id": user_id,
                    "title": data.title,
                    "description": data.description,
                    "location": data.location,
                    "start_time": data.start_time,
                    "end_time": data.end_time,
                    "all_day": data.all_day,
                    "color": data.color,
                    "source": "google" if google_event_id else "local",
                    "external_id": google_event_id,
                    "sync_status": sync_status
                }
            )

            row = result.fetchone()
            conn.commit()

            logger.info(f"✅ Created event '{data.title}' for user {user_id}" + (f" (synced to Google: {google_event_id})" if google_event_id else ""))

            return JSONResponse(
                status_code=201,
                content={
                    "id": str(row.id),
                    "calendar_id": str(row.calendar_id),
                    "title": row.title,
                    "summary": row.title,
                    "description": row.description,
                    "location": row.location,
                    "start": row.start_time.isoformat() if row.start_time else None,
                    "end": row.end_time.isoformat() if row.end_time else None,
                    "all_day": row.all_day,
                    "color": row.color,
                    "source": row.source,
                    "external_id": row.external_id,
                    "sync_status": row.sync_status,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/calendar/events/{event_id}")
async def update_event(request: Request, event_id: UUID, data: EventUpdate):
    """Update an event. If event is synced to Google, also updates there."""
    user_id = get_user_id(request)

    # Validate times if both provided
    if data.start_time and data.end_time and data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    try:
        with engine.connect() as conn:
            # Verify ownership and get external_id for Google sync
            check = conn.execute(
                text("SELECT id, external_id, start_time, end_time, all_day FROM calendar_events WHERE id = :id AND user_id = :user_id"),
                {"id": str(event_id), "user_id": user_id}
            )
            existing = check.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Event not found")

            # If changing calendar, verify new calendar ownership
            if data.calendar_id:
                cal_check = conn.execute(
                    text("SELECT id FROM calendars WHERE id = :id AND user_id = :user_id"),
                    {"id": str(data.calendar_id), "user_id": user_id}
                )
                if not cal_check.fetchone():
                    raise HTTPException(status_code=404, detail="Target calendar not found")

            # Build update query dynamically
            updates = []
            params = {"id": str(event_id), "user_id": user_id}

            if data.calendar_id is not None:
                updates.append("calendar_id = :calendar_id")
                params["calendar_id"] = str(data.calendar_id)
            if data.title is not None:
                updates.append("title = :title")
                params["title"] = data.title
            if data.description is not None:
                updates.append("description = :description")
                params["description"] = data.description
            if data.location is not None:
                updates.append("location = :location")
                params["location"] = data.location
            if data.start_time is not None:
                updates.append("start_time = :start_time")
                params["start_time"] = data.start_time
            if data.end_time is not None:
                updates.append("end_time = :end_time")
                params["end_time"] = data.end_time
            if data.all_day is not None:
                updates.append("all_day = :all_day")
                params["all_day"] = data.all_day
            if data.color is not None:
                updates.append("color = :color")
                params["color"] = data.color

            if updates:
                updates.append("updated_at = NOW()")
                query = f"""
                    UPDATE calendar_events SET {', '.join(updates)}
                    WHERE id = :id AND user_id = :user_id
                    RETURNING *
                """
                result = conn.execute(text(query), params)
                row = result.fetchone()
                conn.commit()

                # If event has external_id, also update in Google
                if existing.external_id:
                    google_service = await get_google_calendar_service(user_id)
                    if google_service:
                        google_data = {
                            'title': data.title if data.title else row.title,
                            'description': data.description if data.description else row.description,
                            'location': data.location if data.location else row.location,
                            'start_time': data.start_time if data.start_time else existing.start_time,
                            'end_time': data.end_time if data.end_time else existing.end_time,
                            'all_day': data.all_day if data.all_day is not None else existing.all_day
                        }
                        await update_google_event(google_service, existing.external_id, google_data)

                return JSONResponse(content={
                    "id": str(row.id),
                    "calendar_id": str(row.calendar_id),
                    "title": row.title,
                    "summary": row.title,
                    "description": row.description,
                    "location": row.location,
                    "start": row.start_time.isoformat() if row.start_time else None,
                    "end": row.end_time.isoformat() if row.end_time else None,
                    "all_day": row.all_day,
                    "color": row.color,
                    "source": row.source,
                    "external_id": row.external_id,
                    "sync_status": row.sync_status,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"message": "No updates provided"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/calendar/events/{event_id}")
async def delete_event(request: Request, event_id: UUID):
    """Delete an event. If event is synced to Google, also deletes there."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # First get the event to check for external_id
            check = conn.execute(
                text("SELECT id, external_id FROM calendar_events WHERE id = :id AND user_id = :user_id"),
                {"id": str(event_id), "user_id": user_id}
            )
            existing = check.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Event not found")

            # Delete from database
            conn.execute(
                text("DELETE FROM calendar_events WHERE id = :id AND user_id = :user_id"),
                {"id": str(event_id), "user_id": user_id}
            )
            conn.commit()

            # If event had external_id, also delete from Google
            if existing.external_id:
                google_service = await get_google_calendar_service(user_id)
                if google_service:
                    await delete_google_event(google_service, existing.external_id)

            logger.info(f"✅ Deleted event {event_id} for user {user_id}" + (f" (also from Google: {existing.external_id})" if existing.external_id else ""))

            return JSONResponse(content={"message": "Event deleted", "id": str(event_id)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# GOOGLE CALENDAR SYNC ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/api/calendar/sync/google")
async def sync_google_calendar(request: Request):
    """
    Pull events from Google Calendar and merge with local database.
    - Creates new events from Google that don't exist locally
    - Updates local events that have changed in Google
    - Does NOT delete local events (user may have local-only events)

    Returns sync statistics and connection status.
    """
    user_id = get_user_id(request)

    try:
        # Check if Google is connected
        google_service = await get_google_calendar_service(user_id)
        if not google_service:
            return JSONResponse(content={
                "success": False,
                "google_connected": False,
                "message": "Google Calendar not connected",
                "synced": 0,
                "created": 0,
                "updated": 0
            })

        # Fetch events from Google (next 90 days)
        time_min = datetime.now(timezone.utc).isoformat()
        time_max = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()

        events_result = google_service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=250,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        google_events = events_result.get('items', [])

        with engine.connect() as conn:
            # Get or create default calendar for user
            cal_result = conn.execute(
                text("SELECT id FROM calendars WHERE user_id = :user_id AND is_default = true"),
                {"user_id": user_id}
            )
            calendar_row = cal_result.fetchone()

            if not calendar_row:
                # Create default calendar
                cal_create = conn.execute(
                    text("""
                        INSERT INTO calendars (user_id, name, color, is_default, source)
                        VALUES (:user_id, 'My Calendar', '#8E0B83', true, 'local')
                        RETURNING id
                    """),
                    {"user_id": user_id}
                )
                calendar_row = cal_create.fetchone()
                conn.commit()

            calendar_id = str(calendar_row.id)

            created_count = 0
            updated_count = 0

            for g_event in google_events:
                google_id = g_event['id']
                summary = g_event.get('summary', '(No Title)')
                description = g_event.get('description', '')
                location = g_event.get('location', '')

                # Parse start/end times
                start_data = g_event.get('start', {})
                end_data = g_event.get('end', {})

                # Check if all-day event
                all_day = 'date' in start_data and 'dateTime' not in start_data

                if all_day:
                    start_time = datetime.fromisoformat(start_data['date'])
                    end_time = datetime.fromisoformat(end_data['date'])
                else:
                    start_str = start_data.get('dateTime', start_data.get('date'))
                    end_str = end_data.get('dateTime', end_data.get('date'))
                    start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))

                # Check if event already exists locally
                existing = conn.execute(
                    text("SELECT id FROM calendar_events WHERE external_id = :external_id AND user_id = :user_id"),
                    {"external_id": google_id, "user_id": user_id}
                ).fetchone()

                if existing:
                    # Update existing event
                    conn.execute(
                        text("""
                            UPDATE calendar_events SET
                                title = :title,
                                description = :description,
                                location = :location,
                                start_time = :start_time,
                                end_time = :end_time,
                                all_day = :all_day,
                                sync_status = 'synced',
                                updated_at = NOW()
                            WHERE id = :id
                        """),
                        {
                            "id": str(existing.id),
                            "title": summary,
                            "description": description,
                            "location": location,
                            "start_time": start_time,
                            "end_time": end_time,
                            "all_day": all_day
                        }
                    )
                    updated_count += 1
                else:
                    # Create new event
                    conn.execute(
                        text("""
                            INSERT INTO calendar_events
                            (calendar_id, user_id, title, description, location, start_time, end_time, all_day, external_id, source, sync_status)
                            VALUES (:calendar_id, :user_id, :title, :description, :location, :start_time, :end_time, :all_day, :external_id, 'google', 'synced')
                        """),
                        {
                            "calendar_id": calendar_id,
                            "user_id": user_id,
                            "title": summary,
                            "description": description,
                            "location": location,
                            "start_time": start_time,
                            "end_time": end_time,
                            "all_day": all_day,
                            "external_id": google_id
                        }
                    )
                    created_count += 1

            conn.commit()

        logger.info(f"✅ Google Calendar sync for user {user_id}: {created_count} created, {updated_count} updated")

        return JSONResponse(content={
            "success": True,
            "google_connected": True,
            "message": f"Synced {len(google_events)} events from Google Calendar",
            "synced": len(google_events),
            "created": created_count,
            "updated": updated_count
        })

    except Exception as e:
        logger.error(f"❌ Error syncing Google Calendar: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/calendar/sync/status")
async def get_sync_status(request: Request):
    """Check if Google Calendar is connected for the current user."""
    user_id = get_user_id(request)

    try:
        google_service = await get_google_calendar_service(user_id)
        return JSONResponse(content={
            "google_connected": google_service is not None
        })
    except Exception as e:
        logger.error(f"❌ Error checking sync status: {e}")
        return JSONResponse(content={
            "google_connected": False
        })
