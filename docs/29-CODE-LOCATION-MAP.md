# CODE LOCATION MAP

**Last Updated:** 2025-12-02
**Current Version:** v1.2.34.6
**Purpose:** Quick reference for finding functionality in the modular codebase

---

## 📋 Table of Contents

1. [Quick Reference](#quick-reference)
2. [Entry Point](#entry-point)
3. [Core Infrastructure](#core-infrastructure)
4. [AI Agents & Teams](#ai-agents--teams)
5. [API Endpoints](#api-endpoints)
6. [External Integrations](#external-integrations)
7. [Middleware & Auth](#middleware--auth)
8. [Helper Functions](#helper-functions)
9. [Tools & Utilities](#tools--utilities)
10. [Admin Features](#admin-features)
11. [Common Tasks](#common-tasks)

---

## Quick Reference

**"Where do I find...?"**

| Feature | File Location |
|---------|---------------|
| **Application startup** | `my_os.py` |
| **Login/Signup** | `cirkelline/endpoints/auth.py` |
| **JWT middleware** | `cirkelline/middleware/middleware.py` |
| **AI agents** | `cirkelline/agents/` |
| **API endpoints** | `cirkelline/endpoints/` |
| **Database connection** | `cirkelline/database.py` |
| **Google OAuth** | `cirkelline/integrations/google/oauth_endpoints.py` |
| **Notion OAuth** | `cirkelline/integrations/notion/oauth_endpoints.py` |
| **Knowledge base** | `cirkelline/endpoints/knowledge.py` |
| **Session management** | `cirkelline/endpoints/sessions.py` |
| **Memory search** | `cirkelline/tools/memory_search_tool.py` |
| **User preferences** | `cirkelline/endpoints/user.py` |

---

## Entry Point

### Main Application

**File:** `my_os.py` (1,017 lines)

**What it does:**
- FastAPI application setup
- Router registration (18 routers)
- CORS configuration
- AgentOS initialization
- Health check endpoint

**Key sections:**
```python
# Lines 1-50: Imports and core setup
# Lines 51-150: Router imports
# Lines 151-200: FastAPI app initialization
# Lines 201-300: Middleware setup
# Lines 301-400: Router registration
# Lines 401-500: Agent/Team initialization
# Lines 501-600: AgentOS setup
# Lines 601-800: Startup and health endpoints
```

---

## Core Infrastructure

### 1. Configuration

**File:** `cirkelline/config.py`

**Contains:**
- Logger setup
- Environment variable loading
- CORS settings

### 2. Database

**File:** `cirkelline/database.py`

**Contains:**
- PostgreSQL connection via SQLAlchemy
- PgVector extension setup
- Database session management
- Connection URL configuration

### 3. Knowledge Base

**File:** `cirkelline/knowledge_base.py`

**Contains:**
- PgVectorDb initialization
- 768-dim Gemini embeddings
- Hybrid search (semantic + BM25)

### 4. Data Models

**File:** `cirkelline/models.py`

**Contains:**
- `FileMetadata` class
- Pydantic models for API requests/responses

### 5. Shared Utilities

**Directory:** `cirkelline/shared/`

**Files:**
- `database.py` - Database helper utilities
- `jwt_utils.py` - JWT token generation and validation

---

## AI Agents & Teams

### Specialist Agents

**File:** `cirkelline/agents/specialists.py`

**Contains 4 agents:**
1. **Audio Specialist** - Transcription, sound identification
2. **Video Specialist** - Scene analysis, video understanding
3. **Image Specialist** - OCR, image description
4. **Document Specialist** - PDF/DOCX processing

**Usage:** Imported and registered in `my_os.py`

### Research Team

**File:** `cirkelline/agents/research_team.py`

**Contains 3 specialized researchers (v1.2.34):**
1. **DuckDuckGo Researcher** - News, current events, quick facts
2. **Exa Researcher** - Semantic/conceptual search, research topics
3. **Tavily Researcher** - Comprehensive deep search, analysis

**Team configuration:**
- Team leader decides which researcher(s) to use
- Leader synthesizes findings directly (no separate analyst)
- Coordinator mode, shared interactions

### Law Team

**File:** `cirkelline/agents/law_team.py`

**Contains 2 agents:**
1. **Legal Researcher** - Finds legal sources
2. **Legal Analyst** - Provides legal analysis

**Team configuration:** Coordinator mode, shared interactions

### Main Orchestrator

**Directory:** `cirkelline/orchestrator/`

**Files:**
- `cirkelline_team.py` - Main Cirkelline orchestrator team (includes MemoryManager v1.2.34.6)
- `instructions.py` - Callable instructions (Deep Research mode switching)
- `memory_manager.py` - ⚠️ DEPRECATED in v1.2.34 - using AGNO MemoryManager instead

**Cirkelline Team:**
- Coordinates all specialist agents and teams
- Routes requests based on intent
- Rewrites responses in conversational tone

---

## API Endpoints

### Core Endpoints

**File:** `cirkelline/endpoints/auth.py`

**Endpoints:**
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User authentication
- `POST /api/auth/logout` - Session termination

---

**File:** `cirkelline/endpoints/user.py`

**Endpoints:**
- `GET /api/user` - Get user profile
- `PATCH /api/user` - Update user profile
- `PATCH /api/user/preferences` - Update theme/notification preferences
- `GET /api/user/tier` - Get user's subscription tier
- `GET /api/user/subscription` - Get subscription details
- `POST /api/user/subscription/upgrade` - Upgrade subscription
- `POST /api/user/subscription/cancel` - Cancel subscription

---

**File:** `cirkelline/endpoints/knowledge.py`

**Endpoints:**
- `POST /api/knowledge/upload` - Upload documents to knowledge base
- `GET /api/knowledge` - List user's documents
- `DELETE /api/knowledge/{doc_id}` - Delete document
- `POST /api/knowledge/search` - Hybrid search across documents

---

**File:** `cirkelline/endpoints/sessions.py`

**Endpoints:**
- `GET /api/sessions` - List user's chat sessions
- `GET /api/sessions/{session_id}` - Get session details
- `DELETE /api/sessions/{session_id}` - Delete session

---

**File:** `cirkelline/endpoints/memories.py`

**Endpoints:**
- `GET /api/memories` - Get user's memories (enhanced with emotional context)

---

**File:** `cirkelline/endpoints/feedback.py`

**Endpoints:**
- `POST /api/feedback` - Submit message feedback
- `GET /api/feedback` - List feedback (admin only)
- `PATCH /api/feedback/{feedback_id}` - Update feedback status
- `DELETE /api/feedback/{feedback_id}` - Delete feedback

---

### Custom Cirkelline Endpoint

**File:** `cirkelline/endpoints/custom_cirkelline.py`

**Endpoint:**
- `POST /teams/cirkelline/runs` - Main chat endpoint with user-specific knowledge filtering

**Special features:**
- User isolation (filters by `user_id`)
- Knowledge base integration
- Session management
- Deep Research mode support
- Delegation freeze monitoring

---

### Tier System

**File:** `cirkelline/services/tier_service.py`

**Endpoints:**
- `GET /api/tiers/public` - Get public tier information (no auth required)
- All tier-related business logic

---

## External Integrations

### Google Services

**Directory:** `cirkelline/integrations/google/`

**Files:**

1. **`google_oauth.py`** - OAuth helper functions
   - Token encryption/decryption
   - Credentials building

2. **`oauth_endpoints.py`** - OAuth flow (4 endpoints)
   - `GET /api/oauth/google/connect` - Initiate OAuth
   - `GET /api/oauth/google/callback` - Handle OAuth callback
   - `GET /api/oauth/google/status` - Check connection status
   - `POST /api/oauth/google/disconnect` - Disconnect account

3. **`gmail_endpoints.py`** - Gmail integration (7 endpoints)
   - `GET /api/google/gmail/messages` - List emails
   - `GET /api/google/gmail/messages/{id}` - Get email details
   - `POST /api/google/gmail/messages/send` - Send email
   - `POST /api/google/gmail/messages/{id}/trash` - Trash email
   - Plus label management endpoints

4. **`calendar_endpoints.py`** - Calendar integration (5 endpoints)
   - `GET /api/google/calendar/events` - List events
   - `POST /api/google/calendar/events` - Create event
   - `GET /api/google/calendar/events/{id}` - Get event details
   - `PATCH /api/google/calendar/events/{id}` - Update event
   - `DELETE /api/google/calendar/events/{id}` - Delete event

5. **`tasks_endpoints.py`** - Google Tasks integration (12 endpoints)
   - Task list management (CRUD)
   - Task management (CRUD)
   - Task completion toggle

### Notion Integration

**Directory:** `cirkelline/integrations/notion/`

**Files:**

1. **`oauth_endpoints.py`** - OAuth flow (4 endpoints)
   - `GET /api/oauth/notion/connect` - Initiate OAuth
   - `GET /api/oauth/notion/callback` - Handle callback
   - `GET /api/oauth/notion/status` - Check status
   - `POST /api/oauth/notion/disconnect` - Disconnect

2. **`database_endpoints.py`** - Dynamic database operations (5 endpoints)
   - `GET /api/notion/databases` - List user's databases
   - `POST /api/notion/databases/discover` - Trigger discovery
   - `GET /api/notion/databases/{type}/items` - Get items by type
   - `POST /api/notion/databases/{type}/items` - Create item
   - `PATCH /api/notion/databases/{type}/columns` - Update column order

3. **`legacy_endpoints.py`** - Legacy static endpoints (5 endpoints)
   - Hardcoded endpoints for backward compatibility

**Helper:**
- `cirkelline/helpers/notion_helpers.py` - Schema discovery and classification

---

## Middleware & Auth

### Middleware

**File:** `cirkelline/middleware/middleware.py`

**Contains:**
- JWT authentication middleware
- User ID extraction from tokens
- Admin profile dependency injection
- Activity logging

**Key functions:**
- `jwt_middleware()` - Extracts user_id from JWT
- `get_user_id_dependency()` - Injects user_id into endpoints
- `get_admin_profile_dependency()` - Injects admin profile if admin

### JWT Utilities

**File:** `cirkelline/shared/jwt_utils.py`

**Contains:**
- `create_access_token()` - Generate JWT tokens
- `verify_token()` - Validate JWT tokens
- Token payload extraction
- Admin token handling

---

## Helper Functions

**Directory:** `cirkelline/helpers/`

### 1. Metadata Extraction

**File:** `metadata.py`

**Functions:**
- `extract_document_metadata()` - Extract metadata from uploaded files
- `create_file_metadata()` - Create FileMetadata objects

### 2. User Context

**File:** `user_context.py`

**Functions:**
- `build_user_context()` - Build context string for AI agents
- Includes admin profiles, preferences, tier info

### 3. Session Naming

**File:** `session_naming.py`

**Functions:**
- `generate_intelligent_session_name()` - AI-powered session naming
- Uses first user message to create meaningful names

### 4. Notion Helpers

**File:** `notion_helpers.py`

**Functions:**
- `discover_user_databases()` - Automatic database discovery
- `classify_database_type()` - Classify databases (Companies, Projects, etc.)
- `extract_database_schema()` - Extract property schemas

---

## Tools & Utilities

**Directory:** `cirkelline/tools/`

### 1. Knowledge Tools

**File:** `knowledge_tools.py`

**Contains:**
- Tools for AI agents to search knowledge base
- User-specific filtering

### 2. Memory Search Tools (v1.2.34.4)

**File:** `memory_search_tool.py`

**Contains:**
- `IntelligentMemoryTool` class - Topic-based memory retrieval
- `search_memories()` - SQL-level topic filtering (not loading all memories)
- `get_recent_memories()` - Get most recent memories

**Key Features:**
- SQL-level filtering: `WHERE topics LIKE '%"family"%'`
- Returns only matching memories (not all 100+)
- Token efficient (~90% reduction vs loading all)

### 3. Notion Tools

**File:** `notion_tools.py`

**Contains:**
- Tools for AI agents to interact with Notion
- Dynamic query building
- CRUD operations for all database types

### 4. Media Tools

**Directory:** `media/`

**Contains:**
- Media processing utilities for specialists
- File handling

---

## Admin Features

**Directory:** `cirkelline/admin/`

### Files:

1. **`users.py`** - User management (2 endpoints)
   - `GET /api/admin/users` - List all users with search/filter
   - `GET /api/admin/users/{user_id}` - Get user details

2. **`stats.py`** - System statistics (1 endpoint)
   - `GET /api/admin/stats` - Dashboard statistics

3. **`profiles.py`** - Admin profile management
   - Profile storage and retrieval

4. **`activity.py`** - Activity logging
   - Real-time activity tracking

---

## Common Tasks

### How to Add a New Endpoint

1. **Create endpoint file** in `cirkelline/endpoints/`
2. **Define FastAPI router:**
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/api/feature", tags=["feature"])
   ```
3. **Import in `my_os.py`:**
   ```python
   from cirkelline.endpoints.feature import router as feature_router
   ```
4. **Register router:**
   ```python
   app.include_router(feature_router)
   ```

### How to Add a New Agent

1. **Create agent in `cirkelline/agents/specialists.py`:**
   ```python
   specialist_agent = Agent(
       name="Agent Name",
       role="Description",
       model=Gemini(id="gemini-2.5-flash"),
       instructions=[...],
       markdown=True
   )
   ```
2. **Add to Cirkelline team** in `cirkelline/orchestrator/cirkelline_team.py`
3. **Register in `my_os.py`:**
   ```python
   agent_os = AgentOS(agents=[..., specialist_agent])
   ```

### How to Add Middleware

1. **Add to `cirkelline/middleware/middleware.py`**
2. **Register in `my_os.py`:**
   ```python
   app.middleware("http")(your_middleware)
   ```

### How to Access Database

**In any endpoint:**
```python
from cirkelline.database import get_db

def your_endpoint():
    db = get_db()
    result = db.execute(text("SELECT * FROM table"))
```

### How to Add a Helper Function

1. **Create in appropriate file** in `cirkelline/helpers/`
2. **Import where needed:**
   ```python
   from cirkelline.helpers.your_helper import your_function
   ```

---

## File Size Reference

| Directory | Total Files | Purpose |
|-----------|-------------|---------|
| `cirkelline/endpoints/` | 7 | API route handlers |
| `cirkelline/agents/` | 3 | AI agent definitions |
| `cirkelline/orchestrator/` | 3 | Main Cirkelline team |
| `cirkelline/integrations/google/` | 5 | Google services |
| `cirkelline/integrations/notion/` | 3 | Notion integration |
| `cirkelline/middleware/` | 1 | Auth & logging |
| `cirkelline/helpers/` | 4 | Utility functions |
| `cirkelline/tools/` | 4 | Agent tools (includes memory_search_tool.py) |
| `cirkelline/admin/` | 4 | Admin features |
| `cirkelline/shared/` | 2 | Shared utilities |
| **Total modular files** | **54** | **Clean architecture** |

---

## Architecture Layers

```
┌─────────────────────────────────────────┐
│         my_os.py (Entry Point)          │
│     FastAPI App + Router Registration   │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌─────────┐   ┌──────────┐   ┌──────────┐
│ Agents  │   │Endpoints │   │Middleware│
│ & Teams │   │ (API)    │   │ (Auth)   │
└─────────┘   └──────────┘   └──────────┘
    │               │               │
    └───────────────┼───────────────┘
                    ▼
        ┌───────────────────────┐
        │   Helpers & Tools     │
        │   (Shared Utilities)  │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Core Infrastructure  │
        │ (DB, Config, Models)  │
        └───────────────────────┘
```

---

## Migration from Monolithic Structure

**Before v1.2.30:** Everything in `my_os.py` (11,454 lines)

**After v1.2.30:** Organized into 54 files

**Finding Old Code:**
- Line numbers from v1.2.29 and earlier are **NO LONGER VALID**
- Use this map or [docs/28-MODULARIZATION-GUIDE.md](./28-MODULARIZATION-GUIDE.md)
- Git history preserves old line numbers: `git show v1.2.29:my_os.py`

---

## Related Documentation

- **[28-MODULARIZATION-GUIDE.md](./28-MODULARIZATION-GUIDE.md)** - Detailed modularization explanation
- **[01-ARCHITECTURE.md](./01-ARCHITECTURE.md)** - System architecture overview
- **[05-BACKEND-REFERENCE.md](./05-BACKEND-REFERENCE.md)** - Complete backend API reference
- **[07-DEVELOPMENT-GUIDE.md](./07-DEVELOPMENT-GUIDE.md)** - Development workflows
- **[57-MEMORY.md](./57-MEMORY.md)** - Memory system documentation (v1.2.34.6)

---

## Quick Search Tips

**Finding functionality:**
```bash
# Search for endpoint definitions
grep -r "router.post\|router.get" cirkelline/endpoints/

# Find agent definitions
grep -r "Agent(" cirkelline/agents/

# Locate middleware
ls cirkelline/middleware/

# Find helper functions
grep -r "def " cirkelline/helpers/
```

**Understanding imports:**
```bash
# See what imports a file
grep "^from\|^import" cirkelline/path/to/file.py

# Find where something is imported
grep -r "from cirkelline.module import" .
```

---

**Document Status:** ✅ Complete and Ready for Developers
**Maintained By:** Development Team
**Questions?** Check the related documentation or ask in team chat
