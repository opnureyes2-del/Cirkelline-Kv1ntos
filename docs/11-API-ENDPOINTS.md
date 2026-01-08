# CIRKELLINE API ENDPOINTS DOCUMENTATION

**Last Updated:** December 19, 2025
**Server:** http://localhost:7777 (Development) | https://api.cirkelline.com (Production)

---

## 📋 TABLE OF CONTENTS

1. [Authentication](#authentication)
2. [Document Management](#document-management)
3. [Chat & AI Agent](#chat--ai-agent)
4. [User Management](#user-management)
5. [Standalone Tasks (v1.3.7)](#standalone-tasks-v137)

---

## 🔐 AUTHENTICATION

All endpoints require JWT authentication via Bearer token in the `Authorization` header.

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### JWT Payload Structure

```json
{
  "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "user_name": "Ivo",
  "user_type": "Admin",
  "user_role": "admin",
  "email": "ivo@cirkelline.com",
  "exp": 1729612800
}
```

---

## 📄 DOCUMENT MANAGEMENT

### 1. Upload Document

Upload a document to the user's knowledge base. Supports private and admin-shared documents.

**Endpoint:** `POST /api/knowledge/upload`

**Authentication:** Required (Bearer token)

**Content-Type:** `multipart/form-data`

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File | ✅ Yes | - | The document file to upload (PDF, DOCX, TXT, etc.) |
| `is_shared` | String | ❌ No | `"false"` | Whether to share with all admins. Only admins can set to `"true"` |

**Request Example:**

```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('is_shared', 'true');  // Only for admins

const response = await fetch('http://localhost:7777/api/knowledge/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  },
  body: formData
});
```

**Response (Success - 200 OK):**

```json
{
  "message": "Document uploaded successfully",
  "document": {
    "id": "d4e5f6a7-b8c9-4d1e-a2b3-c4d5e6f7a8b9",
    "name": "company_policy.pdf",
    "type": "pdf",
    "size": 245760,
    "access_level": "admin-shared",
    "uploaded_at": "2025-10-21T21:18:33.000Z",
    "uploaded_by": "ee461076-8cbb-4626-947b-956f293cf7bf",
    "shared_by_name": "Ivo"
  }
}
```

**Response (Error - 403 Forbidden):**

```json
{
  "detail": "Only admins can share documents with other admins"
}
```

**Response (Error - 401 Unauthorized):**

```json
{
  "detail": "Invalid token"
}
```

**Implementation Details:**

- **File Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 1511-1587)
- **Metadata Creation:** Uses `create_document_metadata()` for admin-shared, `create_private_document_metadata()` for private
- **Embeddings:** Automatically generates vector embeddings using Gemini for semantic search
- **Database:** Stores content in `ai.agno_knowledge`, embeddings in `ai.agno_embeddings`

**Access Control Rules:**

| User Type | Can Upload Private | Can Upload Admin-Shared |
|-----------|-------------------|------------------------|
| Regular User | ✅ Yes | ❌ No (403 Forbidden) |
| Admin | ✅ Yes | ✅ Yes |

**Metadata Structure (Admin-Shared):**

```json
{
  "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "user_type": "Admin",
  "access_level": "admin-shared",
  "uploaded_by": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "uploaded_at": "2025-10-21T21:18:33.000Z",
  "uploaded_via": "frontend_chat",
  "shared_by_name": "Ivo"
}
```

---

### 2. List Documents

Retrieve list of documents accessible to the current user.

**Endpoint:** `GET /api/documents`

**Authentication:** Required (Bearer token)

**Query Parameters:** None

**Request Example:**

```javascript
const response = await fetch('http://localhost:7777/api/documents', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  }
});
```

**Response (Success - 200 OK):**

```json
{
  "documents": [
    {
      "id": "a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9",
      "name": "my_notes.pdf",
      "type": "pdf",
      "size": 123456,
      "description": "Personal meeting notes",
      "metadata": {
        "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
        "access_level": "private",
        "uploaded_at": "2025-10-20T15:30:00.000Z"
      },
      "created_at": "2025-10-20T15:30:00.000Z",
      "updated_at": "2025-10-20T15:30:00.000Z"
    },
    {
      "id": "b2c3d4e5-f6a7-4b2c-d3e4-f5a6b7c8d9e0",
      "name": "company_policy.pdf",
      "type": "pdf",
      "size": 245760,
      "description": "Company policies shared with all admins",
      "metadata": {
        "user_id": "2c0a495c-3e56-4f12-ba68-a2d89e2deb71",
        "access_level": "admin-shared",
        "uploaded_at": "2025-10-21T10:00:00.000Z",
        "shared_by_name": "Rasmus"
      },
      "created_at": "2025-10-21T10:00:00.000Z",
      "updated_at": "2025-10-21T10:00:00.000Z"
    }
  ],
  "total": 2
}
```

**Implementation Details:**

- **File Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 1686-1774)
- **Filtering Logic:**
  - Regular users see only their own documents (`user_id` matches)
  - Admins see their documents + all admin-shared documents
- **Database Query:** Uses SQL with `OR` conditions for admin access

**SQL Query (Admins):**

```sql
SELECT * FROM ai.agno_knowledge
WHERE
  metadata->>'user_id' = :user_id  -- User's own documents
  OR
  metadata->>'access_level' = 'admin-shared'  -- All admin-shared documents
ORDER BY created_at DESC;
```

**SQL Query (Regular Users):**

```sql
SELECT * FROM ai.agno_knowledge
WHERE metadata->>'user_id' = :user_id
ORDER BY created_at DESC;
```

---

### 3. Delete Document

Delete a document from the knowledge base. Users can only delete their own documents.

**Endpoint:** `DELETE /api/documents/{document_id}`

**Authentication:** Required (Bearer token)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | UUID | ✅ Yes | The ID of the document to delete |

**Request Example:**

```javascript
const documentId = 'a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9';
const response = await fetch(`http://localhost:7777/api/documents/${documentId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  }
});
```

**Response (Success - 200 OK):**

```json
{
  "message": "Document deleted successfully",
  "document_id": "a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9"
}
```

**Response (Error - 404 Not Found):**

```json
{
  "detail": "Document not found or you don't have permission to delete it"
}
```

**Implementation Details:**

- **File Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 1846-1926)
- **Permission Check:** Verifies document belongs to user before deletion
- **Cascade Delete:** Automatically deletes associated vector embeddings (FK constraint)

**Access Control:**

- Users can only delete documents where `metadata.user_id` matches their JWT `user_id`
- Admins can delete their own documents and admin-shared documents they created
- Cannot delete other users' private documents (even as admin)

---

### 4. Get Document Status

Check if a document exists and retrieve its metadata.

**Endpoint:** `GET /api/documents/{document_id}/status`

**Authentication:** Required (Bearer token)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | UUID | ✅ Yes | The ID of the document |

**Request Example:**

```javascript
const documentId = 'a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9';
const response = await fetch(`http://localhost:7777/api/documents/${documentId}/status`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  }
});
```

**Response (Success - 200 OK):**

```json
{
  "exists": true,
  "document": {
    "id": "a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9",
    "name": "my_notes.pdf",
    "status": "ready",
    "embeddings_count": 45,
    "metadata": {
      "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
      "access_level": "private"
    }
  }
}
```

**Response (Not Found - 200 OK):**

```json
{
  "exists": false
}
```

---

## 💬 CHAT & AI AGENT

### 1. Send Message to Cirkelline

Send a message to the Cirkelline AI agent and receive a response. The agent automatically searches the user's knowledge base when relevant.

**Endpoint:** `POST /teams/cirkelline/runs`

**Authentication:** Required (Bearer token)

**Content-Type:** `multipart/form-data`

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | String | ✅ Yes | - | The user's message/question |
| `user_id` | String | ✅ Yes | - | User ID (from JWT, also in FormData for agent context) |
| `session_id` | String | ❌ No | Auto-generated | Session ID for conversation continuity |
| `stream` | Boolean | ❌ No | `false` | Whether to stream the response |

**Request Example (Non-Streaming):**

```javascript
const formData = new FormData();
formData.append('message', 'What documents do I have access to?');
formData.append('user_id', 'ee461076-8cbb-4626-947b-956f293cf7bf');
formData.append('session_id', 'sess-123-abc-456');
formData.append('stream', 'false');

const response = await fetch('http://localhost:7777/teams/cirkelline/runs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  },
  body: formData
});
```

**Response (Success - 200 OK):**

```json
{
  "content": "You have access to 2 documents:\n\n1. **my_notes.pdf** - Your personal meeting notes from yesterday\n2. **company_policy.pdf** - Company-wide HR policies (shared by Rasmus)\n\nWould you like me to help you with anything specific from these documents?",
  "session_id": "sess-123-abc-456",
  "run_id": "run-789-def-012",
  "model": "gemini-2.5-flash",
  "metrics": {
    "time": 1.234,
    "tokens": 156
  }
}
```

**Request Example (Streaming):**

```javascript
const formData = new FormData();
formData.append('message', 'Summarize my notes');
formData.append('user_id', 'ee461076-8cbb-4626-947b-956f293cf7bf');
formData.append('stream', 'true');

const response = await fetch('http://localhost:7777/teams/cirkelline/runs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  },
  body: formData
});

// Read streaming response
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data.content);  // Stream content
    }
  }
}
```

**Implementation Details:**

- **File Location:** `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 1142-1283)
- **Knowledge Retrieval:** Uses custom `filtered_knowledge_retriever()` function
- **Access Control:** Retriever automatically filters documents based on user permissions
- **Session Management:** Maintains conversation history via `session_id`

**How Knowledge Filtering Works:**

1. Agent receives message: "What documents do I have?"
2. Agent calls `search_knowledge_base()` tool (because instructions say to)
3. Custom retriever intercepts the search:
   - Gets user_id and user_type from `dependencies` parameter
   - Searches vector DB for semantically relevant documents
   - Filters results to only documents user can access
   - Returns filtered list to agent
4. Agent responds with accessible documents only

**Custom Retriever Function:**

```python
def filtered_knowledge_retriever(
    agent: Any,
    query: str,
    num_documents: Optional[int] = 5,
    **kwargs  # Receives user_id, user_type from dependencies
) -> Optional[List[Dict]]:
    user_id = kwargs.get('user_id')
    user_type = kwargs.get('user_type', 'Regular')
    is_admin = user_id in ADMIN_USER_IDS or user_type.lower() == 'admin'

    # Search ALL documents
    search_results = knowledge.search(query=query, max_results=num_documents * 2)

    # Filter by permissions
    filtered_results = []
    for doc in search_results:
        doc_user_id = doc.meta_data.get('user_id')
        doc_access = doc.meta_data.get('access_level', 'private')

        # Rule 1: User owns document
        if doc_user_id == user_id:
            filtered_results.append(doc)
        # Rule 2: Admin + admin-shared
        elif doc_access == 'admin-shared' and is_admin:
            filtered_results.append(doc)
        # Rule 3: Public (future)
        elif doc_access == 'public':
            filtered_results.append(doc)

    return filtered_results[:num_documents]
```

---

## 👤 USER MANAGEMENT

### 1. User Signup

Create a new user account.

**Endpoint:** `POST /api/signup`

**Authentication:** Not required

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response (Success - 201 Created):**

```json
{
  "message": "User created successfully",
  "user_id": "a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9",
  "email": "user@example.com",
  "user_type": "Regular"
}
```

**Response (Error - 400 Bad Request):**

```json
{
  "detail": "Email already registered"
}
```

---

### 2. User Login

Authenticate and receive JWT token.

**Endpoint:** `POST /api/login`

**Authentication:** Not required

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (Success - 200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "a1b2c3d4-e5f6-4a1b-c2d3-e4f5a6b7c8d9",
    "email": "user@example.com",
    "name": "John Doe",
    "user_type": "Regular"
  }
}
```

**Response (Error - 401 Unauthorized):**

```json
{
  "detail": "Invalid credentials"
}
```

---

## ✅ STANDALONE TASKS (v1.3.7)

Standalone task management endpoints. Works without external connections, with optional Google Tasks sync.

### Task List Endpoints

#### 1. List All Task Lists

**Endpoint:** `GET /api/standalone-tasks/lists`

**Authentication:** Required (Bearer token)

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | String | ❌ No | all | Filter by source: 'local', 'google', or omit for all |

**Response (Success - 200 OK):**

```json
{
  "lists": [
    {
      "id": "uuid",
      "name": "Work Tasks",
      "color": "#4A90D9",
      "is_default": true,
      "source": "local",
      "sync_enabled": false,
      "created_at": "2025-12-19T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### 2. Create Task List

**Endpoint:** `POST /api/standalone-tasks/lists`

**Authentication:** Required (Bearer token)

**Request Body:**

```json
{
  "name": "Work Tasks",
  "color": "#4A90D9",
  "is_default": false
}
```

**Response (Success - 201 Created):**

```json
{
  "id": "uuid",
  "name": "Work Tasks",
  "color": "#4A90D9",
  "is_default": false,
  "source": "local",
  "created_at": "2025-12-19T10:00:00Z"
}
```

---

#### 3. Update Task List

**Endpoint:** `PUT /api/standalone-tasks/lists/{list_id}`

**Request Body:**

```json
{
  "name": "Updated Name",
  "color": "#FF5733"
}
```

---

#### 4. Delete Task List

**Endpoint:** `DELETE /api/standalone-tasks/lists/{list_id}`

**Note:** Deletes all tasks in the list (CASCADE).

---

### Task Endpoints

#### 5. Get Tasks in List

**Endpoint:** `GET /api/standalone-tasks/lists/{list_id}/tasks`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `completed` | Boolean | ❌ No | Filter by completion status |
| `source` | String | ❌ No | Filter by source: 'local' or 'google' |

**Response (Success - 200 OK):**

```json
{
  "tasks": [
    {
      "id": "uuid",
      "list_id": "uuid",
      "list_name": "Work Tasks",
      "title": "Complete report",
      "notes": "Include Q4 metrics",
      "due_date": "2025-12-20T17:00:00Z",
      "completed": false,
      "priority": "high",
      "source": "local",
      "sync_status": "local"
    }
  ],
  "total": 1
}
```

---

#### 6. Create Task

**Endpoint:** `POST /api/standalone-tasks/lists/{list_id}/tasks`

**Request Body:**

```json
{
  "title": "Complete report",
  "notes": "Include Q4 metrics",
  "due_date": "2025-12-20T17:00:00Z",
  "priority": "high"
}
```

**Priority Values:** `low`, `medium`, `high`, `urgent`

---

#### 7. Update Task

**Endpoint:** `PUT /api/standalone-tasks/tasks/{task_id}`

**Request Body:**

```json
{
  "title": "Updated title",
  "completed": true,
  "priority": "medium"
}
```

---

#### 8. Delete Task

**Endpoint:** `DELETE /api/standalone-tasks/tasks/{task_id}`

---

#### 9. Toggle Task Completion

**Endpoint:** `POST /api/standalone-tasks/tasks/{task_id}/complete`

**Response:** Returns updated task with toggled completion status.

---

### Google Tasks Sync Endpoints

#### 10. Check Sync Status

**Endpoint:** `GET /api/standalone-tasks/sync/status`

**Response:**

```json
{
  "google_connected": true,
  "total_lists": 5,
  "synced_lists": 3
}
```

---

#### 11. Pull from Google Tasks

**Endpoint:** `POST /api/standalone-tasks/sync/google/pull`

**Response:**

```json
{
  "success": true,
  "synced_lists": 3,
  "synced_tasks": 25,
  "message": "Successfully synced 25 tasks from 3 lists"
}
```

---

### Tasks API Testing

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

# Create task (replace LIST_ID)
curl -s -X POST http://localhost:7777/api/standalone-tasks/lists/LIST_ID/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "priority": "high"}' | jq

# Toggle task complete (replace TASK_ID)
curl -s -X POST http://localhost:7777/api/standalone-tasks/tasks/TASK_ID/complete \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 📊 APPENDIX

### Document Access Control Matrix

| Scenario | Regular User | Admin User |
|----------|-------------|------------|
| View own private documents | ✅ Yes | ✅ Yes |
| View other's private documents | ❌ No | ❌ No |
| View admin-shared documents | ❌ No | ✅ Yes |
| Upload private documents | ✅ Yes | ✅ Yes |
| Upload admin-shared documents | ❌ No (403) | ✅ Yes |
| Delete own private documents | ✅ Yes | ✅ Yes |
| Delete own admin-shared documents | N/A | ✅ Yes |
| Delete other's documents | ❌ No | ❌ No |

### Document Metadata Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `user_id` | UUID | ✅ Yes | Owner of the document | `"ee461076-8cbb-4626-947b-956f293cf7bf"` |
| `user_type` | String | ✅ Yes | User type at upload time | `"Admin"` or `"Regular"` |
| `access_level` | String | ✅ Yes | Access control level | `"private"`, `"admin-shared"`, `"public"` |
| `uploaded_by` | UUID | ✅ Yes | User who uploaded (same as user_id) | `"ee461076-8cbb-4626-947b-956f293cf7bf"` |
| `uploaded_at` | ISO 8601 | ✅ Yes | Upload timestamp | `"2025-10-21T21:18:33.000Z"` |
| `uploaded_via` | String | ✅ Yes | Upload source | `"frontend_chat"`, `"api"`, `"test_script"` |
| `shared_by_name` | String | ❌ No | Name of admin who shared (admin-shared only) | `"Ivo"` |

### Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE_SNAKE_CASE",
  "timestamp": "2025-10-21T21:18:33.000Z"
}
```

### Rate Limiting

| Endpoint | Rate Limit | Window |
|----------|-----------|---------|
| `/api/knowledge/upload` | 100 requests | 1 hour |
| `/teams/cirkelline/runs` | 500 requests | 1 hour |
| `/api/documents` | 1000 requests | 1 hour |
| `/api/login` | 10 requests | 5 minutes |
| `/api/signup` | 5 requests | 1 hour |

---

**Last Updated:** December 19, 2025
**Version:** 1.3.7
**Maintained By:** Cirkelline Team
