# Database Schema - cirkelline-kv1ntos

**Database:** cirkelline (PostgreSQL 17)
**Port:** 5532 (Docker local), RDS (AWS production)
**Connection:** `postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline`
**Extensions:** pgvector (768-dimensional embeddings)

---

## Overview

The cirkelline-kv1ntos database uses PostgreSQL 17 with pgvector for vector similarity search. Data is organized in two schemas: `public` (users/auth) and `ai` (sessions/knowledge).

### Key Principles
- User isolation via `user_id` filtering on all queries
- HNSW indexes for vector search performance
- JSONB for flexible metadata storage
- Soft deletes via `archived_at` timestamps

---

## Schema: public

### Table: users

**Purpose:** User authentication and profiles

```sql
CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_is_active ON public.users(is_active);
```

**Columns:**
- `id` - Primary key
- `email` - Unique email (login identifier)
- `hashed_password` - bcrypt-hashed password (⚠️ NOT `password_hash`)
- `is_active` - Account status
- `created_at` - Registration timestamp
- `last_login` - Most recent login
- `updated_at` - Last profile update

### Table: admin_profiles

**Purpose:** Extended admin user metadata

```sql
CREATE TABLE public.admin_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES public.users(id),
    name VARCHAR(255),
    role VARCHAR(100),
    context TEXT,
    preferences JSONB,
    custom_instructions TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_admin_profiles_user_id ON public.admin_profiles(user_id);
```

**Columns:**
- `user_id` - Reference to users table
- `name` - Display name
- `role` - Job title/role
- `context` - Personal context for AI agents
- `preferences` - JSONB with communication style, etc.
- `custom_instructions` - How agents should respond
- `created_at`, `updated_at` - Timestamps

---

## Schema: ai

### Table: agno_sessions

**Purpose:** Chat sessions and conversation history

```sql
CREATE TABLE ai.agno_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_archived BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_agno_sessions_user_id ON ai.agno_sessions(user_id);
CREATE INDEX idx_agno_sessions_session_id ON ai.agno_sessions(session_id);
CREATE INDEX idx_agno_sessions_created_at ON ai.agno_sessions(created_at);
```

**Columns:**
- `session_id` - UUID identifying the conversation
- `user_id` - User who owns this session
- `name` - Session title (auto-generated from first message)
- `created_at` - Session start time
- `updated_at` - Last message time
- `is_archived` - Soft delete flag

**Usage:**
```python
# Load sessions for current user
SELECT * FROM ai.agno_sessions
WHERE user_id = 'user-123'
AND is_archived = FALSE
ORDER BY created_at DESC;

# Create new session
INSERT INTO ai.agno_sessions (session_id, user_id, created_at)
VALUES (uuid_generate_v4(), 'user-123', NOW());
```

### Table: agno_memories

**Purpose:** User memories and context

```sql
CREATE TABLE ai.agno_memories (
    id SERIAL PRIMARY KEY,
    memory_id UUID UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    memory TEXT NOT NULL,
    topics JSONB,
    input VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    accessed_at TIMESTAMP
);

CREATE INDEX idx_agno_memories_user_id ON ai.agno_memories(user_id);
CREATE INDEX idx_agno_memories_created_at ON ai.agno_memories(created_at);
```

**Columns:**
- `memory_id` - UUID for memory
- `user_id` - User who owns this memory
- `memory` - Actual memory text
- `topics` - JSONB with extracted topics
- `input` - Original user input
- `created_at`, `updated_at`, `accessed_at` - Timestamps

**Storage Pattern:**
```json
{
  "memory": "User prefers JSON format in responses",
  "topics": ["communication_style", "preferences"],
  "input": "I like well-structured JSON responses"
}
```

### Table: agno_memories_archive

**Purpose:** Archived memories from optimization runs

```sql
CREATE TABLE ai.agno_memories_archive (
    id SERIAL PRIMARY KEY,
    original_memory_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    memory JSONB NOT NULL,
    topics JSONB,
    input VARCHAR,
    created_at TIMESTAMP,
    archived_at TIMESTAMP DEFAULT NOW(),
    optimization_run_id VARCHAR
);

CREATE INDEX idx_archive_user_id ON ai.agno_memories_archive(user_id);
CREATE INDEX idx_archive_run_id ON ai.agno_memories_archive(optimization_run_id);
```

**Columns:**
- Same as agno_memories, plus:
- `archived_at` - When memory was archived
- `optimization_run_id` - Which optimization run archived it

### Table: agno_knowledge

**Purpose:** Document metadata

```sql
CREATE TABLE ai.agno_knowledge (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    content_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agno_knowledge_name ON ai.agno_knowledge(name);
```

**Columns:**
- `name` - Document name/title
- `file_name` - Original filename
- `file_path` - Storage location
- `content_type` - MIME type (application/pdf, etc.)
- `metadata` - JSONB with user_id, tags, etc.

**Metadata Structure:**
```json
{
  "user_id": "user-123",
  "original_name": "report.pdf",
  "upload_date": "2025-01-01",
  "document_type": "pdf",
  "tags": ["research", "2025"],
  "chunk_count": 25
}
```

### Table: cirkelline_knowledge_vectors

**Purpose:** Vector embeddings for semantic search (pgvector extension)

```sql
CREATE TABLE ai.cirkelline_knowledge_vectors (
    id BIGSERIAL PRIMARY KEY,
    embedding VECTOR(768) NOT NULL,
    chunk_text TEXT NOT NULL,
    document_id INTEGER REFERENCES ai.agno_knowledge(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_vectors_document ON ai.cirkelline_knowledge_vectors(document_id);
CREATE INDEX idx_vectors_embedding ON ai.cirkelline_knowledge_vectors
    USING HNSW (embedding vector_cosine_ops)
    WITH (m=16, ef_construction=200);
```

**Columns:**
- `embedding` - 768-dimensional vector from Gemini
- `chunk_text` - Text chunk for this embedding
- `document_id` - Reference to agno_knowledge
- `metadata` - JSONB with chunk index, relevance, etc.
- `created_at`, `updated_at` - Timestamps

**Metadata Structure:**
```json
{
  "user_id": "user-123",
  "chunk_index": 0,
  "chunk_total": 25,
  "page_number": 1,
  "similarity_to_query": 0.87
}
```

**Usage:**
```sql
-- Semantic search (Cosine similarity)
SELECT chunk_text, 1 - (embedding <=> query_embedding) as similarity
FROM ai.cirkelline_knowledge_vectors
WHERE metadata->>'user_id' = 'user-123'
ORDER BY embedding <=> query_embedding
LIMIT 5;

-- With BM25 keyword search (hybrid)
SELECT * FROM ai.cirkelline_knowledge_vectors
WHERE metadata->>'user_id' = 'user-123'
ORDER BY
  (1 - (embedding <=> query_embedding)) * 0.7 +
  bm25_score * 0.3
LIMIT 5;
```

### Table: workflow_runs

**Purpose:** Track KV1NTOS workflow execution (v1.3.0+)

```sql
CREATE TABLE ai.workflow_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR UNIQUE NOT NULL,
    workflow_name VARCHAR NOT NULL,
    user_id VARCHAR,
    status VARCHAR NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    current_step VARCHAR,
    steps_completed JSONB DEFAULT '[]',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    metrics JSONB
);

CREATE INDEX idx_workflow_runs_status ON ai.workflow_runs(status);
CREATE INDEX idx_workflow_runs_user ON ai.workflow_runs(user_id);
```

**Columns:**
- `run_id` - Unique workflow execution ID
- `workflow_name` - Which workflow (e.g., "memory_optimization")
- `user_id` - User who triggered workflow
- `status` - PENDING, RUNNING, COMPLETED, FAILED
- `started_at`, `completed_at` - Timestamps
- `current_step` - Which step currently executing
- `steps_completed` - JSONB array of completed steps
- `input_data`, `output_data` - JSONB payloads
- `error_message` - If failed, why
- `metrics` - Performance data

---

## Key Patterns

### User Isolation
Every query filters by user_id:
```sql
-- Example: Get sessions for user
SELECT * FROM ai.agno_sessions
WHERE user_id = 'current-user-id';

-- Example: Search knowledge
SELECT * FROM ai.cirkelline_knowledge_vectors
WHERE metadata->>'user_id' = 'current-user-id'
ORDER BY embedding <=> query_vector;
```

### JSONB Querying
```sql
-- Extract from metadata
SELECT * FROM ai.agno_knowledge
WHERE metadata->>'user_id' = 'user-123'
AND metadata->>'document_type' = 'pdf';

-- Update metadata
UPDATE ai.agno_knowledge
SET metadata = jsonb_set(metadata, '{tags}', '"new-tag"')
WHERE id = 123;
```

### Vector Search
```sql
-- Cosine similarity (default)
SELECT * FROM ai.cirkelline_knowledge_vectors
ORDER BY embedding <=> query_vector
LIMIT 5;

-- With threshold
SELECT * FROM ai.cirkelline_knowledge_vectors
WHERE 1 - (embedding <=> query_vector) > 0.7;
```

---

## Performance Indexes

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| `idx_users_email` | users | email | Fast login lookup |
| `idx_agno_sessions_user_id` | agno_sessions | user_id | Session filtering |
| `idx_agno_memories_user_id` | agno_memories | user_id | Memory retrieval |
| `idx_vectors_embedding` | cirkelline_knowledge_vectors | embedding (HNSW) | Vector search |
| `idx_archive_user_id` | agno_memories_archive | user_id | Archive queries |
| `idx_workflow_runs_status` | workflow_runs | status | Workflow filtering |

---

## Migration Notes

- Database migrations run automatically on startup (my_os.py)
- New tables created if they don't exist
- No data loss on migration (CREATE TABLE IF NOT EXISTS)
- Archive table created for memory optimization

---

## Common Queries

### Load User Sessions
```python
from cirkelline.database import db

sessions = db.query("""
    SELECT * FROM ai.agno_sessions
    WHERE user_id = %s AND is_archived = FALSE
    ORDER BY created_at DESC
""", user_id)
```

### Search Knowledge
```python
# Semantic search with user filter
results = db.query("""
    SELECT chunk_text, similarity FROM ai.cirkelline_knowledge_vectors
    WHERE metadata->>'user_id' = %s
    ORDER BY embedding <=> %s
    LIMIT 5
""", user_id, query_embedding)
```

### Archive Old Memories
```python
db.execute("""
    INSERT INTO ai.agno_memories_archive
    SELECT *, NOW() FROM ai.agno_memories
    WHERE user_id = %s AND created_at < NOW() - INTERVAL '30 days'
""", user_id)
```

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial DATABASE_SCHEMA.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
