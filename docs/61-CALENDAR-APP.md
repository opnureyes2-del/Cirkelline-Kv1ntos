# Calendar App

**Version:** v1.3.6
**Last Updated:** 2025-12-17

---

## Overview

The Calendar App is a standalone calendar system that works without external connections. Events are stored in PostgreSQL. Users can optionally connect Google Calendar for two-way sync.

**Key Features:**
- Standalone mode (works without Google)
- Optional Google Calendar sync
- Month, Week, Day, Agenda views
- Monday-first weeks with ISO week numbers
- Event CRUD operations
- Multiple calendars with colors
- Mobile responsive design

---

## Architecture

### Backend

**File:** `cirkelline/endpoints/calendar.py`

### Frontend

| File | Purpose |
|------|---------|
| `hooks/useStandaloneCalendar.ts` | State management hook |
| `components/calendar/CalendarView.tsx` | Main calendar component |
| `components/calendar/views/MonthView.tsx` | Month grid view |
| `components/calendar/views/WeekView.tsx` | Week view |
| `components/calendar/views/DayView.tsx` | Day view |
| `components/calendar/views/AgendaView.tsx` | List view |
| `components/calendar/RightPanel.tsx` | Event list & details |
| `types/calendar.ts` | TypeScript types |

---

## Database Schema

### Tables

**calendars:**
```sql
CREATE TABLE calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    is_visible BOOLEAN DEFAULT true,
    source VARCHAR(50) DEFAULT 'local',        -- 'local' | 'google'
    external_id VARCHAR(255),                  -- Google calendar ID
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**calendar_events:**
```sql
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location VARCHAR(500),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    all_day BOOLEAN DEFAULT false,
    recurrence_rule VARCHAR(255),
    color VARCHAR(7),                          -- Override calendar color
    external_id VARCHAR(255),                  -- Google event ID
    external_link VARCHAR(500),                -- Link to Google event
    source VARCHAR(50) DEFAULT 'local',        -- 'local' | 'google'
    sync_status VARCHAR(50) DEFAULT 'local',   -- 'local' | 'synced' | 'pending'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX idx_calendars_user ON calendars(user_id);
CREATE INDEX idx_calendar_events_user ON calendar_events(user_id);
CREATE INDEX idx_calendar_events_calendar ON calendar_events(calendar_id);
CREATE INDEX idx_calendar_events_time ON calendar_events(start_time, end_time);
```

---

## API Endpoints

### Calendar Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/calendars` | List all calendars |
| POST | `/api/calendar/calendars` | Create calendar |
| PUT | `/api/calendar/calendars/{id}` | Update calendar |
| DELETE | `/api/calendar/calendars/{id}` | Delete calendar |

### Event Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/events` | List events (with filters) |
| GET | `/api/calendar/events/{id}` | Get event details |
| POST | `/api/calendar/events` | Create event |
| PUT | `/api/calendar/events/{id}` | Update event |
| DELETE | `/api/calendar/events/{id}` | Delete event |

### Sync Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/sync/status` | Check if Google connected |
| POST | `/api/calendar/sync/google` | Pull events from Google |

### Request/Response Examples

**Create Event:**
```typescript
// POST /api/calendar/events
{
  "calendar_id": "uuid",
  "title": "Meeting",
  "description": "Team standup",
  "location": "Conference Room A",
  "start_time": "2025-12-17T10:00:00Z",
  "end_time": "2025-12-17T11:00:00Z",
  "all_day": false,
  "color": "#FF5733"
}
```

**Event Response:**
```typescript
{
  "id": "uuid",
  "calendar_id": "uuid",
  "calendar_name": "My Calendar",
  "calendar_color": "#8E0B83",
  "title": "Meeting",
  "summary": "Meeting",           // Alias for title
  "description": "Team standup",
  "location": "Conference Room A",
  "start": "2025-12-17T10:00:00Z",
  "end": "2025-12-17T11:00:00Z",
  "start_time": "2025-12-17T10:00:00Z",
  "end_time": "2025-12-17T11:00:00Z",
  "all_day": false,
  "color": "#FF5733",
  "external_id": null,            // Google event ID if synced
  "external_link": null,
  "source": "local",
  "sync_status": "local",
  "created_at": "2025-12-17T09:00:00Z",
  "updated_at": "2025-12-17T09:00:00Z"
}
```

**List Events with Filters:**
```
GET /api/calendar/events?calendar_id=uuid&time_min=2025-12-01T00:00:00Z&time_max=2025-12-31T23:59:59Z&limit=100
```

---

## useStandaloneCalendar Hook

**File:** `cirkelline-ui/src/hooks/useStandaloneCalendar.ts`

### State

```typescript
interface UseStandaloneCalendarReturn {
  // Calendar state
  calendars: Calendar[];
  selectedCalendarIds: string[];

  // Event state
  events: CalendarEvent[];
  currentEvent: CalendarEvent | null;
  loading: boolean;
  error: string | null;

  // Google sync state
  googleConnected: boolean;
  isSyncing: boolean;
  lastSyncResult: SyncResult | null;

  // View state
  activeView: CalendarViewType;        // 'month' | 'week' | 'day' | 'agenda'
  selectedDate: Date;
  selectedEvent: CalendarEvent | null;
  rightPanelState: RightPanelState;    // 'upcoming' | 'details' | 'create'

  // ... actions
}
```

### Actions

**Calendar Actions:**
```typescript
fetchCalendars: () => Promise<void>
createCalendar: (data) => Promise<Calendar | null>
updateCalendar: (id, data) => Promise<boolean>
deleteCalendar: (id) => Promise<boolean>
toggleCalendarVisibility: (id) => void  // Local-only filter
```

**Event Actions:**
```typescript
fetchEvents: (timeMin?, timeMax?, limit?) => Promise<void>
fetchEventDetail: (eventId) => Promise<void>
createEvent: (data) => Promise<boolean>
updateEvent: (eventId, data) => Promise<boolean>
deleteEvent: (eventId) => Promise<boolean>
clearError: () => void
clearCurrentEvent: () => void
```

**Sync Actions:**
```typescript
checkSyncStatus: () => Promise<void>
syncFromGoogle: () => Promise<SyncResult | null>
```

**View Actions:**
```typescript
setActiveView: (view) => void
setSelectedDate: (date) => void
setSelectedEvent: (event) => void
setRightPanelState: (state) => void
goToToday: () => void
```

### Usage

```typescript
// In CalendarView.tsx
const {
  events,
  calendars,
  loading,
  activeView,
  selectedDate,
  setActiveView,
  setSelectedDate,
  fetchCalendars,
  fetchEvents,
  createEvent,
  googleConnected,
  syncFromGoogle,
} = useStandaloneCalendar();

// Load data on mount
useEffect(() => {
  fetchCalendars();
  fetchEvents();
}, []);

// Sync from Google (if connected)
const handleSync = async () => {
  if (googleConnected) {
    await syncFromGoogle();
  }
};
```

---

## Google Calendar Sync

### How It Works

**Standalone Mode (Default):**
- Events stored only in PostgreSQL
- No Google connection required
- Full CRUD operations work locally

**Google Sync Mode (Optional):**
- User connects Google via OAuth
- **Pull Sync:** Events fetched from Google and merged with local DB
- **Write-Through:** New events created locally AND in Google simultaneously
- **Two-Way Updates:** Updates/deletes sync both directions

### Sync Flow

```
User creates event
       ↓
Check if Google connected
       ↓
┌──────┴──────┐
│   Yes       │   No
↓             ↓
Create in     Store locally
Google first  only
       ↓
Store locally
with external_id
```

### API Implementation

**Create Event with Google Sync:**
```python
# cirkelline/endpoints/calendar.py:477
async def create_event(request: Request, data: EventCreate):
    google_service = await get_google_calendar_service(user_id)
    google_event_id = None
    sync_status = 'local'

    # If Google connected, create there first
    if google_service:
        google_event_id = await create_google_event(google_service, event_data)
        if google_event_id:
            sync_status = 'synced'

    # Then store in database
    # ... INSERT with external_id = google_event_id
```

**Pull Sync from Google:**
```python
# cirkelline/endpoints/calendar.py:723
async def sync_google_calendar(request: Request):
    # Fetch events from Google (next 90 days)
    events_result = google_service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        maxResults=250
    ).execute()

    # For each Google event:
    # - If exists locally (by external_id): UPDATE
    # - If not exists: CREATE
    # Does NOT delete local events
```

### Sync Status UI

**Desktop (ServicePanelContainer):**
- Settings dropdown with Google Sync toggle
- Green indicator when sync is enabled
- Refresh button triggers sync

**Mobile (TopBar):**
- Settings dropdown with same options
- Same toggle and indicator pattern

---

## Calendar Views

### Month View

**File:** `components/calendar/views/MonthView.tsx`

**Features:**
- 7×5 or 7×6 grid (depends on month)
- Monday-first weeks
- ISO week numbers in left column
- Event pills (max 2 visible, "+N more" overflow)
- Today highlighted with accent color circle
- Selected date with ring highlight

**Week Calculation:**
```typescript
// Adjust for Monday start (0 = Monday, 6 = Sunday)
const firstDayOfWeek = (firstDay.getDay() + 6) % 7;
```

**ISO Week Number:**
```typescript
const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};
```

**Event Pills Design:**
```tsx
<div className="flex items-center gap-1 px-1 py-0.5 rounded-sm cursor-pointer transition-colors bg-border-primary hover:bg-border-primary/80">
  <span className="text-[9px] md:text-[9px] font-medium text-light-text dark:text-dark-text truncate">
    {event.summary}
  </span>
</div>
```

### Week View

**File:** `components/calendar/views/WeekView.tsx`

**Features:**
- 7-day horizontal layout
- Time slots (hourly grid)
- Events positioned by time
- Current time indicator
- Week number in header

### Day View

**File:** `components/calendar/views/DayView.tsx`

**Features:**
- Single day with hourly grid
- Events positioned by start/end time
- All-day events section at top
- Current time indicator

### Agenda View

**File:** `components/calendar/views/AgendaView.tsx`

**Features:**
- Scrollable list of events
- Grouped by date
- Shows event details inline
- Good for quick overview

---

## Mobile Behavior

On mobile (< 768px):

1. **Header controls move to TopBar** (see `docs/60-APP-CONTAINER.md`)
2. **Panel switcher** toggles between:
   - Calendar view (grid icon)
   - Events list (list icon)
3. **View dropdown** changes Month/Week/Day/Agenda
4. **Date navigation** condensed format
5. **Settings dropdown** with Google Sync toggle

**State Sharing:**

```typescript
// page.tsx
const standaloneCalendar = useStandaloneCalendar();

// Pass to TopBar for mobile controls
calendarControls={{
  activeView: standaloneCalendar.activeView,
  setActiveView: standaloneCalendar.setActiveView,
  selectedDate: standaloneCalendar.selectedDate,
  setSelectedDate: standaloneCalendar.setSelectedDate,
  googleConnected: standaloneCalendar.googleConnected,
  googleSyncEnabled: googleSyncEnabled,
  onGoogleSyncToggle: handleGoogleSyncToggle,
  // ...
}}

// Pass to ServicePanelContainer for panel content
externalCalendarState={standaloneCalendar}
```

---

## Event Types

```typescript
// types/calendar.ts

interface CalendarEvent {
  id: string;
  calendar_id: string;
  calendar_name?: string;
  calendar_color?: string;
  title: string;
  summary: string;              // Alias for title (Google compatibility)
  description?: string;
  location?: string;
  start: string;                // ISO datetime
  end: string;                  // ISO datetime
  start_time?: string;          // Alias
  end_time?: string;            // Alias
  all_day: boolean;
  recurrence_rule?: string;
  color?: string;               // Override color
  external_id?: string;         // Google event ID
  external_link?: string;
  source: 'local' | 'google';
  sync_status: 'local' | 'synced' | 'pending';
  created_at?: string;
  updated_at?: string;
}

interface Calendar {
  id: string;
  name: string;
  color: string;
  is_default: boolean;
  is_visible: boolean;
  source: 'local' | 'google';
  external_id?: string;
  sync_enabled: boolean;
  last_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

type CalendarViewType = 'month' | 'week' | 'day' | 'agenda';
type RightPanelState = 'upcoming' | 'details' | 'create';
```

---

## Date Handling

**Important:** Always use LOCAL time for date comparisons, not UTC.

```typescript
// MonthView.tsx - getEventsForDate
const getEventsForDate = (date: Date): CalendarEvent[] => {
  // Use local date components to avoid UTC conversion issues
  const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

  return events.filter((event) => {
    const eventDate = new Date(event.start);
    // Use local date components for the event too
    const eventDateKey = `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, '0')}-${String(eventDate.getDate()).padStart(2, '0')}`;
    return eventDateKey === dateKey;
  });
};
```

---

## Error Handling

**Backend:**
```python
try:
    # ... operation
except HTTPException:
    raise  # Re-raise HTTP errors as-is
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

**Frontend:**
```typescript
try {
  const response = await authenticatedFetch(endpoint);
  // ...
} catch (err) {
  const errorMessage = err instanceof Error ? err.message : 'Operation failed';
  setError(errorMessage);
  console.error('Error:', err);
}
```

---

## Testing

### API Testing

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"opnureyes2@gmail.com","password":"RASMUS_PASSWORD_HERE"}' | jq -r '.token')

# List calendars
curl -s http://localhost:7777/api/calendar/calendars \
  -H "Authorization: Bearer $TOKEN" | jq

# Create event
curl -s -X POST http://localhost:7777/api/calendar/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "calendar_id": "YOUR_CALENDAR_UUID",
    "title": "Test Event",
    "start_time": "2025-12-17T10:00:00Z",
    "end_time": "2025-12-17T11:00:00Z"
  }' | jq

# Sync from Google
curl -s -X POST http://localhost:7777/api/calendar/sync/google \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Frontend Testing

1. Open calendar panel from sidebar
2. Create event (should auto-create default calendar)
3. Switch views (Month/Week/Day/Agenda)
4. Navigate dates
5. Toggle Google Sync (if connected)
6. Test on mobile

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Events not showing | Check `is_visible` on calendar |
| Wrong dates | Ensure local time comparisons (not UTC) |
| Google sync fails | Check OAuth connection in Google settings |
| No default calendar | Auto-created on first event |
| Mobile controls missing | Check `showCalendarControls` prop |
