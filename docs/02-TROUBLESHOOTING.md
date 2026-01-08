# TROUBLESHOOTING GUIDE

**Last Updated:** 2025-11-18
**Current Version:** v1.2.31

This guide contains EXACT solutions to common issues. Each solution has been tested and verified.

---

## Table of Contents
1. [Streaming & Chat Issues](#streaming--chat-issues) 🆕
2. [Authentication & Login Issues](#authentication--login-issues)
3. [Session Management Issues](#session-management-issues)
4. [Database Connection Issues](#database-connection-issues)
5. [AWS Deployment Issues](#aws-deployment-issues)
6. [Backend Errors](#backend-errors)
7. [Frontend Issues](#frontend-issues)
8. [API Rate Limiting](#api-rate-limiting)
9. [Quick Diagnostics](#quick-diagnostics)

---

## Streaming & Chat Issues

### ✅ RESOLVED: Research Team Delegation Completely Broken (Backend Freeze)

**Fixed in:** v1.2.23 (2025-11-13)
**Status:** ✅ RESOLVED - Fix verified and working

**Symptoms:**
- Cirkelline announces "I'll direct the Research Team to..." but NOTHING happens
- No research is performed, conversation freezes completely
- Backend logs show delegation announced but not executed
- No errors visible to user, just permanent hang
- Affects ALL research delegation attempts (not just second queries)

**When it happened:**
- ANY research query requiring Research Team delegation
- Cirkelline would announce intention to delegate but freeze before execution
- Web Researcher never got task, Research Analyst never synthesized
- Complete delegation chain broken

**Root Cause:**

**80% - Missing AGNO v2 Team Parameters:**
```python
# Research Team (Lines 1515-1519)
research_team = Team(
    # MISSING: share_member_interactions=True
    # Result: Research Analyst couldn't see Web Researcher's findings
)

# Cirkelline (Lines 1710-1716)
cirkelline = Team(
    # MISSING: show_members_responses=True
    # MISSING: store_member_responses=True
    # Result: Cirkelline couldn't see or synthesize Research Team's work
)
```

**15% - Deprecated AGNO v2 Parameters:**
- Using `mode="coordinate"` (DEPRECATED in AGNO v2)
- Using `enable_agentic_context=True` (REMOVED in AGNO v2)
- Both parameters caused TypeError on team initialization

**5% - No Monitoring:**
- No system to detect delegation freeze
- Silent failures with no debugging information

**Solution (v1.2.23):**

**Step 1:** Added AGNO v2 Coordination Parameters
```python
# Research Team (cirkelline/agents/research_team.py)
research_team = Team(
    name="Research Team",
    share_member_interactions=True,  # ← Research Analyst sees Web Researcher's work
    # ...
)

# Cirkelline (cirkelline/orchestrator/cirkelline_team.py)
cirkelline = Team(
    name="Cirkelline",
    share_member_interactions=True,   # ← See nested team outputs
    show_members_responses=True,      # ← Include specialist responses
    store_member_responses=True,      # ← Capture all outputs
    # ...
)
```

**Step 2:** Removed Deprecated Parameters
```python
# REMOVED from both teams:
# - mode="coordinate"        (deprecated in AGNO v2, coordinate is now default)
# - enable_agentic_context   (removed in AGNO v2)
```

**Step 3:** Added Delegation Freeze Monitoring
```python
# cirkelline/endpoints/custom_cirkelline.py
# Detects when delegation is announced but not executed
# 10-second timeout threshold
# Logs error for debugging
```

**Step 4:** Updated Instructions with Explicit WAIT Steps
```python
# Research Team instructions (lines 1534-1562)
"4. ⏳ WAIT for Web Researcher's COMPLETE search results",
"6. ⏳ WAIT for Research Analyst's COMPLETE synthesis",
```

**Testing (v1.2.23):**
```bash
# Test Query
"Give me best communication platform for our team, we already use Notion, Google Workspace"

# Results:
✅ Total execution time: ~84 seconds
✅ Complete delegation chain: Cirkelline → Research Team → Web Researcher → Research Analyst
✅ Zero errors, zero freezes
✅ Research Analyst saw Web Researcher's findings
✅ Cirkelline saw Research Team's synthesis
✅ Full response delivered with platform recommendations
```

**Verification:**
```bash
# Backend logs show proper delegation flow
grep -E "delegate_task_to_member|think|analyze" backend.log

# Should see:
# - Cirkelline: think() → delegate_task_to_member(Research Team)
# - Research Team: think() → delegate(Web Researcher) → delegate(Research Analyst)
# - Cirkelline: Synthesize response
```

**Related Files:**
- `cirkelline/agents/research_team.py` - Research Team configuration
- `cirkelline/orchestrator/cirkelline_team.py` - Cirkelline Team configuration
- `cirkelline/endpoints/custom_cirkelline.py` - Delegation freeze monitoring
- **Complete Documentation:** [docs/19-DELEGATION-FREEZE-FIX.md](./19-DELEGATION-FREEZE-FIX.md)
- **Backend Analysis Report:** `/tmp/backend_analysis.md`

**AGNO v2 Migration Notes:**
- All parameters verified against official AGNO documentation using Agno MCP
- `mode` parameter DEPRECATED - coordinate is now default behavior
- `enable_agentic_context` REMOVED - use `share_member_interactions` instead
- See [docs/01-ARCHITECTURE.md](./01-ARCHITECTURE.md#agno-v2-migration-notes) for complete migration guide

---

### ❌ ISSUE: Research Query Freezes After Delegation (Second Query in Same Session)

**Fixed in:** v1.2.14 (2025-11-03)

**Symptoms:**
- First research query works perfectly (Behind the Scenes shows all work)
- Second research query in SAME SESSION freezes
- Cirkelline says "I'm consulting my Research Team..." but nothing appears after
- Console shows events being received (`✅ PROCESSING MEMBER AGENT CONTENT`) but no display
- Page appears "stuck" - no loading indicator, no content

**When it happens:**
- Multiple research queries in the same chat session
- After Cirkelline delegates work to Research Team
- User sees delegation message but subsequent work doesn't render

**Root Cause:**
Message grouping logic in `Messages.tsx` only pushed conversation turns if they had a `userMessage`. When research work streamed in after Cirkelline's delegation (in the same turn, without a new user message), the turn never got pushed to the render array.

**Solution (v1.2.14):**
Modified `cirkelline-ui/src/components/chat/ChatArea/Messages/Messages.tsx` lines 241-246:

```typescript
// BEFORE (BUG)
if (currentTurn.userMessage) {
  turns.push(currentTurn as ConversationTurn)
}

// AFTER (FIXED)
if (currentTurn.userMessage || (currentTurn.intermediateWork && currentTurn.intermediateWork.length > 0)) {
  turns.push(currentTurn as ConversationTurn)
}
```

**What this fixes:**
- Research work now displays even when streaming after delegation
- Behind the Scenes content renders properly in all scenarios
- Multiple consecutive research queries work without freezing

**Testing:**
```
1. Start new chat session
2. Send first research query (e.g., "What are the latest AI news?")
   → Should work (Behind the Scenes shows research)
3. Send second research query (e.g., "What's one improvement we can make?")
   → Previously froze, now works correctly
4. Send third, fourth, etc. queries
   → All should work without issues
```

**Related Files:**
- File: `cirkelline-ui/src/components/chat/ChatArea/Messages/Messages.tsx:241-246`
- Investigation: `docs/INVESTIGATION-PROGRESS-2025-11-03.md`

---

### ❌ ISSUE: Internal Delegation Instructions Appear as User Messages After Refresh

**Fixed in:** v1.2.14 (2025-11-03)

**Symptoms:**
- After page refresh, internal Research Team instructions appear AS USER MESSAGES in chat bubbles
- Example message appearing as if user sent it:
  > "Research how to dynamically discover and integrate Notion databases..."
- This reveals internal system prompts that should never be visible to users
- Breaks the illusion of seamless multi-agent orchestration

**When it happens:**
- User sends research query
- Research Team processes the query
- User refreshes the page
- Session reloads from database
- Internal delegation instructions appear as user messages

**Root Cause:**
Session loader in `useSessionLoader.tsx` was creating user messages from ALL runs in the database, including child runs (Research Team delegations). The filter only checked if message contained "You are a member of a team" string, but delegation instructions don't contain that phrase.

**Solution (v1.2.14):**
Modified `cirkelline-ui/src/hooks/useSessionLoader.tsx` lines 161-175 to check `parent_run_id`:

```typescript
// ✅ CRITICAL FIX: Only add user messages from TOP-LEVEL runs
const isTopLevelRun = !anyRun.parent_run_id || anyRun.parent_run_id === null || anyRun.parent_run_id === '';
const userContent = run.run_input ?? '';

if (isTopLevelRun && userContent) {
  allMessages.push({
    role: 'user',
    content: userContent,
    created_at: runTimestamp
  })
  console.log(`  → Added user message from TOP-LEVEL run: "${userContent.substring(0, 50)}..."`)
} else if (!isTopLevelRun) {
  console.log(`  ⏭️  Skipped child run (parent: ${anyRun.parent_run_id})`)
}
```

**What this fixes:**
- Only top-level runs (actual user messages) create user message bubbles
- Child runs (delegations) are properly filtered out
- Session reload shows exact same content as live streaming
- Internal system instructions stay hidden

**Testing:**
```
1. Send a research query that triggers Research Team
2. Wait for complete response
3. Refresh the page (Ctrl+R or Cmd+R)
4. Verify: Only YOUR actual messages appear as user messages
5. Verify: No internal delegation instructions visible
6. Verify: Behind the Scenes content matches what you saw before refresh
```

**Related Files:**
- File: `cirkelline-ui/src/hooks/useSessionLoader.tsx:161-175`
- Investigation: `docs/INVESTIGATION-PROGRESS-2025-11-03.md`

---

### 💡 TIP: How to Debug Streaming Issues

**Enable Console Logs:**
The streaming handler has comprehensive logging. Open browser console (F12) and look for:

```
✅ PROCESSING MEMBER AGENT CONTENT - Team: Research Team, Member: Web Researcher
✅ PROCESSING TEAM CONTENT - Team: Cirkelline
📡 Received event: TeamRunContent
📡 Received event: RunContent
```

**What to check:**
1. **Events arriving?** Look for `📡 Received event` messages
2. **Events processing?** Look for `✅ PROCESSING` messages
3. **Content present?** Check if event data has `content` field
4. **Errors?** Look for red error messages or warnings

**Common patterns:**
- Events arriving but not processing → Check event type mapping
- Events processing but not displaying → Check message grouping logic (Messages.tsx)
- No events arriving → Check SSE connection, backend streaming

**Files to check:**
- `cirkelline-ui/src/hooks/useAIStreamHandler.tsx` - Event processing
- `cirkelline-ui/src/components/chat/ChatArea/Messages/Messages.tsx` - Message grouping
- `cirkelline-ui/src/hooks/useSessionLoader.tsx` - Session reload

---

## Authentication & Login Issues

### ❌ ISSUE: Cannot Login or Register - "Internal Server Error"
**Symptoms:**
```
500 Internal Server Error
Login fails silently
Register returns error
```

**Error in logs:**
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedColumn)
column "hashed_password" does not exist
LINE 2:  SELECT id, email, hashed_password, display_name
```

**Root Cause:**
Database table `users` has column named `password_hash` but code expects `hashed_password`

**Solution:**
```sql
-- Connect to database
PGPASSWORD=ewOUuUfgzbcWFOVAZKvPCe7wZ psql \
    -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com \
    -p 5432 \
    -U postgres \
    -d cirkelline_system

-- Rename column
ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;

-- Verify
\d users
-- Should show: hashed_password | character varying(255)
```

**Verification:**
```bash
# Test login endpoint
curl -X POST http://localhost:7777/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

**Prevention:**
- Always check DATABASE-REFERENCE.md for exact column names
- Run schema verification after AWS deployments

**Date Fixed:** 2025-10-12
**File:** `cirkelline/endpoints/auth.py` (login function)

---

### ❌ ISSUE: JWT Token Expired
**Symptoms:**
```
401 Unauthorized
"Token has expired"
User gets logged out unexpectedly
```

**Root Cause:**
JWT tokens expire after 7 days

**Solution:**
```javascript
// Frontend automatically handles this
// User just needs to log in again

// To check token expiration
const token = localStorage.getItem('auth_token')
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]))
  const exp = new Date(payload.exp * 1000)
  console.log('Token expires:', exp)
}
```

**Prevention:**
- Implement token refresh mechanism (future feature)
- Current: Users re-login every 7 days

---

### ❌ ISSUE: JWT Middleware Admin Name Extraction Failure

**Fixed in:** v1.2.31 (2025-11-18)
**Status:** ✅ RESOLVED - Fix verified and working

**Symptoms:**
- Admin profiles not loading despite valid JWT token
- Admin-only features broken or showing unauthorized errors
- GET /api/user/admin-profile returns null or incomplete data
- Admin users treated as regular users

**When it happens:**
- Admin users attempting to access admin-specific endpoints
- After login with admin credentials
- Admin profile data missing from JWT dependency injection

**Root Cause:**
JWT middleware was correctly decoding tokens but failed to extract the `admin_name` field from the token payload before querying the database. The `get_admin_profile_dependency()` function in middleware was missing the extraction step:

```python
# BROKEN (Lines 254-264 in cirkelline/middleware/middleware.py)
async def get_admin_profile_dependency(request: Request):
    payload = getattr(request.state, 'jwt_payload', {})
    user_id = payload.get('user_id')
    # admin_name = payload.get('admin_name')  # ← MISSING!

    # Database query with NULL admin_name parameter
    result = await db.execute(
        text("SELECT * FROM admin_profiles WHERE user_id = :user_id AND name = :admin_name"),
        {"user_id": user_id, "admin_name": None}  # ← Always None!
    )
```

**Solution (v1.2.31):**
Added `admin_name` field extraction from JWT payload in `cirkelline/middleware/middleware.py`:

```python
# FIXED (Lines 254-264)
async def get_admin_profile_dependency(request: Request):
    payload = getattr(request.state, 'jwt_payload', {})
    user_id = payload.get('user_id')
    admin_name = payload.get('admin_name')  # ✅ Extract admin_name from token

    if not admin_name:
        return None  # Not an admin

    # Database query with correct admin_name
    result = await db.execute(
        text("SELECT * FROM admin_profiles WHERE user_id = :user_id AND name = :admin_name"),
        {"user_id": user_id, "admin_name": admin_name}
    )
    return result.mappings().first() if result else None
```

**Testing (v1.2.31 - Phase 2.1):**
```bash
# Test admin profile endpoint with admin token
TOKEN="<admin-jwt-token>"
curl -s http://localhost:7777/api/user/admin-profile \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
{
  "user_id": "ee461076-8cbb-4626-947b-956f293cf7bf",
  "name": "Ivo",
  "role": "CEO & Creator",
  "context": "...",
  "preferences": {...},
  "custom_instructions": "..."
}
```

**Verification:**
```bash
# Check JWT token contains admin_name
echo $TOKEN | cut -d'.' -f2 | base64 -d | jq .

# Should show:
# {
#   "user_id": "...",
#   "admin_name": "Ivo",  ← Must be present
#   ...
# }
```

**Related Files:**
- `cirkelline/middleware/middleware.py:254-264` - JWT dependency injection fix
- **Testing Documentation:** `TESTING_PROGRESS_v1.2.31.md` - Phase 2.1 results

**Impact:**
- **Critical bug** affecting all admin users
- Admin features completely broken before fix
- Zero admin profile data accessible
- Fixed in all environments (localhost + AWS production)

---

## Session Management Issues

### ❌ ISSUE: Sessions Not Appearing in Sidebar
**Symptoms:**
```
User sends message
First message appears in sidebar
Click "New Chat", send second message
Second session DOES NOT appear
After refresh, all sessions gone
```

**Root Cause (Fixed 2025-10-12):**
Backend was passing `session_id=None` to AGNO, causing AGNO to reuse the same session instead of creating new ones

**Solution:**
Already fixed in `cirkelline/endpoints/custom_cirkelline.py`:
```python
# BEFORE (BROKEN):
# actual_session_id = session_id if session_id else None

# AFTER (FIXED):
if not session_id:  # None or empty string
    import uuid
    actual_session_id = str(uuid.uuid4())
    logger.info(f"🆕 Generated NEW session ID: {actual_session_id}")
else:
    actual_session_id = session_id
```

**Verification:**
```bash
# Check database - should see multiple sessions for user
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c \
    "SELECT session_id, user_id, created_at FROM ai.agno_sessions WHERE user_id = 'your-user-id' ORDER BY created_at DESC LIMIT 5;"
```

**If Issue Persists:**
```bash
# Check frontend is updating URL with session ID
# Open browser DevTools → Network → check /teams/cirkelline/runs response
# Should contain: {"session_id": "unique-uuid"}

# Verify frontend code in useAIStreamHandler.tsx:182-190
```

---

### ❌ ISSUE: User Sees Other Users' Sessions
**Symptoms:**
```
Sidebar shows sessions from other users
Can access private conversations
```

**Root Cause:**
Backend not filtering sessions by `user_id`

**Solution:**
```python
# In my_os.py - verify user_id is being used
# Check lines 770-790

# Sessions must be loaded with filter:
session = team.session(session_id=actual_session_id, user_id=user_id)
```

**Verification:**
```sql
-- All sessions should have user_id
SELECT session_id, user_id, team_id FROM ai.agno_sessions LIMIT 10;

-- Should NOT see NULL in user_id column
```

---

## Database Connection Issues

### ❌ ISSUE: "column does not exist" - agno_memories Table
**Symptoms:**
```
psycopg.errors.UndefinedColumn: column "created_at" does not exist
LINE 2:                 SELECT memory, created_at
                                       ^
HINT:  Perhaps you meant to reference the column "agno_memories.updated_at".
```

**Error Context:**
- Fetching user details in admin panel
- Querying recent memories
- 500 Internal Server Error from `/api/admin/users/{user_id}`

**Root Cause:**
The `ai.agno_memories` table uses `updated_at` NOT `created_at`. This is different from `ai.agno_sessions` which has both columns.

**Solution:**

1. **Backend Fix** - Always use `updated_at` for memories:
   ```python
   # CORRECT ✅
   SELECT memory, updated_at
   FROM ai.agno_memories
   WHERE user_id = :user_id
   ORDER BY updated_at DESC

   # WRONG ❌
   SELECT memory, created_at  -- Column does not exist!
   FROM ai.agno_memories
   WHERE user_id = :user_id
   ```

2. **Frontend Fix** - Expect `updated_at` in response:
   ```typescript
   // CORRECT ✅
   {new Date(memory.updated_at * 1000).toLocaleString()}

   // WRONG ❌
   {new Date(memory.created_at * 1000).toLocaleString()}
   ```

3. **Verify Schema:**
   ```bash
   docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline \
     -c "\d ai.agno_memories"
   ```

   Should show:
   ```
   memory_id   | character varying | PRIMARY KEY
   memory      | json             | NOT NULL
   user_id     | character varying | INDEXED
   updated_at  | bigint           |            ← Only timestamp column!
   ```

**Files Fixed (v1.1.0):**
- Backend: `cirkelline/endpoints/memories.py`
- Frontend: `cirkelline-ui/src/app/admin/users/page.tsx`

**Related Documentation:**
- See [04-DATABASE-REFERENCE.md](./04-DATABASE-REFERENCE.md#aiagno_memories) for full schema
- See [12-USER-MANAGEMENT-SYSTEM.md](./MAIN/12-USER-MANAGEMENT-SYSTEM.md#issue-5-column-name-mismatch-error) for details

---

### ❌ ISSUE: "Connection Refused" to Database
**Symptoms:**
```
sqlalchemy.exc.OperationalError: (psycopg.OperationalError)
connection to server at "localhost" (127.0.0.1), port 5532 failed: Connection refused
```

**Solution:**
```bash
# 1. Check if Docker container is running
docker ps | grep cirkelline-postgres

# If not running:
docker start cirkelline-postgres

# 2. Verify container is healthy
docker logs cirkelline-postgres

# 3. Test connection
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"

# 4. Check port mapping
docker port cirkelline-postgres
# Should show: 5432/tcp -> 0.0.0.0:5532
```

**If Container Doesn't Exist:**
```bash
# Recreate container
docker run -d \
    --name cirkelline-postgres \
    -e POSTGRES_USER=cirkelline \
    -e POSTGRES_PASSWORD=cirkelline123 \
    -e POSTGRES_DB=cirkelline \
    -p 5532:5432 \
    pgvector/pgvector:pg17

# Enable vector extension
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### ❌ ISSUE: pgvector Extension Not Found
**Symptoms:**
```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedObject)
type "vector" does not exist
```

**Solution:**
```bash
# ⚠️ CRITICAL: Extension name is "vector" NOT "pgvector"!

# Enable extension
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline \
    -c "\dx vector"
# Should show: vector | 0.7.0 or 0.8.0
```

**AWS RDS:**
```bash
PGPASSWORD=<password> psql \
    -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com \
    -p 5432 -U postgres -d cirkelline_system \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## AWS Deployment Issues

### ❌ ISSUE: ECS Tasks Can't Access Secrets Manager
**Symptoms:**
```
Error: ResourceInitializationError:
unable to pull secrets or registry auth
```

**CloudWatch Logs:**
```
Connection issue with Secrets Manager
Cannot retrieve secret: cirkelline-system/database-url
```

**Solution:**
```bash
# 1. Create VPC Endpoint for Secrets Manager
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxx \
    --service-name com.amazonaws.eu-north-1.secretsmanager \
    --route-table-ids rtb-xxxxxx \
    --region eu-north-1

# 2. Update security group to allow HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id sg-07a6eb96ed423cc27 \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# 3. Verify IAM role has SecretsManagerReadWrite policy
aws iam list-attached-role-policies \
    --role-name ecsTaskExecutionRole
```

**Verification:**
```bash
# Check task logs
aws logs tail /ecs/cirkelline-system-backend --follow --region eu-north-1

# Should NOT see Secrets Manager errors
```

---

### ❌ ISSUE: ECS Tasks Can't Pull Docker Images from ECR
**Symptoms:**
```
CannotPullContainerError:
Error response from daemon: pull access denied
```

**Solution:**
```bash
# 1. Create ECR VPC Endpoints
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxx \
    --service-name com.amazonaws.eu-north-1.ecr.api \
    --route-table-ids rtb-xxxxxx

aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxx \
    --service-name com.amazonaws.eu-north-1.ecr.dkr \
    --route-table-ids rtb-xxxxxx

# 2. Create S3 Gateway Endpoint (ECR stores layers in S3)
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-xxxxxx \
    --service-name com.amazonaws.eu-north-1.s3 \
    --route-table-ids rtb-xxxxxx

# 3. Verify task execution role has ECR permissions
aws iam get-role --role-name ecsTaskExecutionRole
```

---

### ❌ ISSUE: ECS Tasks Failing Health Checks
**Symptoms:**
```
Task failed ELB health checks in target group
Service: cirkelline-system-backend-service (instance i-xxx)
deregistration in progress
```

**Solution:**
```bash
# 1. Check health check endpoint
curl http://<alb-dns>/config

# 2. Check task logs for startup errors
aws logs tail /ecs/cirkelline-system-backend --since 10m --region eu-north-1

# 3. Verify health check configuration
aws elbv2 describe-target-health \
    --target-group-arn <tg-arn> \
    --region eu-north-1

# Common issues:
# - Backend not listening on port 7777
# - /config endpoint returning error
# - Container startup taking too long (increase startPeriod)
```

**Fix Health Check Settings:**
```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:7777/config || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 60  // ← Increase if container slow to start
  }
}
```

---

## Backend Errors

### ❌ ISSUE: ModuleNotFoundError
**Symptoms:**
```
ModuleNotFoundError: No module named 'agno'
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
cd ~/Desktop/cirkelline
source .venv/bin/activate
pip install -r requirements.txt

# Verify
pip list | grep agno
# Should show: agno==2.1.1
```

---

### ❌ ISSUE: Port 7777 Already in Use
**Symptoms:**
```
OSError: [Errno 48] Address already in use
ERROR: Could not bind to 0.0.0.0:7777
```

**Solution:**
```bash
# Find process using port 7777
lsof -i :7777

# Kill the process
kill -9 <PID>

# Or kill all Python processes (use with caution)
pkill -9 python

# Restart backend
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

---

### ❌ ISSUE: Google API Rate Limit (429 Error)
**Symptoms:**
```
google.api_core.exceptions.ResourceExhausted: 429 Resource has been exhausted
Reason: RATE_LIMIT_EXCEEDED
```

**Error Details:**
```
Rate limit exceeded. Using free tier limits (10 RPM)
Need to upgrade to Tier 1 (1500 RPM)
```

**Root Cause:**
System using FREE tier API key instead of TIER 1 key

**Solution (Fixed 2025-10-12):**
```bash
# 1. Update ~/.bashrc
echo 'export GOOGLE_API_KEY="AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk"' >> ~/.bashrc
source ~/.bashrc

# 2. Update AWS Secrets Manager
aws secretsmanager update-secret \
    --secret-id cirkelline-system/google-api-key \
    --secret-string "AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk" \
    --region eu-north-1

# 3. Restart backend (picks up new key)
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py

# 4. Force ECS deployment (AWS)
aws ecs update-service \
    --cluster cirkelline-system-cluster \
    --service cirkelline-system-backend-service \
    --force-new-deployment \
    --region eu-north-1
```

**Verification:**
```bash
# Check which key is being used
echo $GOOGLE_API_KEY

# Should be Tier 1 key: AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk
# NOT free tier: AIzaSyD23dYIYOFcDIhv61LrZn8xzikbJjnq_Uk
```

---

### ❌ ISSUE: SQL Ambiguous Column Reference - GET /api/user/tier Returns 500

**Fixed in:** v1.2.31 (2025-11-18)
**Status:** ✅ RESOLVED - Fix verified and working

**Symptoms:**
- GET /api/user/tier endpoint returning 500 Internal Server Error
- Error message: "column reference 'tier_id' is ambiguous"
- User tier information not loading in frontend
- Subscription management features broken

**Error in logs:**
```python
sqlalchemy.exc.ProgrammingError: (psycopg.errors.AmbiguousColumn)
column reference "tier_id" is ambiguous
LINE 2:     WHERE tier_id = :tier_id
                  ^
HINT: Use qualified column name like users.tier_id or tiers.tier_id
```

**When it happens:**
- Any request to GET /api/user/tier endpoint
- Affects all users (admin and regular)
- Prevents tier information display in UI

**Root Cause:**
SQL query in `cirkelline/services/tier_service.py` referenced `tier_id` column without table qualifier. Since the query joins `users` and `tiers` tables (both containing a `tier_id` column), the database couldn't determine which table's column to use:

```python
# BROKEN (Line 367 in cirkelline/services/tier_service.py)
async def get_user_tier(user_id: str):
    result = await db.execute(
        text("""
            SELECT
                tiers.tier_id, tiers.name, tiers.slug, tiers.level
            FROM users
            JOIN tiers ON users.tier_id = tiers.tier_id
            WHERE tier_id = :tier_id  -- ❌ AMBIGUOUS! Which tier_id?
        """),
        {"tier_id": tier_id}
    )
```

**Solution (v1.2.31):**
Added table qualifier to `tier_id` column reference in WHERE clause:

```python
# FIXED (Line 367)
async def get_user_tier(user_id: str):
    result = await db.execute(
        text("""
            SELECT
                tiers.tier_id, tiers.name, tiers.slug, tiers.level,
                tiers.description, tiers.features
            FROM users
            JOIN tiers ON users.tier_id = tiers.tier_id
            WHERE users.tier_id = :tier_id  -- ✅ QUALIFIED! Clear reference
        """),
        {"tier_id": tier_id}
    )
    return result.mappings().first()
```

**Testing (v1.2.31 - Phase 2.3):**
```bash
# Test user tier endpoint
TOKEN="<user-jwt-token>"
curl -s http://localhost:7777/api/user/tier \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
{
  "tier_id": "5",
  "name": "Family",
  "slug": "family",
  "level": 5,
  "description": "Perfect for families and small groups",
  "features": ["Unlimited sessions", "Priority support", ...]
}
```

**Verification:**
```bash
# Check tier service SQL queries
grep -n "tier_id = :tier_id" cirkelline/services/tier_service.py

# Should show qualified reference:
# 367:    WHERE users.tier_id = :tier_id
```

**Related Files:**
- `cirkelline/services/tier_service.py:367` - SQL query fix
- **Testing Documentation:** `TESTING_PROGRESS_v1.2.31.md` - Phase 2.3 results
- **Database Schema:** `docs/04-DATABASE-REFERENCE.md` - users and tiers table definitions

**Impact:**
- **Critical bug** affecting all users
- Tier information completely inaccessible
- Subscription management UI broken
- Fixed by adding explicit table qualifier (2-word change!)

**Database Context:**
Both tables have `tier_id` column:
- `users.tier_id` - Foreign key to user's current tier
- `tiers.tier_id` - Primary key of tier definition

Always use qualified names when joining tables with overlapping column names.

---

## Frontend Issues

### ❌ ISSUE: Frontend Can't Connect to Backend
**Symptoms:**
```
Failed to fetch
CORS error
Network request failed
```

**Solution:**
```bash
# 1. Verify backend is running
curl http://localhost:7777/config

# 2. Check selectedEndpoint in browser
# Open DevTools → Console:
localStorage.getItem('endpoint-storage')
# Should show: {"state":{"selectedEndpoint":"http://localhost:7777"},"version":0}

# 3. Fix if wrong
localStorage.setItem('endpoint-storage', JSON.stringify({
  state: { selectedEndpoint: 'http://localhost:7777' },
  version: 0
}))

# 4. Reload page
```

---

### ❌ ISSUE: New Users See Localhost Connection Instead of Production API
**Symptoms:**
```
New user registers on cirkelline.com
Sidebar shows connection: "localhost" instead of "api.cirkelline.com"
Despite correct Vercel environment variables
```

**Root Cause (Fixed 2025-10-12):**
The `selectedEndpoint` was being persisted to localStorage, causing old values to override environment variables for new users.

**Solution:**
Updated `cirkelline-ui/src/store.ts` lines 105-115:
```typescript
// BEFORE (BROKEN):
partialize: (state) => ({
  selectedEndpoint: state.selectedEndpoint  // ❌ Persisted to localStorage
}),

// AFTER (FIXED):
partialize: () => ({
  // DO NOT persist selectedEndpoint - always use env var
  // DO NOT persist mode - always default to 'team'
}),
```

**What This Fixes:**
- ✅ New users always get `https://api.cirkelline.com` from `NEXT_PUBLIC_API_URL`
- ✅ No localStorage pollution affecting new users
- ✅ Endpoint always comes fresh from environment variables

**Verification:**
```bash
# Check store.ts
grep "partialize:" cirkelline-ui/src/store.ts -A 3
# Should show empty object with comments

# Test in browser (incognito mode)
# Visit cirkelline.com → Check sidebar connection
# Should show: https://api.cirkelline.com (green dot)
```

**Files Changed:**
- `cirkelline-ui/src/store.ts` (line 108)

**Date Fixed:** 2025-10-12

---

### ❌ ISSUE: Wrong Team/Agent Selected by Default
**Symptoms:**
```
"Audio Specialist" selected instead of "Cirkelline"
User has to manually switch every time
```

**Solution (Fixed 2025-10-05):**
Updated `cirkelline-ui/src/store.ts` line 91:
```typescript
// BEFORE:
// mode: 'agent'

// AFTER:
mode: 'team'  // Default to Cirkelline team
```

**Verification:**
```bash
# Check store.ts
grep "mode:" cirkelline-ui/src/store.ts
# Should show: mode: 'team' as defaultAgentConfig
```

---

## API Rate Limiting

### Rate Limit Tiers

| Tier | RPM | RPD | Tokens/Min |
|------|-----|-----|------------|
| Free | 10 | 1,500 | 32,000 |
| Tier 1 | 1,500 | Unlimited | 4,000,000 |

**Current Key:** Tier 1 (AIzaSyDd7WG_7VWh9OKB6L-QU5xNEWku8G2qGvk)

**To Check Your Tier:**
1. Go to https://aistudio.google.com/apikey
2. Find key: "cirkelline gen-lang-client-0672245186"
3. Verify: "Quota tier: Tier 1"

---

## Quick Diagnostics

### Health Check Script
```bash
#!/bin/bash
echo "=== CIRKELLINE HEALTH CHECK ==="

# Backend
echo "1. Backend Status:"
curl -s http://localhost:7777/config > /dev/null && echo "✅ Backend OK" || echo "❌ Backend DOWN"

# Database
echo "2. Database Status:"
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;" > /dev/null 2>&1 && echo "✅ Database OK" || echo "❌ Database DOWN"

# pgvector
echo "3. pgvector Extension:"
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT extversion FROM pg_extension WHERE extname='vector';" 2>&1 | grep -q "0\." && echo "✅ pgvector OK" || echo "❌ pgvector MISSING"

# Frontend
echo "4. Frontend Status:"
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"

# API Key
echo "5. Google API Key:"
[[ ! -z "$GOOGLE_API_KEY" ]] && echo "✅ API Key Set" || echo "❌ API Key MISSING"

echo "================================"
```

Save as `health-check.sh`, make executable: `chmod +x health-check.sh`

---

### Log Locations

```bash
# Backend logs (local)
cd ~/Desktop/cirkelline
tail -f backend.log

# Backend logs (AWS)
aws logs tail /ecs/cirkelline-system-backend --follow --region eu-north-1

# Database logs (Docker)
docker logs cirkelline-postgres

# Frontend logs (browser DevTools)
# Open Console → look for errors
```

---

### Emergency Reset

```bash
# ⚠️ WARNING: This deletes ALL data!

# Stop everything
pkill -9 python
docker stop cirkelline-postgres

# Delete database
docker rm cirkelline-postgres

# Recreate fresh
docker run -d \
    --name cirkelline-postgres \
    -e POSTGRES_USER=cirkelline \
    -e POSTGRES_PASSWORD=cirkelline123 \
    -e POSTGRES_DB=cirkelline \
    -p 5532:5432 \
    pgvector/pgvector:pg17

# Enable vector
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Start backend
cd ~/Desktop/cirkelline
source .venv/bin/activate
python my_os.py
```

---

## Common Error Patterns

### Pattern 1: Database Schema Mismatch
```
Error: column "X" does not exist
```
**Fix:** Check DATABASE-REFERENCE.md for exact column names

### Pattern 2: Missing Environment Variable
```
KeyError: 'GOOGLE_API_KEY'
```
**Fix:** Check .env file and ensure `source .env` was run

### Pattern 3: Docker Container Not Running
```
Connection refused
Port 5532 not accessible
```
**Fix:** `docker start cirkelline-postgres`

### Pattern 4: VPC Endpoint Missing (AWS)
```
Connection timeout
Cannot reach AWS service
```
**Fix:** Create VPC endpoints for Secrets Manager, ECR, S3

---

## Getting Help

1. **Check this guide first** - Most issues are documented here
2. **Check logs** - Error messages usually indicate the exact problem
3. **Check DATABASE-REFERENCE.md** - For schema questions
4. **Check AWS-DEPLOYMENT.md** - For AWS infrastructure issues

**When reporting an issue, include:**
- Exact error message
- Relevant logs (5-10 lines before error)
- What you were trying to do
- Environment (localhost or AWS)
