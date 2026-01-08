# BACKEND REFERENCE

**Last Updated:** 2025-11-26
**Current Version:** v1.2.33

---

## Table of Contents
- [Backend Structure](#backend-structure)
- [API Endpoints](#api-endpoints)
  - [Admin Endpoints](#admin-endpoints)
- [my_os.py Architecture](#myospy-architecture)
- [Authentication Implementation](#authentication-implementation)
- [Knowledge Upload Process](#knowledge-upload-process)
- [Session Handling](#session-handling)
- [Admin Profile System](#admin-profile-system)
- [Token Usage Metrics System](#token-usage-metrics-system)
- [Environment Variables](#environment-variables)
- [Quick Reference](#quick-reference)

---

## Backend Structure

### File Organization

**NEW IN v1.2.30:** Backend restructured from 11,454-line monolith into modular architecture (91.1% reduction to 1,017 lines main file).

```
/home/eenvy/Desktop/cirkelline/
├── my_os.py                    # Main entry point (1,017 lines)
├── requirements.txt            # Python dependencies
├── .env                        # Environment configuration
├── cirkelline/                 # Modular architecture (54 Python files)
│   ├── config.py               # Logger & environment
│   ├── database.py             # PostgreSQL & PgVector
│   ├── knowledge_base.py       # Knowledge base init
│   ├── models.py               # Data models
│   ├── shared/                 # Shared utilities (2 files)
│   ├── helpers/                # Helper functions (4 files)
│   ├── tools/                  # Tool classes for agents (3 files)
│   ├── agents/                 # AI agents (3 files)
│   ├── orchestrator/           # Main Cirkelline team (3 files)
│   ├── middleware/             # FastAPI middleware (1 file)
│   ├── endpoints/              # Core API endpoints (10 files)
│   ├── integrations/           # External integrations (9 files)
│   │   ├── google/             # Google services (5 files)
│   │   └── notion/             # Notion services (4 files)
│   └── admin/                  # Admin-only endpoints (4 files)
└── Dockerfile                  # AWS production image
```

**Note:** See [docs/27-MODULARIZATION-PROGRESS.md](./27-MODULARIZATION-PROGRESS.md) for complete modular architecture guide.

### Technology Stack

```python
# Core Framework
agno==2.1.1                    # Agent orchestration
fastapi                        # Web framework
uvicorn                        # ASGI server

# AI & ML
google-genai                   # Gemini models
agno.models.google.Gemini      # AGNO Gemini integration

# Database
sqlalchemy                     # ORM
psycopg[binary]               # PostgreSQL driver
pgvector                       # Vector similarity search

# Document Processing
pypdf                          # PDF processing
python-docx                    # DOCX processing
beautifulsoup4                 # HTML parsing
markdown                       # Markdown processing

# Search Tools
duckduckgo-search             # Web search
exa_py                         # Neural search
tavily-python                  # Research API

# Authentication
pyjwt                          # JWT tokens
bcrypt                         # Password hashing

# Utilities
python-dotenv                  # Environment variables
psutil                         # System monitoring
```

---

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/signup
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/auth.py`

**Purpose:** Create new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "display_name": "User Name"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "User Name",
    "is_admin": false
  }
}
```

**Implementation Details:**
```python
# 1. Check if email exists
result = session.execute(
    text("SELECT id FROM users WHERE email = :email"),
    {"email": signup_data.email}
)

# 2. Hash password (bcrypt, 12 rounds)
password_hash = bcrypt.hashpw(
    signup_data.password.encode('utf-8'),
    bcrypt.gensalt()
).decode('utf-8')

# 3. Create user
user_id = str(uuid.uuid4())
session.execute(
    text("""
        INSERT INTO users (id, email, hashed_password, display_name)
        VALUES (:id, :email, :hashed_password, :display_name)
    """),
    {
        "id": user_id,
        "email": signup_data.email,
        "hashed_password": password_hash,
        "display_name": signup_data.display_name
    }
)

# 4. Check if admin (hardcoded emails)
ADMIN_EMAILS = {
    "opnureyes2@gmail.com": "Ivo",
    "opnureyes2@gmail.com": "Rasmus"
}
is_admin = signup_data.email in ADMIN_EMAILS

# 5. Load admin profile if admin
if is_admin:
    admin_result = session.execute(
        text("""
            SELECT name, role, personal_context,
                   preferences, custom_instructions
            FROM admin_profiles
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )

# 6. Generate JWT
jwt_payload = {
    "user_id": user_id,
    "email": email,
    "display_name": display_name,
    "user_name": "Ivo" if admin else display_name,
    "user_role": "CEO & Creator" if admin else "User",
    "user_type": "Admin" if admin else "Regular",
    "is_admin": is_admin,
    "iat": int(time.time()),
    "exp": int(time.time()) + (7 * 24 * 60 * 60)  # 7 days
}

token = pyjwt.encode(jwt_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
```

**Error Responses:**
- `400`: Email already registered
- `500`: Database error

---

#### POST /api/auth/login
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/auth.py`

**Purpose:** Authenticate existing user

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:** Same as signup

**Implementation Details:**
```python
# 1. Find user
result = session.execute(
    text("""
        SELECT id, email, hashed_password, display_name
        FROM users
        WHERE email = :email
    """),
    {"email": login_data.email}
)
user = result.fetchone()

if not user:
    raise HTTPException(status_code=401, detail="Invalid email or password")

# 2. Verify password
password_match = bcrypt.checkpw(
    login_data.password.encode('utf-8'),
    user[2].encode('utf-8')  # hashed_password
)

if not password_match:
    raise HTTPException(status_code=401, detail="Invalid email or password")

# 3. Generate JWT (same as signup)
```

**Error Responses:**
- `401`: Invalid email or password
- `500`: Database error

---

### User Endpoints

#### PATCH /api/user/profile
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/user.py`

**Purpose:** Update user display name

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "display_name": "New Name"
}
```

**Response:**
```json
{
  "success": true,
  "token": "new_jwt_token_with_updated_name",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "New Name"
  }
}
```

**Implementation:**
```python
# 1. Extract user_id from JWT
auth_header = request.headers.get("authorization", "")
token = auth_header[7:]  # Remove "Bearer "
payload = pyjwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
user_id = payload.get("user_id")

# 2. Update database
result = session.execute(
    text("""
        UPDATE users
        SET display_name = :name, updated_at = CURRENT_TIMESTAMP
        WHERE id = :user_id
        RETURNING id, email, display_name
    """),
    {"name": profile_update.display_name, "user_id": user_id}
)

# 3. Generate new JWT with updated info
new_token = pyjwt.encode(new_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
```

**Notes:**
- Now supports additional fields: `bio`, `location`, `job_title`, `instructions`
- All profile fields stored in `users.preferences` JSON column
- Instructions field allows users to customize AI behavior
- See "Custom Instructions Feature" section below for architectural details

---

### Custom Instructions Feature

#### Overview
**Files:**
- `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py` (custom endpoint handler)
- `/home/eenvy/Desktop/cirkelline/cirkelline/orchestrator/instructions.py` (instruction injection logic)

Custom instructions allow users to personalize how Cirkelline responds to them. For example:
- "Always respond in both English and Danish"
- "Be very technical with code examples"
- "Use simple language, I'm a beginner"
- "Always include sources for your information"

#### How It Works

**1. User Sets Instructions** (Frontend)
- User navigates to Profile page (`/profile`)
- Enters custom instructions in "Instructions for Cirkelline" textarea (500 char max)
- Clicks "Save Changes"
- Frontend sends `POST /api/user/profile` with `instructions` field

**2. Instructions Stored** (Backend)
```python
# cirkelline/endpoints/user.py (update_user_profile function)
if profile_update.instructions is not None:
    preferences['instructions'] = profile_update.instructions
# Saved to users.preferences JSON column in PostgreSQL
```

**3. Instructions Retrieved** (Backend)
```python
# cirkelline/endpoints/user.py (get_user_profile function)
"profile": {
    "location": preferences.get('location', ''),
    "job_title": preferences.get('job_title', ''),
    "bio": preferences.get('bio', ''),
    "instructions": preferences.get('instructions', '')
}
```

**4. Instructions Applied to Chat** (Backend - Custom Endpoint)
```python
# cirkelline/endpoints/custom_cirkelline.py (custom_cirkelline_run function)
# Load user preferences from database
result = await asyncio.to_thread(
    lambda: Session(_shared_engine).execute(
        text("SELECT preferences FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
)

if result and result[0]:
    preferences = json.loads(result[0])
    user_instructions = preferences.get('instructions', '').strip()
```

**5. Dynamic Injection** (Backend)
```python
# cirkelline/orchestrator/instructions.py (apply_user_instructions function)
if user_instructions:
    logger.info(f"📝 Injecting user custom instructions into Cirkelline")
    custom_instructions_section = [
        "",
        "═══════════════════════════════════════",
        "USER CUSTOM INSTRUCTIONS",
        "═══════════════════════════════════════",
        "",
        f"🔴 CRITICAL: The user has provided custom instructions that MUST be followed:",
        "",
        user_instructions,
        "",
        "These instructions take priority and must be applied to ALL your responses.",
        ""
    ]
    cirkelline.instructions.extend(custom_instructions_section)
```

#### Critical Architectural Detail: Singleton Pattern & Cleanup

**The Problem:**
```python
# Line ~1056 in my_os.py - MODULE LEVEL (runs ONCE when server starts)
cirkelline = Team(
    members=[...],
    instructions=[...],  # ← Original instructions list
    ...
)
```

The `cirkelline` Team object is a **SINGLETON** - created once when the server starts and **shared across ALL users' requests**. This is different from database isolation:

**Database Isolation (✅ Already Working):**
- Sessions: `WHERE user_id = 'current-user'`
- Memories: `WHERE user_id = 'current-user'`
- Documents: `WHERE metadata->>'user_id' = 'current-user'`
- Data is isolated in PostgreSQL

**In-Memory State (❌ Not Isolated by Default):**
- `cirkelline.instructions` = Python list in server memory
- Shared across ALL requests from ALL users
- NOT stored in database
- NOT filtered by SQL queries

**What Happens Without Cleanup:**

```
Timeline:
1. User A (instructions: "Always respond in Danish")
   cirkelline.instructions = [original] + [User A custom]

2. User B (no custom instructions)
   cirkelline.instructions = [original] + [User A custom]  ← Still there!
   User B gets Danish responses even though they didn't ask!

3. User C (instructions: "Be very technical")
   cirkelline.instructions = [original] + [User A custom] + [User C custom]
   Now BOTH User A's AND User C's instructions are active!
```

**The Solution: Proper Cleanup**

```python
# cirkelline/endpoints/custom_cirkelline.py (custom_cirkelline_run function)
# Cleanup logic in try/finally block
# BEFORE modifying cirkelline
original_instructions = cirkelline.instructions.copy()

# Modify for THIS request only
if user_instructions:
    cirkelline.instructions.extend(custom_instructions_section)

# Run the request
cirkelline.arun(...)

# CRITICAL: Restore original state for next request
finally:
    cirkelline.instructions = original_instructions
    logger.info("🧹 Restored original Cirkelline configuration after stream")
```

**Why This is Necessary:**

```
┌─────────────────────────────────────────┐
│   FastAPI Server (Single Python Process)│
│                                          │
│   ┌─────────────────────────────────┐   │
│   │ cirkelline = Team(...)          │   │ ← Created ONCE
│   │ (Singleton, shared by all)      │   │
│   └─────────────────────────────────┘   │
│                                          │
│   Request 1 (User A) ──────────────────┐│
│   Request 2 (User B) ──────────────────┤│ ← All modify the SAME object
│   Request 3 (User C) ──────────────────┘│
│                                          │
└─────────────────────────────────────────┘
```

**The Restaurant Analogy:**
- **Database isolation** = Each customer has their own table, order, and bill ✅
- **Cirkelline instructions** = The chef's recipe book (shared by everyone) 📖
- **Without cleanup** = Customer A writes "add extra salt" in the recipe book, and now ALL future customers get extra salt!
- **With cleanup** = We use sticky notes for custom instructions, then remove them after each order

**Implementation Details:**

1. **Save Original State:**
   ```python
   original_instructions = cirkelline.instructions.copy()
   original_tools = cirkelline.tools.copy()  # Same pattern for Google tools
   ```

2. **Modify for Request:**
   ```python
   if user_instructions:
       cirkelline.instructions.extend(custom_instructions_section)
   if has_google:
       cirkelline.tools.extend(google_tools)
   ```

3. **Restore After Request:**
   ```python
   # Streaming case (my_os.py:1833-1837)
   finally:
       cirkelline.tools = original_tools
       cirkelline.instructions = original_instructions

   # Non-streaming case (my_os.py:1854-1856)
   cirkelline.tools = original_tools
   cirkelline.instructions = original_instructions
   ```

**Why Alternative Solutions Don't Work:**

1. **Create new Team per request** ❌
   - Too expensive (loads models, tools, etc.)
   - Loses session context
   - AGNO doesn't support this pattern well

2. **Use dependency injection** ❌
   - AGNO Team doesn't have per-request instruction override
   - Would require deep AGNO framework changes

3. **Pass instructions via run() parameters** ❌
   - AGNO's `run()` doesn't accept instructions parameter
   - Instructions are set at Team creation time

**Logging:**
```bash
# Backend logs show the process:
📝 User has custom instructions: provide the answer ALWAYS on both english and danish...
📝 Injecting user custom instructions into Cirkelline
🔍 Session state: {'current_user_id': '...', 'current_user_type': 'Admin'}
🧹 Restored original Cirkelline configuration after stream
```

**Testing:**
1. Set custom instructions in profile page
2. Send a message to Cirkelline
3. Check backend logs for injection confirmation
4. Verify Cirkelline follows your custom instructions
5. Test with multiple users to ensure no leakage

---

#### GET /api/user/activity
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/user.py`

**Purpose:** Fetch user-specific activity logs with filtering and pagination

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
```
page: number (default: 1, min: 1)
limit: number (default: 20, min: 1, max: 100)
action_filter: string (optional, e.g., "chat_started", "document_uploaded")
success_filter: string (optional, "success", "failure", or "all")
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "timestamp": 1730061234,
      "action_type": "chat_started",
      "endpoint": "/api/teams/cirkelline/runs",
      "http_method": "POST",
      "status_code": 200,
      "success": true,
      "error_message": null,
      "error_type": null,
      "target_resource_id": "session-uuid",
      "resource_type": "session",
      "details": {...},
      "duration_ms": 1234,
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3
}
```

**Implementation:**
```python
# 1. Extract user_id from JWT middleware
user_id = getattr(request.state, 'user_id', None)

# 2. Build filtered query
base_query = """
    SELECT id, timestamp, action_type, endpoint, http_method,
           status_code, success, error_message, error_type,
           target_resource_id, resource_type, details,
           duration_ms, ip_address, user_agent
    FROM activity_logs
    WHERE user_id = :user_id
"""

# 3. Apply filters
if action_filter and action_filter != 'all':
    base_query += " AND action_type = :action_type"
if success_filter in ['success', 'failure']:
    base_query += " AND success = :success_value"

# 4. Sort and paginate
base_query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"

# 5. Execute and return
result = session.execute(text(base_query), params)
```

**Security:**
- Only shows activities for authenticated user
- Filtered by JWT user_id from request state
- Anonymous users receive 401 Unauthorized

**Use Cases:**
- User profile activity page
- Debugging user-specific issues
- Activity timeline display

---

#### PATCH /api/user/preferences
**File:** `cirkelline/endpoints/user.py` (v1.2.31+)

**Purpose:** Update user preferences (theme, notifications, etc.)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "theme": "dark"
}
```

**Response:**
```json
{
  "success": true,
  "preferences": {
    "theme": "dark",
    "notifications_enabled": true
  }
}
```

**Notes:**
- **Restored in v1.2.31** after modularization
- Stores preferences in `users.preferences` JSONB column
- Currently supports `theme` field (light/dark)

---

### Tier & Subscription Endpoints

**NEW IN v1.2.31:** Endpoints restored after modularization. These endpoints manage user tiers and subscription operations.

#### GET /api/tiers/public
**File:** `cirkelline/endpoints/user.py` (v1.2.31+)

**Purpose:** Get all available public subscription tiers

**Authentication:** None required (public endpoint)

**Response:**
```json
{
  "success": true,
  "tiers": [
    {
      "id": "uuid",
      "name": "Free",
      "slug": "free",
      "description": "Basic access",
      "price_monthly": 0,
      "features": ["5 sessions/day", "Basic support"],
      "tier_level": 0
    },
    {
      "id": "uuid",
      "name": "Member",
      "slug": "member",
      "description": "Enhanced access",
      "price_monthly": 9.99,
      "features": ["Unlimited sessions", "Priority support"],
      "tier_level": 1
    }
  ]
}
```

**Notes:**
- **Restored in v1.2.31** after modularization
- Public endpoint accessible without authentication
- Returns all tiers sorted by tier_level

---

#### GET /api/user/tier
**File:** `cirkelline/endpoints/user.py` (v1.2.31+)

**Purpose:** Get current user's tier information

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "tier": {
    "id": "uuid",
    "name": "Member",
    "slug": "member",
    "description": "Enhanced access",
    "price_monthly": 9.99,
    "features": ["Unlimited sessions", "Priority support"],
    "tier_level": 1
  }
}
```

**Notes:**
- **Restored in v1.2.31** after modularization
- **Critical Bug Fix (v1.2.31):** Fixed SQL ambiguous column reference (`users.tier_id` vs `tiers.tier_id`)
- Requires authentication
- Returns user's current tier with full details

---

#### GET /api/user/subscription
**File:** `cirkelline/endpoints/user.py` (v1.2.31+)

**Purpose:** Get user's subscription details

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "subscription": {
    "status": "active",
    "tier_slug": "member",
    "tier_name": "Member",
    "billing_cycle": "monthly",
    "next_billing_date": "2025-12-18",
    "can_upgrade": true,
    "can_downgrade": true
  }
}
```

**Notes:**
- **Restored in v1.2.31** after modularization
- Shows subscription status, billing info, and available actions
- Status values: `active`, `canceled`, `expired`, `trial`

---

#### POST /api/user/subscription/upgrade
**File:** `cirkelline/endpoints/user.py` (v1.2.31+)

**Purpose:** Upgrade user's subscription tier

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "tier_slug": "pro"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription upgraded successfully",
  "subscription": {
    "status": "active",
    "tier_slug": "pro",
    "tier_name": "Pro",
    "effective_date": "2025-11-18"
  }
}
```

**Notes:**
- **Restored in v1.2.31** after modularization
- Validates tier_slug exists and is higher level than current tier
- Updates `users.tier_id` in database
- Immediate effect (no billing delay simulation)

---

#### POST /api/user/subscription/cancel
**File:** `cirkelline/endpoints/user.py` (v1.2.31+)

**Purpose:** Cancel user's subscription (downgrades to free tier)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription canceled successfully",
  "subscription": {
    "status": "canceled",
    "tier_slug": "free",
    "tier_name": "Free",
    "effective_date": "2025-11-18"
  }
}
```

**Notes:**
- **Restored in v1.2.31** after modularization
- Immediately downgrades user to free tier
- No refund logic (simplified implementation)
- Sets `users.tier_id` to free tier ID

---

### Knowledge Endpoints

#### POST /api/knowledge/upload
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/knowledge.py`

**Purpose:** Upload file to user's private knowledge base

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request (multipart/form-data):**
```
file: [binary file data]
```

**Response:**
```json
{
  "success": true,
  "message": "✅ document.pdf uploaded to your private knowledge base!",
  "filename": "document.pdf",
  "user_id": "uuid"
}
```

**Implementation:**
```python
# 1. Extract user_id from JWT
token = auth_header[7:]
payload = pyjwt.decode(
    token,
    os.getenv("JWT_SECRET_KEY"),
    algorithms=["HS256"],
    options={"verify_exp": False}
)
user_id = payload.get("user_id")
user_type = payload.get("user_type", "Regular").lower()

# 2. Save file temporarily
temp_dir = "/tmp/cirkelline_uploads"
os.makedirs(temp_dir, exist_ok=True)
file_id = str(uuid.uuid4())[:8]
temp_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")

with open(temp_path, "wb") as buffer:
    shutil.copyfileobj(file.file, buffer)

# 3. Create private metadata
metadata = create_private_document_metadata(
    user_id=user_id,
    user_type=user_type
)
# Returns:
# {
#   "user_id": "uuid",
#   "user_type": "admin",
#   "access_level": "private",
#   "uploaded_by": "uuid",
#   "uploaded_at": "2025-10-12T10:30:00Z",
#   "uploaded_via": "frontend_chat"
# }

# 4. Upload to knowledge base
await knowledge.add_content_async(
    name=file.filename,
    path=temp_path,
    metadata=metadata,
    description=f"Uploaded by user via chat interface"
)

# 5. Clean up temp file
os.remove(temp_path)
```

**Supported File Types:**
- PDF (native Gemini support)
- DOCX (converted via tool)
- TXT, MD, HTML, XML (extracted)

**Error Responses:**
- `401`: No authorization token
- `400`: user_id not in token
- `500`: Upload error

---

#### GET /api/user/memories
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/memories.py`

**Purpose:** Fetch all memories for authenticated user

**Added:** v1.1.20 (2025-10-12)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "count": 15,
  "memories": [
    {
      "memory_id": "7f8e9d2c-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
      "memory": "User prefers dark mode for coding",
      "input": "I always code in dark mode",
      "topics": ["preferences", "development"],
      "updated_at": "2025-10-12T19:30:00Z",
      "agent_id": "cirkelline",
      "team_id": "cirkelline"
    }
  ]
}
```

**Implementation Details:**
```python
@app.get("/api/user/memories")
async def get_user_memories(request: Request):
    """
    Fetch all memories for authenticated user from ai.agno_memories table.
    Returns comprehensive memory data including original input context.
    """

    # 1. Extract user_id from JWT
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header[7:]
    try:
        payload = pyjwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY"),
            algorithms=["HS256"]
        )
        user_id = payload.get("user_id")
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # 2. Fetch memories from database with user isolation
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT
                        memory_id,
                        memory,
                        input,
                        topics,
                        updated_at,
                        agent_id,
                        team_id
                    FROM ai.agno_memories
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                """),
                {"user_id": user_id}
            )

            memories = result.fetchall()

            # 3. Format memories for frontend
            formatted_memories = []
            for mem in memories:
                import json as json_lib

                # Handle memory text
                memory_text = mem[1] if isinstance(mem[1], str) else json_lib.dumps(mem[1])

                # Handle topics list
                topics_list = mem[3] if isinstance(mem[3], list) else (json_lib.loads(mem[3]) if mem[3] else [])

                # Convert timestamp to ISO format
                from datetime import datetime
                timestamp = datetime.fromtimestamp(mem[4]).isoformat() if mem[4] else None

                formatted_memories.append({
                    "memory_id": mem[0],
                    "memory": memory_text,
                    "input": mem[2],
                    "topics": topics_list,
                    "updated_at": timestamp,
                    "agent_id": mem[5],
                    "team_id": mem[6]
                })

            logger.info(f"✅ Retrieved {len(formatted_memories)} memories for user {user_id}")

            return {
                "success": True,
                "count": len(formatted_memories),
                "memories": formatted_memories
            }

    except Exception as e:
        logger.error(f"Memories fetch error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching memories: {str(e)}")
```

**Database Query:**
```sql
SELECT
    memory_id,
    memory,
    input,
    topics,
    updated_at,
    agent_id,
    team_id
FROM ai.agno_memories
WHERE user_id = :user_id
ORDER BY updated_at DESC
```

**Data Processing:**
1. **Memory Text:** JSON or string, converted to string
2. **Topics:** JSON array, parsed if string
3. **Timestamp:** Unix timestamp converted to ISO 8601 format
4. **User Isolation:** WHERE clause ensures users only see their own memories

**Security:**
- JWT authentication required
- User ID extracted from token (cannot be spoofed)
- Database query filters by user_id (guaranteed isolation)
- No pagination (for v1.1.20, all memories returned)

**Use Cases:**
- **Memories Viewer Page:** Display all captured memories in UI
- **Audit Trail:** Review what Cirkelline has learned
- **Quality Verification:** Verify Enhanced MemoryManager accuracy
- **Debugging:** Check memory capture functionality

**Error Responses:**
- `401`: Missing or invalid JWT token
- `401`: User ID not found in token
- `500`: Database query error

**Future Enhancements:**
- Pagination for large memory sets
- Filtering by topic/date
- Search within memories
- Export capabilities

---

### Agent Endpoints

#### POST /teams/cirkelline/runs
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/endpoints/custom_cirkelline.py`

**Purpose:** Send message to Cirkelline orchestrator with knowledge filtering

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request (multipart/form-data):**
```
message: "Your message here"
stream: true
session_id: "uuid" or ""
user_id: "uuid"
deep_research: "true" or "false"  # v1.2.24: Deep Research Mode toggle
```

**New in v1.2.24: Deep Research Mode Parameter**
- **deep_research** (boolean, optional, default: false)
  - `"true"`: Cirkelline delegates research/legal questions to specialist teams (60-90s, comprehensive)
  - `"false"`: Cirkelline uses search tools directly (5-10s, quick answers)
  - Controls runtime mode context injection (see [docs/01-ARCHITECTURE.md#runtime-mode-context-injection](./01-ARCHITECTURE.md#runtime-mode-context-injection))
  - State persisted in session_state across messages

**Response (Server-Sent Events):**
```
event: TeamRunStarted
data: {"session_id": "uuid", "created_at": 1728567890}

event: TeamRunContent
data: {"content": "Hello! How can I help?", "session_id": "uuid"}

event: TeamRunCompleted
data: {"content": "Hello! How can I help?", "session_id": "uuid"}
```

**Implementation:**
```python
@app.post("/teams/cirkelline/runs")
async def cirkelline_with_filtering(
    request: Request,
    message: str = Form(...),
    stream: bool = Form(False),
    session_id: Optional[str] = Form(None),
):
    # 1. Get user_id from JWT middleware
    user_id = getattr(request.state, 'user_id', 'anonymous')

    # 2. Build knowledge filters
    knowledge_filters = {"user_id": user_id}

    # 3. Get dependencies (admin claims)
    dependencies = getattr(request.state, 'dependencies', {})

    # 4. Generate session ID if needed
    if not session_id:
        actual_session_id = str(uuid.uuid4())
        logger.info(f"🆕 Generated NEW session ID: {actual_session_id}")
    else:
        actual_session_id = session_id

    # 5. Stream or non-stream response
    if stream:
        async def event_generator():
            async for event in cirkelline.arun(
                input=message,
                stream=True,
                session_id=actual_session_id,
                user_id=user_id,
                knowledge_filters=knowledge_filters,
                dependencies=dependencies
            ):
                event_type = getattr(event, 'event', 'unknown')
                event_data = event.to_dict()
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        response = await cirkelline.arun(
            input=message,
            stream=False,
            session_id=actual_session_id,
            user_id=user_id,
            knowledge_filters=knowledge_filters,
            dependencies=dependencies
        )
        return response
```

**Event Types:**
- `TeamRunStarted`: Run begins
- `TeamRunContent`: Streaming content
- `TeamToolCallStarted`: Tool execution begins
- `TeamToolCallCompleted`: Tool execution ends
- `TeamReasoningStep`: Reasoning step
- `TeamMemoryUpdateStarted`: Memory update begins
- `TeamMemoryUpdateCompleted`: Memory update ends
- `TeamRunCompleted`: Run finishes
- `TeamRunError`: Error occurred

---

#### GET /config
**File:** `/home/eenvy/Desktop/cirkelline/my_os.py`

**Purpose:** Health check endpoint for AWS ALB

**Response:**
```json
{
  "status": "healthy",
  "service": "cirkelline-system-backend",
  "version": "1.1.6"
}
```

---

### Admin Endpoints

#### GET /api/admin/token-usage
**File:** `/home/eenvy/Desktop/cirkelline/cirkelline/admin/stats.py`

**Purpose:** Get comprehensive token usage analytics (admin only)

**Added:** v1.2.33 (2025-11-26)

**Headers:**
```
Authorization: Bearer {admin_jwt_token}
```

**Query Parameters:**
```
agent_id (optional): Filter by specific agent ID
user_id (optional): Filter by specific user ID
start_date (optional): Start date (ISO format)
end_date (optional): End date (ISO format)
group_by (optional): Group by agent, user, day, week, or month
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "message_count": 150,
      "total_tokens": 2450000,
      "input_tokens": 850000,
      "output_tokens": 1600000,
      "total_cost": 0.66375,
      "input_cost": 0.06375,
      "output_cost": 0.60
    },
    "by_agent": [
      {
        "agent_id": "cirkelline",
        "agent_name": "Cirkelline",
        "agent_type": "team",
        "message_count": 120,
        "total_tokens": 2000000,
        "input_tokens": 700000,
        "output_tokens": 1300000,
        "total_cost": 0.5425,
        "avg_tokens_per_message": 16666
      }
    ],
    "by_user": [
      {
        "user_id": "user-uuid",
        "email": "user@example.com",
        "display_name": "User Name",
        "message_count": 50,
        "total_tokens": 850000,
        "total_cost": 0.31875
      }
    ],
    "timeline": [
      {
        "period": "2025-11-26",
        "message_count": 30,
        "total_tokens": 500000,
        "total_cost": 0.1875
      }
    ],
    "projections": {
      "daily_average": 0.022,
      "weekly_projection": 0.154,
      "monthly_projection": 0.66,
      "yearly_projection": 8.03
    },
    "filters_applied": {
      "agent_id": null,
      "user_id": null,
      "start_date": null,
      "end_date": null,
      "group_by": null
    }
  }
}
```

**Pricing Model (Gemini 2.5 Flash Tier 1):**
- Input tokens: $0.075 per 1M tokens
- Output tokens: $0.30 per 1M tokens

**Authentication:**
- Requires admin JWT token (checked via `is_admin` claim)
- Returns 403 Forbidden if non-admin user

**Example Usage:**
```bash
# Get all metrics
curl -X GET "https://api.cirkelline.com/api/admin/token-usage" \
  -H "Authorization: Bearer {admin_token}"

# Filter by agent
curl -X GET "https://api.cirkelline.com/api/admin/token-usage?agent_id=cirkelline" \
  -H "Authorization: Bearer {admin_token}"

# Filter by user
curl -X GET "https://api.cirkelline.com/api/admin/token-usage?user_id=user-uuid" \
  -H "Authorization: Bearer {admin_token}"

# Filter by date range
curl -X GET "https://api.cirkelline.com/api/admin/token-usage?start_date=2025-11-01&end_date=2025-11-30" \
  -H "Authorization: Bearer {admin_token}"
```

**Related Documentation:**
- Complete metrics system guide: [docs/55-METRICS.md](./55-METRICS.md)
- Database schema: [docs/04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md#aiagno_sessions)
- Frontend dashboard: `/cirkelline-ui/src/app/admin/metrics/page.tsx`

---

## my_os.py Architecture

### Code Structure (1454 lines)

```python
# Lines 1-57: Imports and Initialization
logging.basicConfig(...)
load_dotenv()

# Lines 59-68: FastAPI App Creation (STAGE 1)
app = FastAPI(...)

# Lines 70-90: Database Connections
db = PostgresDb(...)
vector_db = PgVector(...)

# Lines 92-140: Private Document Functions
def create_private_document_metadata(...)
def get_private_knowledge_filters(...)

# Lines 143-182: Knowledge Base Setup
knowledge = Knowledge(...)
async def load_knowledge_async(...)

# Lines 184-246: Private Knowledge Tools
class PrivateKnowledgeTools(Toolkit):
    def save_to_my_knowledge(...)

# Lines 248-689: Agents and Teams
audio_agent = Agent(...)          # Lines 251-273
video_agent = Agent(...)          # Lines 276-299
image_agent = Agent(...)          # Lines 302-324
document_agent = Agent(...)       # Lines 327-356
web_researcher = Agent(...)       # Lines 360-391
research_analyst = Agent(...)     # Lines 393-413
legal_researcher = Agent(...)     # Lines 417-437
legal_analyst = Agent(...)        # Lines 439-458
research_team = Team(...)         # Lines 462-491
law_team = Team(...)              # Lines 493-525
cirkelline = Team(...)            # Lines 529-689

# Lines 691-751: Middleware Configuration (STAGE 2)
app.add_middleware(CORSMiddleware, ...)
class AnonymousUserMiddleware(...)
app.add_middleware(JWTMiddleware, ...)

# Lines 753-853: Custom Endpoints (STAGE 3)
@app.post("/teams/cirkelline/runs")
async def cirkelline_with_filtering(...)

@app.get("/config")
async def health_check(...)

# Lines 855-936: AgentOS Initialization (STAGE 4)
agent_os = AgentOS(
    agents=[...],
    teams=[...],
    base_app=app,
    on_route_conflict="preserve_base_app"
)

# Lines 938-1687: Additional Endpoints
@app.patch("/api/user/profile")
@app.post("/api/knowledge/upload")
@app.post("/api/auth/signup")
@app.post("/api/auth/login")
@app.get("/api/user/memories")

# Lines 1414-1454: Server Startup
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7777)
```

### Key Functions

#### create_private_document_metadata()
**File:** Lines 97-125

```python
def create_private_document_metadata(
    user_id: str,
    user_type: str,
    additional_meta: Optional[Dict] = None
) -> Dict:
    """
    Create metadata for private documents.
    Always sets access_level: "private" for Phase 1.
    """
    metadata = {
        "user_id": user_id,
        "user_type": user_type,
        "access_level": "private",
        "uploaded_by": user_id,
        "uploaded_at": datetime.now().isoformat(),
        "uploaded_via": "frontend_chat",
    }

    if additional_meta:
        metadata.update(additional_meta)

    return metadata
```

#### get_private_knowledge_filters()
**File:** Lines 127-138

```python
def get_private_knowledge_filters(user_id: str) -> Dict:
    """
    Build knowledge filters for private documents only.
    Returns only user's private documents.
    """
    return {"user_id": user_id}
```

**Usage:**
```python
# In custom endpoint
knowledge_filters = {"user_id": user_id}

cirkelline.arun(
    knowledge_filters=knowledge_filters
)
```

**Effect:**
- AGNO adds WHERE clause to vector search
- Only returns documents where metadata->>'user_id' = current user
- Ensures user isolation at database level

---

## Authentication Implementation

### Password Hashing

**Algorithm:** bcrypt with 12 rounds (default)

**Hashing:**
```python
import bcrypt

password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt()
).decode('utf-8')
```

**Verification:**
```python
password_match = bcrypt.checkpw(
    password.encode('utf-8'),
    stored_hash.encode('utf-8')
)
```

### JWT Token Generation

**Secret Key:** From environment variable `JWT_SECRET_KEY` (64-char hex)

**Claims:**
```python
jwt_payload = {
    # Standard claims
    "user_id": "uuid",
    "email": "user@example.com",
    "display_name": "User Name",
    "iat": int(time.time()),              # Issued at
    "exp": int(time.time()) + (7 * 86400), # Expires in 7 days

    # Custom claims for AGNO
    "user_name": "Ivo",                    # Display name
    "user_role": "CEO & Creator",          # Role
    "user_type": "Admin",                  # Type: Admin/Regular (v1.3.4: Anonymous removed)
    "is_admin": True,                      # Admin flag

    # Admin-specific claims (if admin)
    "admin_name": "Ivo",
    "admin_role": "CEO & Creator",
    "admin_context": "Founded Cirkelline...",
    "admin_preferences": "Prefers technical details...",
    "admin_instructions": "Always provide technical..."
}

token = pyjwt.encode(jwt_payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
```

### Middleware Chain (v1.3.4)

**Note:** As of v1.3.4, AnonymousUserMiddleware was removed. Accounts are now required.

#### 1. SessionsDateFilterMiddleware
Handles date-filtered session queries for the frontend calendar view.

#### 2. SessionLoggingMiddleware
Logs session operations (delete, rename) to activity_logs table.

#### 3. JWTMiddleware
**File:** `my_os.py`

```python
app.add_middleware(
    JWTMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256",
    user_id_claim="user_id",              # Extract user_id
    session_id_claim="session_id",         # Extract session_id if present
    dependencies_claims=[                  # Extract these as dependencies
        "user_name",
        "user_role",
        "user_type",
        "tier_slug",
        "tier_level"
    ],
    validate=False  # Validation handled at endpoint level
)
```

**What it does:**
1. Decodes JWT from `Authorization: Bearer {token}`
2. Extracts `user_id` → `request.state.user_id`
3. Extracts dependencies → `request.state.dependencies`
4. Endpoints verify authentication and reject unauthenticated requests

### Admin Detection

**Hardcoded Admin Emails:**
```python
ADMIN_EMAILS = {
    "opnureyes2@gmail.com": "Ivo",
    "opnureyes2@gmail.com": "Rasmus"
}

is_admin = email in ADMIN_EMAILS
```

**Admin Profile Loading:**
```python
if is_admin:
    admin_result = session.execute(
        text("""
            SELECT name, role, personal_context,
                   preferences, custom_instructions
            FROM admin_profiles
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    admin_profile = admin_result.fetchone()

    if admin_profile:
        jwt_payload.update({
            "user_name": admin_profile[0],
            "user_role": admin_profile[1],
            "user_type": "Admin",
            "admin_context": admin_profile[2] or "",
            "admin_preferences": admin_profile[3] or "",
            "admin_instructions": admin_profile[4] or ""
        })
```

---

## Knowledge Upload Process

### Complete Flow

```
1. User drops PDF in chat
     ↓
2. Frontend: POST /api/knowledge/upload
   Headers: Authorization: Bearer {token}
   Body: FormData with file
     ↓
3. Backend extracts user_id from JWT
     ↓
4. Save file temporarily:
   /tmp/cirkelline_uploads/{file_id}_{filename}
     ↓
5. Create metadata:
   {
     "user_id": "uuid",
     "user_type": "admin",
     "access_level": "private",
     "uploaded_by": "uuid",
     "uploaded_at": "2025-10-12T10:30:00Z",
     "uploaded_via": "frontend_chat"
   }
     ↓
6. Call knowledge.add_content_async():
   - Reads file content
   - Chunks text (default: 1000 chars)
   - Generates embeddings (Gemini 768-dim)
   - Stores in ai.agno_knowledge
   - Stores vectors in ai.cirkelline_knowledge_vectors
     ↓
7. Clean up temp file
     ↓
8. Return success to frontend
```

### Database Operations

**Metadata Storage:**
```sql
INSERT INTO ai.agno_knowledge (
    id, name, description, metadata, type, size, status, created_at, updated_at
) VALUES (
    'uuid',
    'document.pdf',
    'Uploaded by user via chat interface',
    '{"user_id": "uuid", "access_level": "private", ...}',
    'pdf',
    123456,
    'completed',
    1728567890,
    1728567890
);
```

**Vector Storage:**
```sql
INSERT INTO ai.cirkelline_knowledge_vectors (
    content_id, embedding, content, metadata
) VALUES (
    123,  -- References agno_knowledge.id
    '[0.123, 0.456, ...]',  -- 768-dimensional vector
    'Chunk of text from document...',
    '{"user_id": "uuid", ...}'  -- Same metadata
);
```

### Knowledge Search

**When user asks about uploaded documents:**

```python
# In custom endpoint
knowledge_filters = {"user_id": user_id}

# AGNO applies this filter to vector search
cirkelline.arun(
    input="What did I upload about X?",
    knowledge_filters=knowledge_filters
)
```

**SQL Query AGNO Generates:**
```sql
SELECT
    content,
    metadata,
    embedding <=> query_vector AS distance
FROM ai.cirkelline_knowledge_vectors
WHERE metadata->>'user_id' = 'current-user-id'
ORDER BY embedding <=> query_vector
LIMIT 5;
```

---

## Session Handling

### Session Creation

**Problem:** AGNO reuses sessions when `session_id=None`

**Solution:** Always generate unique UUID

```python
if not session_id:  # None or empty string
    import uuid
    actual_session_id = str(uuid.uuid4())
    logger.info(f"🆕 Generated NEW session ID: {actual_session_id}")
else:
    actual_session_id = session_id
```

### Session Storage

**Table:** `ai.agno_sessions`

**Schema:**
```sql
session_id VARCHAR PRIMARY KEY
session_type VARCHAR
team_id VARCHAR
user_id VARCHAR        -- CRITICAL for isolation
session_data JSON
runs JSON
created_at BIGINT
updated_at BIGINT
```

**Index:**
```sql
CREATE INDEX idx_agno_sessions_user_id ON ai.agno_sessions(user_id);
```

### Session Isolation

**Backend passes user_id to AGNO:**
```python
cirkelline.arun(
    session_id=actual_session_id,
    user_id=user_id  # Stored with session
)
```

**Frontend loads only user's sessions:**
```typescript
// GET /teams/cirkelline/sessions
// AGNO filters by JWT user_id automatically
```

---

## Admin Profile System

### Database Schema

**Table:** `public.admin_profiles`

```sql
CREATE TABLE public.admin_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    personal_context TEXT,
    preferences TEXT,
    custom_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Profile Loading

**Login/Signup:**
```python
# 1. Check if admin by email
ADMIN_EMAILS = {"opnureyes2@gmail.com": "Ivo"}
is_admin = email in ADMIN_EMAILS

if is_admin:
    # 2. Load profile from database
    admin_result = session.execute(
        text("""
            SELECT name, role, personal_context,
                   preferences, custom_instructions
            FROM admin_profiles
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    )
    admin_profile = admin_result.fetchone()

    # 3. Add to JWT claims
    jwt_payload.update({
        "admin_name": admin_profile[0],
        "admin_role": admin_profile[1],
        "admin_context": admin_profile[2],
        "admin_preferences": admin_profile[3],
        "admin_instructions": admin_profile[4]
    })
```

### Profile Usage in AGNO

**Injection via JWT Middleware:**
```python
# JWT Middleware extracts these claims
dependencies = {
    "user_name": "Ivo",
    "user_role": "CEO & Creator",
    "user_type": "Admin"
}

# Passed to AGNO
cirkelline.arun(
    dependencies=dependencies
)
```

**In Agent Instructions:**
```python
instructions=[
    "User Type: {user_type}",  # "Admin"
    "Current user: {user_name}",  # "Ivo"

    "Adapt internally based on user type:",
    "• Admin users: Technical and direct",
    "• Regular users: Friendly and accessible"
]
```

---

## Token Usage Metrics System

**Added:** v1.2.33 (2025-11-26)

### Overview

Comprehensive token usage tracking system that captures, stores, and analyzes token consumption across all agents and teams. Provides admin dashboard with cost projections and detailed breakdowns.

### Architecture

```
User Message
    ↓
custom_cirkelline.py (captures metrics)
    ↓
ai.agno_sessions.metrics (JSONB storage)
    ↓
/api/admin/token-usage (analytics API)
    ↓
/admin/metrics (frontend dashboard)
```

### Key Features

- **Automatic Capture:** Every message automatically tracked with token counts and costs
- **Per-Agent Tracking:** Separate metrics for Cirkelline, Research Team, Web Researcher, etc.
- **User Analytics:** Token usage breakdown by user with email and display name
- **Cost Calculations:** Real-time cost estimates using Gemini 2.5 Flash Tier 1 pricing
- **Timeline Charts:** Historical token usage with daily/weekly/monthly aggregations
- **Projections:** Daily, weekly, monthly, and yearly cost forecasts
- **Filtering:** Filter by agent, user, date range, or combination
- **Admin Dashboard:** Beautiful React/TypeScript frontend with Framer Motion animations

### Database Schema

**Table:** `ai.agno_sessions`
**Column:** `metrics` (JSONB, DEFAULT '[]')
**Index:** GIN index on `metrics` for fast queries

**Metric Object Structure:**
```json
{
  "timestamp": "2025-11-26T10:30:00",
  "agent_id": "cirkelline",
  "agent_name": "Cirkelline",
  "agent_type": "team",
  "input_tokens": 1500,
  "output_tokens": 3200,
  "total_tokens": 4700,
  "model": "gemini-2.5-flash",
  "message_preview": "What is...",
  "response_preview": "The answer is...",
  "input_cost": 0.0001125,
  "output_cost": 0.00096,
  "total_cost": 0.0010725
}
```

### Pricing Model

**Gemini 2.5 Flash (Tier 1):**
- Input tokens: $0.075 per 1M tokens
- Output tokens: $0.30 per 1M tokens

### API Endpoint

**GET /api/admin/token-usage**

See [Admin Endpoints](#admin-endpoints) section above for complete documentation.

### Frontend Dashboard

**Location:** `/cirkelline-ui/src/app/admin/metrics/page.tsx`

**Features:**
- Summary cards (Total Messages, Total Tokens, Total Cost, Monthly Projection)
- Agent breakdown table with sortable columns
- Top users analytics (top 20 by token usage)
- Cost projections (daily, weekly, monthly, yearly)
- Agent filter dropdown for focused analysis

**Navigation:** Admin Sidebar → Metrics (BarChart3 icon)

### Files Modified/Created

**Backend:**
- `/database_migrations/001_add_metrics_column.sql` - Database migration
- `/cirkelline/endpoints/custom_cirkelline.py` - Metrics capture logic
- `/cirkelline/admin/stats.py` - Token usage analytics API

**Frontend:**
- `/cirkelline-ui/src/app/admin/metrics/page.tsx` - Dashboard component
- `/cirkelline-ui/src/components/admin/AdminSidebar.tsx` - Added Metrics link

**Documentation:**
- `/docs/55-METRICS.md` - **Complete metrics system guide** (500+ lines)
- `/docs/04-DATABASE-REFERENCE.md` - Updated with metrics queries
- `/docs/05-BACKEND-REFERENCE.md` - This file (admin endpoint documentation)

### Usage Example

```bash
# Get all-time token usage
curl -X GET "https://api.cirkelline.com/api/admin/token-usage" \
  -H "Authorization: Bearer {admin_token}"

# Filter by specific agent
curl -X GET "https://api.cirkelline.com/api/admin/token-usage?agent_id=cirkelline" \
  -H "Authorization: Bearer {admin_token}"

# Get monthly usage
curl -X GET "https://api.cirkelline.com/api/admin/token-usage?start_date=2025-11-01&end_date=2025-11-30" \
  -H "Authorization: Bearer {admin_token}"
```

### For Complete Documentation

See **[docs/55-METRICS.md](./55-METRICS.md)** for:
- Detailed architecture diagrams
- Complete database schema
- Backend implementation guide
- Frontend component structure
- Cost calculation formulas
- Testing procedures
- Deployment guide
- Troubleshooting tips
- Future enhancements

---

## Environment Variables

### Development (.env)

**File:** `/home/eenvy/Desktop/cirkelline/.env`

```bash
# AI Services
GOOGLE_API_KEY=AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk
OPENAI_API_KEY=sk-placeholder-for-knowledge-base
EXA_API_KEY=83082804-12e1-4a16-8151-c3c92eef966f
TAVILY_API_KEY=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

# Database
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# JWT Authentication
JWT_SECRET_KEY=c0f7a7e1773b90b74c3ba6c08f21411afe8cbc5f81ca0c0f1f4a9246b8082b68

# Monitoring
AGNO_MONITOR=true
AGNO_DEBUG=false
```

### Production (AWS Secrets Manager)

**Secrets:**
1. `cirkelline-system/database-url`
2. `cirkelline-system/google-api-key`
3. `cirkelline-system/jwt-secret-key`
4. `cirkelline-system/exa-api-key`
5. `cirkelline-system/tavily-api-key`

**Usage in Task Definition:**
```json
{
  "environment": [
    {
      "name": "AGNO_MONITOR",
      "value": "true"
    }
  ],
  "secrets": [
    {
      "name": "DATABASE_URL",
      "valueFrom": "arn:aws:secretsmanager:eu-north-1:710504360116:secret:cirkelline-system/database-url-xxx"
    },
    {
      "name": "GOOGLE_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:eu-north-1:710504360116:secret:cirkelline-system/google-api-key-xxx"
    }
  ]
}
```

### Variable Usage

**Database Connection:**
```python
db = PostgresDb(
    db_url=os.getenv("DATABASE_URL")
)
```

**JWT Signing:**
```python
token = pyjwt.encode(
    payload,
    os.getenv("JWT_SECRET_KEY"),
    algorithm="HS256"
)
```

**AI Models:**
```python
# Gemini API key used by AGNO automatically
os.getenv("GOOGLE_API_KEY")
```

---

## Quick Reference

### Common Operations

```python
# Start backend
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py

# Install dependencies
pip install -r requirements.txt

# Check database connection
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"

# View logs
tail -f cirkelline.log
```

### Key Code Locations

```python
# Main orchestrator
my_os.py:529-689  (Cirkelline team)

# Custom endpoint with filtering
my_os.py:762-853  (/teams/cirkelline/runs)

# Authentication
my_os.py:1150-1277  (signup)
my_os.py:1281-1399  (login)
my_os.py:954-1057   (profile update)

# Knowledge upload
my_os.py:1060-1147  (/api/knowledge/upload)

# User memories
my_os.py:1595-1687  (/api/user/memories)

# Middleware
my_os.py:717-749  (Anonymous + JWT)

# Database functions
my_os.py:97-138  (Private document functions)
```

### API Quick Reference

```bash
# Health check
curl http://localhost:7777/config

# Signup
curl -X POST http://localhost:7777/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass","display_name":"User"}'

# Login
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass"}'

# Send message
curl -X POST http://localhost:7777/teams/cirkelline/runs \
  -H "Authorization: Bearer {token}" \
  -F "message=Hello" \
  -F "stream=false" \
  -F "session_id="

# Upload file
curl -X POST http://localhost:7777/api/knowledge/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf"

# Get user memories
curl -X GET http://localhost:7777/api/user/memories \
  -H "Authorization: Bearer {token}"
```

---

## Delegation Freeze Fix (v1.2.23)

**Updated:** 2025-11-13

### Problem

Research Team delegation was completely broken. When Cirkelline announced "I'll direct the Research Team to...", nothing would happen. The delegation chain froze, preventing any research from being performed.

### Root Cause

**80% - Missing AGNO v2 Team Parameters:**
- `share_member_interactions=True` missing from Research Team → Research Analyst couldn't see Web Researcher's findings
- `show_members_responses=True` missing from Cirkelline → Couldn't see Research Team's synthesis
- `store_member_responses=True` missing from Cirkelline → Couldn't synthesize outputs

**15% - Deprecated AGNO v2 Parameters:**
- `mode="coordinate"` parameter was DEPRECATED in AGNO v2
- `enable_agentic_context=True` parameter was REMOVED in AGNO v2

### Solution

**Lines 1515-1519** - Research Team Configuration:
```python
research_team = Team(
    name="Research Team",
    model=Gemini(id="gemini-2.5-flash"),
    members=[web_researcher, research_analyst],
    tools=[ReasoningTools()],
    # ═══ CRITICAL AGNO TEAM COORDINATION SETTINGS ═══
    # Note: mode="coordinate" removed - deprecated in AGNO v2 (coordinate is now default)
    # Note: enable_agentic_context removed - deprecated in AGNO v2
    share_member_interactions=True,       # ← 🔥 CRITICAL: Analyst sees Researcher's work
    # ═══════════════════════════════════════════════
    instructions=[...],  # Updated with explicit WAIT steps
    ...
)
```

**Lines 1710-1716** - Cirkelline Team Configuration:
```python
cirkelline = Team(
    name="Cirkelline",
    model=Gemini(id="gemini-2.5-flash"),
    members=[
        audio_agent, video_agent, image_agent, document_agent,
        research_team, law_team
    ],
    # ═══ CRITICAL AGNO TEAM COORDINATION SETTINGS ═══
    # Note: mode="coordinate" removed - deprecated in AGNO v2 (coordinate is now default)
    # Note: enable_agentic_context removed - deprecated in AGNO v2
    share_member_interactions=True,       # ← See nested team outputs
    show_members_responses=True,          # ← 🔥 CRITICAL: Include specialist responses
    store_member_responses=True,          # ← 🔥 CRITICAL: Capture all outputs
    # ═══════════════════════════════════════════════
    instructions=[...],
    ...
)
```

**Lines 2899-2986** - Delegation Freeze Monitoring:
```python
# ═══ Delegation Freeze Detection ═══
delegation_announced = False
delegation_executed = False
announcement_time = None

# Track delegation announcements
if event_type in ['RunResponse', 'response', 'agent_response']:
    content = event_data.get('content', '')
    delegation_phrases = ["I'll", "I will", "I'm going to", "Let me have"]
    team_words = ['team', 'specialist', 'delegate', 'have them']

    if has_delegation_phrase and has_team_word:
        delegation_announced = True
        announcement_time = time.time()

# Check for stuck state (10 second timeout)
if delegation_announced and not delegation_executed and announcement_time:
    time_since_announcement = time.time() - announcement_time
    if time_since_announcement > 10:
        logger.error(f"🚨 DELEGATION FREEZE DETECTED!")
```

### Testing Results

**Test Query:** "Give me best communication platform for our team, we already use Notion, Google Workspace"

**Results:**
- ✅ Total execution time: ~84 seconds
- ✅ Complete delegation chain working
- ✅ Zero errors, zero freezes
- ✅ Proper tool usage and output visibility

### AGNO v2 Migration

**Deprecated Parameters (DO NOT USE):**
- `mode="coordinate"` → Coordinate is now default behavior
- `mode="route"` → Use `respond_directly=True`
- `mode="collaborate"` → Use `delegate_task_to_all_members=True`
- `enable_agentic_context=True` → Removed, use `share_member_interactions` and state management

**Current AGNO v2 Parameters:**
- `share_member_interactions: bool = False` - Members see each other's work
- `show_members_responses: bool = False` - Parent sees member responses
- `store_member_responses: bool = False` - Enable synthesis
- `respond_directly: bool = False` - Member responds directly (replaces `mode="route"`)
- `delegate_task_to_all_members: bool = False` - All members get task (replaces `mode="collaborate"`)

See [docs/19-DELEGATION-FREEZE-FIX.md](./19-DELEGATION-FREEZE-FIX.md) for complete technical details.

---

**See Also:**
- [01-ARCHITECTURE.md](./01-ARCHITECTURE.md) - System architecture
- [04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md) - Database schema
- [09-ENVIRONMENT-VARIABLES.md](./09-ENVIRONMENT-VARIABLES.md) - Configuration reference
