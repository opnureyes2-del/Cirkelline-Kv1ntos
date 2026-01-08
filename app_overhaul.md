# Cirkelline App Overhaul Plan

**Version:** v1.3.7
**Date:** 2025-12-19
**Status:** In Progress - Calendar, Email UI, Tasks COMPLETE
**Last Updated:** 2025-12-19

---

## Vision

Transform Cirkelline's integrated apps (Calendar, Email, Tasks, Notion) from external-service-dependent panels into **standalone-first applications** that can optionally connect to external services.

### Core Principles

1. **Standalone First** - Each app works independently without requiring external connections
2. **Connect Later** - Users can import, connect, or sync with external services when ready
3. **Flexible UI** - Apps can be viewed in stacked or side-by-side layout modes
4. **Persistent Storage** - All data stored in PostgreSQL database
5. **Seamless Integration** - Chat assistant can interact with all apps regardless of mode

---

## Container Architecture

**IMPORTANT:** This is the core layout system for ALL of Cirkelline. Understanding this is critical.

### Two Container System

| Container | Location | Purpose |
|-----------|----------|---------|
| **Stacked Container** | BELOW chat | Apps open here by default (top-to-bottom layout) |
| **Side-by-Side Container** | RIGHT of chat | Multi-purpose panel (apps, admin, workflows) |

### Visual Layout

```
STACKED MODE (Default):
┌─────────────────────────────────────────────────────────────┐
│                         CHAT                                │
├─────────────────────────────────────────────────────────────┤
│                    STACKED CONTAINER                        │
│                    (App content here)                       │
└─────────────────────────────────────────────────────────────┘

SIDE-BY-SIDE MODE:
┌────────────────────────────┬────────────────────────────────┐
│                            │                                │
│           CHAT             │      SIDE-BY-SIDE CONTAINER    │
│                            │      (App/Admin/Workflows)     │
│                            │                                │
└────────────────────────────┴────────────────────────────────┘
```

### Side-by-Side Container Usage

The side-by-side container is **multi-purpose** and will display:

| Content Type | Description |
|--------------|-------------|
| **Apps** | Calendar, Email, Tasks, Notion, Notes, Documents |
| **Admin Settings** | User preferences, account settings (future) |
| **Workflows** | Workflow management, automation (future) |

### User Flow

1. User clicks **Calendar** in sidebar → Opens in **Stacked Container** (below chat)
2. User clicks **Layout Toggle** → Calendar moves to **Side-by-Side Container** (right of chat)
3. User clicks **Close** → Container closes, back to chat only

### Workspace Removal

**REMOVED:** The old "Workspace" that opened from top-right chevron is removed.
The side-by-side container replaces this functionality.

---

## Standard App Layout (Inside Containers)

**IMPORTANT:** This layout pattern is the standard for ALL apps in Cirkelline. Every app (Calendar, Email, Tasks, Notion, Notes, Documents) MUST follow this pattern.

### Panel Structure (Inside Either Container)

```
┌─────────────────────────────────────────────────────────────┐
│ FULL WIDTH BACKGROUND (absolute inset-0, z-0)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ CENTERED CONTENT (max-w-7xl mx-auto)                  │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ HEADER (single row)                             │  │  │
│  │  │ [Title] ──── [Controls Center] ──── [Actions]   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ CONTENT AREA                                    │  │  │
│  │  │ (app-specific layout)                           │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Critical CSS Requirements

```tsx
// Panel container - MUST have full-width background
<div className="relative w-full shadow-lg flex flex-col z-50">
  {/* Full width background - covers edge to edge, prevents chat showing through */}
  <div className="absolute inset-0 bg-light-bg dark:bg-dark-bg z-0" />

  {/* Centered content container */}
  <div className="relative w-full max-w-7xl mx-auto flex flex-col h-full overflow-hidden">
    {/* Header and content here */}
  </div>
</div>
```

### Header Pattern (Single Row)

Every app header follows this pattern:
```
[App Title] ──────── [Center Controls] ──────── [Action Icons]
```

Example for Calendar:
```
[Calendar] ──── [< Month Dropdown December 2025 >] ──── [Sync Layout Fullscreen Close]
```

### Z-Index Hierarchy

| Element | Z-Index |
|---------|---------|
| Support Banner | z-40 |
| Containers (Stacked/Side-by-Side) | z-50 |
| Modals | z-[60] |

---

## Implementation Order

| # | App | Current State | Target State |
|---|-----|---------------|--------------|
| 1 | **Calendar** | **COMPLETE** | Standalone + Google sync |
| 2 | **Email** | **UI COMPLETE** | Gmail required (UI done, needs features) |
| 3 | **Tasks** | **COMPLETE** | Standalone + Google Tasks sync |
| 4 | **Notion** | Notion only | Notion required (external only) |
| 5 | **Notes** | Coming soon | New standalone app |
| 6 | **Documents** | Coming soon | New standalone app |

---

## App 1: Calendar (COMPLETE)

### Features Implemented

#### Views
- **Month View** - Grid calendar with week numbers (W column on left)
- **Week View** - 7-day view with week number header
- **Day View** - Single day detail with week number in header
- **Agenda View** - Upcoming events list

#### Calendar Features
- Week starts on **Monday** (ISO 8601)
- **Week numbers** displayed on all views (ISO week numbering)
- Today highlighted with accent color border and circle
- Selected date ring indicator
- Event count badges per day

#### CRUD Operations
- Create events (via "Create Event" button)
- Read events (filtered by selected calendars)
- Update events (edit button on event cards)
- Delete events (with confirmation dialog)
- Multiple calendars support with color coding

#### UI Elements
- Single-row header: `[View Dropdown] --- [Date Navigation] --- [Actions]`
- Create Event button in events panel header (styled like header elements)
- Clickable event cards open edit modal (no inline edit/delete icons)
- Delete confirmation modal
- Compact header styling in side-by-side mode (smaller icons/padding)

#### Layout Modes
- **Stacked mode**: Calendar left (flex-1), Events right (fixed width)
- **Side-by-side mode**: Calendar top (40%), Events bottom (60%) - vertical stack

### Key Files

| File | Purpose |
|------|---------|
| `src/components/calendar/CalendarView.tsx` | Main calendar component |
| `src/components/calendar/views/MonthView.tsx` | Month grid with week numbers |
| `src/components/calendar/views/WeekView.tsx` | Week view with week header |
| `src/components/calendar/views/DayView.tsx` | Day detail view |
| `src/components/calendar/views/AgendaView.tsx` | Upcoming events list |
| `src/hooks/useStandaloneCalendar.ts` | Calendar data hook |
| `src/components/ServicePanelContainer.tsx` | Panel container |
| `cirkelline/endpoints/calendar.py` | Backend API |

### Week Number Implementation

```typescript
// ISO 8601 week number (Monday-based)
const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};
```

### Monday-First Week Calculation

```typescript
// Adjust for Monday start (Monday = 0, Sunday = 6)
const dayOfWeek = (date.getDay() + 6) % 7;
```

---

## Backend API (Calendar)

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/calendars` | List user's calendars |
| POST | `/api/calendar/calendars` | Create new calendar |
| PUT | `/api/calendar/calendars/{id}` | Update calendar |
| DELETE | `/api/calendar/calendars/{id}` | Delete calendar |
| GET | `/api/calendar/events` | List events (with date filter) |
| GET | `/api/calendar/events/{id}` | Get event details |
| POST | `/api/calendar/events` | Create event |
| PUT | `/api/calendar/events/{id}` | Update event |
| DELETE | `/api/calendar/events/{id}` | Delete event |

### Database Tables

```sql
CREATE TABLE calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    is_visible BOOLEAN DEFAULT true,
    source VARCHAR(50) DEFAULT 'local',
    external_id VARCHAR(255),
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

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
    color VARCHAR(7),
    external_id VARCHAR(255),
    external_link VARCHAR(500),
    source VARCHAR(50) DEFAULT 'local',
    sync_status VARCHAR(50) DEFAULT 'local',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## App 2: Email (UI COMPLETE)

### Current State
- Requires Gmail connection
- Shows Gmail inbox
- Can compose and send via Gmail
- **UI updated to match Calendar standard** (v1.4.0)

### UI Implementation (COMPLETE)

#### Header (Single Row)
- `[Folder Dropdown] --- [Compose Button] --- [Actions]`
- Folder dropdown: Inbox, Sent, Drafts, Trash (with icons)
- Compose button: Centered, styled like header elements
- Actions: Settings, Refresh, Layout, Fullscreen, Close

#### Settings Dropdown
- Gmail connection status (green indicator when connected)
- No toggle (Gmail required for email to work)

#### Compact Mode (Side-by-Side)
- Smaller icons: 14px instead of 16px
- Smaller padding: p-1 instead of p-1.5
- Tighter gap between icons

#### Layout Modes
- **Stacked mode**: Email list left, Detail right (horizontal)
- **Side-by-side mode**: Email list top, Detail bottom (vertical stack)

### Target State (Future)

#### Improvements
- Better email threading
- Improved compose UI
- Email templates
- Scheduled sending
- Email search

---

## App 3: Tasks (COMPLETE)

### Features Implemented

#### Core Features
- **Standalone Mode** - Works without Google connection
- **Multiple Task Lists** - Create, rename, delete lists
- **Priority Levels** - Low, Medium, High, Urgent with visual indicators
- **Due Dates** - Set and track due dates
- **Task Notes** - Rich notes/description for each task
- **Show/Hide Completed** - Toggle visibility of completed tasks
- **Google Tasks Sync** - Optional sync (pull + write-through)
- **AI Agent Tools** - CirkellineTasksTools for conversation-based management

#### UI Elements
- Board view with scrollable columns per list
- Settings dropdown with section labels
- List selector in header (side-by-side mode)
- Consistent button styling across views
- Priority flag icons with color coding
- Checkbox toggle for completion
- Strikethrough text for completed tasks

#### Layout Modes
- **Stacked mode**: Horizontal board scroll
- **Side-by-side mode**: Full-width single list view with header selector

### Key Files

| File | Purpose |
|------|---------|
| `src/components/TasksPanel.tsx` | Entry point, props forwarding |
| `src/components/TasksBoardView.tsx` | Board/list view with layout modes |
| `src/components/TaskColumn.tsx` | Individual list column |
| `src/components/TaskCard.tsx` | Task card with priority |
| `src/hooks/useStandaloneTasks.ts` | Tasks data hook (499 lines) |
| `src/types/standaloneTasks.ts` | TypeScript types (96 lines) |
| `cirkelline/endpoints/tasks.py` | Backend API (935 lines) |
| `cirkelline/tools/tasks_tools.py` | AI agent tools (651 lines) |

### Database Schema

```sql
CREATE TABLE task_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    source VARCHAR(50) DEFAULT 'local',
    external_id VARCHAR(255),
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    notes TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(20) DEFAULT 'medium',
    position INTEGER DEFAULT 0,
    parent_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    source VARCHAR(50) DEFAULT 'local',
    sync_status VARCHAR(50) DEFAULT 'local',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints (13 total)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/standalone-tasks/lists` | List all task lists |
| POST | `/api/standalone-tasks/lists` | Create task list |
| GET | `/api/standalone-tasks/lists/{id}` | Get task list |
| PUT | `/api/standalone-tasks/lists/{id}` | Update task list |
| DELETE | `/api/standalone-tasks/lists/{id}` | Delete task list |
| GET | `/api/standalone-tasks/lists/{id}/tasks` | Get tasks in list |
| POST | `/api/standalone-tasks/lists/{id}/tasks` | Create task |
| GET | `/api/standalone-tasks/tasks/{id}` | Get task |
| PUT | `/api/standalone-tasks/tasks/{id}` | Update task |
| DELETE | `/api/standalone-tasks/tasks/{id}` | Delete task |
| POST | `/api/standalone-tasks/tasks/{id}/complete` | Toggle completion |
| GET | `/api/standalone-tasks/sync/status` | Check Google connection |
| POST | `/api/standalone-tasks/sync/google/pull` | Pull from Google |

---

## App 4: Notion

### Current State
- Requires Notion connection
- Shows Notion databases
- Can view and edit pages

### Target State

#### Standalone Features
- **None** - Notion requires external service
- Show "Connect Notion" prompt when not connected

#### UI Requirements (Must Follow Standard Layout)
- Single-row header: `[Notion] --- [Database/Page selector] --- [Actions]`
- Full-width background layer

---

## App 5: Notes (New)

### Target State

#### Standalone Features
- Create/edit/delete notes
- Rich text editor (Markdown support)
- Folders/organization
- Tags
- Search within notes
- Pin important notes

#### UI Requirements (Must Follow Standard Layout)
- Single-row header: `[Notes] --- [Folder selector] --- [Actions]`
- Full-width background layer

---

## App 6: Documents (New)

### Target State

#### Standalone Features
- Upload and store documents
- PDF viewer
- Document organization (folders)
- Search within documents

#### UI Requirements (Must Follow Standard Layout)
- Single-row header: `[Documents] --- [Folder selector] --- [Actions]`
- Full-width background layer

---

## Shared Components

### Layout Mode Toggle
```tsx
// layoutMode state: 'stacked' | 'side-by-side'
<button onClick={() => setLayoutMode(mode === 'stacked' ? 'side-by-side' : 'stacked')}>
  {layoutMode === 'stacked' ? <Columns2 /> : <Square />}
</button>
```

### Week Number Helper (Reusable)
```typescript
// Use in any app that shows dates
export const getWeekNumber = (date: Date): number => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const dayNum = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
};
```

### Monday-First Helper (Reusable)
```typescript
// Get day index where Monday = 0, Sunday = 6
export const getMondayBasedDayIndex = (date: Date): number => {
  return (date.getDay() + 6) % 7;
};
```

---

## Current Progress

| App | Status | Notes |
|-----|--------|-------|
| Calendar | **COMPLETE** | Full CRUD, week numbers, Monday-first, clickable events open modal |
| Email | **UI COMPLETE** | Single-row header, folder dropdown, layout modes, compact styling |
| Tasks | **COMPLETE** | Standalone + Google sync, priority levels, AI tools, settings dropdown |
| Notion | Existing | Needs layout update to match standard |
| Notes | Not Started | New app |
| Documents | Not Started | New app |

---

## Success Criteria

- [x] Calendar works fully standalone
- [x] User can create/edit/delete events
- [x] Week numbers displayed on all calendar views
- [x] Weeks start on Monday
- [x] Full-width background (no chat showing through)
- [x] Single-row header layout
- [x] Stacked/side-by-side layout modes
- [x] Clickable events open edit modal (all views)
- [x] Compact header styling in side-by-side mode
- [x] App panel borders (bottom in stacked, right in side-by-side)
- [x] Email follows standard layout
- [x] Email folder dropdown in header
- [x] Email layout adapts to container mode
- [x] Tasks app implemented (v1.3.7)
- [x] Tasks works fully standalone
- [x] Tasks has Google Tasks sync
- [x] Tasks has priority levels
- [x] Tasks has AI agent integration
- [ ] Notion follows standard layout
- [ ] Notes app implemented
- [ ] Documents app implemented

---

## Google Calendar Sync Architecture (CRITICAL)

### ONE System - NOT Two

**IMPORTANT:** There must be ONE unified calendar system, not two separate systems.

### The Problem (What Was Wrong)

Before the fix, there were TWO separate systems:

| Source | Where events went | Problem |
|--------|-------------------|---------|
| AI (Cirkelline) | → Google Calendar DIRECTLY via AGNO tools | Bypassed local DB |
| UI Panel | → Local Database → optional sync to Google | Different data source |

This meant the AI and UI were NOT using the same data!

### The Solution (Unified System)

**ONE source of truth:** Our local database (`calendars` + `calendar_events` tables)

| Source | Flow | Result |
|--------|------|--------|
| UI creates event | → Local DB → (if sync enabled) → Google | Stored locally |
| AI creates event | → Local DB → (if sync enabled) → Google | Stored locally |
| Google sync | → Pulls from Google → Merges to Local DB | Unified data |

### Implementation Requirements

1. **AI Tools MUST use `/api/calendar/*` endpoints** - NOT AGNO's GoogleCalendarTools
2. **Create custom AI tools** that call our standalone calendar API
3. **All calendar operations go through local database FIRST**
4. **Google sync is OPTIONAL** - user can enable/disable via settings toggle

### Sync Behavior

| Direction | When | Delay |
|-----------|------|-------|
| **Cirkelline → Google** | On create/update/delete (if sync enabled) | Instant |
| **Google → Cirkelline** | On panel open + sync button (if sync enabled) | Instant |

### User Settings

In Calendar header (info icon dropdown):
- **"Sync with Google Calendar"** toggle
- OFF by default
- Requires Google connected first (Profile → Integrations)
- When enabled: bidirectional sync
- When disabled: local-only mode

### Files Involved

| File | Purpose |
|------|---------|
| `cirkelline/endpoints/calendar.py` | Backend API (CRUD + Google sync) |
| `src/hooks/useStandaloneCalendar.ts` | Frontend hook (sync status, sync functions) |
| `cirkelline/tools/calendar_tools.py` | **NEW** - AI tools for calendar (uses our API) |

---

## Next Steps

1. ~~Calendar standalone implementation~~ COMPLETE
2. ~~Container architecture (stacked/side-by-side)~~ COMPLETE
3. ~~Google sync endpoints~~ COMPLETE (POST /api/calendar/sync/google, GET /api/calendar/sync/status)
4. ~~AI calendar tools using local DB~~ COMPLETE (CirkellineCalendarTools v1.3.4)
5. ~~Update Email to follow standard layout pattern~~ COMPLETE (v1.4.0)
6. ~~Compact header styling for side-by-side mode~~ COMPLETE
7. ~~Clickable events open modal (all views)~~ COMPLETE
8. ~~App panel borders~~ COMPLETE
9. ~~Implement Tasks app (standalone + Google sync)~~ COMPLETE (v1.3.7)
10. Update Notion to follow standard layout pattern
11. Implement Notes app
12. Implement Documents app

---

## Technical Notes

### Text Sizes (Consistent across apps)
- Headers: `text-sm font-bold`
- Day names: `text-[9px] md:text-xs`
- Day numbers: `text-[9px] md:text-xs`
- Week numbers: `text-[9px] md:text-xs font-bold text-accent opacity-50`
- Event text: `text-[10px]`
- Event count badges: `text-[8px] md:text-[10px]`

### Color Usage
- Accent color: `var(--accent)` / `text-accent` / `bg-accent`
- Today highlight: `bg-accent/5 dark:bg-accent/10` + `border: 2px solid var(--accent)`
- Week numbers: `text-accent opacity-50`
