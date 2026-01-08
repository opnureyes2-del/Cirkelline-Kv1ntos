"""
Google Calendar Integration Endpoints
======================================
Handles Google Calendar operations (list, detail, create, update, delete events).
"""

from fastapi import APIRouter, Request, HTTPException

from cirkelline.config import logger
from cirkelline.integrations.google.google_oauth import get_user_google_credentials

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# CALENDAR LIST EVENTS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/google/calendar/events")
async def get_calendar_events(
    request: Request,
    time_min: str = None,
    time_max: str = None,
    max_results: int = 20
):
    """
    Get calendar events for user

    Query params:
    - time_min: Start time (ISO 8601 format, default: now)
    - time_max: End time (ISO 8601 format, default: 7 days from now)
    - max_results: Max number of events (default 20, max 100)

    Returns list of calendar events
    """
    try:
        from datetime import datetime, timedelta, timezone

        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Set default time range if not provided
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        if not time_max:
            time_max = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        # Limit max_results
        max_results = min(max_results, 100)

        # Build Calendar service
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=google_creds)

        # Get events
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Format events for frontend
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            formatted_events.append({
                'id': event['id'],
                'summary': event.get('summary', '(No Title)'),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'start': start,
                'end': end,
                'attendees': event.get('attendees', []),
                'html_link': event.get('htmlLink', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', '')
            })

        return {
            'events': formatted_events,
            'total_count': len(formatted_events)
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get calendar events error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

logger.info("✅ Google calendar events list endpoint configured")

@router.get("/api/google/calendar/events/{event_id}")
async def get_calendar_event_detail(request: Request, event_id: str):
    """
    Get full details of a specific calendar event
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Calendar service
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=google_creds)

        # Get event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))

        return {
            'id': event['id'],
            'summary': event.get('summary', '(No Title)'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start': start,
            'end': end,
            'attendees': event.get('attendees', []),
            'organizer': event.get('organizer', {}),
            'html_link': event.get('htmlLink', ''),
            'created': event.get('created', ''),
            'updated': event.get('updated', ''),
            'status': event.get('status', ''),
            'recurrence': event.get('recurrence', [])
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get calendar event detail error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch event: {str(e)}")

logger.info("✅ Google calendar event detail endpoint configured")

@router.post("/api/google/calendar/events")
async def create_calendar_event(request: Request):
    """
    Create a new calendar event

    Request body:
    {
        "summary": "Event title",
        "description": "Event description",
        "location": "Event location",
        "start": "2025-10-27T14:00:00+01:00",  // ISO 8601 format
        "end": "2025-10-27T15:00:00+01:00",
        "attendees": ["email@example.com"]  // optional
    }
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Parse request body
        data = await request.json()
        summary = data.get('summary')
        description = data.get('description', '')
        location = data.get('location', '')
        start_time = data.get('start')
        end_time = data.get('end')
        attendees = data.get('attendees', [])

        if not summary:
            raise HTTPException(status_code=400, detail="Event summary required")
        if not start_time or not end_time:
            raise HTTPException(status_code=400, detail="Start and end times required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Calendar service
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=google_creds)

        # Prepare event data
        event = {
            'summary': summary,
            'description': description,
            'location': location,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time}
        }

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        # Create event
        created_event = service.events().insert(calendarId='primary', body=event).execute()

        return {
            'success': True,
            'message': 'Event created successfully',
            'event_id': created_event['id'],
            'html_link': created_event.get('htmlLink', '')
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Create calendar event error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

logger.info("✅ Google create calendar event endpoint configured")

@router.put("/api/google/calendar/events/{event_id}")
async def update_calendar_event(request: Request, event_id: str):
    """
    Update an existing calendar event

    Request body: Same as create event
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Parse request body
        data = await request.json()

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Calendar service
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=google_creds)

        # Get existing event
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update fields
        if 'summary' in data:
            event['summary'] = data['summary']
        if 'description' in data:
            event['description'] = data['description']
        if 'location' in data:
            event['location'] = data['location']
        if 'start' in data:
            event['start'] = {'dateTime': data['start']}
        if 'end' in data:
            event['end'] = {'dateTime': data['end']}
        if 'attendees' in data:
            event['attendees'] = [{'email': email} for email in data['attendees']]

        # Update event
        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event
        ).execute()

        return {
            'success': True,
            'message': 'Event updated successfully',
            'event_id': updated_event['id'],
            'html_link': updated_event.get('htmlLink', '')
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Update calendar event error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update event: {str(e)}")

logger.info("✅ Google update calendar event endpoint configured")

@router.delete("/api/google/calendar/events/{event_id}")
async def delete_calendar_event(request: Request, event_id: str):
    """
    Delete a calendar event
    """
    try:
        # Get user_id from JWT middleware
        user_id = getattr(request.state, 'user_id', None)
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Check if user has Google connected
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=403, detail="Google account not connected")

        # Build Calendar service
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=google_creds)

        # Delete event
        service.events().delete(calendarId='primary', eventId=event_id).execute()

        return {
            'success': True,
            'message': 'Event deleted successfully'
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Delete calendar event error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")

logger.info("✅ Google delete calendar event endpoint configured")


logger.info("✅ Calendar integration endpoints loaded")
