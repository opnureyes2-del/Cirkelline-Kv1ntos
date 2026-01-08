# DATABASE REFERENCE

**Last Updated:** 2025-12-19
**Current Version:** v1.3.7

---

## Table of Contents
- [Connection Details](#connection-details)
- [Schema Overview](#schema-overview)
- [Table Definitions](#table-definitions)
- [Metadata Structures](#metadata-structures)
- [Common Queries](#common-queries)
- [Database Migrations](#database-migrations)

---

## Connection Details

### Localhost (Development)
```bash
# Connection String
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline

# Docker Container
Container Name: cirkelline-postgres
Image: pgvector/pgvector:pg17
Host Port: 5532 → Container Port: 5432
```

### AWS RDS (Production)
```bash
# Connection String (from Secrets Manager)
DATABASE_URL=postgresql://postgres:<password>@cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com:5432/cirkelline_system

# Database Details
Instance ID: cirkelline-system-db
Engine: PostgreSQL 16.10
Instance Class: db.t3.medium
Storage: 20 GB GP2
```

### PostgreSQL Version & Extensions
```sql
-- Check PostgreSQL version
SELECT version();
-- PostgreSQL 17.6 (localhost) or 16.10 (AWS)

-- Check pgvector extension (CRITICAL: extension name is 'vector' NOT 'pgvector')
\dx vector
-- Should show: vector | 0.7.0 or 0.8.0

-- Enable if missing
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Schema Overview

### Schema Structure
```
cirkelline (database)
├── public (schema)
│   ├── users                    # Authentication
│   ├── admin_profiles           # Admin user profiles
│   ├── notion_tokens            # Notion OAuth tokens (per-user)
│   ├── calendars                # User calendars (v1.3.6)
│   ├── calendar_events          # Calendar events (v1.3.6)
│   ├── task_lists               # Task lists (v1.3.7)
│   └── tasks                    # Tasks with priority, due dates (v1.3.7)
│
└── ai (schema)
    ├── agno_sessions            # AGNO session data
    ├── agno_memories            # User memories
    ├── agno_memories_archive    # Archived memories (recovery)
    ├── agno_knowledge           # Knowledge base metadata
    ├── cirkelline_knowledge_vectors  # Vector embeddings
    ├── workflow_runs            # Workflow execution tracking
    ├── user_journals            # Daily journal entries (v1.3.2)
    └── journal_queue            # Journal processing queue (v1.3.2)
```

---

## Table Definitions

### `public.users`
**Purpose:** User authentication and profile data

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PRIMARY KEY | User identifier |
| `email` | VARCHAR(255) | UNIQUE NOT NULL | Login email |
| `hashed_password` | VARCHAR(255) | NOT NULL | **CRITICAL:** Column is named `hashed_password` NOT `password_hash`! Bcrypt hash (12 rounds) |
| `display_name` | VARCHAR(255) | NOT NULL | User's display name |
| `preferences` | JSONB | DEFAULT '{}'::jsonb | User preferences (theme, accent, sidebar, banner) - **Added 2025-10-22** |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last modification |

**Indexes:**
```sql
PRIMARY KEY: users_pkey (id)
UNIQUE: users_email_key (email)
```

**Critical Notes:**
- ⚠️ **ALWAYS use `hashed_password`** - not `password_hash`!
- This naming inconsistency caused production login failures on 2025-10-12
- AWS database was created with `password_hash` and had to be renamed

**Sample Queries:**
```sql
-- Get user by email
SELECT id, email, hashed_password, display_name
FROM users
WHERE email = 'user@example.com';

-- Create new user
INSERT INTO users (id, email, hashed_password, display_name, created_at, updated_at)
VALUES (
    'uuid-here',
    'user@example.com',
    'bcrypt-hash-here',
    'User Name',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Update display name
UPDATE users
SET display_name = 'New Name', updated_at = CURRENT_TIMESTAMP
WHERE id = 'user-uuid';
```

---

### `public.admin_profiles`
**Purpose:** Extended profile data for admin users

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `user_id` | UUID | PRIMARY KEY, FK → users(id) ON DELETE CASCADE | References users table |
| `name` | VARCHAR(255) | NOT NULL | Admin's real name |
| `role` | VARCHAR(255) | NOT NULL | e.g., "CEO & Creator" |
| `personal_context` | TEXT | | Background info for agents |
| `preferences` | TEXT | | Communication preferences |
| `custom_instructions` | TEXT | | Special instructions for agents |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Profile creation |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last modification |

**Sample Queries:**
```sql
-- Get admin profile
SELECT
    u.email,
    ap.name,
    ap.role,
    ap.personal_context,
    ap.preferences,
    ap.custom_instructions
FROM users u
JOIN admin_profiles ap ON u.id = ap.user_id
WHERE u.email = 'admin@example.com';

-- Check if user is admin
SELECT EXISTS (
    SELECT 1 FROM admin_profiles WHERE user_id = 'user-uuid'
) AS is_admin;
```

---

### `public.notion_tokens`
**Purpose:** Per-user Notion workspace OAuth tokens (encrypted storage)
**Added:** 2025-11-02 (v1.2.12) - ✅ LIVE IN PRODUCTION

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing identifier |
| `user_id` | UUID | UNIQUE NOT NULL, FK → users(id) ON DELETE CASCADE | One workspace per user |
| `workspace_id` | VARCHAR(255) | NOT NULL | Notion workspace identifier |
| `workspace_name` | VARCHAR(255) | | User's workspace name |
| `workspace_icon` | VARCHAR(255) | | Workspace icon (emoji) |
| `access_token` | TEXT | NOT NULL | **ENCRYPTED** with AES-256-GCM |
| `bot_id` | VARCHAR(255) | | Notion bot identifier |
| `owner_email` | VARCHAR(255) | | Workspace owner email |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Token creation |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update (auto-trigger) |

**Indexes:**
```sql
PRIMARY KEY: notion_tokens_pkey (id)
UNIQUE: notion_tokens_user_id_key (user_id)
INDEX: idx_notion_tokens_user_id (user_id)
INDEX: idx_notion_tokens_workspace_id (workspace_id)
```

**Triggers:**
```sql
CREATE TRIGGER update_notion_tokens_updated_at
    BEFORE UPDATE ON notion_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Critical Notes:**
- ⚠️ **Tokens are encrypted** with AES-256-GCM before storage
- Encryption key: `NOTION_TOKEN_ENCRYPTION_KEY` environment variable
- **One workspace per user** (UNIQUE constraint on user_id)
- Tokens automatically deleted when user is deleted (CASCADE)
- Pattern matches `google_tokens` table structure

**Security Features:**
- AES-256-GCM encryption (same pattern as Google OAuth)
- Nonce-based encryption (secure random IV)
- Encrypted format: `<nonce>:<ciphertext>:<tag>` (base64-encoded)
- Helper function: `get_user_notion_credentials(user_id)` for decryption
- Full user isolation via JWT middleware

**Sample Queries:**
```sql
--- Get user's Notion connection status
SELECT
    user_id,
    workspace_name,
    workspace_icon,
    owner_email,
    created_at
FROM notion_tokens
WHERE user_id = 'user-uuid';

--- Check if user has Notion connected
SELECT EXISTS (
    SELECT 1 FROM notion_tokens WHERE user_id = 'user-uuid'
) AS has_notion;

--- Disconnect user's Notion workspace
DELETE FROM notion_tokens WHERE user_id = 'user-uuid';

--- Count total Notion connections
SELECT COUNT(*) FROM notion_tokens;

--- Recent Notion connections
SELECT
    u.email,
    nt.workspace_name,
    nt.created_at
FROM notion_tokens nt
JOIN users u ON nt.user_id = u.id
ORDER BY nt.created_at DESC
LIMIT 10;
```

**Related Endpoints:**
- `GET /api/oauth/notion/start` - Initiate OAuth flow
- `GET /api/oauth/notion/callback` - Handle OAuth callback & store token
- `GET /api/oauth/notion/status` - Check connection status
- `POST /api/oauth/notion/disconnect` - Delete token
- `GET /api/notion/databases` - List discovered databases
- `POST /api/notion/databases/sync` - Refresh database list
- `GET /api/notion/companies` - Fetch companies (requires connected workspace)
- `GET /api/notion/projects` - Fetch projects (requires connected workspace)
- `GET /api/notion/tasks` - Fetch tasks (requires connected workspace)
- `POST /api/notion/tasks` - Create task (requires connected workspace)

**Migration File:** `migrations/003_create_notion_tokens.sql`

---

### `public.notion_user_databases`
**Purpose:** Dynamic database registry - stores discovered Notion databases per user
**Added:** 2025-11-07 (v1.2.19) - ✅ DYNAMIC DISCOVERY SYSTEM
**Status:** 🔥 **REVOLUTIONARY** - Works with ANY database structure!

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing identifier |
| `user_id` | UUID | NOT NULL, FK → users(id) ON DELETE CASCADE | User who owns this database |
| `database_id` | VARCHAR(255) | NOT NULL | Notion database UUID |
| `database_title` | VARCHAR(255) | | Actual database name in Notion |
| `database_type` | VARCHAR(50) | | Auto-classified: 'tasks', 'projects', 'companies', 'documentation', 'custom' |
| `user_label` | VARCHAR(255) | | User can override display name |
| `schema` | JSONB | NOT NULL | Full database schema (properties, types, configs) |
| `is_hidden` | BOOLEAN | DEFAULT FALSE | User can hide databases from UI |
| `last_synced` | TIMESTAMP | | Last discovery/sync timestamp |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | First discovery |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last schema update (auto-trigger) |

**Indexes:**
```sql
PRIMARY KEY: notion_user_databases_pkey (id)
UNIQUE: notion_user_databases_user_id_database_id_key (user_id, database_id)
INDEX: idx_notion_user_dbs_user_id (user_id)
INDEX: idx_notion_user_dbs_type (database_type)
INDEX: idx_notion_user_dbs_database_id (database_id)
```

**Triggers:**
```sql
CREATE TRIGGER update_notion_user_databases_updated_at_trigger
    BEFORE UPDATE ON notion_user_databases
    FOR EACH ROW
    EXECUTE FUNCTION update_notion_user_databases_updated_at();
```

**Critical Features:**
- 🎯 **Dynamic Discovery:** Automatically finds ALL databases user shares with Cirkelline
- 🔄 **Schema-Aware:** Stores full property schema for intelligent querying
- 🏷️ **Auto-Classification:** Analyzes database structure to identify type
- 🌐 **Multi-User Ready:** Each user sees only their databases
- 🚀 **Scalable:** No hardcoded database names - works with ANY structure
- 📊 **JSONB Schema:** Enables complex property extraction without repeated API calls

**Schema JSONB Structure:**
```json
{
  "id": "database-uuid",
  "title": "Tasks",
  "properties": {
    "Name": {
      "id": "title",
      "type": "title",
      "name": "Name"
    },
    "Status": {
      "id": "prop-id",
      "type": "status",
      "name": "Status",
      "options": [
        {"name": "Not Started", "color": "gray"},
        {"name": "In Progress", "color": "blue"},
        {"name": "Done", "color": "green"}
      ],
      "groups": [...]
    },
    "Priority": {
      "id": "prop-id",
      "type": "select",
      "name": "Priority",
      "options": [
        {"name": "High", "color": "red"},
        {"name": "Medium", "color": "yellow"},
        {"name": "Low", "color": "green"}
      ]
    },
    "Due Date": {
      "id": "prop-id",
      "type": "date",
      "name": "Due Date"
    }
  }
}
```

**Discovery & Classification Logic:**
```sql
-- Auto-classification based on title and properties
-- Tasks: Contains "task" in title OR has (title + status + due_date properties)
-- Projects: Contains "project" in title OR has (title + timeline/dates)
-- Companies: Contains "company/client/domain" in title OR has (title + industry/domain)
-- Documentation: Contains "doc/knowledge/wiki" in title OR has (title + category/tags)
-- Custom: Anything else
```

**Sample Queries:**
```sql
--- Get all databases for a user
SELECT
    database_title,
    database_type,
    last_synced
FROM notion_user_databases
WHERE user_id = 'user-uuid'
ORDER BY database_type, database_title;

--- Find user's tasks database (even if renamed!)
SELECT
    database_id,
    database_title,
    schema
FROM notion_user_databases
WHERE user_id = 'user-uuid'
  AND database_type = 'tasks'
  AND is_hidden = FALSE
ORDER BY last_synced DESC
LIMIT 1;

--- Get schema for specific database
SELECT
    database_title,
    jsonb_pretty(schema) as schema_details
FROM notion_user_databases
WHERE user_id = 'user-uuid'
  AND database_id = 'database-uuid';

--- Count databases by type
SELECT
    database_type,
    COUNT(*) as count
FROM notion_user_databases
WHERE user_id = 'user-uuid'
GROUP BY database_type
ORDER BY count DESC;

--- Find databases not synced in 7+ days
SELECT
    database_title,
    database_type,
    last_synced,
    NOW() - last_synced as age
FROM notion_user_databases
WHERE user_id = 'user-uuid'
  AND last_synced < NOW() - INTERVAL '7 days'
ORDER BY last_synced ASC;

--- Check if user renamed "Companies" to "Domains"
SELECT
    database_title,
    database_type,
    schema->'title' as original_title
FROM notion_user_databases
WHERE user_id = 'user-uuid'
  AND database_type = 'companies';
```

**Related Functions:**
- `discover_and_store_user_databases_sync(user_id, access_token)` - Main discovery engine
- `get_database_schema(notion_client, database_id)` - Retrieve full schema from Notion API
- `classify_database_type(schema)` - Auto-classify based on title and properties
- `extract_property_value(prop_data, prop_type)` - Dynamic property extraction

**Related Endpoints:**
- `GET /api/notion/databases` - List user's discovered databases
- `POST /api/notion/databases/sync` - Manually trigger re-discovery
- All Notion tool methods now query this registry instead of searching live

**Discovery Triggers:**
1. **OAuth Connection:** Automatic discovery when user connects Notion workspace
2. **Manual Sync:** User can trigger via `/api/notion/databases/sync` endpoint
3. **Future:** Periodic background sync (daily cron job)

**Migration Strategy:**
```sql
-- Existing users: Run discovery on next Notion tool usage
-- New users: Automatic discovery during OAuth callback
-- Re-sync: Available via API endpoint or reconnecting workspace
```

**Benefits Over Hardcoded Approach:**
- ✅ **User A renames "Companies" → "Domains"** - Still works!
- ✅ **User B has "Clients" instead of "Companies"** - Auto-detected!
- ✅ **User C has custom properties** - Dynamically extracted!
- ✅ **1,000 users with different structures** - All work seamlessly!
- ✅ **No code changes needed** for new database types

**Known Limitations:**
- Schema updates require manual sync (no webhook support yet)
- Deleted databases remain in registry until next sync
- Unshared databases cannot be discovered (Notion API limitation)

---

### `ai.agno_sessions`
**Purpose:** AGNO session storage with user isolation

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `session_id` | VARCHAR | PRIMARY KEY | Session identifier (UUID) |
| `session_type` | VARCHAR | | Type of session |
| `team_id` | VARCHAR | | Team identifier (e.g., "cirkelline") |
| `user_id` | VARCHAR | **INDEXED** | **CRITICAL for user isolation** |
| `session_data` | JSON | | Session state |
| `runs` | JSON | | Conversation history |
| `metrics` | JSONB | DEFAULT '[]' | **NEW v1.2.33:** Token usage metrics (array of metric objects) |
| `created_at` | BIGINT | | Unix timestamp (seconds) |
| `updated_at` | BIGINT | | Unix timestamp (seconds) |

**Indexes:**
```sql
PRIMARY KEY: agno_sessions_pkey (session_id)
INDEX: idx_agno_sessions_user_id (user_id)  -- For user filtering
INDEX: idx_agno_sessions_team_id (team_id)
INDEX: idx_agno_sessions_metrics (metrics) USING GIN  -- NEW v1.2.33: For metrics queries
```

**Critical Notes:**
- Every session MUST have a `user_id` for proper isolation
- Frontend filters sessions by `user_id` when loading sidebar
- Session ID generation: UUID v4 when user clicks "New Chat"

**Metrics JSONB Structure (NEW v1.2.33):**
Each session can contain multiple metric objects tracking token usage per message:
```json
[
  {
    "timestamp": "2025-11-26T10:30:00.123456",
    "agent_id": "cirkelline",
    "agent_name": "Cirkelline",
    "agent_type": "team",
    "input_tokens": 1500,
    "output_tokens": 3200,
    "total_tokens": 4700,
    "model": "gemini-2.5-flash",
    "message_preview": "What is the capital of France?",
    "response_preview": "The capital of France is Paris, known for its iconic landmarks...",
    "input_cost": 0.0001125,
    "output_cost": 0.00096,
    "total_cost": 0.0010725
  }
]
```

**Metrics Pricing (Gemini 2.5 Flash Tier 1):**
- Input tokens: $0.075 per 1M tokens
- Output tokens: $0.30 per 1M tokens

**Sample Queries:**
```sql
-- Get user's sessions (for sidebar)
SELECT session_id, team_id, created_at, updated_at
FROM ai.agno_sessions
WHERE user_id = 'user-uuid'
ORDER BY created_at DESC;

-- Count user's sessions
SELECT COUNT(*) FROM ai.agno_sessions WHERE user_id = 'user-uuid';

-- Get specific session
SELECT * FROM ai.agno_sessions
WHERE session_id = 'session-uuid' AND user_id = 'user-uuid';

-- Delete session
DELETE FROM ai.agno_sessions
WHERE session_id = 'session-uuid' AND user_id = 'user-uuid';

-- ═══ METRICS QUERIES (NEW v1.2.33) ═══

-- Get all metrics for a session
SELECT
    session_id,
    jsonb_array_length(metrics) as metric_count,
    metrics
FROM ai.agno_sessions
WHERE session_id = 'session-uuid'
  AND metrics IS NOT NULL;

-- Calculate total tokens and cost for a session
SELECT
    session_id,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE session_id = 'session-uuid'
GROUP BY session_id;

-- Get metrics breakdown by agent for a session
SELECT
    metric->>'agent_name' as agent_name,
    COUNT(*) as message_count,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE session_id = 'session-uuid'
GROUP BY metric->>'agent_name'
ORDER BY total_tokens DESC;

-- Get all-time token usage for a user
SELECT
    user_id,
    COUNT(DISTINCT session_id) as session_count,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE user_id = 'user-uuid'
GROUP BY user_id;

-- Get top users by token usage (admin query)
SELECT
    s.user_id,
    u.email,
    u.display_name,
    COUNT(DISTINCT s.session_id) as session_count,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions s
CROSS JOIN LATERAL jsonb_array_elements(s.metrics) as metric
LEFT JOIN users u ON s.user_id::uuid = u.id
GROUP BY s.user_id, u.email, u.display_name
ORDER BY total_tokens DESC
LIMIT 20;

-- Get token usage timeline (daily aggregation)
SELECT
    DATE(to_timestamp(created_at)) as date,
    COUNT(DISTINCT session_id) as session_count,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE user_id = 'user-uuid'
GROUP BY DATE(to_timestamp(created_at))
ORDER BY date DESC;

-- Find sessions with high token usage (> 100K tokens)
SELECT
    session_id,
    user_id,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE metrics IS NOT NULL
GROUP BY session_id, user_id
HAVING SUM((metric->>'total_tokens')::int) > 100000
ORDER BY total_tokens DESC;

-- Get cost projections based on recent usage
WITH recent_usage AS (
    SELECT
        DATE(to_timestamp(created_at)) as date,
        SUM((metric->>'total_cost')::numeric) as daily_cost
    FROM ai.agno_sessions,
         jsonb_array_elements(metrics) as metric
    WHERE created_at >= EXTRACT(EPOCH FROM NOW() - INTERVAL '30 days')
    GROUP BY DATE(to_timestamp(created_at))
)
SELECT
    AVG(daily_cost) as avg_daily_cost,
    AVG(daily_cost) * 7 as weekly_projection,
    AVG(daily_cost) * 30 as monthly_projection,
    AVG(daily_cost) * 365 as yearly_projection
FROM recent_usage;
```

---

### `ai.agno_memories`
**Purpose:** User-specific memories for agents

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `memory_id` | VARCHAR | PRIMARY KEY | Unique memory identifier |
| `memory` | JSON | NOT NULL | Memory content (JSON format) |
| `input` | VARCHAR | | Input that generated this memory |
| `agent_id` | VARCHAR | | Agent identifier |
| `team_id` | VARCHAR | | Team identifier |
| `user_id` | VARCHAR | **INDEXED** | User identifier |
| `topics` | JSON | | Memory topics/tags |
| `updated_at` | BIGINT | | Unix timestamp (seconds) |

**Indexes:**
```sql
PRIMARY KEY: agno_memories_pkey (memory_id)
INDEX: idx_agno_memories_user_id (user_id)
INDEX: idx_agno_memories_updated_at (updated_at)
```

**Critical Notes:**
- ⚠️ **Table uses `updated_at` NOT `created_at`!** This is different from `ai.agno_sessions` which has both.
- This naming difference caused user management endpoint failures on 2025-10-24
- **Always use `updated_at`** when querying memory timestamps
- **Memory format is JSON**, not plain text
- Timestamps are stored as BIGINT (Unix seconds), not TIMESTAMP

**Sample Queries:**
```sql
-- Get user's recent memories (CORRECT - uses updated_at)
SELECT memory, updated_at
FROM ai.agno_memories
WHERE user_id = 'user-uuid'
ORDER BY updated_at DESC
LIMIT 10;

-- WRONG: This will fail!
SELECT memory, created_at  -- ❌ Column does not exist
FROM ai.agno_memories
WHERE user_id = 'user-uuid';

-- Clear user's memories
DELETE FROM ai.agno_memories WHERE user_id = 'user-uuid';

-- Count memories per user
SELECT user_id, COUNT(*) as memory_count
FROM ai.agno_memories
GROUP BY user_id
ORDER BY memory_count DESC;
```

---

### `ai.agno_knowledge`
**Purpose:** Knowledge base document metadata

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | VARCHAR | PRIMARY KEY | Document identifier (UUID) |
| `name` | VARCHAR | NOT NULL | Filename |
| `description` | TEXT | | Document description |
| `metadata` | JSONB | | **Contains user_id, access_level, etc.** |
| `type` | VARCHAR | | Document type |
| `size` | INTEGER | | File size in bytes |
| `status` | VARCHAR | | Processing status |
| `created_at` | BIGINT | | Unix timestamp |
| `updated_at` | BIGINT | | Unix timestamp |

**Indexes:**
```sql
PRIMARY KEY: agno_knowledge_pkey (id)
INDEX: idx_agno_knowledge_metadata (metadata) USING GIN  -- For JSON queries
```

**Metadata Structure (CRITICAL):**
```json
{
  "user_id": "cc74dcd6-ce96-4cfb-8295-b619ed0e0d0e",
  "user_type": "admin",
  "access_level": "private",
  "uploaded_by": "user-id",
  "uploaded_at": "2025-10-09T17:30:00Z",
  "uploaded_via": "frontend_chat"
}
```

**Sample Queries:**
```sql
-- Get user's private documents
SELECT id, name, description, metadata, created_at
FROM ai.agno_knowledge
WHERE metadata->>'user_id' = 'user-uuid'
  AND metadata->>'access_level' = 'private'
ORDER BY created_at DESC;

-- Count user's documents
SELECT COUNT(*) FROM ai.agno_knowledge
WHERE metadata->>'user_id' = 'user-uuid';

-- Search by filename
SELECT * FROM ai.agno_knowledge
WHERE name ILIKE '%search-term%'
  AND metadata->>'user_id' = 'user-uuid';
```

---

### `ai.cirkelline_knowledge_vectors`
**Purpose:** Vector embeddings for semantic search

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `content_id` | INTEGER | FK → agno_knowledge(id) | References knowledge document |
| `embedding` | VECTOR(768) | | Gemini embedding (768 dimensions) |
| `content` | TEXT | | Chunked text content |
| `metadata` | JSONB | | Includes user_id for filtering |

**Indexes:**
```sql
PRIMARY KEY: cirkelline_knowledge_vectors_pkey (id)
INDEX: cirkelline_knowledge_vectors_embedding_idx (embedding) USING HNSW
  -- HNSW index for fast approximate nearest neighbor search
```

**Critical Notes:**
- Embedding dimension: **768** (Gemini text-embedding-004)
- Vector search uses HNSW (Hierarchical Navigable Small World) algorithm
- Hybrid search: combines vector similarity + BM25 keyword search

**Sample Queries:**
```sql
-- Check vector index
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'cirkelline_knowledge_vectors';

-- Count vectors
SELECT COUNT(*) FROM ai.cirkelline_knowledge_vectors;

-- Get vectors for specific document
SELECT id, content, metadata
FROM ai.cirkelline_knowledge_vectors
WHERE content_id = 123;
```

---

### `ai.user_journals` (v1.3.2)
**Purpose:** Daily journal entries summarizing user interactions

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `user_id` | VARCHAR | NOT NULL, INDEXED | User identifier |
| `journal_date` | DATE | NOT NULL, INDEXED | Date of the journal entry |
| `summary` | TEXT | NOT NULL | Narrative prose content |
| `topics` | JSONB | | Array of topic keywords (3-7) |
| `outcomes` | JSONB | | Array of key achievements |
| `sessions_processed` | JSONB | | Array of session IDs included |
| `message_count` | INTEGER | | Total messages summarized |
| `created_at` | BIGINT | NOT NULL | Unix timestamp |

**Indexes:**
```sql
PRIMARY KEY: user_journals_pkey (id)
INDEX: idx_user_journals_user_id (user_id)
INDEX: idx_user_journals_date (journal_date)
INDEX: idx_user_journals_topics (topics) USING GIN
UNIQUE: user_journals_user_id_journal_date_key (user_id, journal_date)
```

**Sample Queries:**
```sql
-- Get user's journals
SELECT * FROM ai.user_journals
WHERE user_id = 'user-uuid'
ORDER BY journal_date DESC
LIMIT 10;

-- Get journal count for day number calculation
SELECT COUNT(*) FROM ai.user_journals
WHERE user_id = 'user-uuid'
  AND journal_date < '2025-12-10';

-- Search by topic
SELECT * FROM ai.user_journals
WHERE user_id = 'user-uuid'
  AND topics ? 'deployment';
```

---

### `ai.journal_queue` (v1.3.2)
**Purpose:** Queue for journal processing jobs

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | SERIAL | PRIMARY KEY | Auto-incrementing ID |
| `user_id` | VARCHAR | NOT NULL | User identifier |
| `target_date` | DATE | NOT NULL | Date to generate journal for |
| `status` | VARCHAR | DEFAULT 'pending' | pending/processing/completed/failed |
| `priority` | INTEGER | DEFAULT 0 | Higher = processed first |
| `error_message` | TEXT | | Error details if failed |
| `created_at` | TIMESTAMP | DEFAULT NOW() | When job was queued |
| `processed_at` | TIMESTAMP | | When job completed |

**Indexes:**
```sql
PRIMARY KEY: journal_queue_pkey (id)
INDEX: idx_journal_queue_status (status)
INDEX: idx_journal_queue_priority (priority DESC, created_at)
UNIQUE: journal_queue_user_id_target_date_key (user_id, target_date)
```

**Sample Queries:**
```sql
-- Get queue stats
SELECT status, COUNT(*) FROM ai.journal_queue GROUP BY status;

-- Get next job to process
SELECT * FROM ai.journal_queue
WHERE status = 'pending'
ORDER BY priority DESC, created_at ASC
LIMIT 1;

-- Mark job as processing
UPDATE ai.journal_queue
SET status = 'processing'
WHERE id = 123;
```

---

### `public.task_lists` (v1.3.7)
**Purpose:** User task lists for standalone tasks app

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | List identifier |
| `user_id` | UUID | NOT NULL, FK → users(id) ON DELETE CASCADE | Owner |
| `name` | VARCHAR(255) | NOT NULL | List name |
| `color` | VARCHAR(7) | DEFAULT '#8E0B83' | Hex color code |
| `is_default` | BOOLEAN | DEFAULT false | Default list for new tasks |
| `source` | VARCHAR(50) | DEFAULT 'local' | 'local' or 'google' |
| `external_id` | VARCHAR(255) | | Google Tasks list ID |
| `sync_enabled` | BOOLEAN | DEFAULT false | Google sync enabled |
| `last_synced_at` | TIMESTAMP | | Last Google sync |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last modification |

**Indexes:**
```sql
PRIMARY KEY: task_lists_pkey (id)
INDEX: idx_task_lists_user (user_id)
```

**Sample Queries:**
```sql
-- Get user's task lists
SELECT * FROM task_lists
WHERE user_id = 'user-uuid'
ORDER BY is_default DESC, created_at;

-- Get default list
SELECT * FROM task_lists
WHERE user_id = 'user-uuid' AND is_default = true
LIMIT 1;

-- Create list
INSERT INTO task_lists (user_id, name, color)
VALUES ('user-uuid', 'Work Tasks', '#4A90D9');
```

---

### `public.tasks` (v1.3.7)
**Purpose:** Tasks with priority levels, due dates, and notes

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Task identifier |
| `list_id` | UUID | NOT NULL, FK → task_lists(id) ON DELETE CASCADE | Parent list |
| `user_id` | UUID | NOT NULL, FK → users(id) ON DELETE CASCADE | Owner |
| `title` | VARCHAR(500) | NOT NULL | Task title |
| `notes` | TEXT | | Task description/notes |
| `due_date` | TIMESTAMP WITH TIME ZONE | | Due date |
| `completed` | BOOLEAN | DEFAULT false | Completion status |
| `completed_at` | TIMESTAMP WITH TIME ZONE | | When completed |
| `priority` | VARCHAR(20) | DEFAULT 'medium' | 'low', 'medium', 'high', 'urgent' |
| `position` | INTEGER | DEFAULT 0 | Sort order within list |
| `parent_id` | UUID | FK → tasks(id) ON DELETE CASCADE | For subtasks (future) |
| `external_id` | VARCHAR(255) | | Google Tasks ID |
| `source` | VARCHAR(50) | DEFAULT 'local' | 'local' or 'google' |
| `sync_status` | VARCHAR(50) | DEFAULT 'local' | 'local', 'synced', 'pending' |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Creation time |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last modification |

**Indexes:**
```sql
PRIMARY KEY: tasks_pkey (id)
INDEX: idx_tasks_user (user_id)
INDEX: idx_tasks_list (list_id)
INDEX: idx_tasks_due (due_date)
```

**Sample Queries:**
```sql
-- Get tasks in list (active first, then completed)
SELECT * FROM tasks
WHERE list_id = 'list-uuid'
ORDER BY completed, position;

-- Get user's overdue tasks
SELECT t.*, tl.name as list_name
FROM tasks t
JOIN task_lists tl ON t.list_id = tl.id
WHERE t.user_id = 'user-uuid'
  AND t.completed = false
  AND t.due_date < NOW()
ORDER BY t.due_date;

-- Toggle task completion
UPDATE tasks
SET completed = NOT completed,
    completed_at = CASE WHEN NOT completed THEN NOW() ELSE NULL END,
    updated_at = NOW()
WHERE id = 'task-uuid';

-- Get tasks by priority
SELECT priority, COUNT(*) as count
FROM tasks
WHERE user_id = 'user-uuid' AND completed = false
GROUP BY priority;
```

---

## Metadata Structures

### Private Document Metadata
Used in `agno_knowledge.metadata` and `cirkelline_knowledge_vectors.metadata`

```json
{
  "user_id": "uuid",
  "user_type": "admin" | "regular",
  "access_level": "private" | "public",
  "uploaded_by": "uuid",
  "uploaded_at": "ISO-8601-timestamp",
  "uploaded_via": "frontend_chat" | "os_agno_com"
}
```

**Knowledge Filtering:**
```python
# Backend applies this filter automatically
knowledge_filters = {"user_id": current_user_id}

# Only returns documents where metadata->>'user_id' = current_user_id
```

---

## Common Queries

### User Authentication
```sql
-- Verify login
SELECT id, email, hashed_password, display_name
FROM users
WHERE email = $1;

-- Check if admin
SELECT ap.name, ap.role, ap.personal_context
FROM users u
LEFT JOIN admin_profiles ap ON u.id = ap.user_id
WHERE u.id = $1;
```

### Session Management
```sql
-- Load user's recent sessions
SELECT session_id, team_id, created_at
FROM ai.agno_sessions
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 20;

-- Check if session belongs to user
SELECT EXISTS (
    SELECT 1 FROM ai.agno_sessions
    WHERE session_id = $1 AND user_id = $2
) AS has_access;
```

### Knowledge Base
```sql
-- User's document count
SELECT COUNT(*) FROM ai.agno_knowledge
WHERE metadata->>'user_id' = $1;

-- Search user's documents
SELECT id, name, description
FROM ai.agno_knowledge
WHERE metadata->>'user_id' = $1
  AND name ILIKE '%' || $2 || '%';
```

### Token Usage Metrics (NEW v1.2.33)
```sql
-- Get user's total token usage and cost
SELECT
    user_id,
    COUNT(DISTINCT session_id) as session_count,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'input_tokens')::int) as input_tokens,
    SUM((metric->>'output_tokens')::int) as output_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE user_id = $1
GROUP BY user_id;

-- Get token usage breakdown by agent
SELECT
    metric->>'agent_name' as agent_name,
    metric->>'agent_type' as agent_type,
    COUNT(*) as message_count,
    SUM((metric->>'total_tokens')::int) as total_tokens,
    SUM((metric->>'total_cost')::numeric) as total_cost,
    AVG((metric->>'total_tokens')::int) as avg_tokens_per_message
FROM ai.agno_sessions,
     jsonb_array_elements(metrics) as metric
WHERE user_id = $1
GROUP BY metric->>'agent_name', metric->>'agent_type'
ORDER BY total_tokens DESC;

-- Calculate monthly cost projection (admin)
WITH recent_usage AS (
    SELECT
        DATE(to_timestamp(created_at)) as date,
        SUM((metric->>'total_cost')::numeric) as daily_cost
    FROM ai.agno_sessions,
         jsonb_array_elements(metrics) as metric
    WHERE created_at >= EXTRACT(EPOCH FROM NOW() - INTERVAL '30 days')
    GROUP BY DATE(to_timestamp(created_at))
)
SELECT
    AVG(daily_cost) as avg_daily_cost,
    AVG(daily_cost) * 30 as monthly_projection,
    AVG(daily_cost) * 365 as yearly_projection
FROM recent_usage;
```

---

## Database Migrations

### Initial Setup (Localhost)
```bash
# Start PostgreSQL with pgvector
docker run -d \
    --name cirkelline-postgres \
    -e POSTGRES_USER=cirkelline \
    -e POSTGRES_PASSWORD=cirkelline123 \
    -e POSTGRES_DB=cirkelline \
    -p 5532:5432 \
    pgvector/pgvector:pg17

# Enable vector extension
docker exec cirkelline-postgres \
    psql -U cirkelline -d cirkelline \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
docker exec cirkelline-postgres \
    psql -U cirkelline -d cirkelline \
    -c "\dx vector"
```

### AWS RDS Setup
```bash
# Enable vector extension
PGPASSWORD=<password> psql \
    -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com \
    -p 5432 \
    -U postgres \
    -d cirkelline_system \
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create schemas if needed
CREATE SCHEMA IF NOT EXISTS ai;
```

### Schema Changes

**2025-11-26: Add metrics column (v1.2.33)**
```sql
-- Add metrics column to track token usage per message
ALTER TABLE ai.agno_sessions
ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '[]'::jsonb;

-- Create GIN index for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_agno_sessions_metrics
ON ai.agno_sessions USING GIN (metrics);

-- Add column comment
COMMENT ON COLUMN ai.agno_sessions.metrics IS
'Array of metric objects tracking token usage per message. Each object contains:
timestamp, agent_id, agent_name, agent_type, input_tokens, output_tokens,
total_tokens, model, message_preview, response_preview, input_cost, output_cost, total_cost';

-- Verify
\d ai.agno_sessions
-- Should show: metrics | jsonb | | '[]'::jsonb

-- Test query
SELECT session_id, jsonb_array_length(metrics) as metric_count
FROM ai.agno_sessions
WHERE metrics IS NOT NULL AND jsonb_array_length(metrics) > 0
LIMIT 5;
```

**2025-10-22: Add preferences column**
```sql
-- Add preferences column to store user preferences
ALTER TABLE users ADD COLUMN preferences JSONB DEFAULT '{}'::jsonb;

-- Verify
\d users
-- Should show: preferences | jsonb | | '{}'::jsonb
```

**2025-10-12: Fix column name**
```sql
-- Production fix - AWS database had wrong column name
ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;

-- Verify
\d users
```

---

## Backup & Restore

### Backup Database
```bash
# Localhost
docker exec cirkelline-postgres pg_dump -U cirkelline cirkelline > backup.sql

# AWS RDS
PGPASSWORD=<password> pg_dump \
    -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com \
    -U postgres \
    -d cirkelline_system \
    > backup.sql
```

### Restore Database
```bash
# Localhost
cat backup.sql | docker exec -i cirkelline-postgres \
    psql -U cirkelline -d cirkelline

# AWS RDS
PGPASSWORD=<password> psql \
    -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com \
    -U postgres \
    -d cirkelline_system \
    < backup.sql
```

---

## Troubleshooting

### Connection Refused
```bash
# Check Docker container running
docker ps | grep cirkelline-postgres

# Start if stopped
docker start cirkelline-postgres

# Check logs
docker logs cirkelline-postgres
```

### Column Not Found Error
```
ERROR: column "hashed_password" does not exist
```
**Solution:** Database has wrong column name. Run:
```sql
ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;
```

### pgvector Extension Missing
```
ERROR: type "vector" does not exist
```
**Solution:** Enable extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Quick Reference Card

```bash
# Connection strings
LOCALHOST: postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
AWS:       postgresql://postgres:<pass>@cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com:5432/cirkelline_system

# Critical column names
users.hashed_password  (NOT password_hash!)
agno_sessions.user_id  (REQUIRED for isolation)
agno_knowledge.metadata->>'user_id'  (For filtering)

# Extension name
CREATE EXTENSION vector;  (NOT pgvector!)

# Vector dimensions
768  (Gemini text-embedding-004)
```
