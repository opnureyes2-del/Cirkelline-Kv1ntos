# Notion Integration - Complete Documentation

**Last Updated:** 2025-11-07
**Version:** v1.2.20 (Drag-and-Drop Column Ordering)
**Status:** ✅ Production Ready

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Registry System](#database-registry-system)
4. [OAuth Flow](#oauth-flow)
5. [Backend API Endpoints](#backend-api-endpoints)
6. [Frontend Implementation](#frontend-implementation)
7. [Dynamic Schema System](#dynamic-schema-system)
8. [Column Ordering & Customization](#column-ordering--customization)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Notion integration provides users with seamless access to their Notion workspace data directly within Cirkelline. Users can view, create, and manage their Notion databases without leaving the application.

### Key Features

- **✅ OAuth 2.0 Authentication** - Secure workspace connection
- **✅ Automatic Database Discovery** - Finds all user databases on connect
- **✅ Dynamic Registry System** - NO hardcoded database names
- **✅ Schema-Aware Queries** - Adapts to any database structure
- **✅ Real-Time Table View** - View all properties dynamically
- **✅ Type Classification** - Automatically categorizes databases (tasks, projects, companies, documentation)
- **✅ Encrypted Token Storage** - Secure credential management

### Supported Database Types

| Type | Description | Example Names |
|------|-------------|---------------|
| `tasks` | Task management databases | "Tasks", "To-Do", "My Tasks" |
| `projects` | Project tracking databases | "Projects", "Work Projects" |
| `companies` | Company/domain databases | "Companies", "Domains", "Clients" |
| `documentation` | Documentation databases | "Documentation", "Docs", "Knowledge Base" |

**IMPORTANT:** Database names are flexible - the system identifies databases by analyzing their properties, NOT by their names!

---

## Architecture

### High-Level Flow

```
User Connects Notion
    ↓
OAuth 2.0 Flow (Notion API)
    ↓
Store Encrypted Access Token
    ↓
Automatic Database Discovery
    ↓
Classify & Store in Registry (notion_user_databases)
    ↓
Frontend Requests Data by TYPE
    ↓
Backend Looks Up database_id from Registry
    ↓
Query Notion API by ID
    ↓
Return Data to Frontend
```

### Component Breakdown

1. **OAuth Layer** - Handles Notion workspace authorization
2. **Discovery Service** - Automatically finds and classifies databases
3. **Registry Database** - PostgreSQL table storing database metadata
4. **API Layer** - Dynamic endpoints that query by TYPE
5. **Frontend Hooks** - React hooks for data fetching
6. **UI Components** - Table views with dynamic columns

---

## Database Registry System

### The Core Concept

**PROBLEM:** Different users name their databases differently
- User A: "Tasks", "Companies", "Projects"
- User B: "To-Do", "Domains", "Work Items"

**SOLUTION:** Database Registry (`notion_user_databases` table)

### Registry Table Schema

```sql
CREATE TABLE notion_user_databases (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    database_id VARCHAR(255) NOT NULL,           -- Notion database ID
    database_title VARCHAR(255),                 -- User's database name
    database_type VARCHAR(50),                   -- Our classification
    user_label VARCHAR(255),                     -- Optional custom label
    schema JSONB NOT NULL,                       -- Complete property schema
    is_hidden BOOLEAN DEFAULT FALSE,
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, database_id)
);

CREATE INDEX idx_notion_user_dbs_user_id ON notion_user_databases(user_id);
CREATE INDEX idx_notion_user_dbs_type ON notion_user_databases(database_type);
CREATE INDEX idx_notion_user_dbs_database_id ON notion_user_databases(database_id);
```

### Database Classification Logic

Databases are classified by analyzing their property names:

```python
def classify_database(properties):
    """
    Classify database by analyzing its properties
    """
    prop_names_lower = [p.lower() for p in properties.keys()]

    # Tasks: has status/priority/due date
    if any(term in ' '.join(prop_names_lower) for term in ['status', 'priority', 'due']):
        return 'tasks'

    # Projects: has timeline/budget/team
    elif any(term in ' '.join(prop_names_lower) for term in ['timeline', 'budget', 'team', 'milestone']):
        return 'projects'

    # Companies: has domain/industry/size
    elif any(term in ' '.join(prop_names_lower) for term in ['domain', 'website', 'industry', 'company']):
        return 'companies'

    # Documentation: has content/tags/category
    elif any(term in ' '.join(prop_names_lower) for term in ['content', 'tags', 'category', 'documentation']):
        return 'documentation'

    return None  # Unclassified
```

### Registry Population

The registry is populated during:

1. **Initial OAuth Connection** - Discovers all databases
2. **Manual Sync** - User triggers re-discovery via `/api/notion/databases/sync`
3. **Periodic Background Sync** - (Future feature)

---

## OAuth Flow

### Configuration

**Environment Variables:**

```bash
# Development (localhost:7777)
NOTION_CLIENT_ID=<your-client-id>
NOTION_CLIENT_SECRET=<your-client-secret>
NOTION_TOKEN_ENCRYPTION_KEY=<64-char-hex>
NOTION_REDIRECT_URI=http://localhost:7777/api/oauth/notion/callback

# Production (api.cirkelline.com)
NOTION_CLIENT_ID=<production-client-id>
NOTION_CLIENT_SECRET=<production-client-secret>
NOTION_TOKEN_ENCRYPTION_KEY=<64-char-hex>
NOTION_REDIRECT_URI=https://api.cirkelline.com/api/oauth/notion/callback
```

**AWS Secrets Manager (Production):**
- Secret Name: `cirkelline-system/notion-credentials`
- Keys: `client_id`, `client_secret`, `token_encryption_key`, `redirect_uri`

### OAuth Endpoints

#### 1. Initiate OAuth Flow

```
GET /api/oauth/notion/connect
```

Redirects user to Notion authorization page.

#### 2. OAuth Callback

```
GET /api/oauth/notion/callback?code={auth_code}
```

**Process:**
1. Exchange authorization code for access token
2. Encrypt access token with `NOTION_TOKEN_ENCRYPTION_KEY`
3. Store in `notion_tokens` table
4. **Trigger automatic database discovery**
5. Store discovered databases in registry
6. Redirect to frontend with success

#### 3. Check Connection Status

```
GET /api/oauth/notion/status
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "connected": true,
  "workspace_name": "Ivo's Workspace",
  "workspace_id": "workspace-uuid"
}
```

#### 4. Disconnect

```
POST /api/oauth/notion/disconnect
Authorization: Bearer {jwt_token}
```

Removes all Notion data for user (tokens + registry entries).

---

## Backend API Endpoints

### Core Dynamic Endpoint (NEW)

#### Get Database Items

```
GET /api/notion/databases/{database_type}/items
Authorization: Bearer {jwt_token}
```

**Path Parameters:**
- `database_type`: One of `tasks`, `projects`, `companies`, `documentation`

**How It Works:**
1. Extract `user_id` from JWT
2. Query registry: `SELECT database_id FROM notion_user_databases WHERE user_id = ? AND database_type = ?`
3. Query Notion API with `database_id`
4. Return all items with ALL properties

**Response:**
```json
{
  "tasks": [
    {
      "id": "page-uuid",
      "url": "https://notion.so/page-uuid",
      "created_time": "2025-11-07T10:00:00.000Z",
      "last_edited_time": "2025-11-07T12:00:00.000Z",
      "name": "Fix authentication bug",           // Property: Name
      "status": "In Progress",                    // Property: Status
      "priority": "High",                         // Property: Priority
      "due_date": "2025-11-10",                   // Property: Due Date
      "assignee": 1,                              // Count of people
      "project": 1,                               // Count of relations
      "description": "Auth token expiring early"  // Property: Description
    }
  ]
}
```

**Benefits:**
- ✅ Works with ANY database name ("Tasks", "To-Do", "My Tasks")
- ✅ Returns ALL properties (not just hardcoded ones)
- ✅ Single endpoint for all database types
- ✅ Type-safe and predictable

### Legacy Endpoints (Deprecated)

These still exist for backward compatibility but are NO LONGER USED:

```
GET /api/notion/tasks         ❌ OLD: Searches for "task" in name
GET /api/notion/projects      ❌ OLD: Searches for "project" in name
GET /api/notion/companies     ❌ OLD: Searches for "compan" in name
GET /api/notion/documentation ❌ OLD: Searches for "doc" in name
```

**DO NOT USE THESE!** They will be removed in future versions.

### Schema Endpoint

#### Get Database Schema

```
GET /api/notion/databases/{database_type}/schema
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "database_id": "29e07b81-0579-80a1-b779-000b69b71866",
  "database_title": "Tasks",
  "properties": {
    "Name": {
      "id": "title",
      "name": "Name",
      "type": "title"
    },
    "Status": {
      "id": "status",
      "name": "Status",
      "type": "status",
      "status": {
        "options": [
          {"name": "Not started", "id": "1", "color": "gray"},
          {"name": "In progress", "id": "2", "color": "blue"},
          {"name": "Done", "id": "3", "color": "green"}
        ]
      }
    },
    "Priority": {
      "id": "priority",
      "name": "Priority",
      "type": "select",
      "select": {
        "options": [
          {"name": "Low", "id": "1", "color": "gray"},
          {"name": "Medium", "id": "2", "color": "yellow"},
          {"name": "High", "id": "3", "color": "red"}
        ]
      }
    }
    // ... all other properties
  },
  "total_properties": 8
}
```

### Database List Endpoint

#### Get User's Databases

```
GET /api/notion/databases
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "databases": [
    {
      "database_id": "29e07b81-0579-80a1-b779-000b69b71866",
      "database_title": "Tasks",
      "database_type": "tasks",
      "user_label": null,
      "is_hidden": false,
      "last_synced": "2025-11-07T12:00:00.000Z",
      "created_at": "2025-11-01T10:00:00.000Z"
    },
    {
      "database_id": "29e07b81-0579-80ae-8b30-000b2a568b1a",
      "database_title": "Domains",
      "database_type": "companies",
      "user_label": null,
      "is_hidden": false,
      "last_synced": "2025-11-07T12:00:00.000Z",
      "created_at": "2025-11-01T10:00:00.000Z"
    }
  ]
}
```

### Manual Sync Endpoint

#### Trigger Database Re-Discovery

```
POST /api/notion/databases/sync
Authorization: Bearer {jwt_token}
```

Use this when:
- User adds new databases in Notion
- User renames databases
- Database properties change

**Response:**
```json
{
  "success": true,
  "discovered": 4,
  "classified": {
    "tasks": 1,
    "projects": 1,
    "companies": 1,
    "documentation": 1
  },
  "unclassified": 0
}
```

---

## Frontend Implementation

### React Hook: `useNotionData`

**Location:** `/cirkelline-ui/src/hooks/useNotionData.tsx`

```typescript
export function useNotionData() {
  const [companies, setCompanies] = useState<NotionCompany[]>([])
  const [projects, setProjects] = useState<NotionProject[]>([])
  const [tasks, setTasks] = useState<NotionTask[]>([])
  const [documentation, setDocumentation] = useState<NotionDocumentation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // NEW DYNAMIC ENDPOINTS
  const fetchCompanies = useCallback(async () => {
    const response = await authenticatedFetch('/api/notion/databases/companies/items')
    const data = await response.json()
    setCompanies(data.companies || [])
  }, [authenticatedFetch])

  const fetchProjects = useCallback(async () => {
    const response = await authenticatedFetch('/api/notion/databases/projects/items')
    const data = await response.json()
    setProjects(data.projects || [])
  }, [authenticatedFetch])

  const fetchTasks = useCallback(async () => {
    const response = await authenticatedFetch('/api/notion/databases/tasks/items')
    const data = await response.json()
    setTasks(data.tasks || [])
  }, [authenticatedFetch])

  const fetchDocumentation = useCallback(async () => {
    const response = await authenticatedFetch('/api/notion/databases/documentation/items')
    const data = await response.json()
    setDocumentation(data.documentation || [])
  }, [authenticatedFetch])

  return {
    companies,
    projects,
    tasks,
    documentation,
    loading,
    error,
    fetchCompanies,
    fetchProjects,
    fetchTasks,
    fetchDocumentation
  }
}
```

### Dynamic Table Component: `NotionTableView`

**Location:** `/cirkelline-ui/src/components/NotionTableView.tsx`

**Key Features:**
- **✅ Dynamic Schema Fetching** - Loads schema on mount
- **✅ Dynamic Column Generation** - Creates columns from schema
- **✅ Backward Compatible** - Works with both old flat format and new schema
- **✅ Universal Cell Renderer** - Handles 15+ Notion property types
- **✅ Row Virtualization** - Smooth scrolling with @tanstack/react-virtual

```typescript
function NotionTableView({ items, databaseType }: Props) {
  const [schema, setSchema] = useState<NotionDatabaseSchema | null>(null)

  // Fetch schema on mount
  useEffect(() => {
    const fetchSchema = async () => {
      const response = await fetch(
        `${apiUrl}/api/notion/databases/${databaseType}/schema`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      const data = await response.json()
      setSchema(data)
    }
    fetchSchema()
  }, [databaseType])

  // Generate columns dynamically from schema
  const columns = useDynamicColumns(schema)

  return <TanStackTable data={items} columns={columns} />
}
```

### Service Panel Container

**Location:** `/cirkelline-ui/src/components/ServicePanelContainer.tsx`

Integrates Notion UI into main chat interface with:
- Database selector tabs (only shows databases with items)
- Dynamic table view
- Create task button
- Notion connection status

---

## Dynamic Schema System

### Property Type Support

The system supports all Notion property types:

| Property Type | Backend Extraction | Frontend Display |
|---------------|-------------------|------------------|
| `title` | Extract text from array | Truncated text with link |
| `rich_text` | Extract text from array | Truncated text |
| `number` | Direct value | Formatted number |
| `select` | Extract name | Colored badge |
| `multi_select` | Extract names array | Multiple badges |
| `status` | Extract name | Status badge |
| `date` | Extract start date | Formatted date |
| `checkbox` | Boolean value | Checkbox |
| `url` | Direct value | Clickable link |
| `email` | Direct value | Mailto link |
| `phone_number` | Direct value | Text |
| `people` | Count | Number badge |
| `files` | Count | Number badge |
| `relation` | Count | Number badge |
| `formula` | Computed value | Depends on type |
| `rollup` | Aggregated value | Depends on type |
| `created_time` | Timestamp | Formatted date |
| `last_edited_time` | Timestamp | Formatted date |
| `created_by` | Person object | Name |
| `last_edited_by` | Person object | Name |

### Backward Compatibility

The accessor functions try multiple key formats:

```typescript
accessorFn: (row) => {
  const schemaKey = propName.toLowerCase().replace(/\s+/g, '_')

  // Try multiple formats for backward compatibility
  if (propName.toLowerCase().includes('status')) {
    return row[schemaKey] ?? row['status'] ?? row[propName] ?? null
  }

  if (propName.toLowerCase().includes('priority')) {
    return row[schemaKey] ?? row['priority'] ?? row[propName] ?? null
  }

  // Default: try schema key, exact name, then null
  return row[schemaKey] ?? row[propName] ?? null
}
```

This ensures compatibility with:
- ✅ Old flat format: `{ status: "In Progress", priority: "High" }`
- ✅ New schema format: `{ "Status": "In Progress", "Priority": "High" }`
- ✅ Mixed format: Works with any combination

---

## Column Ordering & Customization

### Overview

Users can customize the order of columns in their Notion database views with **drag-and-drop** functionality. Column preferences are saved per-user and persist across sessions.

### Key Features

- **✅ Drag-and-Drop** - Visually reorder columns by dragging column headers
- **✅ Persistent Preferences** - Custom order saved to database per user
- **✅ Smart Defaults** - New users see Name/title column first automatically
- **✅ TanStack Table Integration** - Smooth animations and state management
- **✅ Per-Database Configuration** - Each database type (tasks, projects, etc.) has its own column order

### User Experience

#### First-Time User
1. User connects Notion → databases discovered
2. Database tables display with **Name column first** by default
3. All other columns in Notion's original property order
4. User can drag columns to preferred positions
5. Order automatically saved on each drag operation

#### Returning User
1. Tables load with **user's custom column order**
2. Drag columns to reorder → saves automatically
3. Order persists across page reloads and sessions

### Implementation Architecture

```
User drags column
    ↓
TanStack Table updates columnOrder state
    ↓
handleDragEnd fires
    ↓
saveColumnOrder() API call
    ↓
Backend saves to user_property_order column
    ↓
Next load: fetches schema with user_property_order
    ↓
Frontend initializes columnOrder from saved preference
```

### Database Schema

Column ordering uses two fields in `notion_user_databases` table:

```sql
CREATE TABLE notion_user_databases (
    -- ... other columns ...
    property_order JSONB,           -- Default order (set during sync)
    user_property_order JSONB,      -- User's custom order
    -- ... other columns ...
);
```

**Field Usage:**
- `property_order`: Default order for all users (Name first, then Notion's original order)
- `user_property_order`: User-specific customization (overrides `property_order`)

### Frontend Implementation

**Location:** `/cirkelline-ui/src/components/NotionTableView.tsx`

**Dependencies:**
- `@dnd-kit/core` - Drag-and-drop primitives
- `@dnd-kit/sortable` - Sortable list behavior
- `@dnd-kit/modifiers` - Restrict drag axis
- `@tanstack/react-table` - Table state management

**Key Code Sections:**

```typescript
// 1. DnD Context wraps entire table
<DndContext
  collisionDetection={closestCenter}
  modifiers={[restrictToHorizontalAxis]}
  onDragEnd={handleDragEnd}
>
  <SortableContext items={columnOrder} strategy={horizontalListSortingStrategy}>
    <table>
      {/* Draggable column headers */}
    </table>
  </SortableContext>
</DndContext>

// 2. Handle drag completion
const handleDragEnd = (event: DragEndEvent) => {
  const { active, over } = event

  if (over && active.id !== over.id) {
    setColumnOrder((items) => {
      const oldIndex = items.indexOf(active.id as string)
      const newIndex = items.indexOf(over.id as string)

      const newOrder = arrayMove(items, oldIndex, newIndex)

      // Save to backend automatically
      saveColumnOrder(databaseType, newOrder).then((success) => {
        if (success) {
          console.log('✅ Column order saved successfully')
        } else {
          console.error('❌ Failed to save column order')
        }
      })

      return newOrder
    })
  }
}

// 3. TanStack Table integration
const table = useReactTable({
  data: items,
  columns,
  getCoreRowModel: getCoreRowModel(),
  state: {
    columnOrder: columnOrder,  // Connect state
  },
  onColumnOrderChange: setColumnOrder,  // Update callback
})

// 4. Draggable column headers
function DraggableColumnHeader({ column }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: column.id
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    cursor: 'grab',
  }

  return (
    <th ref={setNodeRef} style={style} {...attributes} {...listeners}>
      {column.columnDef.header}
    </th>
  )
}
```

**Critical Fix (v1.2.19):**
All columns must use property name as `id`, including Name/title column:

```typescript
// ❌ WRONG - breaks drag-and-drop
if (propConfig.type === 'title') {
  columns.push({
    id: 'title',  // Hardcoded ID doesn't match property name
    header: propName,
  })
}

// ✅ CORRECT - enables drag-and-drop for all columns
if (propConfig.type === 'title') {
  columns.push({
    id: propName,  // Uses actual property name (e.g., "Name")
    header: propName,
  })
}
```

### Backend Implementation

**Location:** `/home/eenvy/Desktop/cirkelline/my_os.py`

#### 1. Default Order (Database Sync)

When databases are discovered, Name/title property is placed first:

```python
# Lines 5406-5421
# Extract property order with Name/title first for better UX
properties = schema.get("properties", {})
property_keys = list(properties.keys())

# Find the title property (usually "Name")
title_property = None
for prop_name, prop_config in properties.items():
    if prop_config.get("type") == "title":
        title_property = prop_name
        break

# Put title first, then the rest in Notion's original order
if title_property and title_property in property_keys:
    property_order = [title_property] + [k for k in property_keys if k != title_property]
else:
    property_order = property_keys
```

This is stored in `property_order` column during sync.

#### 2. Save Custom Order API

**Endpoint:**
```
PUT /api/notion/databases/{database_type}/column-order
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "column_order": ["Name", "Status", "Priority", "Due Date", "Assignee"]
}
```

**Backend Logic:**

```python
# Lines 6123-6164
@app.put("/api/notion/databases/{database_type}/column-order")
async def save_column_order(
    database_type: str,
    request: Request
):
    user_id = getattr(request.state, 'user_id', None)
    body = await request.json()
    column_order = body.get("column_order", [])

    # Validate database type
    if database_type not in ['tasks', 'projects', 'companies', 'documentation']:
        raise HTTPException(status_code=400, detail="Invalid database type")

    # Get user's database ID from registry
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    engine = create_engine(os.getenv("DATABASE_URL"))

    with Session(engine) as session:
        result = session.execute(
            text("""
                SELECT database_id FROM notion_user_databases
                WHERE user_id = :user_id AND database_type = :database_type
                LIMIT 1
            """),
            {"user_id": user_id, "database_type": database_type}
        ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Database not found")

        database_id = result[0]

        # Save custom order
        session.execute(
            text("""
                UPDATE notion_user_databases
                SET user_property_order = :column_order,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = :user_id AND database_id = :database_id
            """),
            {
                "column_order": json.dumps(column_order),
                "user_id": user_id,
                "database_id": database_id
            }
        )
        session.commit()

    return {"success": True}
```

**Uses SQLAlchemy** (not psycopg) to match codebase conventions.

#### 3. Load Order (Schema Endpoint)

When frontend requests schema, backend returns user's custom order:

```python
# Priority order:
# 1. user_property_order (if exists) - User's custom preferences
# 2. property_order (fallback) - Default order (Name first)
# 3. schema keys (last resort) - Raw Notion order

if user_property_order:
    property_order = user_property_order
elif property_order:
    property_order = property_order
else:
    property_order = list(schema['properties'].keys())
```

### Hook Integration

**Location:** `/cirkelline-ui/src/hooks/useNotionData.tsx`

```typescript
const saveColumnOrder = useCallback(async (
  databaseType: 'tasks' | 'projects' | 'companies' | 'documentation',
  columnOrder: string[]
): Promise<boolean> => {
  setLoading(true);
  setError(null);

  try {
    await authenticatedFetch(`/api/notion/databases/${databaseType}/column-order`, {
      method: 'PUT',
      body: JSON.stringify({ column_order: columnOrder }),
    });

    console.log(`✅ Saved column order for ${databaseType}:`, columnOrder);
    return true;
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Failed to save column order';
    setError(errorMessage);
    console.error('Error saving column order:', err);
    return false;
  } finally {
    setLoading(false);
  }
}, [authenticatedFetch]);
```

### Testing Checklist

#### Drag-and-Drop Behavior
- [ ] Columns can be dragged by header
- [ ] Visual feedback during drag (cursor, opacity)
- [ ] Column moves to new position on drop
- [ ] Other columns shift smoothly
- [ ] ALL columns draggable (including Name)

#### Persistence
- [ ] Order saves automatically after drag
- [ ] Console shows "✅ Column order saved successfully"
- [ ] Reload page → order persists
- [ ] Close browser → reopen → order persists
- [ ] Different database types have independent orders

#### Default Behavior
- [ ] New user connects → Name column appears first
- [ ] Other columns in logical order
- [ ] After dragging → custom order replaces default

#### Error Handling
- [ ] Failed save shows error message
- [ ] Visual state reverts on save failure
- [ ] Backend logs show meaningful errors

### Known Limitations

1. **No Multi-Select Drag** - Only one column at a time
2. **No Pinned Columns** - All columns draggable (future: pin Name column)
3. **No Reset Button** - Must manually drag to restore default (future: "Reset to Default" button)
4. **No Column Visibility Toggle** - All columns always visible (future: show/hide columns)

### Future Enhancements

- **Column Visibility** - Show/hide individual columns
- **Pinned Columns** - Lock columns to prevent accidental dragging
- **Reset to Default** - One-click restore to default order
- **Column Presets** - Save multiple layout configurations
- **Bulk Reorder** - List view with up/down buttons

---

## Testing

### Manual Testing Checklist

#### OAuth Flow
- [ ] Click "Connect Notion" → redirects to Notion
- [ ] Authorize workspace → redirects back with success
- [ ] Check `notion_tokens` table has encrypted token
- [ ] Check `notion_user_databases` has discovered databases

#### Database Discovery
- [ ] All user databases appear in registry
- [ ] Databases correctly classified by type
- [ ] Schema stored completely in JSONB column
- [ ] `last_synced` timestamp is current

#### Data Fetching
- [ ] Open Notion panel → databases load
- [ ] Click database tab → items display
- [ ] All properties show correctly
- [ ] Names display (not "Untitled")
- [ ] Status/priority badges show correct colors

#### Dynamic Behavior
- [ ] Rename database in Notion → still works after sync
- [ ] Add new database → appears after sync
- [ ] Add new property → shows in table after sync
- [ ] Database with 25+ properties → all display

### API Testing

```bash
# 1. Check connection status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:7777/api/oauth/notion/status

# 2. List databases
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:7777/api/notion/databases

# 3. Get schema
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:7777/api/notion/databases/tasks/schema

# 4. Get items
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:7777/api/notion/databases/tasks/items

# 5. Trigger sync
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:7777/api/notion/databases/sync
```

---

## Troubleshooting

### Issue: Databases Not Showing

**Symptoms:**
- Notion connected but no databases in UI
- `notion_user_databases` table empty

**Diagnosis:**
```sql
SELECT * FROM notion_user_databases WHERE user_id = 'your-user-id';
```

**Solutions:**
1. **Trigger manual sync:**
   ```bash
   curl -X POST -H "Authorization: Bearer $TOKEN" \
     http://localhost:7777/api/notion/databases/sync
   ```

2. **Check backend logs:**
   ```bash
   tail -100 backend.log | grep -i notion
   ```

3. **Verify Notion token:**
   ```sql
   SELECT user_id, workspace_name, created_at
   FROM notion_tokens
   WHERE user_id = 'your-user-id';
   ```

### Issue: Items Showing "Untitled"

**Cause:** Property name mismatch between schema and data

**Solution:** The new accessor functions should handle this automatically. If still showing "Untitled":

1. Check what keys are in the data:
   ```javascript
   console.log('Item keys:', Object.keys(items[0]))
   ```

2. Check schema property names:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:7777/api/notion/databases/tasks/schema \
     | jq '.properties | keys'
   ```

3. Verify backend is extracting properties correctly (check logs)

### Issue: Database Not Classified

**Symptoms:**
- Database appears in registry with `database_type = NULL`
- Not showing in any tab

**Solution:**

1. Check property names:
   ```sql
   SELECT database_title, schema->'properties'
   FROM notion_user_databases
   WHERE user_id = 'your-user-id' AND database_type IS NULL;
   ```

2. Manually classify:
   ```sql
   UPDATE notion_user_databases
   SET database_type = 'tasks'  -- or 'projects', 'companies', 'documentation'
   WHERE database_id = 'database-uuid';
   ```

3. Improve classification logic in `classify_database()` function

### Issue: Token Encryption Errors

**Symptoms:**
- `cryptography.fernet.InvalidToken` error
- OAuth works but can't fetch data

**Cause:** `NOTION_TOKEN_ENCRYPTION_KEY` changed or incorrect

**Solution:**

1. **Check key format:**
   ```bash
   echo $NOTION_TOKEN_ENCRYPTION_KEY | wc -c
   # Should be 64 characters (32 bytes hex)
   ```

2. **Regenerate key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Update everywhere:**
   - `.env` file
   - AWS Secrets Manager (production)
   - Re-connect Notion for all users

### Issue: "Companies" Tab Missing

**This was the bug we just fixed!**

**Cause:** Old hardcoded endpoint searching for "compan" in database name, but user's database is named "Domains"

**Solution:** Use new dynamic endpoint `/api/notion/databases/companies/items` (already implemented)

---

## Implementation Files Reference

### Backend
- **Main File:** `/home/eenvy/Desktop/cirkelline/my_os.py`
  - OAuth endpoints: Lines 5500-5700
  - Database discovery: Lines 5700-5850
  - Schema endpoint: Lines 5863-5932
  - **Dynamic items endpoint:** Lines 5933-6090 ⭐ NEW
  - Legacy endpoints: Lines 6091-6500 (deprecated)

### Frontend
- **Hook:** `/cirkelline-ui/src/hooks/useNotionData.tsx`
- **Table View:** `/cirkelline-ui/src/components/NotionTableView.tsx` (578 lines)
- **Container:** `/cirkelline-ui/src/components/ServicePanelContainer.tsx`
- **Types:** `/cirkelline-ui/src/types/notion.ts`

### Database
- **Tokens Table:** `notion_tokens` (encrypted access tokens)
- **Registry Table:** `notion_user_databases` (database metadata & schemas)

---

## Future Enhancements

### Phase 2: Inline Editing
- Edit text, number, date, checkbox properties
- Update via Notion API
- Real-time UI updates

### Phase 3: Dropdown Editing
- Edit select, multi-select, status properties
- Dropdown pickers with current options
- Color-coded badges

### Phase 4: Rich Text Editing
- BlockNote editor integration
- Full rich text support
- Nested blocks

### Phase 5: Complex Properties
- People picker (resolve user names)
- Relation picker (link to other pages)
- File uploads

### Phase 6: Advanced Features
- Filters and sorting
- Bulk operations
- Export to CSV/Excel
- Offline mode with sync

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.2.20 | 2025-11-07 | **Drag-and-Drop Column Ordering**: Full implementation with persistent user preferences and smart defaults (Name first) |
| v1.2.19 | 2025-11-07 | **MAJOR**: Dynamic registry-based system. Fixed "Domains not showing" bug. |
| v1.2.12 | 2025-11-02 | Initial production release with OAuth & basic CRUD |

---

## Support

For issues or questions:
1. Check this documentation
2. Check [TROUBLESHOOTING.md](./02-TROUBLESHOOTING.md)
3. Check backend logs: `tail -100 backend.log | grep -i notion`
4. Check database: `SELECT * FROM notion_user_databases WHERE user_id = 'your-id'`

---

**Document Maintained By:** Development Team
**Last Review:** 2025-11-07
**Next Review:** After Phase 2 implementation
