# CIRKELLINE KNOWLEDGE DOCUMENT SYSTEM - COMPLETE REFERENCE
**Last Updated:** October 22, 2025
**Status:** Phase 3 Complete ✅ | Admin-Shared Upload Fixed ✅ | Custom Retriever Implemented ✅ | Document Listing Fixed ✅

---

## 📋 TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [Manual Filtering System](#manual-filtering-system)
7. [Access Control Rules](#access-control-rules)
8. [Critical Bug Fixes](#critical-bug-fixes)
9. [Testing & Verification](#testing--verification)
10. [Deployment Guide](#deployment-guide)
11. [Troubleshooting](#troubleshooting)
12. [Future Enhancements](#future-enhancements)

---

## 📊 SYSTEM OVERVIEW

### Purpose
Complete document management system integrated into Cirkelline with:
- **User Isolation**: Private documents per user
- **Admin Collaboration**: Shared documents between admins
- **Real-time RAG**: Knowledge base integration for AI queries
- **Manual Filtering**: Python-based access control (not Agno's knowledge_filters)

### Key Features
✅ Upload documents via UI
✅ View documents in sidebar
✅ Delete with confirmation
✅ Real-time status tracking
✅ Per-user isolation
✅ Admin document sharing
✅ RAG search with manual filtering
✅ Conversation history override protection

### Technology Stack
- **Backend**: Agno AgentOS + FastAPI + Python
- **Database**: PostgreSQL 16 + pgvector
- **Vector Search**: Gemini embeddings + hybrid search
- **Frontend**: React + TypeScript
- **Authentication**: JWT tokens
- **Deployment**: AWS ECS Fargate + RDS

---

## 🏗️ ARCHITECTURE

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CIRKELLINE FRONTEND                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Upload     │  │  Documents   │  │   Delete     │      │
│  │   Dialog     │  │   Sidebar    │  │   Dialog     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  JWT Middleware → extracts user_id → request.state   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Custom Endpoint: /teams/cirkelline/runs             │   │
│  │  - Manual knowledge filtering (NOT knowledge_filters)│   │
│  │  - Enhanced message with filtered docs               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Standard Endpoints:                                 │   │
│  │  - POST /api/knowledge/upload                        │   │
│  │  - GET  /api/documents                               │   │
│  │  - DELETE /api/documents/{id}                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              AGNO KNOWLEDGE BASE (PostgreSQL)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ai.agno_knowledge (Contents)                        │   │
│  │  - id, name, description, type, size, metadata       │   │
│  │  - metadata contains: user_id, access_level          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ai.agno_embeddings (Vector Search)                  │   │
│  │  - document_id, embeddings (pgvector)                │   │
│  │  - Gemini embeddings for hybrid search               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow: Document Upload

```
1. User uploads file in UI
   ↓
2. Frontend sends FormData to /api/knowledge/upload
   - file: File
   - is_shared: boolean (optional)
   - Authorization: Bearer {JWT}
   ↓
3. Backend extracts user_id from JWT
   ↓
4. Creates metadata:
   {
     "user_id": "...",
     "access_level": "private" | "admin-shared",
     "shared_by_name": "Ivo" (if admin-shared)
   }
   ↓
5. Saves to Agno Knowledge Base
   - Stores content in ai.agno_knowledge
   - Generates embeddings via Gemini
   - Stores vectors in ai.agno_embeddings
   ↓
6. Returns success to frontend
   ↓
7. Frontend auto-refreshes sidebar (3s interval)
```

### Data Flow: RAG Query with Manual Filtering

```
1. User asks: "what documents do I have?"
   ↓
2. Frontend sends to /teams/cirkelline/runs
   - message: "what documents do I have?"
   - user_id: "..." (from FormData)
   - Authorization: Bearer {JWT}
   ↓
3. Backend /teams/cirkelline/runs endpoint:

   STEP 1: Vector Search (NO FILTERS)
   ┌────────────────────────────────────────┐
   │ search_results = knowledge.search(     │
   │     query=message,                     │
   │     max_results=10                     │
   │ )                                      │
   │ # Returns ALL potentially relevant docs│
   └────────────────────────────────────────┘

   STEP 2: Manual Filtering in Python
   ┌────────────────────────────────────────┐
   │ filtered_results = []                  │
   │ for doc in search_results:             │
   │   doc_user_id = doc.metadata.user_id   │
   │   doc_access = doc.metadata.access_level│
   │                                        │
   │   # Rule 1: User owns document         │
   │   if doc_user_id == user_id:           │
   │     filtered_results.append(doc)       │
   │                                        │
   │   # Rule 2: Admin + admin-shared       │
   │   elif doc_access == "admin-shared"    │
   │        and user_type == "Admin":       │
   │     filtered_results.append(doc)       │
   └────────────────────────────────────────┘

   STEP 3: Build Enhanced Message
   ┌────────────────────────────────────────┐
   │ if filtered_results:                   │
   │   enhanced_message = f"""             │
   │   You have access to these documents:  │
   │   {document_contents}                  │
   │                                        │
   │   User's question: {message}           │
   │   """                                  │
   │ else:                                  │
   │   enhanced_message = message           │
   └────────────────────────────────────────┘

   STEP 4: Run Cirkelline Agent
   ┌────────────────────────────────────────┐
   │ response = await cirkelline.arun(             │
   │     input=enhanced_message,            │
   │     session_id=session_id,             │
   │     user_id=user_id,                   │
   │     dependencies=agent_dependencies    │
   │     # NO knowledge_filters parameter!  │
   │ )                                      │
   └────────────────────────────────────────┘
   ↓
4. Cirkelline responds using ONLY current message
   - Instructions prevent using conversation history
   - Must use documents from enhanced_message
   ↓
5. Response returned to user
```

---

## 💾 DATABASE SCHEMA

### Table: ai.agno_knowledge

```sql
CREATE TABLE ai.agno_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    type TEXT,  -- 'pdf', 'docx', 'txt', etc.
    size BIGINT,  -- bytes
    content TEXT,  -- Full document text
    metadata JSONB,  -- CRITICAL: Contains access control
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast user_id lookups
CREATE INDEX idx_knowledge_user_id
ON ai.agno_knowledge ((metadata->>'user_id'));

-- Index for access_level lookups
CREATE INDEX idx_knowledge_access_level
ON ai.agno_knowledge ((metadata->>'access_level'));
```

### Metadata Structure

**Private Document:**
```json
{
  "user_id": "6f174494-1055-474c-8d6f-73afb6610745",
  "user_type": "Regular",
  "access_level": "private",
  "uploaded_by": "6f174494-1055-474c-8d6f-73afb6610745",
  "uploaded_at": "2025-10-21T10:30:00Z",
  "uploaded_via": "frontend_chat"
}
```

**Admin-Shared Document:**
```json
{
  "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "user_type": "Admin",
  "access_level": "admin-shared",
  "uploaded_by": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "uploaded_at": "2025-10-21T10:30:00Z",
  "uploaded_via": "frontend_chat",
  "shared_by_name": "Ivo"
}
```

### Table: ai.agno_embeddings

```sql
CREATE TABLE ai.agno_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES ai.agno_knowledge(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    chunk_text TEXT,
    embedding vector(768),  -- Gemini embedding dimension
    created_at TIMESTAMP DEFAULT NOW()
);

-- pgvector index for fast similarity search
CREATE INDEX idx_embeddings_vector
ON ai.agno_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 🔧 BACKEND IMPLEMENTATION

### File: my_os.py

#### Cirkelline Team Configuration (Lines 798-900)

**PHASE 3 - Agent Instructions (Lines 832-845):**

```python
instructions=[
    "You are Cirkelline, a warm and thoughtful personal assistant.",
    "",
    "═══════════════════════════════════════",
    "KNOWLEDGE BASE SEARCH CAPABILITY",
    "═══════════════════════════════════════",
    "",
    "You have direct access to search the knowledge base:",
    "• When users ask about documents ('my notes', 'my documents', 'what I uploaded', 'my files')",
    "• Use your search_knowledge_base() tool to find relevant documents",
    "• The custom retriever automatically filters for documents the user has access to",
    "• Regular users see only their private documents",
    "• Admins see their documents plus admin-shared documents",
    "• Results are automatically filtered - you'll only see what the user can access",
    "",
    # ... rest of instructions
]
```

**Why This Is Better (Phase 3):**
- Cirkelline now has `search_knowledge=True` and can search directly
- Custom retriever handles all filtering automatically
- Agent searches only when needed (proper RAG pattern)
- No document content leaking in UI messages
- Scalable to thousands of documents

---

## 🐛 CRITICAL BUG FIXES

### Bug #1: Admin-Shared Documents Not Working (UPLOAD ENDPOINT FIX)

**Date Fixed:** October 21, 2025 21:18 UTC

**Symptoms:**
- Admin uploads document with "Share with all admins" checkbox checked
- Document appears in uploader's "My Documents" instead of "Shared Documents"
- Other admins cannot see the document at all
- Cirkelline cannot access the document when other admins ask about it
- Database shows `access_level: "private"` when it should be `"admin-shared"`

**Root Cause:**
The `/api/knowledge/upload` endpoint was NOT accepting the `is_shared` parameter from the frontend. The function signature was:

```python
async def upload_to_knowledge(
    file: UploadFile = File(...),
    request: Request = None
)
```

It always called `create_private_document_metadata()`, ignoring the checkbox state from the UI.

**The Fix (my_os.py lines 1511-1587):**

```python
@app.post("/api/knowledge/upload")
async def upload_to_knowledge(
    file: UploadFile = File(...),
    is_shared: str = Form("false"),  # ← NOW ACCEPTS is_shared PARAMETER!
    request: Request = None
):
    """
    Upload file to user's knowledge base.
    Supports both private and admin-shared documents.
    """
    # ... JWT extraction ...

    # Parse is_shared flag
    is_shared_bool = is_shared.lower() == "true"

    # Only admins can create admin-shared documents
    if is_shared_bool and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only admins can share documents with other admins"
        )

    # Create metadata based on sharing preference
    if is_shared_bool:
        # Admin-shared document
        metadata = create_document_metadata(
            user_id=user_id,
            user_type=user_type,
            access_level="admin-shared",  # ← CORRECT ACCESS LEVEL!
            shared_by_name=user_name      # ← ATTRIBUTION
        )
        logger.info(f"📤 Creating ADMIN-SHARED document for all admins")
    else:
        # Private document
        metadata = create_private_document_metadata(
            user_id=user_id,
            user_type=user_type
        )
        logger.info(f"📤 Creating PRIVATE document")

    # Upload to knowledge base with correct metadata
    await knowledge.add_content_async(
        name=file.filename,
        path=temp_path,
        metadata=metadata,
        description=f"User uploaded document: {file.filename}"
    )
```

**What Changed:**
1. Added `is_shared: str = Form("false")` to function signature
2. Extract `user_name` from JWT for `shared_by_name` metadata field
3. Added permission check - only admins can create admin-shared docs
4. Conditional metadata creation based on `is_shared` flag
5. Proper logging to show which type of document is being created

**Impact:**
- ✅ Admin-shared documents now work end-to-end
- ✅ Documents appear in correct sidebar section ("Shared Documents")
- ✅ All admins can see and access admin-shared documents
- ✅ Cirkelline can retrieve admin-shared documents for all admins
- ✅ Non-admins are blocked from creating admin-shared documents
- ✅ Proper attribution with `shared_by_name` field

**Files Modified:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 1511-1587)

---

### Bug #2: Deleted Documents Still Appearing in Responses

**Date Fixed:** October 21, 2025

**Symptoms:**
- User deleted all documents from UI
- Cirkelline still listed the deleted documents when asked "what documents do I have?"
- Backend logs showed 0 accessible documents (correct)
- But Cirkelline's response didn't match backend's findings

**Root Cause:**
1. Cirkelline's instructions (line 733) told her to use `search_knowledge_base` tool
2. This tool doesn't exist (we removed `search_knowledge=True` from team config)
3. When instructed tool doesn't exist, agent falls back to conversation history/memories
4. Cirkelline has `enable_session_summaries=True` and `search_session_history=True`
5. She remembered documents from previous sessions and responded with cached data
6. Instructions didn't tell her to IGNORE conversation history for document state

**The Fix:**

**BEFORE (WRONG):**
```python
"When user asks about 'my notes', 'my documents', 'what I uploaded', 'my files':",
"• IMMEDIATELY search knowledge base using search_knowledge_base tool",  # ← TOOL DOESN'T EXIST!
"• Don't ask for clarification - search first, then present what you found",
"• The knowledge base contains their private documents with user isolation",
"• After searching, present results in a friendly, conversational way",
```

**AFTER (FIXED):**
```python
"CRITICAL: When user asks about documents ('my notes', 'my documents', 'what I uploaded', 'my files'):",
"• The filtered, accessible documents are PROVIDED TO YOU in the message itself",
"• You do NOT have a search tool - the backend already searched and filtered for you",
"• If documents are listed in the message, present them to the user",
"• If NO documents are listed in the message, tell the user they have no accessible documents",
"• NEVER rely on conversation history or memory for current document state",  # ← CRITICAL FIX
"• ALWAYS use the document information from the CURRENT message only",  # ← CRITICAL FIX
```

**Why This Works:**
- Agent now knows to ignore her memories about documents
- Agent will only report documents that are explicitly listed in enhanced_message
- When no documents are accessible, agent correctly reports "no documents"
- Aligns agent behavior with the manual filtering implementation

**Test Results:**
```
Backend logs:
📊 Step 2: Found 1 total documents from vector search
  📄 Evaluating: requirements.txt
     Owner: 2c0a495c-3e56-4f12-b...
     Access: private
     ❌ EXCLUDED: not accessible to this user
✅ Step 3: After filtering: 0 accessible documents

Cirkelline's response:
"It looks like you don't have any documents uploaded to your knowledge base
just yet. Is there anything I can help you with today?"

✅ CORRECT! No more deleted documents in response!
```

**Files Modified:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 728-739)

**Impact:**
- ✅ Eliminates stale document responses from conversation history
- ✅ Ensures real-time accuracy of document listings
- ✅ Prevents security issue where deleted documents appeared accessible
- ✅ Aligns agent behavior with manual filtering implementation

---

### Bug #3: Document Listing Not Working (PRODUCTION ISSUE - v1.1.27)

**Date Fixed:** October 22, 2025 08:00 UTC

**Symptoms:**
- User asks "list all available documents" on production (cirkelline.com)
- Cirkelline only returns semantically matching documents
- Private documents not appearing in results
- Generic queries like "documents" or "files" fail to list documents
- Different behavior than localhost

**Root Cause:**
The `search_my_documents` tool was using **semantic vector search** for ALL queries. When users asked to "list all documents", the system was searching for documents whose **content** semantically matched the word "documents", not listing all accessible documents.

Additionally, Cirkelline (the AI agent) was calling the tool with simplified queries like "documents" instead of the full user message "list all available documents", causing keyword detection to fail.

**Example of the Problem:**
```
User query: "list all available documents"
Cirkelline calls tool with: query="documents"
Tool checks: "documents" contains ['list', 'all', 'available']? ❌ NO
Result: SEARCH mode (semantic) instead of LIST mode
Returns: Only docs with content matching "documents"
```

**The Fix (v1.1.26 - FAILED):**

First attempt added keyword detection but it didn't work because keywords were in the user's original message, not in the simplified query passed to the tool.

```python
# v1.1.26 - FAILED
list_keywords = ['list', 'all', 'show', 'my documents', 'what documents', 'files i have']
is_listing = any(keyword in query.lower() for keyword in list_keywords)
# ❌ Didn't work - query was just "documents", not "list all documents"
```

**The Fix (v1.1.27 - SUCCESS):**

Enhanced keyword detection to treat **generic query terms** as LIST mode triggers:

```python
# my_os.py lines 361-447
@tool(name="search_my_documents")
def search_my_documents(query: str, max_results: int = 10, session_state: dict = None) -> str:
    """
    Search user's accessible documents in the knowledge base.
    Supports two modes: LIST ALL (show all documents) or SEARCH (semantic search).
    """

    # Step 1: Extract user context from session_state
    user_id = session_state.get('user_id') if session_state else None
    user_type = session_state.get('user_type', 'Regular')

    # Step 2: Detect if user wants to LIST ALL documents (not search)
    list_keywords = ['list', 'all', 'show', 'my documents', 'what documents', 'files i have', 'available']

    # CRITICAL FIX: Also treat generic "documents" query as LIST ALL
    # When Cirkelline calls tool with query="documents", user wants to see all docs
    query_lower = query.lower().strip()
    is_listing = any(keyword in query_lower for keyword in list_keywords) or query_lower in ['documents', 'files', 'my files', 'uploads']

    if is_listing:
        logger.info("📋 LIST mode - returning ALL accessible documents")

        # Direct database query for ALL documents
        all_docs_query = """
        SELECT id, name, description, metadata, content
        FROM ai.agno_knowledge
        ORDER BY created_at DESC
        """

        results = db.execute(all_docs_query)
        all_documents = results.fetchall()

        # Apply permission filtering
        accessible_documents = []
        for doc in all_documents:
            doc_metadata = doc[3] if doc[3] else {}
            doc_user_id = doc_metadata.get('user_id')
            doc_access_level = doc_metadata.get('access_level', 'private')

            # Permission rules
            if doc_user_id == user_id:
                accessible_documents.append(doc)
            elif doc_access_level == 'admin-shared' and is_admin:
                accessible_documents.append(doc)
            elif doc_access_level == 'public':
                accessible_documents.append(doc)
    else:
        logger.info("🔎 SEARCH mode - using vector similarity search")

        # Semantic search for relevant documents
        search_results = knowledge.search(
            query=query,
            max_results=max_results * 2
        )

        # Apply permission filtering to search results
        accessible_documents = []
        for result in search_results:
            doc_metadata = result.metadata if hasattr(result, 'metadata') else {}
            doc_user_id = doc_metadata.get('user_id')
            doc_access_level = doc_metadata.get('access_level', 'private')

            if doc_user_id == user_id:
                accessible_documents.append(result)
            elif doc_access_level == 'admin-shared' and is_admin:
                accessible_documents.append(result)
            elif doc_access_level == 'public':
                accessible_documents.append(result)

    # Format response with document list
    if not accessible_documents:
        return "No accessible documents found."

    # Build document list
    doc_list = []
    for doc in accessible_documents[:max_results]:
        # Extract document info
        if hasattr(doc, 'name'):
            doc_name = doc.name
            doc_metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        else:
            doc_name = doc[1]
            doc_metadata = doc[3] if doc[3] else {}

        # Get access level info
        access_level = doc_metadata.get('access_level', 'private')
        shared_by = doc_metadata.get('shared_by_name', '')

        if access_level == 'admin-shared' and shared_by:
            doc_list.append(f"- {doc_name} (Shared by {shared_by})")
        else:
            doc_list.append(f"- {doc_name}")

    mode_label = "LIST ALL" if is_listing else "SEARCH"
    return f"Found {len(accessible_documents)} accessible documents ({mode_label} mode):\n" + "\n".join(doc_list)
```

**What Changed:**

1. **Enhanced Keyword Detection:**
   ```python
   # v1.1.26 (FAILED)
   is_listing = any(keyword in query_lower for keyword in list_keywords)

   # v1.1.27 (SUCCESS)
   is_listing = any(keyword in query_lower for keyword in list_keywords) or query_lower in ['documents', 'files', 'my files', 'uploads']
   ```

2. **Fixed content_map Bug:**
   ```python
   # v1.1.26 (BUG)
   content_map = {result.name: result.content for result in search_results if hasattr(result, 'content')}
   # ❌ search_results doesn't exist in LIST mode!

   # v1.1.27 (FIXED)
   content_map = {}
   if not is_listing and 'search_results' in locals():
       content_map = {result.name: result.content for result in search_results if hasattr(result, 'content')}
   ```

**Dual-Mode System:**

| Mode | Trigger | Query | Result |
|------|---------|-------|--------|
| **LIST ALL** | Generic queries | "documents", "files", "list all" | ALL accessible documents from database |
| **SEARCH** | Specific queries | "contract terms", "vacation policy" | Top N semantically similar documents |

**Test Results:**

**Production (v1.1.27):**
```
User: "list all available documents"
Cirkelline calls tool: query="documents"
Tool detects: query_lower in ['documents', 'files', 'my files', 'uploads']
Mode: LIST ALL ✅
Result: Returns both ivo_private.txt AND README.md ✅
```

**CloudWatch Logs:**
```
2025-10-22 08:00:15 - __main__ - INFO - 📋 LIST mode - returning ALL accessible documents
2025-10-22 08:00:15 - __main__ - INFO - Found 2 accessible documents (LIST ALL mode):
  - README.md (Shared by Ivo)
  - ivo_private.txt
```

**Impact:**
- ✅ Document listing now works on production
- ✅ Generic queries ("documents", "files") trigger LIST ALL mode
- ✅ Specific queries still use semantic search
- ✅ Both private and admin-shared documents accessible
- ✅ Proper attribution for shared documents
- ✅ Clear mode indication in response

**Files Modified:**
- `/home/eenvy/Desktop/cirkelline/my_os.py` (lines 361-447)
- `/home/eenvy/Desktop/cirkelline/aws_deployment/task-definition.json` (image updated to v1.1.27)

**Deployment:**
- **v1.1.26:** Deployed but failed (keyword detection issue)
- **v1.1.27:** Successfully deployed and verified working ✅

---

## 🔐 CUSTOM KNOWLEDGE RETRIEVER (PHASE 3 - PROPER IMPLEMENTATION)

### Evolution from Manual Filtering to Custom Retriever

**Phase 2 Problem (Manual Filtering):**
- We were passing ALL filtered documents with EVERY message
- This wouldn't scale with 1000+ documents
- Documents were leaking in the UI (appearing in message content)
- Agent couldn't search knowledge dynamically - only used what we injected

**Phase 3 Solution (Custom Retriever):**
- Agent now has `search_knowledge=True` capability
- Custom retriever function filters documents DURING search
- Agent searches knowledge only when needed (proper RAG pattern)
- Returns only top 5-10 relevant docs, not all matching docs

### Phase 3 Implementation: Custom Knowledge Retriever (Lines 616-717)

```python
def filtered_knowledge_retriever(
    agent: Any,
    query: str,
    num_documents: Optional[int] = 5,
    **kwargs  # Receives user context from dependencies
) -> Optional[List[Dict]]:
    """
    Custom knowledge retriever that filters documents based on user permissions.
    Called automatically when agent uses search_knowledge_base() tool.
    """
    user_id = kwargs.get('user_id')
    user_type = kwargs.get('user_type', 'Regular').lower()

    if not user_id:
        return []

    is_admin = user_id in ADMIN_USER_IDS or user_type == 'admin'

    # Search knowledge base WITHOUT filters
    search_results = knowledge.search(
        query=query,
        max_results=num_documents * 2  # Get extra to account for filtering
    )

    # Filter results based on user permissions
    filtered_results = []
    for doc in search_results:
        doc_metadata = doc.meta_data if hasattr(doc, 'meta_data') else {}
        doc_user_id = doc_metadata.get('user_id')
        doc_access_level = doc_metadata.get('access_level', 'private')

        should_include = False

        # Rule 1: User owns document
        if doc_user_id == user_id:
            should_include = True
        # Rule 2: Admin shared access
        elif doc_access_level == 'admin-shared' and is_admin:
            should_include = True
        # Rule 3: Public documents (future)
        elif doc_access_level == 'public':
            should_include = True

        if should_include:
            filtered_results.append({
                'id': doc.id if hasattr(doc, 'id') else None,
                'name': doc.name if hasattr(doc, 'name') else 'Unknown',
                'content': doc.content if hasattr(doc, 'content') else "",
                'metadata': doc_metadata,
                'score': doc.score if hasattr(doc, 'score') else 1.0
            })

        if num_documents and len(filtered_results) >= num_documents:
            break

    return filtered_results
```

### Team Configuration with Custom Retriever (Lines 798-831)

```python
cirkelline = Team(
    members=[...],
    model=Gemini(id="gemini-2.5-flash"),
    tools=[...],
    name="Cirkelline",
    description="Personal assistant that helps with everyday tasks",
    # PHASE 3: Using custom knowledge retriever for proper filtering
    knowledge=knowledge,
    knowledge_retriever=filtered_knowledge_retriever,  # ← Custom retriever
    search_knowledge=True,  # ← Agent can search knowledge directly!
    db=db,
    # ... other parameters
)
```

### Simplified Endpoint - No More Manual Injection! (Lines 1142-1283)

```python
@app.post("/teams/cirkelline/runs")
async def cirkelline_with_custom_retriever(
    request: Request,
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    stream: bool = Form(False),
    user_id: str = Form(...)
):
    """
    PHASE 3 Implementation:
    - Agent now has search_knowledge=True and custom retriever
    - Retriever automatically filters documents based on user permissions
    - No manual filtering or document injection needed
    - Agent searches knowledge only when needed (proper RAG pattern)
    """

    # Build dependencies for agent context and retriever
    agent_dependencies = {
        'user_id': user_id,  # CRITICAL: Pass user_id for retriever filtering
        'user_name': user_name,
        'user_role': user_role,
        'user_type': user_type,
    }

    # Run Cirkelline - it will call the custom retriever when needed
    response = await cirkelline.arun(
        input=message,  # Pass original message, no enhancement needed!
        stream=stream,
        session_id=session_id,
        user_id=user_id,
        dependencies=agent_dependencies  # Includes user_id for retriever
    )

    return response
```

---

## 🚀 DEPLOYMENT GUIDE

### Local Development

**1. Start PostgreSQL with pgvector:**
```bash
docker run -d \
  --name cirkelline-postgres \
  -e POSTGRES_USER=cirkelline \
  -e POSTGRES_PASSWORD=cirkelline123 \
  -e POSTGRES_DB=cirkelline \
  -p 5532:5432 \
  pgvector/pgvector:pg16
```

**2. Set Environment Variables:**
```bash
# .env file
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
JWT_SECRET_KEY=your-secret-key-here
GOOGLE_API_KEY=your-gemini-key-here
```

**3. Run Backend:**
```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

**4. Run Frontend:**
```bash
cd cirkelline-ui
npm run dev
```

---

## 🔧 TROUBLESHOOTING

### Issue: Deleted documents still appearing

**Symptoms:**
- Document deleted from sidebar
- But Cirkelline still mentions it in responses

**Solution:**
- ✅ **FIXED** in my_os.py:728-739 (see Critical Bug Fixes section)
- Cirkelline's instructions now force using enhanced_message only
- No longer relies on conversation history for document state

---

## 🔮 FUTURE ENHANCEMENTS

### Phase 3: Public Documents
- New access_level: "public"
- Only admins can upload public docs
- All users can view (but not delete) public docs
- Use case: Terms of Service, Privacy Policy, Help docs

### Phase 4: Advanced UI/UX
- Search documents by name
- Filter by type (PDF, DOC, etc.)
- Document preview modal
- Bulk operations
- Drag & drop upload

---

**End of Complete Reference Documentation**

**Last Updated:** October 21, 2025
**Document Version:** 1.0.0
**Status:** Complete & Production Ready ✅
