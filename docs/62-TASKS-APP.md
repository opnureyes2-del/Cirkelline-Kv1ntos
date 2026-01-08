# Tasks App

**Version:** v1.3.7
**Last Updated:** 2025-12-19

---

## Overview

The Tasks App is a standalone task management system that works without external connections. Tasks are stored in PostgreSQL. Users can optionally connect Google Tasks for two-way sync.

**Key Features:**
- Standalone mode (works without Google)
- Optional Google Tasks sync (pull + write-through)
- Multiple task lists with custom colors
- Priority levels (Low, Medium, High, Urgent)
- Due dates and notes
- Show/hide completed tasks toggle
- AI agent integration for task management
- Mobile responsive design

---

## Architecture

### Backend

**File:** `cirkelline/endpoints/tasks.py` (935 lines)

### AI Agent Tools

**File:** `cirkelline/tools/tasks_tools.py` (651 lines)

### Frontend

| File | Purpose |
|------|---------|
| `hooks/useStandaloneTasks.ts` | State management hook (499 lines) |
| `components/TasksPanel.tsx` | Entry point, props forwarding |
| `components/TasksBoardView.tsx` | Board/list view with layout modes |
| `components/TaskColumn.tsx` | Individual list column with CRUD |
| `components/TaskCard.tsx` | Task card with priority indicator |
| `components/TaskSkeleton.tsx` | Loading skeleton |
| `types/standaloneTasks.ts` | TypeScript types (96 lines) |

---

## Database Schema

### Tables

**task_lists:**
```sql
CREATE TABLE task_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    source VARCHAR(50) DEFAULT 'local',        -- 'local' | 'google'
    external_id VARCHAR(255),                  -- Google tasklist ID
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**tasks:**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    notes TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(20) DEFAULT 'medium',     -- 'low' | 'medium' | 'high' | 'urgent'
    position INTEGER DEFAULT 0,
    parent_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    external_id VARCHAR(255),                  -- Google task ID
    source VARCHAR(50) DEFAULT 'local',        -- 'local' | 'google'
    sync_status VARCHAR(50) DEFAULT 'local',   -- 'local' | 'synced' | 'pending'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX idx_task_lists_user ON task_lists(user_id);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_list ON tasks(list_id);
CREATE INDEX idx_tasks_due ON tasks(due_date);
```

---

## API Endpoints

### Task List Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/standalone-tasks/lists` | List all task lists |
| POST | `/api/standalone-tasks/lists` | Create task list |
| GET | `/api/standalone-tasks/lists/{id}` | Get task list details |
| PUT | `/api/standalone-tasks/lists/{id}` | Update task list |
| DELETE | `/api/standalone-tasks/lists/{id}` | Delete task list |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/standalone-tasks/lists/{id}/tasks` | Get tasks in list |
| POST | `/api/standalone-tasks/lists/{id}/tasks` | Create task in list |
| GET | `/api/standalone-tasks/tasks/{id}` | Get task details |
| PUT | `/api/standalone-tasks/tasks/{id}` | Update task |
| DELETE | `/api/standalone-tasks/tasks/{id}` | Delete task |
| POST | `/api/standalone-tasks/tasks/{id}/complete` | Toggle task completion |

### Sync Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/standalone-tasks/sync/status` | Check if Google connected |
| POST | `/api/standalone-tasks/sync/google/pull` | Pull tasks from Google |

### Request/Response Examples

**Create Task List:**
```typescript
// POST /api/standalone-tasks/lists
{
  "name": "Work Tasks",
  "color": "#4A90D9",
  "is_default": false
}
```

**Create Task:**
```typescript
// POST /api/standalone-tasks/lists/{list_id}/tasks
{
  "title": "Complete project report",
  "notes": "Include Q4 metrics",
  "due_date": "2025-12-20T17:00:00Z",
  "priority": "high"
}
```

**Task Response:**
```typescript
{
  "id": "uuid",
  "list_id": "uuid",
  "list_name": "Work Tasks",
  "list_color": "#4A90D9",
  "title": "Complete project report",
  "notes": "Include Q4 metrics",
  "due_date": "2025-12-20T17:00:00Z",
  "completed": false,
  "completed_at": null,
  "priority": "high",
  "position": 0,
  "parent_id": null,
  "external_id": null,
  "source": "local",
  "sync_status": "local",
  "created_at": "2025-12-19T10:00:00Z",
  "updated_at": "2025-12-19T10:00:00Z"
}
```

**List Tasks with Filters:**
```
GET /api/standalone-tasks/lists/{id}/tasks?completed=false&source=local
```

---

## useStandaloneTasks Hook

**File:** `cirkelline-ui/src/hooks/useStandaloneTasks.ts`

### State

```typescript
interface UseStandaloneTasksReturn {
  // List state
  lists: TaskList[];
  selectedListId: string | null;

  // Task state
  tasks: Task[];
  currentTask: Task | null;
  loading: boolean;
  error: string | null;

  // Google sync state
  googleConnected: boolean;
  isSyncing: boolean;
  lastSyncResult: SyncResult | null;

  // ... actions
}
```

### Actions

**List Actions:**
```typescript
fetchLists: (source?: 'local') => Promise<void>
createList: (data: CreateTaskListRequest) => Promise<TaskList | null>
updateList: (id: string, data: UpdateTaskListRequest) => Promise<boolean>
deleteList: (id: string) => Promise<boolean>
selectList: (id: string | null) => void
```

**Task Actions:**
```typescript
fetchTasks: (listId?: string, completed?: boolean, source?: 'local') => Promise<void>
fetchTaskDetail: (taskId: string) => Promise<void>
createTask: (data: CreateTaskRequest) => Promise<Task | null>
updateTask: (taskId: string, data: UpdateTaskRequest) => Promise<boolean>
deleteTask: (taskId: string) => Promise<boolean>
toggleTaskComplete: (taskId: string) => Promise<boolean>
clearError: () => void
clearCurrentTask: () => void
```

**Sync Actions:**
```typescript
checkSyncStatus: () => Promise<void>
syncFromGoogle: () => Promise<SyncResult | null>
disconnectGoogle: () => Promise<boolean>
```

**Utility Actions:**
```typescript
getDefaultList: () => TaskList | undefined
getTasksByList: (listId: string) => Task[]
hasLists: boolean
```

### Usage

```typescript
// In TasksBoardView.tsx
const {
  lists,
  tasks,
  loading,
  error,
  googleConnected,
  fetchLists,
  fetchTasks,
  createTask,
  toggleTaskComplete,
  syncFromGoogle,
} = useStandaloneTasks();

// Load data on mount
useEffect(() => {
  fetchLists();
  fetchTasks();
}, []);

// Create task in list
const handleCreateTask = async (listId: string, title: string) => {
  await createTask({ list_id: listId, title });
};

// Toggle completion
const handleToggle = async (taskId: string) => {
  await toggleTaskComplete(taskId);
};
```

---

## Google Tasks Sync

### How It Works

**Standalone Mode (Default):**
- Tasks stored only in PostgreSQL
- No Google connection required
- Full CRUD operations work locally

**Google Sync Mode (Optional):**
- User connects Google via OAuth
- **Pull Sync:** Tasks fetched from Google and merged with local DB
- **Write-Through:** New tasks created locally AND in Google simultaneously
- **Two-Way Updates:** Updates/deletes sync both directions

### Sync Flow

```
User creates task
       |
Check if Google connected
       |
+------+------+
|   Yes       |   No
v             v
Create in     Store locally
Google first  only
       |
Store locally
with external_id
```

### API Implementation

**Create Task with Google Sync:**
```python
# cirkelline/endpoints/tasks.py
async def create_task(request: Request, list_id: UUID, data: TaskCreate):
    google_service = await get_google_tasks_service(user_id)
    google_task_id = None
    sync_status = 'local'

    # If Google connected, create there first
    if google_service and list_external_id:
        google_task_id = await create_google_task(google_service, list_external_id, task_data)
        if google_task_id:
            sync_status = 'synced'

    # Then store in database
    # ... INSERT with external_id = google_task_id
```

**Pull Sync from Google:**
```python
# cirkelline/endpoints/tasks.py
async def sync_google_tasks(request: Request):
    # Fetch all task lists from Google
    tasklists = google_service.tasklists().list().execute()

    # For each list:
    # - If exists locally (by external_id): UPDATE
    # - If not exists: CREATE

    # For each task in each list:
    # - If exists locally (by external_id): UPDATE
    # - If not exists: CREATE
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

## Priority Levels

Tasks support four priority levels with visual indicators:

| Priority | Color | CSS Class |
|----------|-------|-----------|
| Low | Gray | `text-gray-400` |
| Medium | Blue | `text-blue-500` |
| High | Orange | `text-orange-500` |
| Urgent | Red | `text-red-500` |

**Priority Badge Component:**
```tsx
const priorityColors: Record<string, string> = {
  low: 'text-gray-400',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  urgent: 'text-red-500'
};

<Flag
  size={12}
  className={priorityColors[task.priority] || 'text-gray-400'}
/>
```

---

## AI Agent Integration

**File:** `cirkelline/tools/tasks_tools.py`

The `CirkellineTasksTools` class enables AI agents to manage tasks through conversation.

### Available Tools

| Tool | Description |
|------|-------------|
| `list_task_lists` | Get all task lists for user |
| `get_tasks` | Get tasks (all or by list) |
| `create_task` | Create new task with title, notes, due date, priority |
| `update_task` | Update existing task |
| `delete_task` | Delete task |
| `toggle_task_complete` | Mark task complete/incomplete |
| `create_task_list` | Create new task list |
| `delete_task_list` | Delete task list |

### Usage in Cirkelline

```python
# cirkelline/orchestrator/cirkelline_team.py
from cirkelline.tools.tasks_tools import CirkellineTasksTools

tasks_tools = CirkellineTasksTools(user_id=user_id, db=db)

# Tools are added to Cirkelline's available tools
```

### Example Agent Interactions

**User:** "Add a task to call mom tomorrow"
**Agent:** Creates task with title "Call mom" and due_date = tomorrow

**User:** "What tasks do I have?"
**Agent:** Lists all tasks across all lists

**User:** "Mark the project report task as done"
**Agent:** Finds and toggles completion on matching task

---

## Type Definitions

```typescript
// types/standaloneTasks.ts

interface TaskList {
  id: string;
  name: string;
  color: string;
  is_default: boolean;
  source: 'local' | 'google';
  external_id?: string;
  sync_enabled: boolean;
  last_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

interface Task {
  id: string;
  list_id: string;
  list_name?: string;
  list_color?: string;
  title: string;
  notes?: string;
  due_date?: string;
  completed: boolean;
  completed_at?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  position: number;
  parent_id?: string;
  external_id?: string;
  source: 'local' | 'google';
  sync_status: 'local' | 'synced' | 'pending';
  created_at?: string;
  updated_at?: string;
}

interface SyncStatus {
  google_connected: boolean;
  total_lists: number;
  synced_lists: number;
}

interface SyncResult {
  success: boolean;
  synced_lists: number;
  synced_tasks: number;
  message: string;
}
```

---

## UI Components

### TasksBoardView

**File:** `components/TasksBoardView.tsx`

Main container that displays task lists as columns (board view).

**Features:**
- Horizontal scrolling for multiple lists
- Full-width mode for single list view
- Settings integration (show/hide completed)
- Loading states

**Props:**
```typescript
interface TasksBoardViewProps {
  googleSyncEnabled?: boolean;
  layoutMode?: 'stacked' | 'side-by-side';
  showCompleted?: boolean;
  selectedListId?: string | null;
  onListChange?: (listId: string) => void;
  onListsLoaded?: (lists: TaskList[]) => void;
}
```

### TaskColumn

**File:** `components/TaskColumn.tsx`

Individual task list column with CRUD operations.

**Features:**
- Column header with list name and task count
- Inline rename functionality
- Settings menu (rename, delete)
- Add task form at bottom
- Scrollable task list

### TaskCard

**File:** `components/TaskCard.tsx`

Individual task card with completion toggle and priority indicator.

**Features:**
- Checkbox for completion toggle
- Strikethrough text when completed
- Priority flag icon with color
- Hover state for edit action
- Framer Motion animations

---

## Mobile Behavior

On mobile (< 768px):

1. **Header controls move to TopBar** (see `docs/60-APP-CONTAINER.md`)
2. **Settings dropdown** with:
   - Show/Hide completed toggle
   - Google Sync toggle (if connected)
3. **List selector** in header for quick list switching
4. **Stacked layout only** (no side-by-side on mobile)

---

## Task Sorting

Tasks are sorted within each list:

1. **Active tasks first** (completed = false)
2. **Completed tasks last** (completed = true)
3. **Within each group:** Original order preserved

```typescript
const visibleTasks = tasks
  .filter(task => showCompleted || !task.completed)
  .sort((a, b) => {
    if (a.completed === b.completed) return 0;
    return a.completed ? 1 : -1;
  });
```

---

## CSS Variables

**App Container Background:**
```css
:root {
  --app-container-bg: #E4E4E2;  /* Light mode */
}

.dark {
  --app-container-bg: #1A1A1A;  /* Dark mode */
}

/* Usage */
.task-column {
  background-color: var(--app-container-bg);
}
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
  if (!response.ok) {
    const error: TaskApiError = await response.json();
    throw new Error(error.detail || 'Operation failed');
  }
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

# List task lists
curl -s http://localhost:7777/api/standalone-tasks/lists \
  -H "Authorization: Bearer $TOKEN" | jq

# Create task list
curl -s -X POST http://localhost:7777/api/standalone-tasks/lists \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Tasks", "color": "#4A90D9"}' | jq

# Create task
curl -s -X POST http://localhost:7777/api/standalone-tasks/lists/{LIST_ID}/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "priority": "high",
    "due_date": "2025-12-20T17:00:00Z"
  }' | jq

# Toggle task complete
curl -s -X POST http://localhost:7777/api/standalone-tasks/tasks/{TASK_ID}/complete \
  -H "Authorization: Bearer $TOKEN" | jq

# Sync from Google
curl -s -X POST http://localhost:7777/api/standalone-tasks/sync/google/pull \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Frontend Testing

1. Open tasks panel from sidebar
2. Create task list (should appear as column)
3. Add tasks with different priorities
4. Toggle task completion
5. Toggle show/hide completed
6. Toggle Google Sync (if connected)
7. Test on mobile (stacked layout)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tasks not showing | Check list filter, ensure list is selected |
| Google sync fails | Check OAuth connection in Google settings |
| No default list | First list created becomes default |
| Priority not saving | Ensure priority value is lowercase |
| Completed tasks visible | Check "Show completed" toggle in settings |
| Mobile layout broken | Ensure layoutMode prop is passed correctly |

---

## Related Documentation

- `docs/60-APP-CONTAINER.md` - App Container architecture (layout modes, resize)
- `docs/61-CALENDAR-APP.md` - Calendar App (similar architecture pattern)
- `docs/12-GOOGLE-SERVICES.md` - Google OAuth and API integration
