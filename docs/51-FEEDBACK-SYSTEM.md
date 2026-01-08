# Feedback System Documentation

**Version:** 1.0.0
**Last Updated:** 2025-10-24
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Backend API](#backend-api)
5. [Frontend Components](#frontend-components)
6. [User Flow](#user-flow)
7. [Admin Dashboard](#admin-dashboard)
8. [Real-Time Updates](#real-time-updates)
9. [Security](#security)
10. [Production Checklist](#production-checklist)
11. [Testing](#testing)
12. [Maintenance](#maintenance)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The Feedback System allows users to provide feedback on Cirkelline's responses with a thumbs up/down mechanism. Admins can view, manage, and track all feedback submissions through a dedicated admin dashboard.

### Key Features

✅ **User Feedback Submission**
- Thumbs up/down on any Cirkelline message
- Optional comments for additional context
- Pre-filled with the message content
- Authentication required (blocks anonymous users)

✅ **Admin Dashboard**
- Centralized feedback management
- Real-time notification badge
- Feedback preview in dropdown
- Status tracking (unread/seen/done)
- Filtering and pagination

✅ **Real-Time Updates**
- Instant notification count updates
- Event-driven architecture
- No page refresh required

---

## Architecture

### System Flow

```
User Message
    ↓
Cirkelline Response
    ↓
User hovers → Thumbs up/down buttons appear
    ↓
User clicks thumbs down → FeedbackModal opens
    ↓
User adds comments → Submits
    ↓
POST /api/feedback
    ↓
Stored in public.feedback_submissions
    ↓
Admin sees notification badge (2)
    ↓
Admin clicks badge → Admin Feedback Page
    ↓
Admin marks as "seen"
    ↓
PATCH /api/feedback/:id/status
    ↓
Event: 'feedbackStatusChanged' dispatched
    ↓
UserDropdown refreshes count → Badge updates (1)
```

### Component Hierarchy

```
TopBar
├── UserDropdown (with notification badge)
│   ├── Notification Circle Badge (clickable → /admin/feedback)
│   ├── Username Dropdown Button
│   └── Dropdown Menu
│       ├── User Info + Admin Badge
│       ├── Recent Feedback Preview (admin only)
│       │   ├── Feedback Item 1
│       │   ├── Feedback Item 2
│       │   └── "View all →" link
│       ├── Profile
│       ├── Administration (admin only)
│       └── ...other options

MessageItem (Agent Message)
├── Message Content
└── Action Buttons (on hover)
    ├── Copy Button
    ├── Thumbs Up Button → Opens FeedbackModal
    └── Thumbs Down Button → Opens FeedbackModal

FeedbackModal
├── Feedback Type Icon (👍/👎)
├── Cirkelline's Message (read-only)
├── User Comments Textarea
└── Submit Button → POST /api/feedback

Admin Dashboard (/admin)
├── AdminNav (horizontal tabs)
│   ├── Overview
│   ├── Users
│   └── Feedback ← Active
└── Feedback Page
    ├── Header (count, filters)
    ├── Feedback List (expandable rows)
    │   ├── Feedback Item
    │   │   ├── Type Icon (👍/👎)
    │   │   ├── User Email + Timestamp
    │   │   ├── Message Preview
    │   │   ├── Status Badge
    │   │   └── Expand Button
    │   └── Expanded View
    │       ├── Full Message
    │       ├── User Comments
    │       ├── Metadata (session_id, feedback_id)
    │       └── Status Change Buttons
    └── Pagination
```

---

## Database Schema

### Table: `public.feedback_submissions`

**Created:** 2025-10-24
**Location:** `public` schema

```sql
CREATE TABLE IF NOT EXISTS public.feedback_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR,
    message_content TEXT NOT NULL,
    feedback_type VARCHAR NOT NULL CHECK (feedback_type IN ('positive', 'negative')),
    user_comments TEXT,
    status VARCHAR NOT NULL DEFAULT 'unread' CHECK (status IN ('unread', 'seen', 'done')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback_submissions(status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback_submissions(created_at DESC);
```

### Schema Details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique feedback identifier |
| `user_id` | UUID | NOT NULL, FOREIGN KEY | References `users(id)`, cascades on delete |
| `session_id` | VARCHAR | NULL | Chat session ID (optional) |
| `message_content` | TEXT | NOT NULL | Cirkelline's message being rated |
| `feedback_type` | VARCHAR | CHECK constraint | 'positive' or 'negative' |
| `user_comments` | TEXT | NULL | Optional user comments |
| `status` | VARCHAR | DEFAULT 'unread' | 'unread', 'seen', or 'done' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Submission timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

### Indexes

- **idx_feedback_user_id**: Fast user-specific queries
- **idx_feedback_status**: Efficient filtering by status
- **idx_feedback_created_at**: Optimized sorting by date (DESC)

### Data Retention

- Feedback is stored indefinitely
- Deleted users cascade delete their feedback (`ON DELETE CASCADE`)
- No automatic cleanup policy (future consideration)

---

## Backend API

**Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (Lines 2388-2746)

### 1. Submit Feedback

**Endpoint:** `POST /api/feedback`
**Auth:** Required (JWT token)
**Access:** Authenticated users only (blocks anonymous)

#### Request

```json
{
  "session_id": "uuid-of-session",
  "message_content": "Cirkelline's message text",
  "feedback_type": "negative",
  "user_comments": "Optional user comments"
}
```

#### Validation

- `message_content`: Required, max 5000 characters
- `user_comments`: Optional, max 2000 characters
- `feedback_type`: Must be 'positive' or 'negative'
- `session_id`: Optional
- Anonymous users blocked (400 error)

#### Response (201 Created)

```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "feedback_id": "uuid"
}
```

#### Error Responses

```json
// Anonymous user
{
  "detail": "Anonymous users cannot submit feedback. Please log in."
}

// Validation error
{
  "detail": "Message content exceeds maximum length of 5000 characters"
}
```

---

### 2. List Feedback (Admin Only)

**Endpoint:** `GET /api/feedback`
**Auth:** Required (JWT token)
**Access:** Admin only (`is_admin = true`)

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page |
| `status` | string | all | Filter: 'all', 'unread', 'seen', 'done' |

#### Example Request

```
GET /api/feedback?page=1&limit=20&status=unread
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "user_email": "user@example.com",
      "session_id": "session-uuid",
      "message_content": "Cirkelline's message",
      "feedback_type": "negative",
      "user_comments": "User's comments",
      "status": "unread",
      "created_at": 1729699200,
      "updated_at": 1729699200
    }
  ],
  "total": 25,
  "unread_count": 5,
  "page": 1,
  "limit": 20
}
```

#### Features

- Joins with `users` table to get `user_email`
- Returns total count and unread count
- Ordered by `created_at DESC`
- Pagination support

---

### 3. Update Feedback Status (Admin Only)

**Endpoint:** `PATCH /api/feedback/{feedback_id}/status`
**Auth:** Required (JWT token)
**Access:** Admin only

#### Request

```json
{
  "status": "seen"
}
```

#### Validation

- `status`: Must be 'unread', 'seen', or 'done'
- `feedback_id`: Must exist in database

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Feedback status updated successfully"
}
```

---

### 4. Get Unread Count (Admin Only)

**Endpoint:** `GET /api/feedback/unread-count`
**Auth:** Required (JWT token)
**Access:** Admin only

#### Response (200 OK)

```json
{
  "unread_count": 5
}
```

#### Usage

- Powers the notification badge
- Polled every 30 seconds by `UserDropdown`
- Also triggered on `feedbackStatusChanged` event

---

## Frontend Components

### 1. FeedbackModal Component

**Location:** `/cirkelline-ui/src/components/chat/FeedbackModal.tsx`

#### Purpose
Modal dialog for submitting feedback on a Cirkelline message.

#### Props

```typescript
interface FeedbackModalProps {
  message: ChatMessage          // The Cirkelline message being rated
  feedbackType: 'positive' | 'negative'  // Type of feedback
  sessionId: string | null      // Current session ID (from URL)
  onClose: () => void           // Close handler
}
```

#### Features

- Displays feedback type icon (👍 green or 👎 red)
- Shows Cirkelline's message in read-only div
- Textarea for user comments (2000 char limit with counter)
- Submit button with loading state
- Toast notifications (success/error)

#### State Management

```typescript
const [comments, setComments] = useState('')
const [isSubmitting, setIsSubmitting] = useState(false)
```

#### Submission Flow

1. User fills optional comments
2. Click Submit → `setIsSubmitting(true)`
3. POST to `/api/feedback` with:
   - `session_id` from props
   - `message_content` from message
   - `feedback_type` from props
   - `user_comments` from state
4. Success → Toast + close modal
5. Error → Toast error + keep modal open

---

### 2. MessageItem Updates

**Location:** `/cirkelline-ui/src/components/chat/ChatArea/Messages/MessageItem.tsx`

#### Added Features

**State:**
```typescript
const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
const [feedbackModalOpen, setFeedbackModalOpen] = useState(false)
const [feedbackType, setFeedbackType] = useState<'positive' | 'negative' | null>(null)
```

**Feedback Handler:**
```typescript
const handleFeedback = (type: 'up' | 'down') => {
  // Check authentication
  if (!user || user.isAnonymous) {
    toast.error('Please log in to submit feedback')
    return
  }

  // Set visual feedback
  setFeedback(type)

  // Open modal
  setFeedbackType(type === 'up' ? 'positive' : 'negative')
  setFeedbackModalOpen(true)
}
```

**Render:**
```typescript
{/* Action buttons - only show on hover and when message has content */}
{isHovered && messageContent && !isStreaming && (
  <motion.div className="flex items-center gap-2 absolute bottom-0 right-0">
    {/* Copy button */}
    <button onClick={handleCopy}>...</button>

    {/* Thumbs up */}
    <button onClick={() => handleFeedback('up')}>
      <ThumbsUp fill={feedback === 'up' ? 'currentColor' : 'none'} />
    </button>

    {/* Thumbs down */}
    <button onClick={() => handleFeedback('down')}>
      <ThumbsDown fill={feedback === 'down' ? 'currentColor' : 'none'} />
    </button>
  </motion.div>
)}

{/* Feedback Modal */}
{feedbackModalOpen && feedbackType && (
  <FeedbackModal
    message={message}
    feedbackType={feedbackType}
    sessionId={sessionId}
    onClose={() => {
      setFeedbackModalOpen(false)
      setFeedbackType(null)
    }}
  />
)}
```

---

### 3. UserDropdown Updates

**Location:** `/cirkelline-ui/src/components/UserDropdown.tsx`

#### Added State

```typescript
const [unreadCount, setUnreadCount] = useState(0)
const [recentFeedback, setRecentFeedback] = useState<any[]>([])
```

#### Notification Badge

**Visual Design:**
- Circle badge with accent color background
- White text showing count (max "9+")
- Size: `w-5 h-5`, font: `text-[10px]`
- Positioned before username with `gap-0.5`

**Functionality:**
```typescript
{user?.is_admin && unreadCount > 0 && (
  <motion.button
    onClick={() => router.push('/admin/feedback')}
    className="w-5 h-5 rounded-full flex items-center justify-center"
    style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
    whileHover={{ scale: 1.1 }}
  >
    <span className="text-[10px] font-bold text-white">
      {unreadCount > 9 ? '9+' : unreadCount}
    </span>
  </motion.button>
)}
```

#### Feedback Preview in Dropdown

**Location:** After user info, before Profile link

**Structure:**
```typescript
{user?.is_admin && unreadCount > 0 && (
  <>
    <div className="px-4 py-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold">Recent Feedback</p>
        <button onClick={() => router.push('/admin/feedback')}>
          View all →
        </button>
      </div>

      {/* Feedback Items */}
      <div className="space-y-2 max-h-48 overflow-y-auto overflow-x-hidden">
        {recentFeedback.map((item) => (
          <div onClick={() => router.push('/admin/feedback')}>
            {/* Icon (👍/👎) */}
            {/* User email */}
            {/* Message preview (60 chars) */}
          </div>
        ))}
      </div>
    </div>
  </>
)}
```

#### Data Fetching

**Effect Hook:**
```typescript
useEffect(() => {
  const fetchFeedbackData = async () => {
    // Fetch unread count
    const countResponse = await fetch('/api/feedback/unread-count')
    setUnreadCount(countData.unread_count || 0)

    // Fetch recent unread (max 3)
    const feedbackResponse = await fetch('/api/feedback?page=1&limit=3&status=unread')
    setRecentFeedback(feedbackData.data || [])
  }

  if (user && user.is_admin) {
    fetchFeedbackData()
    const interval = setInterval(fetchFeedbackData, 30000) // Poll every 30s

    // Listen for real-time updates
    window.addEventListener('feedbackStatusChanged', fetchFeedbackData)

    return () => {
      clearInterval(interval)
      window.removeEventListener('feedbackStatusChanged', fetchFeedbackData)
    }
  }
}, [user])
```

---

### 4. Admin Feedback Page

**Location:** `/cirkelline-ui/src/app/admin/feedback/page.tsx`

#### Features

**Header:**
- Title: "User Feedback"
- Unread count display
- Status filter dropdown (All/Unread/Seen/Done)

**Feedback List:**
- Paginated (20 per page)
- Expandable rows
- Each row shows:
  - Type icon (👍 green bg / 👎 red bg)
  - User email + timestamp
  - Message preview (150 chars)
  - User comments preview (100 chars, if any)
  - Status badge (colored)
  - Expand/Collapse button

**Expanded View:**
- Full message content (scrollable)
- Full user comments
- Metadata (session_id, feedback_id)
- Status change buttons

**Pagination:**
- Previous/Next buttons
- Page X of Y display
- Disabled states on boundaries

#### Status Management

```typescript
const updateStatus = async (feedbackId: string, newStatus: string) => {
  const response = await fetch(`/api/feedback/${feedbackId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ status: newStatus })
  })

  if (response.ok) {
    toast.success(`Marked as ${newStatus}`)
    fetchFeedback() // Refresh list
    window.dispatchEvent(new CustomEvent('feedbackStatusChanged')) // Update badge
  }
}
```

#### Empty State

- MessageSquare icon
- "No feedback yet" heading
- Helpful message

---

### 5. AdminNav Component

**Location:** `/cirkelline-ui/src/components/AdminNav.tsx`

#### Purpose
Horizontal tab navigation for admin pages.

#### Tabs

- **Overview** (`/admin`)
- **Users** (`/admin/users`) - Coming soon
- **Feedback** (`/admin/feedback`)

#### Active Indicator

- Animated underline using `layoutId="admin-tab-indicator"`
- Smooth transitions between tabs
- Accent color styling

---

### 6. Admin Layout

**Location:** `/cirkelline-ui/src/app/admin/layout.tsx`

#### Structure

```typescript
<div className="relative">
  <Sidebar />
  <TopBar onNotesToggle={() => setIsRightSidebarOpen(!isRightSidebarOpen)} />

  {/* Admin Navigation (horizontal tabs) */}
  <div className="fixed top-16 right-0 ...">
    <AdminNav />
  </div>

  <main className="min-h-screen pt-28 ...">
    {children}
  </main>

  <RightSidebar isOpen={isRightSidebarOpen} onClose={...} />
</div>
```

#### Protection

- Redirects non-admins to `/`
- Checks `user.is_admin` on mount
- Returns `null` if not admin

---

## User Flow

### Submitting Feedback (Regular User)

1. User sends message to Cirkelline
2. Cirkelline responds
3. User hovers over Cirkelline's message
4. Action buttons appear (Copy, 👍, 👎)
5. User clicks 👎 (thumbs down)
6. **Check:** Is user authenticated?
   - ❌ Anonymous → Toast: "Please log in to submit feedback"
   - ✅ Authenticated → Continue
7. FeedbackModal opens
8. Modal shows:
   - Red 👎 icon + "Negative Feedback" header
   - Cirkelline's message (read-only)
   - Comments textarea (optional)
9. User adds comments (optional)
10. User clicks "Submit Feedback"
11. POST to `/api/feedback`
12. Success toast: "Feedback submitted successfully"
13. Modal closes

### Viewing Feedback (Admin User)

#### Quick Preview

1. Admin sees notification badge next to username: `[2] eenvy`
2. Admin clicks username "eenvy" (opens dropdown)
3. Dropdown shows "Recent Feedback" section
4. See up to 3 recent unread items:
   - 👎 icon
   - User: "john"
   - Preview: "Did you know that..."
5. Click any item → Navigate to `/admin/feedback`

#### Full Dashboard

1. Admin clicks notification badge `[2]` or "Administration" → `/admin`
2. Clicks "Feedback" tab in AdminNav
3. See all feedback submissions
4. Filter by status: All / Unread / Seen / Done
5. Click "Expand" on any row
6. See full message, comments, metadata
7. Click "Mark as: Seen"
8. Feedback status updates
9. Notification badge decreases: `[2]` → `[1]`
10. Preview updates (item removed from "Recent Feedback")

---

## Admin Dashboard

### Overview Page

**Route:** `/admin`

**Content:**
- Welcome header with Shield icon
- Admin section cards:
  - **User Feedback** - Shows unread count badge
  - **Users** - "Coming soon" badge
- System Status widget
  - Feedback Submissions (unread count)
  - Active Users (coming soon)
  - System Health (✓ Operational)

### Feedback Page

**Route:** `/admin/feedback`

**Layout:**
- TopBar (with notification badge)
- AdminNav (horizontal tabs)
- Page content:
  - Header with unread count
  - Status filter dropdown
  - Feedback list (expandable rows)
  - Pagination controls

**Features:**
- Real-time updates (no refresh needed)
- Responsive design
- Smooth animations
- Empty state handling

---

## Real-Time Updates

### Event System

**Event Name:** `feedbackStatusChanged`

**Dispatch Location:**
`/admin/feedback/page.tsx` → `updateStatus()` function

```typescript
if (response.ok) {
  toast.success(`Marked as ${newStatus}`)
  fetchFeedback() // Refresh list
  window.dispatchEvent(new CustomEvent('feedbackStatusChanged'))
}
```

**Listener Location:**
`UserDropdown.tsx` → `useEffect()` hook

```typescript
useEffect(() => {
  const handleFeedbackChange = () => {
    fetchFeedbackData() // Refresh count and preview
  }

  window.addEventListener('feedbackStatusChanged', handleFeedbackChange)

  return () => {
    window.removeEventListener('feedbackStatusChanged', handleFeedbackChange)
  }
}, [user])
```

### Update Flow

```
Admin clicks "Mark as: Seen"
    ↓
PATCH /api/feedback/:id/status
    ↓
Database updates status
    ↓
200 OK response
    ↓
Event dispatched: 'feedbackStatusChanged'
    ↓
UserDropdown hears event
    ↓
Fetches new data:
  - GET /api/feedback/unread-count
  - GET /api/feedback?page=1&limit=3&status=unread
    ↓
State updates:
  - unreadCount: 2 → 1
  - recentFeedback: [...updated list]
    ↓
UI updates instantly:
  - Badge: [2] → [1]
  - Preview: 2 items → 1 item
```

### Polling

**Interval:** 30 seconds
**Endpoints:**
- `GET /api/feedback/unread-count`
- `GET /api/feedback?page=1&limit=3&status=unread`

**Purpose:** Ensures badge updates even without status changes (e.g., new submissions)

---

## Security

### Authentication

**Required For:**
- Submitting feedback
- Viewing feedback (admin only)
- Updating feedback status (admin only)

**Implementation:**
- JWT token in `Authorization: Bearer <token>` header
- Backend validates token and extracts `user_id`
- Anonymous users blocked from submission (400 error)

### Authorization

**Admin-Only Endpoints:**
- `GET /api/feedback`
- `PATCH /api/feedback/:id/status`
- `GET /api/feedback/unread-count`

**Check:**
```python
if not user.get('is_admin'):
    raise HTTPException(status_code=403, detail="Admin access required")
```

**Frontend:**
- Admin routes redirect non-admins to `/`
- Admin UI elements hidden for non-admins
- Protected at layout level

### Input Validation

**Backend Validation:**
```python
# Message content
if len(message_content) > 5000:
    raise HTTPException(400, "Message content exceeds maximum length")

# User comments
if user_comments and len(user_comments) > 2000:
    raise HTTPException(400, "Comments exceed maximum length")

# Feedback type
if feedback_type not in ['positive', 'negative']:
    raise HTTPException(400, "Invalid feedback type")

# Status
if new_status not in ['unread', 'seen', 'done']:
    raise HTTPException(400, "Invalid status")
```

**Frontend Validation:**
- Character counters on textareas
- Disabled submit when empty
- Real-time validation feedback

### SQL Injection Prevention

- **Method:** Parameterized queries via SQLAlchemy
- **Example:**
```python
query = text("""
    UPDATE public.feedback_submissions
    SET status = :status, updated_at = CURRENT_TIMESTAMP
    WHERE id = :feedback_id
""")
result = conn.execute(query, {
    "status": new_status,
    "feedback_id": feedback_id
})
```

### XSS Prevention

- **Backend:** Text fields (no HTML allowed)
- **Frontend:** React's built-in escaping
- **Display:** All user content rendered as plain text

---

## Production Checklist

### Pre-Deployment

- [ ] **Database Migration**
  ```sql
  -- Run on production database
  CREATE TABLE IF NOT EXISTS public.feedback_submissions (...);
  CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback_submissions(user_id);
  CREATE INDEX IF NOT EXISTS idx_feedback_status ON public.feedback_submissions(status);
  CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback_submissions(created_at DESC);
  ```

- [ ] **Environment Variables**
  - Backend: No new env vars needed
  - Frontend: `NEXT_PUBLIC_API_URL` already set

- [ ] **Backend Deployment**
  - Code includes lines 2388-2746 in `my_os.py`
  - All 4 endpoints registered
  - Restart backend service

- [ ] **Frontend Deployment**
  - All components in place
  - Build succeeds (`pnpm build`)
  - Deploy to Vercel

### Post-Deployment

- [ ] **Smoke Tests**
  ```bash
  # Test health
  curl https://api.cirkelline.com/config

  # Test feedback count (as admin)
  curl -H "Authorization: Bearer <admin-token>" \
       https://api.cirkelline.com/api/feedback/unread-count
  ```

- [ ] **Functional Tests**
  - [ ] Submit feedback as regular user
  - [ ] Block anonymous user submission
  - [ ] View feedback as admin
  - [ ] Update feedback status
  - [ ] Verify real-time badge update
  - [ ] Check notification preview

- [ ] **Performance Tests**
  - [ ] Feedback list loads in < 2s
  - [ ] Status update responds in < 500ms
  - [ ] No memory leaks (check polling cleanup)

### Monitoring

- [ ] **CloudWatch Logs**
  - Monitor `/api/feedback` endpoints
  - Watch for 400/500 errors
  - Check response times

- [ ] **Database**
  - Monitor `feedback_submissions` table size
  - Check index usage
  - Verify query performance

- [ ] **Alerts**
  - Set up alert for high error rate (>5%)
  - Alert if feedback count exceeds threshold

---

## Testing

### Manual Testing

#### Test 1: Submit Feedback (Positive Flow)

1. Log in as regular user
2. Send message to Cirkelline
3. Hover over response → Click 👍
4. Modal opens
5. Add comment: "Great response!"
6. Click Submit
7. ✅ Success toast appears
8. ✅ Modal closes
9. Check database:
   ```sql
   SELECT * FROM public.feedback_submissions
   ORDER BY created_at DESC LIMIT 1;
   ```
10. ✅ Record exists with correct data

#### Test 2: Block Anonymous User

1. Open incognito window
2. Go to Cirkelline chat (anonymous session)
3. Hover over Cirkelline message → Click 👎
4. ✅ Toast: "Please log in to submit feedback"
5. ✅ Modal does NOT open

#### Test 3: Admin Notification Badge

1. Submit 2 feedback items as user
2. Log in as admin (`opnureyes2@gmail.com`)
3. ✅ Badge shows `[2]` next to username
4. ✅ Badge is accent color circle
5. ✅ Click badge → Navigate to `/admin/feedback`

#### Test 4: Notification Preview

1. As admin, click username "eenvy"
2. Dropdown opens
3. ✅ See "Recent Feedback" section
4. ✅ See 2 feedback items with icons, user, preview
5. ✅ "View all →" link present
6. Click any item
7. ✅ Navigate to `/admin/feedback`

#### Test 5: Real-Time Update

1. As admin, open `/admin/feedback`
2. Note badge shows `[2]`
3. Mark one feedback as "Seen"
4. ✅ Toast: "Marked as seen"
5. ✅ Badge updates to `[1]` (no refresh!)
6. ✅ Preview updates (item removed)

#### Test 6: Status Management

1. As admin, on feedback page
2. Click "Expand" on unread item
3. Click "Mark as: Seen"
4. ✅ Status badge changes color
5. ✅ Button disabled
6. Click "Mark as: Done"
7. ✅ Status badge changes to green
8. Filter by "Unread"
9. ✅ Item no longer in list

### Automated Testing (Future)

```typescript
// Example test structure
describe('Feedback System', () => {
  describe('User Submission', () => {
    it('should allow authenticated users to submit feedback')
    it('should block anonymous users from submitting')
    it('should validate comment length')
  })

  describe('Admin Dashboard', () => {
    it('should show notification badge with correct count')
    it('should update badge in real-time when status changes')
    it('should filter feedback by status')
    it('should paginate results correctly')
  })
})
```

---

## Maintenance

### Database Maintenance

**Monitor Table Size:**
```sql
SELECT
  pg_size_pretty(pg_total_relation_size('public.feedback_submissions')) as total_size,
  COUNT(*) as total_records
FROM public.feedback_submissions;
```

**Archive Old Feedback (Optional):**
```sql
-- Example: Archive feedback older than 1 year
CREATE TABLE public.feedback_submissions_archive AS
SELECT * FROM public.feedback_submissions
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM public.feedback_submissions
WHERE created_at < NOW() - INTERVAL '1 year';
```

### Performance Optimization

**Analyze Slow Queries:**
```sql
EXPLAIN ANALYZE
SELECT f.*, u.email as user_email
FROM public.feedback_submissions f
LEFT JOIN users u ON f.user_id = u.id
WHERE f.status = 'unread'
ORDER BY f.created_at DESC
LIMIT 20 OFFSET 0;
```

**Index Usage:**
```sql
-- Check if indexes are being used
SELECT
  schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'feedback_submissions';
```

### Cleanup Tasks

**Remove Test Data (if any):**
```sql
-- Be careful! Only in development
DELETE FROM public.feedback_submissions
WHERE user_id IN (
  SELECT id FROM users WHERE email LIKE '%test%'
);
```

---

## Troubleshooting

### Issue: Badge Not Updating

**Symptoms:**
- Notification count stays same after marking as seen
- Need to refresh page to see update

**Diagnosis:**
```javascript
// Check if event is firing
window.addEventListener('feedbackStatusChanged', () => {
  console.log('Event received!')
})
```

**Fix:**
1. Verify event dispatch in `updateStatus()` function
2. Check listener registration in `UserDropdown`
3. Ensure cleanup in useEffect return

### Issue: Feedback Not Submitting

**Symptoms:**
- Submit button does nothing
- No error message

**Diagnosis:**
```bash
# Check backend logs
aws logs tail /ecs/cirkelline-system-backend --follow

# Check network tab
# Look for POST /api/feedback request
# Check response status and body
```

**Common Causes:**
- Anonymous user (check `user.isAnonymous`)
- Network error (check API URL)
- Validation error (check character limits)

**Fix:**
1. Verify user authentication
2. Check NEXT_PUBLIC_API_URL
3. Validate input lengths

### Issue: Admin Page Shows 403 Error

**Symptoms:**
- Cannot access `/admin/feedback`
- 403 Forbidden error

**Diagnosis:**
```sql
-- Check user admin status
SELECT id, email, is_admin FROM users WHERE email = 'opnureyes2@gmail.com';
```

**Fix:**
1. Verify `is_admin = true` in database
2. Check JWT token contains `is_admin` claim
3. Verify backend middleware checks `is_admin`

### Issue: Horizontal Scrollbar in Preview

**Symptoms:**
- Scrollbar appears when hovering feedback items

**Fix:**
Already fixed! Verify these classes are present:
```typescript
className="space-y-2 max-h-48 overflow-y-auto overflow-x-hidden"
```

### Issue: Badge Size Too Large

**Symptoms:**
- Notification circle bigger than username

**Fix:**
Already fixed! Verify these styles:
```typescript
className="w-5 h-5" // Circle size
<span className="text-[10px]"> // Text size
```

---

## Future Enhancements

### Phase 2 (Planned)

- [ ] **Email Notifications**
  - Notify admins of new feedback via email
  - Daily digest of unread feedback

- [ ] **Feedback Analytics**
  - Positive/negative ratio chart
  - Trend over time graph
  - Most common issues

- [ ] **Response System**
  - Admin can respond to feedback
  - User sees response in their dashboard

- [ ] **Categories**
  - Tag feedback by category (bug, feature request, etc.)
  - Filter by category

### Phase 3 (Future)

- [ ] **Export Functionality**
  - Export feedback to CSV
  - Generate PDF reports

- [ ] **Advanced Filters**
  - Date range picker
  - User search
  - Message content search

- [ ] **Bulk Actions**
  - Mark multiple as seen/done
  - Batch delete

---

## API Reference Summary

| Endpoint | Method | Auth | Admin | Description |
|----------|--------|------|-------|-------------|
| `/api/feedback` | POST | ✅ | ❌ | Submit feedback |
| `/api/feedback` | GET | ✅ | ✅ | List all feedback |
| `/api/feedback/:id/status` | PATCH | ✅ | ✅ | Update status |
| `/api/feedback/unread-count` | GET | ✅ | ✅ | Get unread count |

---

## File Reference

### Backend Files

| File | Lines | Description |
|------|-------|-------------|
| `my_os.py` | 2388-2482 | POST /api/feedback |
| `my_os.py` | 2484-2614 | GET /api/feedback |
| `my_os.py` | 2616-2689 | PATCH /api/feedback/:id/status |
| `my_os.py` | 2691-2746 | GET /api/feedback/unread-count |

### Frontend Files

| File | Description |
|------|-------------|
| `components/chat/FeedbackModal.tsx` | Feedback submission modal |
| `components/chat/ChatArea/Messages/MessageItem.tsx` | Message with thumbs up/down |
| `components/UserDropdown.tsx` | Badge and preview |
| `components/AdminNav.tsx` | Admin horizontal tabs |
| `app/admin/layout.tsx` | Admin layout wrapper |
| `app/admin/page.tsx` | Admin overview |
| `app/admin/feedback/page.tsx` | Feedback management page |
| `app/admin/users/page.tsx` | Users placeholder |
| `types/os.ts` | FeedbackSubmission interface |

---

## Changelog

### Version 1.0.0 (2025-10-24)

**Initial Release**

✅ **Features:**
- User feedback submission (thumbs up/down)
- Admin notification badge with count
- Feedback preview in dropdown
- Admin dashboard with filtering
- Status management (unread/seen/done)
- Real-time updates via events
- Pagination support

✅ **Security:**
- JWT authentication
- Admin authorization
- Anonymous user blocking
- Input validation
- Parameterized queries

✅ **Performance:**
- Database indexes
- Efficient queries
- Polling optimization
- Event-driven updates

---

## Support

**For Issues:**
1. Check [Troubleshooting](#troubleshooting) section
2. Review CloudWatch logs
3. Check database connectivity
4. Verify authentication

**For Questions:**
- Email: opnureyes2@gmail.com (Ivo)
- Documentation: `/docs/`

---

**Document Status:** ✅ Production Ready
**Maintained By:** Cirkelline Development Team
**Next Review:** 2025-11-24

