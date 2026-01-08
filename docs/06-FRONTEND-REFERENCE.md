# FRONTEND REFERENCE

**Last Updated:** 2025-11-30
**Current Version:** v1.2.33

---

## Table of Contents
- [Frontend Structure](#frontend-structure)
- [Directory Organization](#directory-organization)
- [Key Components](#key-components)
  - [TopBar](#topbartsx)
  - [ChatInput](#chatinputtsx)
  - [GooglePanelContainer](#googlepanelcontainertsx--new-v121) ⭐ NEW
  - [Sidebar](#sidebar-component)
- [Pages](#pages)
- [State Management](#state-management)
- [API Integration](#api-integration)
- [Hooks Documentation](#hooks-documentation)
- [Authentication Context](#authentication-context)
- [Session Management](#session-management)
- [Profile System](#profile-system-v123) ⭐ NEW
- [Icon System](#icon-system-v122)
- [Google Services Integration](#google-services-integration-v121)
- [Quick Reference](#quick-reference)

---

## Frontend Structure

### Technology Stack

```
Framework:
├── Next.js 14 (App Router)
├── React 18
└── TypeScript

State Management:
├── Zustand (Global state)
└── React Context (Auth)

Styling:
├── TailwindCSS
├── CSS Variables (dynamic theming)
└── Custom UI components

Communication:
├── Server-Sent Events (SSE)
├── Fetch API
└── FormData for multipart uploads

Routing:
├── Next.js App Router
└── nuqs (URL state management)
```

### Project Root

```
/home/eenvy/Desktop/cirkelline/cirkelline-ui/
├── src/
│   ├── api/                   # API client functions
│   ├── app/                   # Next.js pages (App Router)
│   ├── components/            # React components
│   ├── contexts/              # React contexts
│   ├── hooks/                 # Custom React hooks
│   ├── types/                 # TypeScript types
│   ├── lib/                   # Utility functions
│   ├── config/                # Configuration files
│   └── store.ts               # Zustand store
├── public/                    # Static assets
├── package.json               # Dependencies
└── next.config.js             # Next.js configuration
```

---

## Directory Organization

### `/src/api/` - API Client

**Files:**
- `routes.ts` - API endpoint definitions
- `os.ts` - API client functions

**routes.ts** (18 lines):
```typescript
export const APIRoutes = {
  GetAgents: (agentOSUrl: string) => `${agentOSUrl}/agents`,
  AgentRun: (agentOSUrl: string) => `${agentOSUrl}/agents/{agent_id}/runs`,
  Status: (agentOSUrl: string) => `${agentOSUrl}/health`,
  GetSessions: (agentOSUrl: string) => `${agentOSUrl}/sessions`,
  GetSession: (agentOSUrl: string, sessionId: string) =>
    `${agentOSUrl}/sessions/${sessionId}/runs`,
  DeleteSession: (agentOSUrl: string, sessionId: string) =>
    `${agentOSUrl}/sessions/${sessionId}`,
  GetTeams: (agentOSUrl: string) => `${agentOSUrl}/teams`,
  TeamRun: (agentOSUrl: string, teamId: string) =>
    `${agentOSUrl}/teams/${teamId}/runs`,
  DeleteTeamSession: (agentOSUrl: string, teamId: string, sessionId: string) =>
    `${agentOSUrl}/v1//teams/${teamId}/sessions/${sessionId}`
}
```

### `/src/app/` - Next.js Pages

**Structure:**
```
app/
├── page.tsx                   # Home page (chat interface)
├── layout.tsx                 # Root layout
├── login/
│   └── page.tsx               # Login page
├── signup/
│   └── page.tsx               # Signup page
├── memories/
│   └── page.tsx               # Memories Viewer page
└── api/
    └── auth/
        ├── login/route.ts     # Login API route (proxy)
        └── signup/route.ts    # Signup API route (proxy)
```

**page.tsx** - Main Chat Interface:
- Renders chat messages
- Handles file uploads
- Manages session state
- Coordinates all hooks

**layout.tsx** - Root Layout:
```typescript
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
```

### `/src/components/` - React Components

**Key Components:**
```
components/
├── TopBar.tsx                 # Header with auth controls + Google icons
├── ThemeToggle.tsx            # Dark/light theme switch
├── GooglePanelContainer.tsx   # Unified slide-down panel (NEW v1.2.1)
├── EmailPanel.tsx             # Gmail UI panel (deprecated - replaced by container)
├── CalendarPanel.tsx          # Calendar UI panel (deprecated - replaced by container)
├── GoogleConnect.tsx          # Google OAuth connect button (v1.2.0)
├── GoogleIndicator.tsx        # Google connection status indicator (v1.2.0)
├── ProfileModal.tsx           # User profile with Google settings (v1.2.0)
├── chat/
│   ├── ChatArea/
│   │   ├── ChatArea.tsx       # Main chat container
│   │   ├── ChatInput/
│   │   │   ├── ChatInput.tsx  # FIXED at bottom input (v1.2.1)
│   │   │   ├── FilePreview.tsx
│   │   │   └── FileUploadDropdown.tsx
│   │   └── MessageArea.tsx    # Scrollable messages
│   └── Sidebar/
│       ├── Sidebar.tsx        # Session sidebar
│       └── Sessions/
│           ├── SessionList.tsx  # List of sessions
│           └── SessionItem.tsx  # Individual session
└── ui/                        # Reusable UI components
    ├── button.tsx
    ├── textarea.tsx
    ├── select.tsx
    ├── tooltip/
    ├── icon/
    └── typography/
```

**Component Hierarchy:**
```
page.tsx (Main)
├── Sidebar (FIXED left)
│   └── SessionList
│       └── SessionItem[]
├── TopBar (FIXED top)
│   ├── ThemeToggle
│   ├── Google Icons (Email/Calendar)
│   └── UserDropdown
├── Content Wrapper (FIXED below TopBar, responsive to sidebar)
│   ├── GooglePanelContainer (slides down, pushes chat)
│   │   ├── Email Panel Content (list/detail views)
│   │   └── Calendar Panel Content (list/detail views)
│   └── ChatArea (height adjusts dynamically)
│       └── MessageArea (scrollable with padding-bottom)
└── ChatInput (FIXED at viewport bottom, NEVER moves)
    ├── FilePreview
    ├── FileUploadDropdown
    └── Send Button
```

### `/src/contexts/` - React Contexts

**AuthContext.tsx** (153 lines):
- User authentication state
- JWT token management
- Anonymous user handling
- Login/logout functions

```typescript
interface AuthContextType {
  user: User | null
  login: (token: string) => void
  register: (token: string) => void
  logout: () => void
  getUserId: () => string
}
```

### `/src/hooks/` - Custom Hooks

**Key Hooks:**
```
hooks/
├── useAIStreamHandler.tsx     # Main SSE streaming logic (467 lines)
├── useAIResponseStream.tsx    # Low-level SSE handling
├── useSessionLoader.tsx       # Load sessions and history (224 lines)
├── useSidebar.ts              # Sidebar state management
├── useFileUpload.ts           # File upload handling
├── useChatActions.ts          # Chat message actions
├── useEmailData.tsx           # Email panel data management (NEW v1.1.30)
└── useCalendarData.tsx        # Calendar panel data management (NEW v1.1.30)
```

### `/src/types/` - TypeScript Types

**Core Type Files:**
```
types/
├── os.ts                      # Core chat/session types
├── email.ts                   # Email data types (NEW v1.1.30)
└── calendar.ts                # Calendar event types (NEW v1.1.30)
```

**os.ts** - Core type definitions:
```typescript
export interface ChatMessage {
  role: 'user' | 'agent'
  content: string
  tool_calls?: ToolCall[]
  extra_data?: ExtraData
  images?: string[]
  videos?: string[]
  audio?: string[]
  response_audio?: ResponseAudio
  streamingError?: boolean
  created_at: number
}

export interface SessionEntry {
  session_id: string
  session_name?: string
  created_at: number
  updated_at?: number
}

export interface AgentDetails {
  agent_id: string
  name: string
  description: string
}

export interface TeamDetails {
  team_id: string
  name: string
  description: string
  members: AgentDetails[]
}
```

---

## Key Components

### TopBar.tsx

**Purpose:** Fixed header with authentication controls and Google Services access

**Location:** `/src/components/TopBar.tsx`

**Positioning:**
```typescript
className="fixed top-0 right-0 h-16 ${isCollapsed ? 'left-16' : 'left-64'}"
style={{
  left: typeof window !== 'undefined' && window.innerWidth >= 768
    ? (isCollapsed ? '4rem' : '16rem')
    : '0'
}}
```

**Features:**
- Theme toggle (dark/light)
- Google Email icon (opens/closes email panel)
- Google Calendar icon (opens/closes calendar panel)
- User dropdown with profile
- Login/signup buttons (anonymous)
- Logout button (authenticated)

**Props (v1.2.1):**
```typescript
interface TopBarProps {
  onNotesToggle?: () => void
  openPanel?: PanelType  // 'email' | 'calendar' | null
  onPanelChange?: (panel: PanelType) => void
}
```

**User States:**
```typescript
if (user?.isAnonymous) {
  // Show: Login | Signup buttons
} else {
  // Show: User name + Logout button
}

// Google icons only visible if connected
if (googleConnected) {
  // Show: Email icon + Calendar icon
}
```

**Google Connection Check:**
```typescript
const checkGoogleConnection = async () => {
  const token = localStorage.getItem('token')
  const response = await fetch(`${apiUrl}/api/oauth/google/status`, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const data = await response.json()
  setGoogleConnected(data.connected)
}
```

### ChatInput.tsx

**Purpose:** FIXED message input at viewport bottom (NEVER moves!)

**Location:** `/src/components/chat/ChatArea/ChatInput/ChatInput.tsx`

**Key Change (v1.2.1):**
- **CRITICAL:** Input is now `position: fixed` at viewport bottom
- **No longer moves** when GooglePanelContainer opens/closes
- **Always visible** at bottom of screen

**Positioning:**
```typescript
className={`
  fixed bottom-0 right-0
  ${sidebarCollapsed ? 'left-16' : 'left-64'}
  md:left-auto
  border-t border-border-primary
  bg-light-surface dark:bg-dark-surface
  z-20
  transition-all duration-300 ease-in-out
`}
style={{
  left: typeof window !== 'undefined' && window.innerWidth >= 768
    ? (sidebarCollapsed ? '4rem' : '16rem')
    : '0'
}}
```

**Sidebar State Monitoring:**
```typescript
const [sidebarCollapsed, setSidebarCollapsed] = useState(true)

useEffect(() => {
  const checkSidebar = () => {
    const collapsed = localStorage.getItem('sidebarCollapsed') === 'true'
    setSidebarCollapsed(collapsed)
  }
  checkSidebar()
  window.addEventListener('storage', checkSidebar)
  return () => window.removeEventListener('storage', checkSidebar)
}, [])
```

**Features:**
- **Deep Research Mode Toggle** (v1.2.24 - NEW!)
- Textarea with auto-resize
- File drag-and-drop
- File upload to `/api/knowledge/upload`

**Deep Research Mode Toggle (v1.2.24):**

**Purpose:** User-controlled research flexibility - choose between Quick Search (fast, direct) and Deep Research (comprehensive, team-based)

**Location:** Above message input (lines 333-368)

**State Management:**
```typescript
// Line 31: Toggle state
const [deepResearch, setDeepResearch] = useState(false)

// Lines 89-109: Load state from session on mount
useEffect(() => {
  if (sessionId) {
    const token = localStorage.getItem('token')
    if (!token) return

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
    fetch(`${apiUrl}/api/sessions/${sessionId}/state`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setDeepResearch(data.deep_research || false)
      })
      .catch(err => console.error('Failed to load session state:', err))
  } else {
    // New session - reset to default (false)
    setDeepResearch(false)
  }
}, [sessionId])
```

**Form Submission (Line 239):**
```typescript
formData.append('deep_research', deepResearch.toString())
```

**UI Implementation (Lines 333-368):**
```typescript
<div className="mb-3 flex items-center gap-2 px-1">
  <TooltipProvider>
    <Tooltip>
      <TooltipTrigger asChild>
        <label className="flex items-center gap-2 cursor-pointer group">
          <div className="relative">
            <input
              type="checkbox"
              checked={deepResearch}
              onChange={(e) => setDeepResearch(e.target.checked)}
              disabled={isDisabled}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-light-text/20 dark:bg-dark-text/20 rounded-full peer peer-checked:bg-accent-start ...">
            </div>
          </div>
          <span className="text-sm font-medium">Deep Research</span>
          {deepResearch && (
            <motion.span className="text-xs font-semibold text-accent-start bg-accent-start/10 px-2 py-0.5 rounded-full">
              ON
            </motion.span>
          )}
        </label>
      </TooltipTrigger>
      <TooltipContent>
        <p>{deepResearch
          ? 'Deep Research mode active - uses Research Team for comprehensive analysis'
          : 'Quick Search mode - uses built-in Google Search for fast answers'
        }</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
</div>
```

**Visual States:**

1. **Quick Search Mode (Default - Toggle OFF):**
   - Toggle switch: light gray background
   - NO "ON" badge visible
   - Tooltip: "Quick Search mode - uses built-in Google Search for fast answers"

2. **Deep Research Mode (Toggle ON):**
   - Toggle switch: accent color background (bg-accent-start)
   - "ON" badge appears next to label (animated with framer-motion)
   - Tooltip: "Deep Research mode active - uses Research Team for comprehensive analysis"

**Behavior:**
- State persists across messages in same session (stored in session_state on backend)
- State resets to `false` when starting new session
- Toggle disabled when no agent/team selected (`isDisabled`)
- Smooth animations on state change (framer-motion)

**Related Files:**
- Backend: `/home/eenvy/Desktop/cirkelline/my_os.py` (mode context injection)
- Documentation: [docs/08-FEATURES.md#deep-research-mode](./08-FEATURES.md#deep-research-mode)
- Send button with dynamic icon color
- Loading states
- Knowledge base upload button

**File Upload Flow:**
```typescript
1. User drops file
2. Upload to /api/knowledge/upload with JWT
3. Show success toast
4. Send message: "I uploaded a file about X"
```

**Why Fixed Positioning?**
- Panel slides down from top → pushes chat area down
- If input was relative → would "jump" when panel opens/closes
- Fixed position → stays at viewport bottom, smooth UX

### GooglePanelContainer.tsx ⭐ NEW v1.2.1

**Purpose:** Unified slide-down panel for Gmail and Google Calendar

**Location:** `/src/components/GooglePanelContainer.tsx`

**Design Philosophy:**
- Single container that switches content (Email ↔ Calendar)
- Stays mounted during panel type changes (smooth transitions)
- Slides down from below TopBar
- Pushes chat area down (NOT overlay)
- Takes 25% of available viewport height

**Props:**
```typescript
interface GooglePanelContainerProps {
  openPanel: 'email' | 'calendar' | null
  onClose: () => void
}
```

**Positioning Architecture:**
```typescript
// Panel is NOT fixed - it's in document flow
// Positioned INSIDE the content wrapper
<motion.div
  initial={{ height: 0, opacity: 0 }}
  animate={{ height: 'calc((100vh - 64px) * 0.25)', opacity: 1 }}
  exit={{ height: 0, opacity: 0 }}
  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
  className="
    relative
    w-full
    bg-light-surface dark:bg-dark-surface
    shadow-lg
    overflow-hidden
    flex flex-col
    border-b border-gray-200 dark:border-gray-700
  "
>
```

**Key Features:**

1. **Height-Based Animation:**
   - Animate `height` from 0 to 25% (NOT y-transform)
   - Smooth slide-down/slide-up effect
   - Spring animation for natural feel

2. **Content Switching:**
   - No remounting when switching email ↔ calendar
   - Only content changes, container stays
   - Prevents jarring animations

3. **Data Loading:**
   ```typescript
   useEffect(() => {
     if (openPanel === 'email') {
       emailData.fetchEmails(20)
       setEmailView('list')
     } else if (openPanel === 'calendar') {
       calendarData.fetchEvents()
       setCalendarView('list')
     }
   }, [openPanel])
   ```

4. **View Management:**
   - Email views: `'list' | 'detail' | 'compose' | 'reply'`
   - Calendar views: `'list' | 'detail' | 'create' | 'edit'`
   - Currently only list and detail views implemented

5. **Content Layout:**
   ```typescript
   <div className="w-full max-w-3xl mx-auto flex flex-col h-full overflow-y-auto">
     {/* Header with back button, title, close button */}
     {/* Error display if needed */}
     {/* Content area with loading spinner or list/detail view */}
   </div>
   ```

**Email Panel Content:**
- List view: Shows inbox (20 most recent emails)
- Detail view: Shows full email with sender, recipient, date, body
- Unread indicator (blue dot)
- Click email → fetch details → show detail view

**Calendar Panel Content:**
- List view: Shows upcoming events
- Detail view: Shows event details (summary, description, location, time)
- Click event → fetch details → show detail view

**Why This Approach?**
1. **Smooth UX:** Single container = no flashing during panel switches
2. **Performance:** Component stays mounted, only content changes
3. **Layout Stability:** Predictable positioning, no horizontal scroll
4. **Responsive:** Full-width layout matches chat interface

**Integration with page.tsx:**
```typescript
// Content wrapper positioned BELOW TopBar
<div
  className={`
    fixed top-16 right-0
    ${isCollapsed ? 'left-16' : 'left-64'}
    md:left-auto
    transition-all duration-300 ease-in-out
  `}
>
  {/* Panel in document flow */}
  <GooglePanelContainer
    openPanel={openPanel}
    onClose={() => setOpenPanel(null)}
  />

  {/* Chat area height adjusts dynamically */}
  <div
    style={{
      height: openPanel
        ? 'calc(100vh - 64px - (100vh - 64px) * 0.25)'  // 75% when panel open
        : 'calc(100vh - 64px)',                           // 100% when closed
      transition: 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
    }}
  >
    <ChatArea />
  </div>
</div>
```

**Page Layout Architecture (v1.2.1):**
```
┌─────────────────────────────────────────────┐
│ TopBar (FIXED: top-0, height: 64px)       │ ← z-30
├─────────────────────────────────────────────┤
│ Content Wrapper (FIXED: top-16, responsive) │
│ ┌─────────────────────────────────────────┐│
│ │ GooglePanelContainer (animated height)  ││
│ │ - Slides down from 0 to 25%             ││
│ │ - In document flow                      ││
│ └─────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────┐│
│ │ ChatArea (dynamic height)               ││
│ │ - 100% when panel closed                ││
│ │ - 75% when panel open                   ││
│ │ - Smooth transition                     ││
│ │   ┌─────────────────────────────────┐   ││
│ │   │ MessageArea (scrollable)        │   ││
│ │   │ - padding-bottom: 8rem          │   ││
│ │   └─────────────────────────────────┘   ││
│ └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│ ChatInput (FIXED: bottom-0)                 │ ← z-20
└─────────────────────────────────────────────┘
```

**Critical Implementation Details:**

1. **No Margins on Panel:** Panel is full-width, wrapper handles positioning
2. **Height Calculation:** Uses `calc()` for precise 25% of available space
3. **Smooth Transitions:** CSS transition on chat area height
4. **Z-Index Layering:** TopBar (z-30) > ChatInput (z-20) > Content
5. **Responsive Positioning:** Adjusts left offset based on sidebar state

**Deprecated Components:**
- `EmailPanel.tsx` - Replaced by GooglePanelContainer
- `CalendarPanel.tsx` - Replaced by GooglePanelContainer

These old components used fixed positioning and overlaid content, causing:
- Content jumping
- Horizontal scroll issues
- Layout instability

The new GooglePanelContainer fixes all these issues with proper document flow positioning.

### Sidebar Component

**Purpose:** Display user's sessions

**Features:**
- New Chat button
- Session list (sorted by date)
- Delete session
- Load session on click

**Session Loading:**
```typescript
// On mount
useEffect(() => {
  getSessions({
    entityType: 'team',
    teamId: 'cirkelline',
    dbId: 'cirkelline-v1'
  })
}, [teamId, getUserId])
```

### MessageBubble.tsx

**Purpose:** Display individual message

**Features:**
- User/agent role styling
- Markdown rendering
- Tool call display
- Reasoning steps
- File attachments
- Timestamps

**Message Types:**
```typescript
if (role === 'user') {
  // Blue bubble, right-aligned
} else {
  // Gray bubble, left-aligned
  // Show tool calls
  // Show reasoning steps
}
```

---

## Google Integration Components (NEW v1.1.30)

### EmailPanel.tsx

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/EmailPanel.tsx` (430 lines)

**Purpose:** Full-featured Gmail UI panel that slides down from TopBar

**Features:**
- **List View:** Latest 20 emails with sender, subject, snippet, unread indicator
- **Detail View:** Full email display (from, to, subject, date, body HTML/text)
- **Compose View:** Send new emails (to, subject, body)
- **Reply View:** Reply to emails
- **Actions:** Archive, delete emails
- **Slide-down Animation:** Framer Motion spring physics
- **Responsive Layout:** Adjusts to sidebar state (collapsed/expanded)
- **Centered Content:** max-width: 768px matching chat interface

**Props:**
```typescript
interface EmailPanelProps {
  isOpen: boolean;
  onClose: () => void;
}
```

**Usage:**
```typescript
// In TopBar.tsx
const [emailPanelOpen, setEmailPanelOpen] = useState(false);

<EmailPanel isOpen={emailPanelOpen} onClose={() => setEmailPanelOpen(false)} />
```

**Positioning:**
- `fixed top-16` (directly below TopBar)
- `right-0` (flush with right edge)
- Dynamic left margin based on sidebar:
  - Collapsed: `left-16` (64px)
  - Expanded: `left-64` (256px)
- `z-40` (between TopBar and higher modals)

**Data Hook:** `useEmailData()` - Manages email state, API calls, loading, errors

---

### CalendarPanel.tsx

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/CalendarPanel.tsx` (520 lines)

**Purpose:** Full-featured Google Calendar UI panel

**Features:**
- **List View:** Upcoming events (next 7 days) with title, date/time, location
- **Detail View:** Full event details with attendees
- **Create View:** Create new events with date/time pickers
- **Edit View:** Update existing events
- **Actions:** Delete events
- **Same responsive layout as EmailPanel**

**Props:**
```typescript
interface CalendarPanelProps {
  isOpen: boolean;
  onClose: () => void;
}
```

**Event Data:**
```typescript
interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start: string; // ISO 8601
  end: string;
  attendees?: CalendarAttendee[];
}
```

**Data Hook:** `useCalendarData()` - Manages event state, API calls, CRUD operations

---

### GoogleConnect.tsx

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/GoogleConnect.tsx`

**Purpose:** Google OAuth connection button

**Features:**
- Initiates OAuth flow via `/api/oauth/google/auth`
- Shows loading state during authentication
- Redirects to Google's OAuth consent screen
- Used in ProfileModal

**Usage:**
```typescript
<GoogleConnect onSuccess={() => {
  // Refresh connection status
}} />
```

---

### GoogleIndicator.tsx

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/components/GoogleIndicator.tsx`

**Purpose:** Visual indicator of Google connection status

**Features:**
- Green checkmark when connected
- Gray icon when disconnected
- Tooltip with connection email
- Click to open ProfileModal

---

### TopBar.tsx (Updated)

**Updates in v1.1.30:**
- Checks Google connection status on mount via `/api/oauth/google/status`
- Conditionally renders Mail and Calendar icons (left of UserDropdown)
- Icons only visible when Google is connected
- Manages EmailPanel and CalendarPanel visibility state
- Renders panels directly in component tree (NOT via createPortal)

**New Features:**
```typescript
const [emailPanelOpen, setEmailPanelOpen] = useState(false);
const [calendarPanelOpen, setCalendarPanelOpen] = useState(false);
const [googleConnected, setGoogleConnected] = useState(false);

// Check Google connection
useEffect(() => {
  const checkGoogleConnection = async () => {
    const response = await fetch('/api/oauth/google/status', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.ok) {
      const data = await response.json();
      setGoogleConnected(data.connected);
    }
  };
  checkGoogleConnection();
}, []);

// Render icons conditionally
{googleConnected && (
  <button onClick={() => setEmailPanelOpen(true)}>
    <Mail size={18} />
  </button>
)}
{googleConnected && (
  <button onClick={() => setCalendarPanelOpen(true)}>
    <Calendar size={18} />
  </button>
)}
```

---

## Custom Hooks (Google Integration)

### useEmailData.tsx

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useEmailData.tsx` (280 lines)

**Purpose:** Email data management and API integration

**State Management:**
```typescript
const [emails, setEmails] = useState<Email[]>([]);
const [currentEmail, setCurrentEmail] = useState<EmailDetail | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**Functions:**
- `fetchEmails(count)` - GET /api/google/emails
- `fetchEmailDetail(emailId)` - GET /api/google/emails/{id}
- `sendEmail(data)` - POST /api/google/emails/send
- `replyToEmail(emailId, data)` - POST /api/google/emails/{id}/reply
- `archiveEmail(emailId)` - POST /api/google/emails/{id}/archive
- `deleteEmail(emailId)` - DELETE /api/google/emails/{id}

**Authentication:**
All API calls include JWT token from localStorage:
```typescript
const authenticatedFetch = useCallback(async (endpoint, options) => {
  const token = localStorage.getItem('token');
  return fetch(`${apiUrl}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
}, []);
```

**Error Handling:**
- 401: Not authenticated
- 403: Google account not connected
- All errors set `error` state and display in UI

---

### useCalendarData.tsx

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useCalendarData.tsx` (240 lines)

**Purpose:** Calendar data management and API integration

**Functions:**
- `fetchEvents(timeMin, timeMax, maxResults)` - GET /api/google/calendar/events
- `fetchEventDetail(eventId)` - GET /api/google/calendar/events/{id}
- `createEvent(data)` - POST /api/google/calendar/events
- `updateEvent(eventId, data)` - PUT /api/google/calendar/events/{id}
- `deleteEvent(eventId)` - DELETE /api/google/calendar/events/{id}

**State Management:**
```typescript
const [events, setEvents] = useState<CalendarEvent[]>([]);
const [currentEvent, setCurrentEvent] = useState<CalendarEvent | null>(null);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**Same authentication pattern as useEmailData**

---

## TypeScript Types (Google Integration)

### email.ts

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/types/email.ts` (60 lines)

```typescript
export interface Email {
  id: string;
  from: string;
  subject: string;
  snippet: string;
  is_unread: boolean;
  date: string;
}

export interface EmailDetail {
  id: string;
  from: string;
  to: string;
  subject: string;
  body_text: string;
  body_html: string;
  date: string;
  labels: string[];
  is_unread: boolean;
}

export interface SendEmailRequest {
  to: string;
  subject: string;
  body: string;
}

export interface ReplyEmailRequest {
  body: string;
  reply_all?: boolean;
}
```

### calendar.ts

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/types/calendar.ts` (60 lines)

```typescript
export interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start: string; // ISO 8601 datetime
  end: string;
  attendees?: CalendarAttendee[];
  created?: string;
  updated?: string;
}

export interface CalendarAttendee {
  email: string;
  displayName?: string;
  responseStatus?: 'needsAction' | 'accepted' | 'declined' | 'tentative';
}

export interface CreateEventRequest {
  summary: string;
  description?: string;
  location?: string;
  start: string;
  end: string;
  attendees?: string[]; // Email addresses
}

export interface UpdateEventRequest {
  summary?: string;
  description?: string;
  location?: string;
  start?: string;
  end?: string;
  attendees?: string[];
}
```

---

## Pages

### Main Chat Page (page.tsx)

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/app/page.tsx`

**Purpose:** Primary chat interface with Cirkelline

**Features:**
- Real-time streaming chat
- Session management
- File upload support
- Sidebar with sessions
- URL state management

**Key Logic:**
```typescript
export default function HomePage() {
  const [sessionId, setSessionId] = useQueryState('session')
  const messages = useStore(state => state.messages)
  const { handleStreamResponse } = useAIStreamHandler()

  return (
    <div>
      <Sidebar />
      <ChatMessages messages={messages} />
      <ChatInput onSend={handleStreamResponse} />
    </div>
  )
}
```

### Memories Viewer Page (memories/page.tsx)

**Location:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/app/memories/page.tsx`

**Purpose:** Display all captured memories with full transparency

**Added:** v1.1.20 (2025-10-12)

**Features:**
- View all user memories in card layout
- Shows memory content + original input
- Topic categorization with tags
- Timestamps for each memory
- Technical details (collapsible)
- Loading and error states
- Empty state for new users
- Refresh functionality
- Responsive grid (1/2/3 columns)
- Dark mode support

**Component Structure:**
```typescript
export default function MemoriesPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { token } = useAuthStore()

  const fetchMemories = async () => {
    const response = await fetch('http://localhost:7777/api/user/memories', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    const data = await response.json()
    setMemories(data.memories)
  }

  return (
    <div className="min-h-screen p-8">
      {/* Header with count */}
      {/* Memory cards grid */}
      {/* Refresh button */}
    </div>
  )
}
```

**Data Structure:**
```typescript
interface Memory {
  memory_id: string
  memory: string              // What Cirkelline learned
  input: string | null        // What user said
  topics: string[]            // Categories
  updated_at: string | null   // ISO timestamp
  agent_id: string | null
  team_id: string | null
}

interface MemoriesResponse {
  success: boolean
  count: number
  memories: Memory[]
}
```

**API Integration:**
```typescript
// Endpoint
GET /api/user/memories

// Authentication
Authorization: Bearer {token}

// Response
{
  "success": true,
  "count": 15,
  "memories": [
    {
      "memory_id": "uuid",
      "memory": "User prefers dark mode",
      "input": "I always code in dark mode",
      "topics": ["preferences"],
      "updated_at": "2025-10-12T19:30:00Z",
      "agent_id": "cirkelline",
      "team_id": "cirkelline"
    }
  ]
}
```

**Visual Components:**

1. **Header Section:**
```typescript
<div className="mb-8">
  <div className="flex items-center gap-3">
    <Brain className="w-8 h-8 text-indigo-600" />
    <h1 className="text-3xl font-bold">Your Memories</h1>
  </div>
  <p className="text-gray-600">
    Cirkelline's understanding of you - captured organically through conversation
  </p>
  <div className="mt-4 px-4 py-2 bg-indigo-100 rounded-lg">
    <span className="font-semibold">{memories.length}</span> memories captured
  </div>
</div>
```

2. **Memory Card:**
```typescript
<div className="bg-white rounded-lg shadow-md p-6 border">
  {/* Memory Content */}
  <p className="text-gray-800 font-medium">{memory.memory}</p>

  {/* Original Input */}
  {memory.input && (
    <div className="p-3 bg-gray-50 rounded-md">
      <FileText className="w-4 h-4" />
      <span className="text-xs">From conversation:</span>
      <p className="text-sm italic">"{memory.input}"</p>
    </div>
  )}

  {/* Topics */}
  {memory.topics.map(topic => (
    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs">
      <Tag className="w-3 h-3" />
      {topic}
    </span>
  ))}

  {/* Timestamp */}
  <div className="flex items-center gap-2 text-xs text-gray-500 pt-4 border-t">
    <Calendar className="w-3 h-3" />
    <span>{formatDate(memory.updated_at)}</span>
  </div>

  {/* Technical Details */}
  <details className="mt-3 text-xs">
    <summary>Technical details</summary>
    <div className="mt-2 p-2 bg-gray-50 rounded">
      <div>ID: {memory.memory_id.substring(0, 8)}...</div>
      <div>Agent: {memory.agent_id}</div>
      <div>Team: {memory.team_id}</div>
    </div>
  </details>
</div>
```

3. **Loading State:**
```typescript
{loading && (
  <div className="flex flex-col items-center justify-center min-h-screen">
    <Loader2 className="w-12 h-12 animate-spin" />
    <p className="mt-4">Loading your memories...</p>
  </div>
)}
```

4. **Error State:**
```typescript
{error && (
  <div className="flex flex-col items-center justify-center min-h-screen">
    <p className="text-red-600 mb-4">{error}</p>
    <button
      onClick={fetchMemories}
      className="px-4 py-2 bg-indigo-600 text-white rounded-lg"
    >
      Try Again
    </button>
  </div>
)}
```

5. **Empty State:**
```typescript
{memories.length === 0 && (
  <div className="text-center py-16">
    <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
    <h2 className="text-xl font-semibold mb-2">No memories yet</h2>
    <p className="text-gray-500">
      Start chatting with Cirkelline to build your memory profile!
    </p>
  </div>
)}
```

**Styling:**
```css
/* Gradient background */
bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50
dark:from-gray-900 dark:via-gray-800 dark:to-indigo-900

/* Responsive grid */
grid gap-4 md:grid-cols-2 lg:grid-cols-3

/* Card hover effects */
hover:shadow-lg transition-shadow

/* Topic tags */
bg-indigo-100 dark:bg-indigo-900/30
text-indigo-700 dark:text-indigo-300
```

**Navigation:**
```typescript
// Access via sidebar
<button onClick={() => window.location.href = '/memories'}>
  <Brain icon />
  Memories
</button>

// Or direct URL
http://localhost:3000/memories
```

**Use Cases:**
1. **Verify Memory Capture:** See if Cirkelline accurately captured what you said
2. **Audit Stored Data:** Review all information Cirkelline knows about you
3. **Debug Memory System:** Verify Enhanced MemoryManager is working
4. **Build Trust:** Visual proof of memory capture functionality

**Future Enhancements:**
- Search/filter memories by topic
- Export memories (JSON, Markdown)
- Edit/delete memories
- Memory analytics dashboard
- Real-time updates via WebSocket

### Login Page (login/page.tsx)

**Purpose:** User authentication

**Features:**
- Email/password form
- JWT token storage
- Redirect to home after login

### Signup Page (signup/page.tsx)

**Purpose:** New user registration

**Features:**
- Email/password/display_name form
- JWT token storage
- Redirect to home after signup

---

## State Management

### Zustand Store

**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/store.ts` (117 lines)

**State Structure:**
```typescript
interface Store {
  // Hydration
  hydrated: boolean
  setHydrated: () => void

  // Streaming
  isStreaming: boolean
  setIsStreaming: (isStreaming: boolean) => void
  streamingErrorMessage: string
  setStreamingErrorMessage: (error: string) => void

  // Endpoint configuration
  selectedEndpoint: string
  setSelectedEndpoint: (endpoint: string) => void
  isEndpointActive: boolean
  isEndpointLoading: boolean

  // Messages
  messages: ChatMessage[]
  setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void

  // Agents/Teams
  agents: AgentDetails[]
  teams: TeamDetails[]
  selectedModel: string
  mode: 'agent' | 'team'
  setMode: (mode: 'agent' | 'team') => void

  // Sessions
  sessionsData: SessionEntry[] | null
  setSessionsData: (sessions: SessionEntry[] | ((prev: SessionEntry[] | null) => SessionEntry[] | null)) => void
  isSessionsLoading: boolean
}
```

**Persistence:**
```typescript
// Only selectedEndpoint is persisted to localStorage
{
  name: 'endpoint-storage',
  storage: createJSONStorage(() => localStorage),
  partialize: (state) => ({
    selectedEndpoint: state.selectedEndpoint
  })
}
```

**Default Values:**
```typescript
selectedEndpoint: process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
mode: 'team'  // Default to Cirkelline team
messages: []
sessionsData: null
```

**Usage Example:**
```typescript
import { useStore } from '@/store'

function Component() {
  const messages = useStore((state) => state.messages)
  const setMessages = useStore((state) => state.setMessages)

  // Add message
  setMessages((prev) => [...prev, newMessage])
}
```

---

## API Integration

### Authentication Requests

**Login:**
```typescript
const response = await fetch(`${API_URL}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})

const data = await response.json()
if (data.success) {
  login(data.token)  // Save to localStorage
}
```

**Signup:**
```typescript
const response = await fetch(`${API_URL}/api/auth/signup`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password, display_name })
})
```

### Message Sending

**SSE Streaming:**
```typescript
// FormData for multipart
const formData = new FormData()
formData.append('message', input)
formData.append('stream', 'true')
formData.append('session_id', sessionId ?? '')
formData.append('user_id', getUserId())

// SSE connection
const response = await fetch(apiUrl, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: formData
})

const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  const chunk = decoder.decode(value)
  const lines = chunk.split('\n')

  for (const line of lines) {
    if (line.startsWith('event:')) {
      // event: TeamRunContent
    } else if (line.startsWith('data:')) {
      const data = JSON.parse(line.slice(5))
      onChunk(data)
    }
  }
}
```

### File Upload

**Upload to Knowledge Base:**
```typescript
const formData = new FormData()
formData.append('file', file)

const response = await fetch(`${API_URL}/api/knowledge/upload`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: formData
})

const data = await response.json()
if (data.success) {
  toast.success(data.message)
}
```

### Session Loading

**Get All Sessions:**
```typescript
const response = await fetch(
  `${selectedEndpoint}/teams/${teamId}/sessions`,
  {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  }
)

const data = await response.json()
setSessionsData(data.data ?? [])
```

**Get Specific Session:**
```typescript
const response = await fetch(
  `${selectedEndpoint}/sessions/${sessionId}/runs`,
  {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
  }
)

const runs = await response.json()
// Convert runs to messages
const messages = runs.map(run => ({
  role: 'user',
  content: run.run_input,
  created_at: new Date(run.created_at).getTime() / 1000
}))
```

### Get User Memories

**Fetch All Memories:**
```typescript
const response = await fetch(
  `${API_URL}/api/user/memories`,
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json'
    }
  }
)

const data = await response.json()
// {
//   success: true,
//   count: 15,
//   memories: [
//     {
//       memory_id: "uuid",
//       memory: "User prefers dark mode",
//       input: "I always code in dark mode",
//       topics: ["preferences"],
//       updated_at: "2025-10-12T19:30:00Z",
//       agent_id: "cirkelline",
//       team_id: "cirkelline"
//     }
//   ]
// }
```

---

## Hooks Documentation

### useAIStreamHandler

**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx` (467 lines)

**Purpose:** Main SSE streaming logic for chat

**Key Functions:**
```typescript
const { handleStreamResponse } = useAIStreamHandler()

// Usage
await handleStreamResponse(message)
```

**Flow:**
1. Add user message to state
2. Add empty agent message
3. POST to `/teams/cirkelline/runs`
4. Stream SSE events
5. Update agent message incrementally
6. Handle session_id from first event
7. Optimistically add session to sidebar
8. Update URL with session_id

**Event Handling:**
```typescript
onChunk: (chunk: RunResponse) => {
  if (chunk.event === RunEvent.TeamRunContent) {
    // Append content to message
    lastMessage.content += chunk.content
  } else if (chunk.event === RunEvent.TeamToolCallStarted) {
    // Show tool execution
    lastMessage.tool_calls.push(chunk.tool)
  } else if (chunk.event === RunEvent.TeamRunCompleted) {
    // Finalize message
  }

  // Optimistic session add
  if (chunk.session_id && !sessionId) {
    setSessionId(chunk.session_id)
    setSessionsData(prev => [
      { session_id: chunk.session_id, created_at: chunk.created_at },
      ...prev
    ])
  }
}
```

**Critical Fix (2025-10-12):**
```typescript
// BEFORE (BROKEN):
// Only added session on TeamRunStarted event
if (chunk.event === RunEvent.TeamRunStarted) {
  // But TeamRunStarted sometimes arrives AFTER other events!
}

// AFTER (FIXED):
// Add session on ANY event with session_id
if (chunk.session_id && (!sessionId || sessionId !== chunk.session_id)) {
  // Works regardless of event order
  setSessionId(chunk.session_id)
  setSessionsData(/* add session */)
}
```

### useSessionLoader

**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useSessionLoader.tsx` (224 lines)

**Purpose:** Load sessions and conversation history

**Functions:**
```typescript
const { getSessions, getSession } = useSessionLoader()

// Load all sessions
await getSessions({
  entityType: 'team',
  teamId: 'cirkelline',
  dbId: 'cirkelline-v1'
})

// Load specific session
await getSession(
  {
    entityType: 'team',
    teamId: 'cirkelline',
    dbId: 'cirkelline-v1'
  },
  sessionId
)
```

**Message Processing:**
```typescript
// Convert backend runs to frontend messages
const messages = runs.flatMap(run => {
  const messages = []

  // User message
  if (run.run_input && !run.run_input.includes('You are a member')) {
    messages.push({
      role: 'user',
      content: run.run_input,
      created_at: new Date(run.created_at).getTime() / 1000
    })
  }

  // Agent message
  messages.push({
    role: 'agent',
    content: run.content,
    tool_calls: run.tools,
    created_at: new Date(run.created_at).getTime() / 1000 + 1
  })

  return messages
})

// Sort by timestamp
messages.sort((a, b) => a.created_at - b.created_at)
```

### useFileUpload

**Purpose:** Handle file uploads to knowledge base

**Usage:**
```typescript
const { uploadFile, isUploading } = useFileUpload()

// Upload file
await uploadFile(file, {
  onSuccess: () => {
    toast.success('File uploaded!')
  },
  onError: (error) => {
    toast.error(error.message)
  }
})
```

**Implementation:**
```typescript
const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/api/knowledge/upload`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: formData
  })

  return response.json()
}
```

### useChatActions

**Purpose:** Common chat actions (add message, clear, etc.)

**Functions:**
```typescript
const { addMessage, clearMessages, focusChatInput } = useChatActions()

// Add message
addMessage({
  role: 'user',
  content: 'Hello!',
  created_at: Math.floor(Date.now() / 1000)
})

// Clear all messages
clearMessages()

// Focus input
focusChatInput()
```

---

## Authentication Context

### AuthContext Implementation

**File:** `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/contexts/AuthContext.tsx` (153 lines)

**User Types:**
```typescript
interface User {
  user_id: string
  email?: string
  display_name?: string
  isAnonymous: boolean
  is_admin?: boolean
  tier_slug?: string
  tier_level?: number
  subscription_status?: string
}
```

**Note (v1.3.4):** Anonymous user ID generation was removed. Accounts are now required to use Cirkelline.

**Initialization Flow:**
```typescript
useEffect(() => {
  // 1. Check for JWT in localStorage
  const token = localStorage.getItem('token')

  if (token) {
    // 2. Decode JWT
    const payload = JSON.parse(atob(token.split('.')[1]))

    // 3. Check expiration
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      // Expired - user needs to login
      localStorage.removeItem('token')
      setNotAuthenticated()
    } else {
      // Valid - set authenticated user
      setUser({
        user_id: payload.user_id,
        email: payload.email,
        display_name: payload.display_name,
        isAnonymous: false,
        is_admin: payload.is_admin,
        tier_slug: payload.tier_slug || 'member',
        tier_level: payload.tier_level || 1,
        subscription_status: payload.subscription_status || 'active'
      })
    }
  } else {
    // No JWT - user needs to login
    // v1.3.4: No anon IDs generated - accounts required
    setNotAuthenticated()
  }
}, [])

// Set user as not authenticated (triggers login gate)
const setNotAuthenticated = () => {
  setUser({
    user_id: '',  // Empty - no user ID for unauthenticated users
    isAnonymous: true  // Triggers login gate in page.tsx
  })
}
```

**Login Gate (page.tsx):**
```typescript
// v1.3.4: If anonymous, render ONLY login/register screen
const isAnonymous = !user || user.isAnonymous
if (isAnonymous) {
  return (
    <div className="...">
      <LoginForm /> or <RegisterForm />
    </div>
  )
}
// Only authenticated users see the full app
```

**Login Function:**
```typescript
const login = (token: string) => {
  // 1. Clear all chat state from previous session
  useStore.getState().setMessages([])
  useStore.getState().setSessionsData([])

  // 2. Save JWT
  localStorage.setItem('token', token)

  // 3. Decode and set user
  const payload = JSON.parse(atob(token.split('.')[1]))
  setUser({
    user_id: payload.user_id,
    email: payload.email,
    display_name: payload.display_name,
    isAnonymous: false,
    is_admin: payload.is_admin,
    tier_slug: payload.tier_slug || 'member',
    tier_level: payload.tier_level || 1,
    subscription_status: payload.subscription_status || 'active'
  })

  // 4. Load user preferences
  loadUserPreferences(token, payload.user_id)

  // 5. Save timezone
  saveUserTimezone(token)
}
```

**Logout Function:**
```typescript
const logout = () => {
  // 1. Clear JWT
  localStorage.removeItem('token')

  // 2. Clear chat state
  useStore.getState().setMessages([])
  useStore.getState().setSessionsData([])

  // 3. Set as not authenticated (triggers login gate)
  setNotAuthenticated()

  // 4. Redirect home (shows login form)
  window.location.href = '/'
}
```

**getUserId Hook:**
```typescript
const getUserId = (): string => {
  return user?.user_id || ''
}

// Used in API calls
formData.append('user_id', getUserId())
```

---

## Session Management

### Session Creation Flow

```
User clicks "New Chat"
    ↓
Frontend: sessionId = null
    ↓
URL: ?team=cirkelline&session=
    ↓
User sends message
    ↓
useAIStreamHandler:
  formData.append('session_id', sessionId ?? '')
    ↓
Backend receives empty session_id
    ↓
Backend generates UUID
    ↓
First SSE event includes session_id
    ↓
Frontend receives event with session_id
    ↓
useAIStreamHandler:
  if (chunk.session_id && !sessionId) {
    setSessionId(chunk.session_id)  // Updates URL
    setSessionsData(prev => [sessionData, ...prev])  // Adds to sidebar
  }
    ↓
Session appears in sidebar immediately
```

### URL State Management

**Using nuqs:**
```typescript
import { useQueryState } from 'nuqs'

const [sessionId, setSessionId] = useQueryState('session')
const [teamId] = useQueryState('team')

// Update URL
setSessionId('new-uuid')
// URL becomes: ?team=cirkelline&session=new-uuid
```

### Sidebar Update

**Optimistic Update:**
```typescript
// In useAIStreamHandler
if (chunk.session_id && !sessionId) {
  console.log('✨ OPTIMISTIC SESSION ADD')

  const sessionData = {
    session_id: chunk.session_id,
    session_name: formData.get('message'),
    created_at: chunk.created_at
  }

  setSessionsData(prevSessionsData => {
    // Check if already exists
    const exists = prevSessionsData?.some(
      s => s.session_id === chunk.session_id
    )
    if (exists) return prevSessionsData

    // Add to beginning
    return [sessionData, ...(prevSessionsData ?? [])]
  })
}
```

### Session Loading

**On Page Load:**
```typescript
useEffect(() => {
  if (sessionId) {
    // Load specific session
    getSession({ /* params */ }, sessionId)
  } else {
    // Load all sessions for sidebar
    getSessions({ /* params */ })
  }
}, [sessionId, teamId])
```

---

## Quick Reference

### Key Files

```bash
# Main chat interface
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/app/page.tsx

# Memories Viewer page
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/app/memories/page.tsx

# State management
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/store.ts

# Authentication
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/contexts/AuthContext.tsx

# SSE streaming
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx

# Session loading
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useSessionLoader.tsx

# API routes
/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/api/routes.ts
```

### Common Patterns

**Add Message:**
```typescript
const setMessages = useStore(state => state.setMessages)
setMessages(prev => [...prev, newMessage])
```

**Get Auth Headers:**
```typescript
import { getAuthHeaders } from '@/lib/auth-headers'

fetch(url, {
  headers: getAuthHeaders()
})
// Returns: { 'Authorization': 'Bearer {token}' }
```

**Update URL:**
```typescript
import { useQueryState } from 'nuqs'

const [sessionId, setSessionId] = useQueryState('session')
setSessionId('new-uuid')
```

**Show Toast:**
```typescript
import { toast } from 'sonner'

toast.success('Success!')
toast.error('Error!')
```

## Theme & Color System

### Overview

Cirkelline features a comprehensive theme and color system that allows users to customize both **theme mode** (light/dark) and **accent colors** (contrast, purple, orange, green, blue, pink). The system ensures proper contrast and readability across all theme and color combinations.

**Key Features:**
- 🎨 **6 Accent Colors**: Contrast (dynamic), Purple, Orange, Green, Blue, Pink
- 🌓 **3 Theme Modes**: Light, Dark, System (follows OS preference)
- 🔄 **Real-time Updates**: All UI elements update instantly when theme/color changes
- 💾 **Persistence**: Preferences saved to database for logged-in users
- ♿ **Accessibility**: Automatic contrast adjustments for readability

---

### Theme Modes

**Location:** `cirkelline-ui/src/components/UserDropdown.tsx`

```typescript
type ThemeMode = 'light' | 'dark' | 'system'

const selectTheme = async (newTheme: ThemeMode) => {
  setTheme(newTheme)
  localStorage.setItem('theme', newTheme)

  if (newTheme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', prefersDark)
  } else {
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  // ALWAYS re-apply accent color when theme changes
  // This ensures contrast colors recalculate based on new theme
  applyAccentColor(accentColor)

  // Save to backend...
}
```

**How It Works:**
1. Theme selection updates `<html>` class: `<html class="dark">` or `<html>`
2. All components use Tailwind's `dark:` variant for theme-aware styling
3. Accent color is re-applied to recalculate contrast colors
4. Preference saved to database for logged-in users

---

### Accent Colors

**Available Colors:**

| Color | RGB Value | Hex | Preview |
|-------|-----------|-----|---------|
| **Contrast** | Dynamic | Dynamic | 🎨 Adapts to theme |
| Purple | `142, 11, 131` | `#8E0B83` | 🟣 |
| Orange | `236, 75, 19` | `#EC4B13` | 🟠 |
| Green | `19, 236, 129` | `#13EC81` | 🟢 |
| Blue | `19, 128, 236` | `#1380EC` | 🔵 |
| Pink | `236, 19, 128` | `#EC1380` | 🔴 |

**Contrast Mode (Dynamic):**

Contrast mode provides maximum readability by using theme-aware black/white colors:

```typescript
if (color === 'contrast') {
  // Dynamic contrast color based on theme
  const isDark = document.documentElement.classList.contains('dark')
  rgbValue = isDark ? '224, 224, 224' : '33, 33, 36' // #E0E0E0 (dark) : #212124 (light)
}
```

**Dark Theme:**
- Button background: `#E0E0E0` (light gray/white)
- Button text/icon: `#212124` (black)

**Light Theme:**
- Button background: `#212124` (black)
- Button text/icon: `#E0E0E0` (light gray/white)

---

### Button Text & Icon Colors

**Critical Implementation Detail:**

Buttons (New Chat, Send Message) must have proper text/icon contrast based on **both theme AND accent color**.

**Color Matrix:**

| Theme | Accent Type | Button Background | Text/Icon Color |
|-------|-------------|-------------------|-----------------|
| **Dark** | Color (green, blue, etc.) | Accent color | `#FFFFFF` (white) ✅ |
| **Dark** | Contrast | `#E0E0E0` (white) | `#212124` (black) ✅ |
| **Light** | Color (green, blue, etc.) | Accent color | `#FFFFFF` (white) ✅ |
| **Light** | Contrast | `#212124` (black) | `#E0E0E0` (white) ✅ |

**Implementation:**

**`button.tsx` (New Chat button):**
```typescript
const updateTextColor = () => {
  const accentColor = localStorage.getItem('accentColor')
  const isDark = document.documentElement.classList.contains('dark')

  if (accentColor === 'contrast' || accentColor === null) {
    // CONTRAST MODE:
    // Dark theme: white button (#E0E0E0) → black text (#212124)
    // Light theme: black button (#212124) → white text (#E0E0E0)
    setTextColor(isDark ? '#212124' : '#E0E0E0')
  } else {
    // COLOR ACCENTS (green, blue, etc.): Always white text
    setTextColor('#FFFFFF')
  }
}

// Listen for theme changes
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.attributeName === 'class') {
      updateTextColor()
    }
  })
})
observer.observe(document.documentElement, { attributes: true })

// Listen for accent color changes
window.addEventListener('accentColorChange', updateTextColor)
```

**`ChatInput.tsx` (Send button):**
```typescript
const updateIconColor = () => {
  const accentColor = localStorage.getItem('accentColor')
  const isDark = document.documentElement.classList.contains('dark')

  if (accentColor === 'contrast' || accentColor === null) {
    // CONTRAST MODE:
    // Dark theme: white button (#E0E0E0) → black icon (#212124)
    // Light theme: black button (#212124) → white icon (#E0E0E0)
    setIconColor(isDark ? '#212124' : '#E0E0E0')
  } else {
    // COLOR ACCENTS (green, blue, etc.): Always white icon
    setIconColor('#FFFFFF')
  }
}
```

**Event System:**

When theme or accent color changes, components are notified via:

1. **MutationObserver** - Detects `class` changes on `<html>` (theme changes)
2. **Custom Event** - `accentColorChange` event dispatched when accent color changes

```typescript
// In UserDropdown.tsx - selectAccentColor()
window.dispatchEvent(new CustomEvent('accentColorChange'))

// In button.tsx - listen for event
window.addEventListener('accentColorChange', updateTextColor)
```

---

**Dynamic Accent Colors:**
```typescript
// CORRECT: Use inline style with CSS variable for dynamic colors
<div style={{ backgroundColor: 'rgb(var(--accent-rgb))' }} />

// WRONG: Tailwind class won't work with dynamic CSS variables
<div className="bg-accent" />  // ❌ Won't update when theme changes

// Example: Avatar with dynamic color
<motion.div
  className="w-6 h-6 rounded-full"
  style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
/>
```

### Dynamic Theming System

**Overview:**
Cirkelline uses CSS variables for dynamic theming, allowing users to select both light/dark mode and accent colors (purple, orange, green, blue, pink).

**Color Configuration:**

Location: `cirkelline-ui/src/app/globals.css`

```css
:root {
  --accent-rgb: 142, 11, 131;      /* Default purple #8E0B83 */
  --accent: rgb(var(--accent-rgb));
}
```

**Available Colors:**
```typescript
const colorMap = {
  purple: '142, 11, 131',    // #8E0B83 (default)
  orange: '236, 75, 19',      // #EC4B13
  green: '19, 236, 129',      // #13EC81
  blue: '19, 128, 236',       // #1380EC
  pink: '236, 19, 128',       // #EC1380
}
```

**How It Works:**

1. **User selects color** in UserDropdown component
2. **JavaScript updates CSS variable** on document root:
   ```typescript
   document.documentElement.style.setProperty('--accent-rgb', '236, 75, 19')
   ```
3. **All components update instantly** using the CSS variable

**Implementation Examples:**

1. **Inline Style (CORRECT for dynamic colors):**
```typescript
// UserDropdown Admin badge (line 238)
<span
  className="px-2 py-0.5 rounded-md text-xs font-semibold text-white"
  style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
>
  Admin
</span>

// Avatar dot animation
<motion.div
  className="w-6 h-6 rounded-full"
  style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
  animate={{ scale: [1, 1.3, 1] }}
/>
```

2. **Tailwind Classes (works for static utilities):**
```typescript
// These Tailwind classes work because they're configured in tailwind.config.ts
<button className="bg-accent/10 text-accent">
  Theme Option
</button>
```

3. **Tailwind Config:**
```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      accent: {
        DEFAULT: 'rgb(var(--accent-rgb) / <alpha-value>)',
        start: 'rgb(var(--accent-rgb))',
        end: 'rgb(var(--accent-rgb))',
      }
    }
  }
}
```

**When to Use Each Approach:**

| Use Case | Method | Example |
|----------|--------|---------|
| Background colors | Inline style | `style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}` |
| Text colors | Tailwind class | `className="text-accent"` |
| Background with opacity | Tailwind class | `className="bg-accent/10"` |
| Borders | Tailwind class | `className="border-accent"` |

**UserDropdown Implementation:**

Location: `cirkelline-ui/src/components/UserDropdown.tsx`

```typescript
const applyAccentColor = (color: string) => {
  const colorMap = {
    purple: '142, 11, 131',
    orange: '236, 75, 19',
    green: '19, 236, 129',
    blue: '19, 128, 236',
    pink: '236, 19, 128',
  }

  const rgbValue = colorMap[color] || colorMap.purple
  document.documentElement.style.setProperty('--accent-rgb', rgbValue)
}

const selectAccentColor = (color: string) => {
  setAccentColor(color)
  localStorage.setItem('accentColor', color)
  applyAccentColor(color)

  // Force reflow for immediate update
  const root = document.documentElement
  root.style.setProperty('display', 'none')
  void root.offsetHeight
  root.style.removeProperty('display')
}
```

**Common Mistakes:**

❌ **WRONG - Tailwind class won't update dynamically:**
```typescript
<div className="bg-accent" />
```

✅ **CORRECT - Inline style updates dynamically:**
```typescript
<div style={{ backgroundColor: 'rgb(var(--accent-rgb))' }} />
```

❌ **WRONG - Hard-coded color:**
```typescript
<div style={{ backgroundColor: '#8E0B83' }} />
```

✅ **CORRECT - Uses CSS variable:**
```typescript
<div style={{ backgroundColor: 'rgb(var(--accent-rgb))' }} />
```

**Testing Dynamic Colors:**

1. Open app in browser
2. Click user dropdown
3. Expand "Theme" section
4. Click different color dots
5. Verify all accent-colored elements update:
   - Send button
   - New chat button
   - Active session highlight
   - Admin badges
   - Avatar dots
   - All other accent elements

**Persistence:**

```typescript
// On mount
useEffect(() => {
  const savedAccent = localStorage.getItem('accentColor') || 'purple'
  setAccentColor(savedAccent)
  applyAccentColor(savedAccent)
}, [])
```

### Moving Avatar Animation

**Overview:**
The Cirkelline avatar smoothly animates between agent messages, showing only ONE avatar at a time on the currently active message. The avatar uses pulsing animation when thinking and remains static when idle.

**Implementation:**

**Location:** `cirkelline-ui/src/components/chat/ChatArea/Messages/`

**Key Files:**
- `MessageItem.tsx` - Individual message rendering with avatar placeholder
- `Messages.tsx` - Calculates which message should display the avatar
- `Avatar.tsx` - Avatar component with thinking animation

**How It Works:**

1. **Every agent message reserves space** for the avatar (18px × 18px)
2. **Only the last agent message** actually renders the avatar
3. **Framer Motion's `layoutId`** automatically animates the avatar between positions
4. **Positioning** uses negative margins to align correctly with message content

**MessageItem.tsx Implementation:**

```typescript
interface AgentMessageProps extends MessageProps {
  showAvatar?: boolean  // Controls if avatar renders
}

const AgentMessage = ({ message, showAvatar = false }: AgentMessageProps) => {
  const isThinking = !message.content && (!message.response_audio || !message.response_audio.transcript)

  return (
    <motion.div className="flex flex-row items-start gap-3 font-heading">
      {/* Avatar placeholder - always present but conditionally visible */}
      <div
        className="flex-shrink-0"
        style={{
          width: '18px',
          height: '18px',
          marginRight: '18px',  // Positioning adjustment
          marginTop: '-18px'     // Positioning adjustment
        }}
      >
        {showAvatar && (
          <motion.div
            layoutId="cirkelline-avatar"  // Enables smooth position animation
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <Avatar type="ai" thinking={isThinking} />
          </motion.div>
        )}
      </div>

      {messageContent && (
        <motion.div className="flex-1">
          {messageContent}
        </motion.div>
      )}
    </motion.div>
  )
}
```

**Messages.tsx Implementation:**

```typescript
const Messages = ({ messages }: MessageListProps) => {
  // Find the last agent message
  let lastAgentMessageIndex = -1
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === 'agent') {
      lastAgentMessageIndex = i
      break
    }
  }

  return (
    <>
      {messages.map((message, index) => {
        const isLastAgentMessage = index === lastAgentMessageIndex

        if (message.role === 'agent') {
          return (
            <AgentMessageWrapper
              key={key}
              message={message}
              isLastAgentMessage={isLastAgentMessage}  // Passed down to AgentMessage
            />
          )
        }
        return <UserMessage key={key} message={message} />
      })}
    </>
  )
}
```

**Avatar.tsx (Thinking Animation):**

```typescript
<motion.div
  className="rounded-full"
  style={{
    backgroundColor: 'rgb(var(--accent-rgb))',  // Dynamic color
    width: '18px',
    height: '18px'
  }}
  animate={thinking ? {
    scale: [1, 1.3, 1],      // Grows and shrinks
    opacity: [1, 0.6, 1]      // Pulses
  } : undefined}
  transition={thinking ? {
    duration: 1.2,
    repeat: Infinity,
    ease: "easeInOut"
  } : undefined}
/>
```

**Key Technical Concepts:**

1. **layoutId Magic:**
   ```typescript
   // Framer Motion tracks elements with the same layoutId
   // When showAvatar moves from one message to another,
   // it automatically animates the position transition
   <motion.div layoutId="cirkelline-avatar">
   ```

2. **Conditional Rendering vs Visibility:**
   ```typescript
   // ❌ WRONG - Changes DOM structure, breaks layout
   {showAvatar ? <div>Avatar</div> : null}

   // ✅ CORRECT - Maintains DOM structure, just hides content
   <div style={{ width: '18px', height: '18px' }}>
     {showAvatar && <Avatar />}
   </div>
   ```

3. **Positioning Adjustments:**
   ```typescript
   // Negative margins align avatar correctly with message text
   style={{
     marginRight: '18px',  // Space between avatar and message
     marginTop: '-18px'     // Vertical alignment
   }}
   ```

**Flow When New Message Arrives:**

```
User sends message
    ↓
New user message added to state
    ↓
New empty agent message added (isLastAgentMessage = true)
    ↓
Avatar appears on new message
    ↓
Framer Motion detects layoutId change
    ↓
Avatar smoothly animates from old position to new position
    ↓
Old message no longer shows avatar (showAvatar = false)
    ↓
New message shows avatar with thinking animation
    ↓
Agent response streams in
    ↓
Thinking animation stops when content arrives
```

**Animation Properties:**

- **Move animation:** Spring (stiffness: 300, damping: 30)
- **Thinking animation:** Scale 1 → 1.3 → 1, Opacity 1 → 0.6 → 1
- **Duration:** 1.2 seconds per cycle
- **Repeat:** Infinite while thinking

**Why This Approach Works:**

1. **No absolute positioning** - Avoids layout breaking issues
2. **Reserved space** - Every message has placeholder, so layout is consistent
3. **Framer Motion layoutId** - Handles animation automatically
4. **Single source of truth** - `lastAgentMessageIndex` determines visibility
5. **Dynamic color** - Uses CSS variables for theme integration

**Common Pitfalls to Avoid:**

❌ **Don't use absolute positioning:**
```typescript
<div style={{ position: 'absolute', left: 0, top: 0 }}>
  <Avatar />  // Breaks when scrolling or layout changes
</div>
```

❌ **Don't add/remove elements conditionally:**
```typescript
{showAvatar && <div className="avatar-space" />}  // Changes layout
```

❌ **Don't use margins on message content:**
```typescript
<div style={{ marginBottom: '20px' }}>  // Breaks spacing
  {messageContent}
</div>
```

✅ **Do use reserved space with conditional rendering:**
```typescript
<div style={{ width: '18px', height: '18px' }}>
  {showAvatar && <Avatar />}
</div>
```

**Testing:**

1. Send multiple messages in chat
2. Verify only ONE avatar shows at a time
3. Verify avatar moves smoothly between messages
4. Verify thinking animation works (scale + opacity pulse)
5. Verify layout doesn't break or shift
6. Verify avatar color matches selected theme

### Environment Variables

```bash
# Frontend .env.local
NEXT_PUBLIC_API_URL=http://localhost:7777

# Production
NEXT_PUBLIC_API_URL=https://api.cirkelline.com
```

### Development Commands

```bash
# Install dependencies
cd cirkelline-ui
npm install

# Start dev server
npm run dev
# Runs on http://localhost:3000

# Build for production
npm run build

# Start production server
npm start
```

---

## Profile System (v1.2.3)

### Overview

The Profile System provides a comprehensive user profile management interface with multiple configuration sections. It replaced the previous modal-based profile with a full-page experience similar to the Administration panel.

**Key Features:**
- 📄 **Full-Page Layout**: Dedicated route with horizontal tab navigation
- 🔒 **Auth Protection**: Layout-level authentication (guests redirected to home)
- 🎨 **4 Sections**: Account, Integrations, Preferences, Security
- 🎭 **Theme Management**: Moved from UserDropdown to dedicated Preferences page
- 🔄 **Real-time Updates**: Theme and color changes apply instantly
- 💾 **Backend Persistence**: Settings saved to database for logged-in users
- ♿ **Responsive Design**: Adapts to sidebar collapse/expand state

**Added:** v1.2.3 (2025-10-27)

---

### Architecture

**Route Structure:**
```
/profile/                    # Account settings (default)
/profile/activity           # User activity logs (NEW in v1.2.4)
/profile/integrations        # Google OAuth and future services
/profile/preferences         # Theme, colors, notifications
/profile/security            # Password, 2FA, account deletion
```

**File Structure:**
```
src/
├── app/profile/
│   ├── layout.tsx                    # Auth protection + responsive wrapper
│   ├── page.tsx                      # Account settings (name, email, bio, instructions)
│   ├── activity/
│   │   └── page.tsx                  # User activity logs (NEW in v1.2.4)
│   ├── integrations/
│   │   └── page.tsx                  # Google OAuth + future integrations
│   ├── preferences/
│   │   └── page.tsx                  # Theme, accent color, notifications
│   └── security/
│       └── page.tsx                  # Password, 2FA, danger zone
└── components/
    └── ProfileNav.tsx                # Horizontal tab navigation
```

**Component Hierarchy:**
```
ProfileLayout
├── Sidebar (inherited from root layout)
├── TopBar (inherited from root layout)
├── Content Wrapper (responsive to sidebar state)
│   ├── ProfileNav (horizontal tabs with animated indicator)
│   └── Page Content (Account | Integrations | Preferences | Security)
```

---

### ProfileNav Component

**Location:** `/src/components/ProfileNav.tsx` (96 lines)

**Purpose:** Horizontal tab navigation with animated active indicator (similar to AdminNav)

**Tab Configuration:**
```typescript
const tabs = [
  { name: 'Account', path: '/profile', icon: User },
  { name: 'Activity', path: '/profile/activity', icon: Activity },  // NEW in v1.2.4
  { name: 'Integrations', path: '/profile/integrations', icon: Link },
  { name: 'Preferences', path: '/profile/preferences', icon: Settings },
  { name: 'Security', path: '/profile/security', icon: Shield }
]
```

**Implementation:**
```typescript
'use client'

import { User, Link, Settings, Shield, X } from 'lucide-react'
import { usePathname, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'

export default function ProfileNav() {
  const pathname = usePathname()
  const router = useRouter()

  const tabs = [
    { name: 'Account', path: '/profile', icon: User },
    { name: 'Integrations', path: '/profile/integrations', icon: Link },
    { name: 'Preferences', path: '/profile/preferences', icon: Settings },
    { name: 'Security', path: '/profile/security', icon: Shield }
  ]

  return (
    <nav className="border-b border-border-primary bg-light-surface dark:bg-dark-surface">
      <div className="flex items-center justify-between px-6 h-14">
        {/* Tabs */}
        <div className="flex gap-1">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const active = pathname === tab.path

            return (
              <button
                key={tab.path}
                onClick={() => router.push(tab.path)}
                className="relative px-4 py-2 flex items-center gap-2"
              >
                <Icon size={18} className={active ? 'text-accent' : 'text-light-text-secondary'} />
                <span className={active ? 'text-accent font-medium' : 'text-light-text'}>{tab.name}</span>

                {/* Animated indicator */}
                {active && (
                  <motion.div
                    layoutId="profile-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </button>
            )
          })}
        </div>

        {/* Close button */}
        <button onClick={() => router.push('/')} className="p-2">
          <X size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
        </button>
      </div>
    </nav>
  )
}
```

**Key Features:**
- **Framer Motion layoutId**: `"profile-tab-indicator"` enables smooth animation between tabs
- **Pathname detection**: Uses Next.js `usePathname()` to determine active tab
- **Icon colors**: Active tabs use accent color, inactive use secondary text color
- **Close button**: Returns to home (`/`) with X icon

---

### Profile Layout

**Location:** `/src/app/profile/layout.tsx` (85 lines)

**Purpose:** Authentication wrapper and responsive layout for all profile pages

**Auth Protection:**
```typescript
'use client'

import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import ProfileNav from '@/components/ProfileNav'

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const router = useRouter()

  // Redirect guests to home
  useEffect(() => {
    if (user && user.isAnonymous) {
      router.push('/')
    }
  }, [user, router])

  // Show loading while checking auth
  if (!user || user.isAnonymous) {
    return null
  }

  return (
    <div className={`
      min-h-screen pt-28
      bg-light-bg dark:bg-dark-bg
      transition-all duration-300 ease-in-out
      ${isCollapsed ? 'md:ml-16' : 'md:ml-64'}
    `}>
      <ProfileNav />
      {children}
    </div>
  )
}
```

**Key Features:**
- **Auth Check**: Redirects anonymous users to home on mount
- **Responsive Margin**: Adjusts left margin based on sidebar state (`isCollapsed`)
- **Consistent Layout**: Provides wrapper for all profile pages
- **Loading State**: Shows nothing while auth check in progress

---

### Account Settings Page

**Location:** `/src/app/profile/page.tsx` (187 lines)

**Purpose:** Edit profile information (display name, email, bio)

**Features:**
- ✏️ **Display Name**: Editable text field with save to backend
- 📧 **Email**: Read-only, grayed out (cannot change)
- 📝 **Bio**: Textarea with 200 character limit (NOT saved to backend yet)
- 💾 **Save Button**: Updates backend and refreshes JWT token
- 🎉 **Toast Notifications**: Success/error feedback

**Implementation:**
```typescript
'use client'

import { useState, useEffect } from 'react'
import { User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'

export default function ProfileAccountPage() {
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [bio, setBio] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (user) {
      setName(user.display_name || '')
      setEmail(user.email || '')
    }
  }, [user])

  const handleSave = async () => {
    setSaving(true)
    try {
      const token = localStorage.getItem('token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'

      const response = await fetch(`${apiUrl}/api/user/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ display_name: name })
      })

      if (!response.ok) throw new Error('Failed to update profile')

      const data = await response.json()

      // Update token with new display_name
      localStorage.setItem('token', data.token)

      toast.success('Profile updated successfully!')

      // Refresh page to update all components
      setTimeout(() => window.location.reload(), 500)
    } catch (error) {
      toast.error('Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <User className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
              Account
            </h1>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
            Manage your personal information
          </p>
        </div>

        {/* Profile Settings Card */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary">
          <div className="space-y-6">
            {/* Display Name */}
            <div>
              <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg"
              />
            </div>

            {/* Email (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg opacity-50 cursor-not-allowed"
              />
            </div>

            {/* Bio (Not saved yet) */}
            <div>
              <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                Bio
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value.slice(0, 200))}
                maxLength={200}
                rows={4}
                className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg"
              />
              <p className="text-xs text-light-text-secondary mt-1">
                {bio.length}/200 characters
              </p>
            </div>

            {/* Save Button */}
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 rounded-lg bg-accent text-white"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Backend Integration:**
```typescript
// Endpoint: PATCH /api/user/profile
// Request body: { display_name: string }
// Response: { success: true, token: string }
// Note: Backend returns NEW JWT token with updated display_name
```

**Future Enhancements:**
- Avatar upload functionality
- Bio backend save (needs API endpoint)
- Password change form
- Email change verification

---

### Integrations Page

**Location:** `/src/app/profile/integrations/page.tsx` (106 lines)

**Purpose:** Manage third-party service connections (Google OAuth, future integrations)

**Features:**
- 🔗 **Google Services**: Active integration with GoogleConnect component
- 📧 **Gmail Access**: Connect/disconnect Google account
- 📅 **Calendar Access**: Included in Google OAuth scope
- 🚀 **Future Services**: Placeholder cards for Slack, Discord, Notion

**Implementation:**
```typescript
'use client'

import { Link as LinkIcon } from 'lucide-react'
import GoogleConnect from '@/components/GoogleConnect'

export default function ProfileIntegrationsPage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <LinkIcon className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold">Integrations</h1>
          </div>
          <p className="text-sm text-light-text-secondary">
            Connect your accounts and services to enhance your Cirkelline experience
          </p>
        </div>

        {/* Google Services Card */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary">
          <h2 className="text-xl font-semibold mb-2">Google Services</h2>
          <p className="text-sm text-light-text-secondary mb-6">
            Connect your Google account to access Gmail and Calendar directly in Cirkelline
          </p>

          <GoogleConnect />
        </div>

        {/* Future Integrations - Placeholders */}
        <div className="mt-6 space-y-4">
          {/* Slack */}
          <div className="bg-light-surface rounded-2xl p-6 border border-border-primary opacity-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Slack</h3>
                <p className="text-sm text-light-text-secondary mt-1">
                  Connect your Slack workspace (Coming soon)
                </p>
              </div>
              <button disabled className="px-4 py-2 rounded-lg bg-light-bg cursor-not-allowed">
                Coming Soon
              </button>
            </div>
          </div>

          {/* Discord */}
          <div className="bg-light-surface rounded-2xl p-6 border border-border-primary opacity-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Discord</h3>
                <p className="text-sm text-light-text-secondary mt-1">
                  Connect your Discord account (Coming soon)
                </p>
              </div>
              <button disabled className="px-4 py-2 rounded-lg bg-light-bg cursor-not-allowed">
                Coming Soon
              </button>
            </div>
          </div>

          {/* Notion */}
          <div className="bg-light-surface rounded-2xl p-6 border border-border-primary opacity-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Notion</h3>
                <p className="text-sm text-light-text-secondary mt-1">
                  Connect your Notion workspace (Coming soon)
                </p>
              </div>
              <button disabled className="px-4 py-2 rounded-lg bg-light-bg cursor-not-allowed">
                Coming Soon
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**GoogleConnect Component:**
- Shows "Connect" button when not connected
- Shows "Connected as [email]" + "Disconnect" button when connected
- Handles OAuth flow via `/api/oauth/google/auth`
- Manages token storage and refresh

**Future Integrations:**
Each placeholder card includes:
- Service name and logo
- Description of integration
- "Coming Soon" disabled button
- Grayed out appearance (`opacity-50`)

---

### Preferences Page

**Location:** `/src/app/profile/preferences/page.tsx` (285 lines)

**Purpose:** Customize app appearance, theme, and notifications

**Features:**
- 🌓 **Theme Mode**: Light / Dark / System (follows OS preference)
- 🎨 **Accent Colors**: 6 colors (Contrast, Purple, Orange, Green, Blue, Pink)
- 🌐 **Language & Region**: Placeholder for future localization
- 🔔 **Notifications**: Placeholder for notification preferences

**Theme Mode Selection:**
```typescript
const selectTheme = async (newTheme: 'light' | 'dark' | 'system') => {
  setTheme(newTheme)
  localStorage.setItem('theme', newTheme)

  if (newTheme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.classList.toggle('dark', prefersDark)
  } else {
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  // Re-apply accent color when theme changes
  applyAccentColor(accentColor)

  // Save to backend if authenticated
  try {
    const token = localStorage.getItem('token')
    if (token) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
      await fetch(`${apiUrl}/api/user/preferences`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ theme: newTheme })
      })
    }
  } catch (error) {
    console.error('Failed to save theme:', error)
  }

  toast.success(`Theme changed to ${newTheme}`)
}
```

**Accent Color Picker:**
```typescript
const colorMap = {
  contrast: '',  // Dynamic based on theme
  purple: '142, 11, 131',
  orange: '236, 75, 19',
  green: '19, 236, 129',
  blue: '19, 128, 236',
  pink: '236, 19, 128',
}

const applyAccentColor = (color: string) => {
  let rgbValue = colorMap[color] || colorMap.purple

  if (color === 'contrast') {
    const isDark = document.documentElement.classList.contains('dark')
    rgbValue = isDark ? '224, 224, 224' : '33, 33, 36'
  }

  document.documentElement.style.setProperty('--accent-rgb', rgbValue)

  // Dispatch event for components that need to update
  window.dispatchEvent(new CustomEvent('accentColorChange'))
}

const selectAccentColor = async (color: string) => {
  setAccentColor(color)
  localStorage.setItem('accentColor', color)
  applyAccentColor(color)

  // Save to backend
  try {
    const token = localStorage.getItem('token')
    if (token) {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
      await fetch(`${apiUrl}/api/user/preferences`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ accent_color: color })
      })
    }
  } catch (error) {
    console.error('Failed to save accent color:', error)
  }

  toast.success('Accent color updated')
}
```

**UI Layout:**
```typescript
return (
  <div className="p-4 sm:p-6 lg:p-8">
    <div className="max-w-3xl mx-auto">
      {/* Theme Mode Selection */}
      <div className="grid grid-cols-3 gap-3">
        <motion.button
          onClick={() => selectTheme('light')}
          className={theme === 'light' ? 'bg-accent/10 border-2 border-accent' : '...'}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Sun size={24} />
          <span>Light</span>
        </motion.button>

        <motion.button onClick={() => selectTheme('dark')}>
          <Moon size={24} />
          <span>Dark</span>
        </motion.button>

        <motion.button onClick={() => selectTheme('system')}>
          <Monitor size={24} />
          <span>System</span>
        </motion.button>
      </div>

      {/* Accent Color Picker */}
      <div className="flex flex-wrap gap-3">
        {['contrast', 'purple', 'orange', 'green', 'blue', 'pink'].map(color => (
          <motion.button
            key={color}
            onClick={() => selectAccentColor(color)}
            className={`w-12 h-12 rounded-full ${accentColor === color ? 'ring-4 ring-offset-2' : ''}`}
            style={{ backgroundColor: color === 'contrast' ? '#212124' : colorMap[color] }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          />
        ))}
      </div>
    </div>
  </div>
)
```

**Backend Integration:**
```typescript
// Endpoint: PATCH /api/user/preferences
// Request body: { theme?: string, accent_color?: string }
// Response: { success: true }
```

---

### Security Page

**Location:** `/src/app/profile/security/page.tsx` (119 lines)

**Purpose:** Security settings and account management

**Features:**
- 🔒 **Password Change**: Placeholder for password update form
- 📱 **Two-Factor Authentication**: Placeholder for 2FA setup
- 💻 **Active Sessions**: Placeholder for session management
- ⚠️ **Danger Zone**: Export data and delete account

**Implementation:**
```typescript
'use client'

import { Shield, Lock, Smartphone, LogOut, AlertTriangle } from 'lucide-react'

export default function ProfileSecurityPage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold">Security</h1>
          </div>
          <p className="text-sm text-light-text-secondary">
            Manage your account security and privacy settings
          </p>
        </div>

        {/* Password Section (Placeholder) */}
        <div className="bg-light-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <Lock className="w-6 h-6" />
            <h2 className="text-xl font-semibold">Password</h2>
          </div>
          <p className="text-sm text-light-text-secondary mb-4">
            Change your account password to keep your account secure
          </p>
          <button disabled className="px-4 py-2 rounded-lg cursor-not-allowed">
            Change Password (Coming Soon)
          </button>
        </div>

        {/* Two-Factor Authentication (Placeholder) */}
        <div className="bg-light-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <Smartphone className="w-6 h-6" />
            <h2 className="text-xl font-semibold">Two-Factor Authentication</h2>
          </div>
          <p className="text-sm text-light-text-secondary mb-4">
            Add an extra layer of security to your account with 2FA
          </p>
          <button disabled className="px-4 py-2 rounded-lg cursor-not-allowed">
            Enable 2FA (Coming Soon)
          </button>
        </div>

        {/* Active Sessions (Placeholder) */}
        <div className="bg-light-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <LogOut className="w-6 h-6" />
            <h2 className="text-xl font-semibold">Active Sessions</h2>
          </div>
          <p className="text-sm text-light-text-secondary mb-4">
            Manage and review devices that are currently logged into your account
          </p>
          <div className="bg-light-bg rounded-lg p-4 border border-border-primary">
            <p className="text-sm text-light-text-secondary text-center">
              Session management coming soon
            </p>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-light-surface rounded-2xl p-6 sm:p-8 border-2 border-error/20">
          <div className="flex items-center gap-3 mb-6">
            <AlertTriangle className="w-6 h-6 text-error" />
            <h2 className="text-xl font-semibold text-error">Danger Zone</h2>
          </div>

          <div className="space-y-4">
            {/* Export Data */}
            <div className="pb-4 border-b border-border-primary">
              <h3 className="text-sm font-semibold mb-2">Export Your Data</h3>
              <p className="text-sm text-light-text-secondary mb-3">
                Download a copy of all your data (conversations, documents, settings)
              </p>
              <button disabled className="px-4 py-2 rounded-lg cursor-not-allowed opacity-50">
                Export Data (Coming Soon)
              </button>
            </div>

            {/* Delete Account */}
            <div>
              <h3 className="text-sm font-semibold text-error mb-2">Delete Account</h3>
              <p className="text-sm text-light-text-secondary mb-3">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <button disabled className="px-4 py-2 rounded-lg bg-error/10 text-error cursor-not-allowed opacity-50">
                Delete Account (Coming Soon)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Danger Zone Features:**
- **Export Data**: Download conversations, documents, memories, settings
- **Delete Account**: Permanent account deletion with warning
- **Visual Styling**: Red border (`border-error/20`), red text, AlertTriangle icon

---

### Migration from Modal (v1.2.2) to Full Page (v1.2.3)

**Previous Implementation (ProfileModal):**
- Modal popup rendered via `createPortal`
- Limited space (fixed height/width)
- Cluttered interface (all settings in one view)
- Profile + Theme + Google integration mixed together

**New Implementation (Profile System):**
- Dedicated `/profile/*` routes
- Full-page layout with horizontal tabs
- Clear separation of concerns (4 sections)
- Room for expansion (future features)

**Migration Steps:**

1. **Created ProfileNav Component:**
   - Horizontal tabs like AdminNav
   - Animated active indicator with Framer Motion layoutId
   - Close button returns to home

2. **Created Profile Layout:**
   - Auth protection (redirects anonymous users)
   - Responsive wrapper (adapts to sidebar state)
   - Consistent structure across all sections

3. **Split Functionality into Sections:**
   - **Account**: Name, email, bio (from ProfileModal)
   - **Integrations**: Google OAuth (from ProfileModal)
   - **Preferences**: Theme, colors (from UserDropdown)
   - **Security**: New section for future features

4. **Updated UserDropdown Navigation:**
   - Changed `handleProfile()` to `router.push('/profile')`
   - Removed ProfileModal import and component rendering
   - Removed modal state management

**Files Removed:**
- None (ProfileModal.tsx kept for reference, may be removed later)

**Files Modified:**
- `UserDropdown.tsx`: Removed ProfileModal logic, added route navigation
- `ProfileModal.tsx`: Deprecated (no longer rendered)

---

### Navigation & Access

**How Users Access Profile:**

1. **From UserDropdown:**
   ```typescript
   // UserDropdown.tsx
   const handleProfile = () => {
     router.push('/profile')
     setIsOpen(false)
   }

   <button onClick={handleProfile}>
     <User size={18} />
     Profile
   </button>
   ```

2. **Direct URL:**
   - `/profile` - Default (Account page)
   - `/profile/integrations` - Google OAuth
   - `/profile/preferences` - Theme settings
   - `/profile/security` - Security settings

3. **Tab Navigation:**
   - Click any tab in ProfileNav
   - Smooth animation between sections
   - Active tab highlighted with accent color

**Auth Flow:**
```
User clicks "Profile" in UserDropdown
    ↓
Next.js navigates to /profile
    ↓
ProfileLayout checks auth status
    ↓
Is user anonymous?
    ├─ Yes → Redirect to /
    └─ No → Render ProfileNav + Account page
```

---

### Styling & Responsive Design

**Layout Responsiveness:**
```typescript
// Profile layout adapts to sidebar state
className={`
  min-h-screen pt-28
  bg-light-bg dark:bg-dark-bg
  transition-all duration-300 ease-in-out
  ${isCollapsed ? 'md:ml-16' : 'md:ml-64'}
`}
```

**Breakpoints:**
- **Mobile (< 768px)**: Full width, no left margin
- **Desktop (≥ 768px)**: Left margin based on sidebar state
  - Collapsed: `ml-16` (64px)
  - Expanded: `ml-64` (256px)

**Card Styling:**
```typescript
className="
  bg-light-surface dark:bg-dark-surface
  rounded-2xl
  p-6 sm:p-8
  border border-border-primary
"
```

**Theme Colors:**
```typescript
// Light theme
'text-light-text'           // Main text: rgb(33, 33, 36)
'text-light-text-secondary' // Secondary text: rgb(107, 107, 107)
'bg-light-surface'          // Cards: rgb(255, 255, 255)
'bg-light-bg'               // Background: rgb(249, 249, 249)

// Dark theme
'text-dark-text'            // Main text: rgb(224, 224, 224)
'text-dark-text-secondary'  // Secondary text: rgb(160, 160, 160)
'bg-dark-surface'           // Cards: rgb(30, 30, 33)
'bg-dark-bg'                // Background: rgb(18, 18, 20)
```

---

### Testing Checklist

**Functionality Tests:**
- [ ] Profile nav tabs switch smoothly with animation
- [ ] Active tab indicator animates between tabs
- [ ] Close button (X) returns to home page
- [ ] Anonymous users redirected to home
- [ ] Authenticated users can access all sections

**Account Page:**
- [ ] Display name field editable
- [ ] Email field read-only (grayed out)
- [ ] Bio textarea limited to 200 characters
- [ ] Save button updates display_name in backend
- [ ] Success toast appears after save
- [ ] Page refreshes to show new name in TopBar

**Integrations Page:**
- [ ] GoogleConnect component renders correctly
- [ ] Google OAuth flow works (connect/disconnect)
- [ ] Placeholder integrations show "Coming Soon"

**Preferences Page:**
- [ ] Theme selector switches light/dark/system
- [ ] Theme changes apply immediately to all UI
- [ ] Accent color picker shows 6 colors
- [ ] Color selection updates all accent elements
- [ ] Contrast mode adapts to theme (black/white)
- [ ] Settings saved to backend for logged-in users

**Security Page:**
- [ ] Placeholder sections visible
- [ ] Danger zone has red border and styling
- [ ] All "Coming Soon" buttons disabled

**Responsive Tests:**
- [ ] Mobile (< 768px): Full width layout
- [ ] Desktop collapsed sidebar: Correct left margin (64px)
- [ ] Desktop expanded sidebar: Correct left margin (256px)
- [ ] Sidebar toggle triggers smooth transition
- [ ] All pages adapt to sidebar state

**Theme Tests:**
- [ ] Light theme: Correct colors, readable text
- [ ] Dark theme: Correct colors, readable text
- [ ] Theme persists across page refreshes
- [ ] Theme applies to all profile pages

---

### Future Enhancements

**Planned Features:**

1. **Account Page:**
   - Avatar upload and crop
   - Bio backend save (needs API endpoint)
   - Profile visibility settings
   - Account creation date display

2. **Integrations Page:**
   - Slack workspace connection
   - Discord account linking
   - Notion workspace integration
   - GitHub OAuth
   - Custom API integrations

3. **Preferences Page:**
   - Language selection (localization)
   - Timezone configuration
   - Date/time format preferences
   - Email notifications toggles
   - Push notifications settings
   - Sound effects toggle
   - Keyboard shortcuts customization

4. **Security Page:**
   - Password change form with validation
   - Two-factor authentication (TOTP)
   - SMS-based 2FA
   - Active sessions list with device info
   - Session revocation (logout other devices)
   - Account activity log
   - Data export (JSON, CSV)
   - Account deletion flow with confirmation

**Implementation Notes:**
- All placeholder sections have "Coming Soon" disabled buttons
- UI structure already in place, just needs backend endpoints
- Existing patterns (save buttons, toast notifications) can be reused

---

### API Endpoints

**Current Endpoints:**

```typescript
// Update profile
PATCH /api/user/profile
Body: { display_name: string }
Response: { success: true, token: string }

// Update preferences
PATCH /api/user/preferences
Body: { theme?: string, accent_color?: string }
Response: { success: true }
```

**Future Endpoints Needed:**

```typescript
// Update bio
PATCH /api/user/profile
Body: { bio: string }

// Upload avatar
POST /api/user/avatar
Body: FormData with image file

// Change password
PATCH /api/user/password
Body: { current_password: string, new_password: string }

// Enable 2FA
POST /api/user/2fa/enable
Response: { secret: string, qr_code: string }

// Verify 2FA
POST /api/user/2fa/verify
Body: { code: string }

// Get active sessions
GET /api/user/sessions
Response: { sessions: Session[] }

// Revoke session
DELETE /api/user/sessions/:session_id

// Export user data
GET /api/user/export
Response: JSON file download

// Delete account
DELETE /api/user/account
Body: { password: string, confirmation: 'DELETE MY ACCOUNT' }
```

---

### Key Takeaways

1. **Full-Page Experience**: Profile system now has dedicated routes with room for expansion
2. **Clear Separation**: Four distinct sections (Account, Integrations, Preferences, Security)
3. **Theme Management Moved**: Preferences moved from UserDropdown to dedicated page
4. **Auth Protection**: Layout-level authentication check protects all profile pages
5. **Responsive Design**: Adapts to sidebar state with smooth transitions
6. **Future-Proof**: Structure supports many planned features with minimal changes
7. **Consistent Patterns**: Follows same design language as Admin panel
8. **Backend Integration**: Settings persist to database for logged-in users

---

## Icon System (v1.2.2)

### Overview

Cirkelline uses a standardized icon system based on the **lucide-react** library. All icons follow consistent sizing and color patterns for visual harmony and accessibility across light and dark themes.

**Key Standards:**
- 📐 **Standard Size**: 18px for all icons (with 3 exceptions)
- 🎨 **Standard Colors**: rgb(107, 107, 107) light theme, rgb(160, 160, 160) dark theme
- 🔧 **Library**: lucide-react (52 unique icons, 150+ instances)
- ♿ **No Hover Opacity**: Icons maintain consistent visibility

---

### Icon Sizes

**Standard Size: 18px**

All icons use `size={18}` by default for consistency and optimal readability.

**Exceptions (Keep Current Sizes):**
1. **Send Message Button**: 20px (ChatInput.tsx:377)
   - Primary action button, needs visual prominence
   - Uses dynamic accent color background

2. **Sidebar Collapse/Expand Toggle**: 20px (Sidebar.tsx:469-471)
   - ChevronRight/ChevronLeft icons
   - Needs to be prominent for navigation

3. **New Chat Button (+)**: 20px (Sidebar.tsx:506)
   - Primary action button in sidebar
   - Matches Send button prominence

4. **Theme Selector Icons**: 16px (UserDropdown.tsx:644-672)
   - Sun, Moon, Monitor icons in theme picker
   - Smaller size appropriate for compact selector UI

---

### Icon Colors

**Standard Color Pattern:**

All icons (except semantic/accent icons) use theme-aware secondary text colors:

```typescript
className="text-light-text-secondary dark:text-dark-text-secondary"
```

**Tailwind Config Values:**
```typescript
// tailwind.config.ts
colors: {
  light: {
    'text-secondary': '#6B6B6B'  // rgb(107, 107, 107)
  },
  dark: {
    'text-secondary': '#A0A0A0'  // rgb(160, 160, 160)
  }
}
```

**Color Categories:**

| Category | Usage | Color Class | Example Icons |
|----------|-------|-------------|---------------|
| **Standard** | Most UI icons | `text-light-text-secondary dark:text-dark-text-secondary` | Menu, Calendar, Mail, Upload, User, Globe |
| **Semantic Success** | Success states | `text-success` (#10B981) | CheckCircle |
| **Semantic Error** | Error states | `text-error` (#EF4444) | AlertCircle, LogOut |
| **Accent** | Shared/special indicators | `text-accent` (dynamic) | Share2, Shield (admin) |
| **Dynamic Accent** | Primary actions | `rgb(var(--accent-rgb))` | Send button, New chat + |

---

### Icon Inventory

**52 Unique Icons from lucide-react:**

#### Navigation & Layout (8 icons)
- `ChevronLeft`, `ChevronRight`, `ChevronDown` - Navigation, section expansion
- `Menu` - Mobile hamburger menu
- `X` - Close buttons
- `Plus` - New chat button
- `Home` - Not currently used
- `Search` - Not currently used

#### Communication & Content (10 icons)
- `Send` - Send message button
- `Mail` - Email panel
- `Calendar` - Calendar panel
- `MessageSquare` - Chat/messages
- `FileText` - Documents
- `Upload` - File upload
- `Share2` - Share documents
- `Trash2` - Delete documents

#### User & Account (8 icons)
- `User` - Profile
- `UserPlus` - Register
- `LogIn` - Login
- `LogOut` - Logout
- `Shield` - Admin badge
- `Settings` - Settings (removed in v1.2.2)
- `Globe` - Language selection
- `HelpCircle` - Learn more

#### Theme & Display (4 icons)
- `Sun` - Light theme
- `Moon` - Dark theme
- `Monitor` - System theme
- `Palette` - Color selection

#### Status & Feedback (6 icons)
- `CheckCircle` - Success state
- `AlertCircle` - Error state
- `Loader2` - Loading spinner
- `RefreshCw` - Refresh data
- `Clock` - Time indicators
- `Bell` - Notifications

#### Actions & Tools (6 icons)
- `Edit` - Edit action
- `Copy` - Copy to clipboard
- `Download` - Download files
- `ExternalLink` - Open in new tab
- `MoreVertical` - More options menu
- `Filter` - Filter content

#### Media & Rich Content (4 icons)
- `Image` - Image files
- `Video` - Video files
- `Mic` - Audio/microphone
- `Headphones` - Audio playback

#### Data & Info (6 icons)
- `Activity` - Activity logs
- `BarChart` - Analytics
- `TrendingUp` - Growth metrics
- `Users` - User management
- `Database` - Data storage
- `Code` - Development

---

### Implementation Examples

**Standard Icons (18px, secondary color):**

```typescript
// TopBar.tsx - Calendar/Email icons
<Calendar size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
<Mail size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />

// UserDropdown.tsx - Profile, Language, Learn More
<User size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
<Globe size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
<HelpCircle size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />

// Sidebar.tsx - Section expansion chevrons
<ChevronRight size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
```

**Semantic Color Icons:**

```typescript
// ChatInput.tsx - Success/Error states
<CheckCircle size={18} className="text-success" />
<AlertCircle size={18} className="text-error" />

// UserDropdown.tsx - Logout
<LogOut size={18} className="text-error" />
```

**Accent Color Icons:**

```typescript
// DocumentCard.tsx - Shared indicator
<Share2 size={18} className="text-accent" />

// UploadDialog.tsx - Share checkbox
<Share2 size={18} className="text-accent" />
```

**Exception Icons (Keep Larger Sizes):**

```typescript
// Sidebar.tsx - Collapse/Expand toggle
<ChevronRight size={20} className="text-light-text-secondary dark:text-dark-text-secondary" />
<ChevronLeft size={20} className="text-light-text-secondary dark:text-dark-text-secondary" />

// Sidebar.tsx - New chat button
<Plus size={20} />

// ChatInput.tsx - Send button (dynamic color handled separately)
<Send size={20} />

// UserDropdown.tsx - Theme selector
<Sun size={16} />
<Moon size={16} />
<Monitor size={16} />
```

---

### Icon Color Logic

**Standard Icons:**
- Use Tailwind utility class: `text-light-text-secondary dark:text-dark-text-secondary`
- Automatically adapts to theme changes
- No opacity changes on hover (removed in v1.2.2)

**Dynamic Accent Buttons (Send, New Chat):**

The Send and New Chat buttons use special logic to ensure proper contrast:

```typescript
// ChatInput.tsx - Send button icon color
const updateIconColor = () => {
  const accentColor = localStorage.getItem('accentColor')
  const isDark = document.documentElement.classList.contains('dark')

  if (accentColor === 'contrast' || accentColor === null) {
    // CONTRAST MODE:
    // Dark theme: white button (#E0E0E0) → black icon (#212124)
    // Light theme: black button (#212124) → white icon (#E0E0E0)
    setIconColor(isDark ? '#212124' : '#E0E0E0')
  } else {
    // COLOR ACCENTS (green, blue, etc.): Always white icon
    setIconColor('#FFFFFF')
  }
}
```

**Important:** Send and New Chat buttons are the ONLY icons that use dynamic color logic. All other icons use standard Tailwind classes.

---

### Migration from v1.2.1 to v1.2.2

**What Changed:**

1. **Icon Sizes Standardized:**
   - All icons changed to 18px (except 4 exceptions)
   - Theme selector icons reduced from 20px to 16px
   - Consistency across all components

2. **Hardcoded Colors Removed:**
   - `text-green-500` → `text-success` (CheckCircle)
   - `text-red-500` → `text-error` (AlertCircle)
   - Uses semantic color tokens from Tailwind config

3. **Standard Color Applied:**
   - All non-semantic icons use `text-light-text-secondary dark:text-dark-text-secondary`
   - Proper contrast in both light and dark themes

4. **Hover Behaviors Removed:**
   - No more `opacity-50` or `opacity-100` transitions
   - Icons maintain consistent visibility
   - Only scale animations remain (for interactive buttons)

**Files Modified:**
- `TopBar.tsx` - Calendar, Mail, Menu, ChevronLeft icons
- `UserDropdown.tsx` - All menu icons, theme selector sizes
- `Sidebar.tsx` - Section chevrons, RefreshCw, X button
- `ChatInput.tsx` - CheckCircle, AlertCircle, Upload, Loader2
- `DocumentsList.tsx` - Upload icons
- `DocumentCard.tsx` - Share2, Trash2 icons
- `UploadDialog.tsx` - X, Share2, Loader2 icons

---

### Testing Checklist

**Visual Consistency:**
- [ ] All standard icons are 18px
- [ ] Exceptions (Send, Sidebar toggle, New chat) are 20px
- [ ] Theme selector icons are 16px
- [ ] All icons visible in light theme (rgb 107, 107, 107)
- [ ] All icons visible in dark theme (rgb 160, 160, 160)
- [ ] No opacity changes on hover

**Semantic Colors:**
- [ ] Success states show green (CheckCircle)
- [ ] Error states show red (AlertCircle, LogOut)
- [ ] Shared indicators show accent color (Share2)

**Dynamic Colors:**
- [ ] Send button icon adapts to accent color selection
- [ ] New chat button icon adapts to accent color selection
- [ ] Contrast mode shows black/white icons correctly

**Theme Switching:**
- [ ] Icons update when switching light/dark theme
- [ ] No visual glitches during theme transitions
- [ ] Colors maintain proper contrast

---

## Google Services Integration (v1.2.1)

### Overview

The Google Services integration provides access to Gmail and Google Calendar directly within the Cirkelline interface through a slide-down panel system.

### Architecture Summary

**Key Innovation:** Panel slides down from TopBar and pushes chat content down (NOT overlay), while chat input remains FIXED at bottom.

**Component Flow:**
```
User clicks Email/Calendar icon in TopBar
    ↓
TopBar calls onPanelChange(type)
    ↓
page.tsx updates openPanel state
    ↓
GooglePanelContainer animates height 0 → 25%
    ↓
Chat area height animates 100% → 75%
    ↓
Messages scroll with padding-bottom
    ↓
ChatInput stays FIXED at viewport bottom (no movement)
```

### File Locations

**Core Files:**
```
src/
├── components/
│   ├── TopBar.tsx                     # Icons + state management
│   ├── GooglePanelContainer.tsx       # Unified panel (NEW)
│   ├── GoogleConnect.tsx              # OAuth connection flow
│   ├── GoogleIndicator.tsx            # Connection status
│   └── chat/ChatArea/ChatInput/
│       └── ChatInput.tsx              # FIXED positioning
├── hooks/
│   ├── useEmailData.tsx               # Gmail data management
│   └── useCalendarData.tsx            # Calendar data management
├── types/
│   ├── email.ts                       # Email type definitions
│   └── calendar.ts                    # Calendar type definitions
└── app/
    └── page.tsx                       # Layout orchestration
```

### Implementation Checklist

✅ **Phase 1: OAuth Setup** (v1.2.0)
- Backend OAuth endpoints (`/api/oauth/google/*`)
- Frontend GoogleConnect button
- GoogleIndicator status display
- Token encryption and storage

✅ **Phase 2: REST Endpoints** (v1.2.0)
- Gmail endpoints (`/api/gmail/*`)
- Calendar endpoints (`/api/calendar/*`)
- Authentication middleware
- Error handling

✅ **Phase 3: UI Panels** (v1.2.1)
- GooglePanelContainer unified component
- TopBar integration
- Fixed ChatInput positioning
- Layout architecture with proper document flow

### Layout Positioning Strategy

**Problem Solved:**
- ❌ Old approach: Fixed overlay panels → content jumping, horizontal scroll
- ✅ New approach: Document flow panels → smooth transitions, stable layout

**Key Positioning Rules:**

1. **TopBar:** `position: fixed; top: 0; left: [sidebar-width]; right: 0;`
2. **Content Wrapper:** `position: fixed; top: 64px; left: [sidebar-width]; right: 0;`
3. **GooglePanelContainer:** `position: relative; height: [animated];` (in document flow)
4. **ChatArea:** `position: relative; height: [dynamic];` (adjusts to panel)
5. **ChatInput:** `position: fixed; bottom: 0; left: [sidebar-width]; right: 0;`

**Responsive Left Offset:**
```typescript
// Mobile: left: 0
// Desktop (collapsed): left: 4rem (64px)
// Desktop (expanded): left: 16rem (256px)

style={{
  left: typeof window !== 'undefined' && window.innerWidth >= 768
    ? (sidebarCollapsed ? '4rem' : '16rem')
    : '0'
}}
```

### Height Calculations

**TopBar:** Fixed `h-16` = 64px

**Available Space:** `100vh - 64px`

**Panel Height (when open):** `(100vh - 64px) * 0.25` = 25% of available space

**Chat Height (panel closed):** `100vh - 64px` = 100% of available space

**Chat Height (panel open):** `100vh - 64px - (100vh - 64px) * 0.25` = 75% of available space

**ChatInput:** `position: fixed` at `bottom: 0` (independent of chat height)

### Animation Details

**GooglePanelContainer:**
```typescript
<motion.div
  initial={{ height: 0, opacity: 0 }}
  animate={{ height: 'calc((100vh - 64px) * 0.25)', opacity: 1 }}
  exit={{ height: 0, opacity: 0 }}
  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
>
```

**ChatArea:**
```typescript
<div
  style={{
    height: openPanel ? 'calc(100vh - 64px - (100vh - 64px) * 0.25)' : 'calc(100vh - 64px)',
    transition: 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
  }}
>
```

**Result:** Smooth, synchronized animations without any "jumping"

### Common Issues & Solutions

#### Issue: Chat input "jumps" when panel opens/closes

**Cause:** ChatInput was positioned relative inside animated container

**Solution:**
```typescript
// ChatInput.tsx
<div
  className="fixed bottom-0 right-0 ..."  // position: fixed
  style={{ left: sidebarCollapsed ? '4rem' : '16rem' }}
>
```

#### Issue: Horizontal scroll appears

**Cause:** Panel and chat area both had left margins (double margin)

**Solution:**
```typescript
// Wrapper handles positioning
<div className="fixed top-16 right-0 left-[sidebar-width]">

  // Children are full-width, no margins
  <GooglePanelContainer className="w-full" />
  <ChatArea className="w-full" />
</div>
```

#### Issue: Panel not responsive to sidebar changes

**Cause:** Panel had hardcoded margin classes

**Solution:**
```typescript
// Remove margins from panel, let wrapper handle positioning
// Panel only needs: className="w-full"
```

#### Issue: Content switches between email/calendar cause flash

**Cause:** Separate EmailPanel and CalendarPanel components mounting/unmounting

**Solution:**
```typescript
// Single GooglePanelContainer stays mounted
// Content switches internally
{openPanel === 'email' && <EmailContent />}
{openPanel === 'calendar' && <CalendarContent />}
```

### Testing Checklist

**Layout Tests:**
- [ ] Panel slides down smoothly from TopBar
- [ ] Panel slides up smoothly when closed
- [ ] Chat area height adjusts smoothly
- [ ] ChatInput NEVER moves (stays at bottom)
- [ ] No horizontal scroll on any screen size
- [ ] Panel is full-width like chat

**Responsive Tests:**
- [ ] Mobile (0-768px): Panel full width, left: 0
- [ ] Desktop collapsed (768px+): Panel adjusts, left: 64px
- [ ] Desktop expanded (768px+): Panel adjusts, left: 256px
- [ ] Sidebar toggle triggers smooth panel reposition

**Interaction Tests:**
- [ ] Click Email icon → Panel opens with email list
- [ ] Click Calendar icon (email open) → Smooth switch to calendar
- [ ] Click same icon again → Panel closes smoothly
- [ ] Click X button → Panel closes
- [ ] ESC key → Panel closes
- [ ] Messages scrollable when panel open
- [ ] Chat input always visible and usable

**Content Tests:**
- [ ] Email list loads (20 emails)
- [ ] Click email → Detail view appears
- [ ] Back button → Returns to list
- [ ] Calendar list loads (upcoming events)
- [ ] Click event → Detail view appears
- [ ] Back button → Returns to list
- [ ] Error messages display properly
- [ ] Loading states show correctly

### Performance Considerations

**Optimizations:**
1. **Single Container:** GooglePanelContainer stays mounted (no remounting)
2. **Lazy Data Loading:** Only fetches when panel opens
3. **Smooth Transitions:** Hardware-accelerated CSS/Framer Motion
4. **Z-Index Layers:** Proper stacking (TopBar z-30, ChatInput z-20)

**Avoid:**
- ❌ Multiple panel components mounting/unmounting
- ❌ Y-transform animations (use height-based)
- ❌ Margins for positioning (use left/right fixed positioning)
- ❌ Absolute positioning in document flow (breaks layout)

### Future Enhancements

**Planned Features:**
- [ ] Compose email view
- [ ] Reply to email view
- [ ] Create calendar event view
- [ ] Edit calendar event view
- [ ] Archive/delete email actions
- [ ] Multiple calendar views (day/week/month)

**Implementation Notes:**
- Uncomment TODOs in GooglePanelContainer.tsx
- Add form validation
- Implement API calls (already exist in backend)
- Update view state management

---

**See Also:**
- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture
- [05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md) - Backend API
- [07-DEVELOPMENT-GUIDE.md](./07-DEVELOPMENT-GUIDE.md) - Developer guide
- [21-GOOGLE-INTEGRATION-PROGRESS.md](./21-GOOGLE-INTEGRATION-PROGRESS.md) - Google OAuth implementation
