-- ============================================================================
-- Cirkelline Memory Migration SQL Script
-- ============================================================================
--
-- This script migrates sessions and memories from old DB to new DB
--
-- ⚠️  DO NOT RUN THIS WITHOUT REVIEWING FIRST!
-- ⚠️  This is a BACKUP approach - prefer organic memory creation
--
-- ============================================================================

-- Step 1: Connect to OLD database and export sessions
-- Run this on OLD database first:

\echo 'Exporting sessions for Ivo and Rasmus...'

COPY (
    SELECT
        session_id,
        user_id,
        team_id,
        session_data,
        runs,
        created_at,
        updated_at
    FROM ai.agno_sessions
    WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com')
    ORDER BY created_at
) TO '/tmp/sessions_export.csv' WITH CSV HEADER;

-- Step 2: Export memories
\echo 'Exporting memories...'

COPY (
    SELECT
        memory_id,
        memory,
        input,
        user_id,
        agent_id,
        team_id,
        topics,
        updated_at
    FROM ai.agno_memories
    WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com')
    ORDER BY updated_at
) TO '/tmp/memories_export.csv' WITH CSV HEADER;

-- Step 3: Export agent memories (if table exists)
\echo 'Exporting agent memories...'

COPY (
    SELECT *
    FROM ai.agent_memory
    WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com')
    ORDER BY created_at
) TO '/tmp/agent_memories_export.csv' WITH CSV HEADER;

-- ============================================================================
-- Step 4: Import to NEW database
-- Run these on NEW database after reviewing exports:
-- ============================================================================

-- Import sessions
\echo 'Importing sessions to new database...'

COPY ai.agno_sessions (
    session_id,
    user_id,
    team_id,
    session_data,
    runs,
    created_at,
    updated_at
)
FROM '/tmp/sessions_export.csv'
WITH CSV HEADER
ON CONFLICT (session_id) DO NOTHING;

-- Import memories
\echo 'Importing memories to new database...'

COPY ai.agno_memories (
    memory_id,
    memory,
    input,
    user_id,
    agent_id,
    team_id,
    topics,
    updated_at
)
FROM '/tmp/memories_export.csv'
WITH CSV HEADER
ON CONFLICT (memory_id) DO NOTHING;

-- Import agent memories
\echo 'Importing agent memories to new database...'

COPY ai.agent_memory
FROM '/tmp/agent_memories_export.csv'
WITH CSV HEADER
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- Verification
-- ============================================================================

\echo 'Verifying migration...'

SELECT 'Sessions imported:' as status, COUNT(*) as count
FROM ai.agno_sessions
WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com');

SELECT 'Memories imported:' as status, COUNT(*) as count
FROM ai.agno_memories
WHERE user_id IN ('opnureyes2@gmail.com', 'opnureyes2@gmail.com');

\echo 'Migration complete!'
