# Cirkelline Modularization Guide

**Version:** v1.2.33 | **Date:** 2025-11-30

This guide explains the new modular architecture implemented in v1.2.30, replacing the monolithic `my_os.py` structure.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [How It Works](#how-it-works)
5. [Development Workflows](#development-workflows)
6. [Migration Guide](#migration-guide)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### The Problem

**Before v1.2.30:**
- Single monolithic `my_os.py` file with **11,454 lines**
- All code in one place: agents, endpoints, middleware, helpers
- Hard to maintain, navigate, test, and understand
- Difficult for multiple developers to work simultaneously
- High risk of merge conflicts

### The Solution

**v1.2.30 Modularization:**
- Reduced `my_os.py` to **985 lines** (91.4% reduction)
- Created **38 modular files** across **12 directories**
- Clear separation of concerns
- Each module < 700 lines
- Zero functionality lost - all **90 routes** operational

### Benefits

**Maintainability**
- Easy to find code (clear file organization)
- Each file focuses on one responsibility
- No duplicate code

**Testability**
- Isolated modules can be tested independently
- Mock dependencies easily
- Clearer error messages with file paths

**Scalability**
- Add new features without touching existing code
- Multiple developers can work on different modules
- Reduced merge conflicts

**Collaboration**
- Clear ownership of components
- Easier code reviews
- Better onboarding for new developers

---

## Architecture

### Layered Design

The modular architecture follows a layered approach:

```
┌─────────────────────────────────────┐
│      my_os.py (Entry Point)         │  ← Application initialization
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│        API Layer (18 Routers)       │  ← HTTP endpoints
│  endpoints/ integrations/ admin/    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│       Middleware Layer              │  ← JWT auth, dependencies
│         middleware/                 │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      AI Agent Layer                 │  ← Specialists, teams
│   agents/ orchestrator/             │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│       Tools Layer                   │  ← Agent tools
│          tools/                     │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Helper Layer                   │  ← Utility functions
│         helpers/                    │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│   Infrastructure Layer              │  ← Config, DB, models
│  config, database, knowledge, models│
└─────────────────────────────────────┘
```

---

## Directory Structure

### Complete Module Map

```
/home/eenvy/Desktop/cirkelline/
│
├── my_os.py                           # Main entry point (985 lines)
│
└── cirkelline/                        # Modular codebase (38 files)
    │
    ├── config.py                      # Logger & environment setup
    ├── database.py                    # PostgreSQL & PgVector
    ├── knowledge_base.py              # Knowledge base init
    ├── models.py                      # Data models
    │
    ├── helpers/                       # Utility functions (4 files)
    │   ├── __init__.py
    │   ├── metadata.py                # Document metadata extraction
    │   ├── user_context.py            # User context building
    │   ├── session_naming.py          # Intelligent session naming
    │   └── notion_helpers.py          # Notion schema & classification
    │
    ├── shared/                        # Shared utilities (2 files)
    │   ├── __init__.py
    │   ├── database.py                # Database helper utilities
    │   └── jwt_utils.py               # JWT token utilities
    │
    ├── tools/                         # Agent tools (3 files)
    │   ├── __init__.py
    │   ├── knowledge_tools.py         # Knowledge base search
    │   ├── notion_tools.py            # Notion operations
    │   └── media/                     # Media processing
    │
    ├── agents/                        # AI Agents (3 files)
    │   ├── __init__.py
    │   ├── specialists.py             # 4 specialist agents
    │   ├── research_team.py           # Research Team (2 agents)
    │   └── law_team.py                # Law Team (2 agents)
    │
    ├── orchestrator/                  # Main Cirkelline (3 files)
    │   ├── __init__.py
    │   ├── cirkelline_team.py         # Cirkelline orchestrator
    │   ├── instructions.py            # Callable instructions
    │   └── memory_manager.py          # Enhanced memory
    │
    ├── middleware/                    # FastAPI middleware (1 file)
    │   ├── __init__.py
    │   └── middleware.py              # JWT, dependencies, activity
    │
    ├── endpoints/                     # Core endpoints (7 files)
    │   ├── __init__.py
    │   ├── auth.py                    # Signup, login, logout
    │   ├── user.py                    # User profile
    │   ├── knowledge.py               # Document management
    │   ├── sessions.py                # Session history
    │   ├── memories.py                # User memories (1 endpoint)
    │   ├── feedback.py                # User feedback (4 endpoints)
    │   └── custom_cirkelline.py       # Custom endpoint
    │
    ├── integrations/                  # External services (9 files)
    │   ├── google/
    │   │   ├── __init__.py
    │   │   ├── google_oauth.py        # OAuth helper
    │   │   ├── oauth_endpoints.py     # OAuth flow (4 endpoints)
    │   │   ├── gmail_endpoints.py     # Gmail (7 endpoints)
    │   │   ├── calendar_endpoints.py  # Calendar (5 endpoints)
    │   │   └── tasks_endpoints.py     # Tasks (12 endpoints)
    │   │
    │   └── notion/
    │       ├── __init__.py
    │       ├── oauth_endpoints.py     # OAuth flow (4 endpoints)
    │       ├── database_endpoints.py  # Dynamic (5 endpoints)
    │       └── legacy_endpoints.py    # Legacy (5 endpoints)
    │
    └── admin/                         # Admin endpoints (4 files)
        ├── __init__.py
        ├── users.py                   # User management (2 endpoints)
        ├── stats.py                   # System stats (1 endpoint)
        ├── subscriptions.py           # Subscriptions (3 endpoints)
        └── activity.py                # Activity log (2 endpoints + SSE)
```

### Module Descriptions

#### Infrastructure Layer

**`config.py`**
- Logger configuration
- Environment variable loading
- Application settings

**`database.py`**
- PostgreSQL connection setup
- PgVector initialization
- Database utilities

**`knowledge_base.py`**
- Knowledge base initialization
- Vector storage configuration

**`models.py`**
- Data models (FileMetadata)
- Schema definitions

#### Helper Layer (`helpers/`)

**`metadata.py`**
- Extract metadata from documents
- Build document metadata objects
- Handle file information

**`user_context.py`**
- Build user context for agents
- Gather user preferences
- Admin profile handling

**`session_naming.py`**
- Intelligent session naming
- Conversation summarization
- Session title generation

**`notion_helpers.py`**
- Notion schema parsing
- Property classification
- Database discovery

#### Tools Layer (`tools/`)

**`knowledge_tools.py`**
- Knowledge base search tools
- Document retrieval
- Semantic search

**`notion_tools.py`**
- Notion API tools for agents
- Database operations
- Page/block operations

**`media/`**
- Media processing tools
- File handling utilities

#### AI Agent Layer

**`agents/specialists.py`**
- Audio Specialist (transcription, sound ID)
- Video Specialist (scene analysis)
- Image Specialist (OCR, description)
- Document Specialist (PDF, DOCX processing)

**`agents/research_team.py`**
- Web Researcher (searches)
- Research Analyst (synthesizes)
- Team coordination

**`agents/law_team.py`**
- Legal Researcher (finds sources)
- Legal Analyst (provides analysis)
- Team coordination

#### Orchestrator Layer (`orchestrator/`)

**`cirkelline_team.py`**
- Main Cirkelline orchestrator
- Team member coordination
- Delegation logic

**`instructions.py`**
- Callable instructions (returns different instructions based on mode)
- Deep Research mode handling
- Dynamic instruction generation

**`memory_manager.py`**
- Enhanced memory management
- User preference capture
- Context building

#### Middleware Layer (`middleware/`)

**`middleware.py`**
- JWT authentication
- User dependency injection
- Activity logging
- Request/response handling

#### API Endpoints Layer

**Core Endpoints (`endpoints/`)**
- `auth.py` - User authentication (signup, login, logout)
- `user.py` - Profile management
- `knowledge.py` - Document operations (upload, search, delete)
- `sessions.py` - Session history & management
- `memories.py` - GET user memories
- `feedback.py` - Submit, list, update, count feedback
- `custom_cirkelline.py` - Custom Cirkelline endpoint with knowledge filtering

**Google Integration (`integrations/google/`)**
- `google_oauth.py` - OAuth credential helper
- `oauth_endpoints.py` - OAuth flow (start, callback, status, disconnect)
- `gmail_endpoints.py` - 7 Gmail endpoints
- `calendar_endpoints.py` - 5 Calendar endpoints
- `tasks_endpoints.py` - 12 Tasks endpoints

**Notion Integration (`integrations/notion/`)**
- `oauth_endpoints.py` - OAuth flow (start, callback, status, disconnect)
- `database_endpoints.py` - 5 dynamic registry-based endpoints
- `legacy_endpoints.py` - 5 legacy name-based endpoints

**Admin APIs (`admin/`)**
- `users.py` - List users, get user details
- `stats.py` - System statistics
- `subscriptions.py` - Subscription management
- `activity.py` - Activity logging + SSE stream

---

## How It Works

### Application Startup Flow

```python
# 1. my_os.py imports infrastructure
from cirkelline.config import logger
from cirkelline.database import db, vector_db
from cirkelline.knowledge_base import knowledge_base
from cirkelline.models import FileMetadata

# 2. Imports AI agents
from cirkelline.agents.specialists import (
    audio_agent, video_agent, image_agent, document_agent
)
from cirkelline.agents.research_team import research_team
from cirkelline.agents.law_team import law_team
from cirkelline.orchestrator.cirkelline_team import cirkelline

# 3. Imports all routers
from cirkelline.endpoints.auth import router as auth_router
from cirkelline.endpoints.user import router as user_router
# ... (18 routers total)

# 4. Registers routers with FastAPI
app = FastAPI(...)
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/user", tags=["User"])
# ... (registers all 18 routers)

# 5. Initializes AgentOS
agent_os = AgentOS(
    agents=[
        audio_agent, video_agent, image_agent, document_agent,
        cirkelline
    ],
    teams=[research_team, law_team],
    ...
)

# 6. Starts Uvicorn server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7777)
```

### Request Flow

```
HTTP Request
    ↓
FastAPI App (my_os.py)
    ↓
Router (e.g., auth_router from endpoints/auth.py)
    ↓
Middleware (JWT auth, user dependency)
    ↓
Endpoint Function
    ↓
Uses Agents/Tools (from agents/, tools/)
    ↓
Uses Helpers (from helpers/)
    ↓
Accesses Database (via database.py)
    ↓
Returns Response
    ↓
Response to Client
```

---

## Development Workflows

### 1. Adding a New API Endpoint

**Step 1: Create Router File**

Choose the appropriate directory:
- Core functionality → `cirkelline/endpoints/`
- External integration → `cirkelline/integrations/<service>/`
- Admin functionality → `cirkelline/admin/`

Example: `cirkelline/endpoints/notifications.py`

```python
from fastapi import APIRouter, Request
from typing import List, Dict, Any

router = APIRouter()

@router.get("/api/notifications")
async def get_notifications(request: Request) -> List[Dict[str, Any]]:
    """
    Get user notifications.
    """
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # Your logic here
    notifications = fetch_notifications(user_id)

    return notifications
```

**Step 2: Register Router in `my_os.py`**

```python
# Import router
from cirkelline.api.notifications import router as notifications_router

# Register with app
app.include_router(notifications_router, tags=["Notifications"])
```

**Step 3: Test**

```bash
curl http://localhost:7777/api/notifications \
  -H "Authorization: Bearer <jwt-token>"
```

### 2. Adding a New Agent

**Step 1: Create Agent File**

Example: `cirkelline/agents/translator.py`

```python
from agno import Agent, Gemini
from cirkelline.database import db

translator_agent = Agent(
    name="Translator",
    role="Language translation specialist",
    model=Gemini(id="gemini-2.5-flash"),
    instructions=[
        "You are an expert translator.",
        "Translate text accurately while preserving meaning and tone.",
        "Support multiple languages."
    ],
    markdown=True,
    db=db
)
```

**Step 2: Add to Cirkelline Team**

Edit `cirkelline/orchestrator/cirkelline_team.py`:

```python
from cirkelline.agents.translator import translator_agent

cirkelline = Team(
    name="Cirkelline",
    members=[
        audio_agent,
        video_agent,
        image_agent,
        document_agent,
        translator_agent,  # Add here
    ],
    ...
)
```

**Step 3: Register with AgentOS**

Edit `my_os.py`:

```python
from cirkelline.agents.translator import translator_agent

agent_os = AgentOS(
    agents=[
        audio_agent,
        video_agent,
        image_agent,
        document_agent,
        translator_agent,  # Add here
        cirkelline
    ],
    ...
)
```

### 3. Modifying Existing Code

**Example: Update Cirkelline instructions**

Edit `cirkelline/orchestrator/instructions.py`:

```python
def get_cirkelline_instructions(session_state: dict = None) -> List[str]:
    """
    Returns dynamic instructions based on session state.
    """
    # Your changes here
    return instructions
```

**Example: Add new middleware**

Edit `cirkelline/middleware/middleware.py`:

```python
@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    # Your middleware logic
    response = await call_next(request)
    return response
```

### 4. Adding Helper Functions

**Step 1: Choose/Create Helper Module**

- Document operations → `helpers/metadata.py`
- User operations → `helpers/user_context.py`
- Session operations → `helpers/session_naming.py`
- Notion operations → `helpers/notion_helpers.py`
- New category → Create new file

Example: `cirkelline/helpers/analytics.py`

```python
def calculate_user_stats(user_id: str) -> dict:
    """
    Calculate user statistics.
    """
    # Your logic here
    return stats
```

**Step 2: Import Where Needed**

```python
from cirkelline.helpers.analytics import calculate_user_stats

stats = calculate_user_stats(user_id)
```

---

## Migration Guide

### For Developers Familiar with Old Structure

**Before (Monolithic `my_os.py`):**
```python
# All in one file (lines 97-11454)
# - Lines 97-172: Document metadata functions
# - Lines 251-356: Specialist agents
# - Lines 462-570: Teams
# - Lines 659-926: Cirkelline orchestrator
# - Lines 1006-1144: Custom endpoint
# - Lines 1699-2044: Auth endpoints
# ... (and so on)
```

**After (Modular Structure):**
```python
# Organized into focused modules
cirkelline/helpers/metadata.py       # Document metadata functions
cirkelline/agents/specialists.py     # Specialist agents
cirkelline/agents/research_team.py   # Research Team
cirkelline/agents/law_team.py        # Law Team
cirkelline/orchestrator/cirkelline_team.py  # Cirkelline orchestrator
cirkelline/endpoints/custom_cirkelline.py   # Custom endpoint
cirkelline/endpoints/auth.py         # Auth endpoints
```

### Finding Code

**Old Way:**
- Search in massive my_os.py file
- Navigate thousands of lines
- Hard to find related code

**New Way:**
- Know the category (agent/endpoint/helper/tool)
- Go to appropriate directory
- Find file by name
- Each file is focused and small

**Example:**

Want to find auth endpoints?
- Old: Search my_os.py for "signup" or "login" (lines 1699-2044)
- New: Open `cirkelline/endpoints/auth.py` (583 lines, clear structure)

Want to modify Cirkelline orchestrator?
- Old: Navigate to lines 659-926 in my_os.py
- New: Open `cirkelline/orchestrator/cirkelline_team.py` (108 lines)

### Import Changes

**Old:**
```python
# Everything was in my_os.py
# No imports needed for internal code
```

**New:**
```python
# Import from appropriate modules
from cirkelline.database import db, vector_db
from cirkelline.agents.specialists import audio_agent
from cirkelline.helpers.metadata import extract_metadata
```

---

## Best Practices

### 1. Module Organization

**DO:**
- Create new files in appropriate directories
- Keep files focused (< 700 lines)
- Use clear, descriptive names
- Group related functionality

**DON'T:**
- Add unrelated code to existing modules
- Create files in root directory
- Mix different concerns in one file

### 2. Import Patterns

**DO:**
```python
# Import specific items
from cirkelline.database import db, vector_db

# Use absolute imports
from cirkelline.helpers.metadata import extract_metadata
```

**DON'T:**
```python
# Import everything
from cirkelline.database import *

# Use relative imports (hard to track)
from ..helpers.metadata import extract_metadata
```

### 3. Router Creation

**DO:**
```python
# Create router instance
router = APIRouter()

# Use clear endpoint paths
@router.post("/api/feature/action")
async def action_handler(request: Request):
    ...
```

**DON'T:**
```python
# Use app directly (should only be in my_os.py)
@app.post("/api/feature/action")
async def action_handler(request: Request):
    ...
```

### 4. Code Duplication

**DO:**
- Create helper functions for repeated logic
- Put helpers in appropriate `helpers/` module
- Import and reuse

**DON'T:**
- Copy-paste code between files
- Duplicate logic across modules

### 5. Testing

**DO:**
```python
# Test individual modules
from cirkelline.helpers.metadata import extract_metadata

def test_extract_metadata():
    result = extract_metadata(file_path)
    assert result.filename == "test.pdf"
```

**DON'T:**
```python
# Test only through my_os.py
# Hard to isolate issues
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'cirkelline'
```

**Solution:**
- Ensure you're in the project root directory
- Ensure `cirkelline/` directory exists with `__init__.py` files
- Check Python path: `export PYTHONPATH=/home/eenvy/Desktop/cirkelline:$PYTHONPATH`

#### 2. Circular Import Errors

**Error:**
```
ImportError: cannot import name 'db' from partially initialized module
```

**Solution:**
- Check for circular dependencies
- Move shared code to infrastructure layer
- Use late imports if necessary

#### 3. Router Not Registered

**Error:**
```
404 Not Found for endpoint
```

**Solution:**
- Verify router is imported in `my_os.py`
- Verify `app.include_router()` is called
- Check prefix and tags
- Restart backend

#### 4. Agent Not Found

**Error:**
```
Agent 'translator' not found in AgentOS
```

**Solution:**
- Verify agent is imported in `my_os.py`
- Verify agent is added to `AgentOS(agents=[...])`
- Restart backend

### Debugging Tips

**1. Check Startup Logs**
```bash
python my_os.py 2>&1 | grep -E "(✅|❌|ERROR)"
```

**2. Verify Imports**
```bash
python -c "from cirkelline.agents.specialists import audio_agent; print('OK')"
```

**3. Count Routes**
```bash
curl http://localhost:7777/openapi.json | jq '.paths | length'
# Should return 90
```

**4. Check Module Structure**
```bash
tree cirkelline/ -L 2 -I __pycache__
```

---

## Summary

### Key Takeaways

1. **Modularization = Better Code**
   - Easier to maintain
   - Easier to test
   - Easier to collaborate

2. **Clear Organization**
   - Infrastructure in root
   - Helpers in `helpers/`
   - Agents in `agents/` and `orchestrator/`
   - Endpoints in `endpoints/`, `integrations/`, `api/`, `admin/`

3. **Simple Workflow**
   - Create module in appropriate directory
   - Import in `my_os.py`
   - Register (if router or agent)
   - Test and deploy

4. **Zero Functionality Lost**
   - All 90 routes operational
   - All agents working
   - All features preserved

### Next Steps

1. **Read the Codebase**
   - Explore `cirkelline/` directory
   - Understand module organization
   - Review `my_os.py` to see how it all connects

2. **Make Small Changes**
   - Start with helper function
   - Add new endpoint
   - Modify existing agent

3. **Ask Questions**
   - Reference this guide
   - Check `docs/27-MODULARIZATION-PROGRESS.md` for history
   - Review CLAUDE.md for updated workflows

---

**Document Status:** ✅ Complete and Ready for Developers
**Maintained By:** Development Team
**Questions?** Check [CLAUDE.md](../CLAUDE.md) or [docs/](.) directory
