-- CKC Brain Database Schema
-- Version: 1.0.0 | Date: 2025-12-10
--
-- Dette er CKC's primære database schema.
-- Indeholder tabeller for:
--   - Task Context Persistence
--   - Workflow Steps
--   - Agent Memory (episodic, semantic, procedural)
--   - Learning Events
--   - ILCP Messages
--   - Knowledge Entries
--   - Audit Trail

-- ==========================================================
-- Schema Setup
-- ==========================================================
CREATE SCHEMA IF NOT EXISTS ckc;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ==========================================================
-- Task Context Persistence
-- Holder styr på alle aktive og afsluttede task contexts
-- ==========================================================
CREATE TABLE ckc.task_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(50) UNIQUE NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    original_prompt TEXT,
    current_agent VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    -- Metadata og flags som JSONB for fleksibilitet
    metadata JSONB DEFAULT '{}',
    flags JSONB DEFAULT '{}',
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger for auto-update af updated_at
CREATE OR REPLACE FUNCTION ckc.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_contexts_update_timestamp
    BEFORE UPDATE ON ckc.task_contexts
    FOR EACH ROW EXECUTE FUNCTION ckc.update_timestamp();

-- ==========================================================
-- Workflow Steps
-- Tracker individuelle steps i en work-loop
-- ==========================================================
CREATE TABLE ckc.workflow_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(50) REFERENCES ckc.task_contexts(context_id) ON DELETE CASCADE,
    step_id VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    action VARCHAR(200),
    status VARCHAR(50) DEFAULT 'pending',
    -- Input/output data
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
            THEN EXTRACT(MILLISECONDS FROM (completed_at - started_at))::INTEGER
            ELSE NULL
        END
    ) STORED,
    -- Error tracking
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================================
-- Agent Memory
-- Tre typer hukommelse: episodic, semantic, procedural
-- ==========================================================
CREATE TABLE ckc.agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) NOT NULL,
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('episodic', 'semantic', 'procedural')),
    -- Content som JSONB for fleksibel struktur
    content JSONB NOT NULL,
    -- Memory metadata
    importance FLOAT DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    -- Embedding for semantic search (kan tilføjes senere med pgvector)
    -- embedding VECTOR(768),
    -- Tags for kategorisering
    tags TEXT[] DEFAULT '{}',
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ
);

-- ==========================================================
-- Learning Events
-- Logger alle læringshændelser fra Learning Rooms
-- ==========================================================
CREATE TABLE ckc.learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id INTEGER NOT NULL,
    room_name VARCHAR(200),
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100),
    -- Event content
    content JSONB NOT NULL,
    -- Integrity check
    integrity_hash VARCHAR(64),
    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================================
-- ILCP Messages
-- Inter-Læringsrum Kommunikation Protokol messages
-- ==========================================================
CREATE TABLE ckc.ilcp_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(100) UNIQUE NOT NULL,
    -- Routing
    sender_room_id INTEGER NOT NULL,
    recipient_room_id INTEGER NOT NULL,
    -- Message details
    message_type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    content JSONB NOT NULL,
    -- Task context reference
    task_context_id VARCHAR(50) REFERENCES ckc.task_contexts(context_id) ON DELETE SET NULL,
    task_context_data JSONB,
    -- Validation
    validation_mode VARCHAR(20) DEFAULT 'normal' CHECK (validation_mode IN ('strict', 'normal', 'lenient', 'disabled')),
    is_validated BOOLEAN DEFAULT FALSE,
    validation_errors TEXT[],
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'acknowledged', 'failed', 'expired')),
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

-- ==========================================================
-- Knowledge Entries
-- Vidensposter fra Bibliotekar
-- ==========================================================
CREATE TABLE ckc.knowledge_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id VARCHAR(100) UNIQUE NOT NULL,
    -- Content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    -- Kategorisering
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    tags TEXT[] DEFAULT '{}',
    -- Referencer
    source_refs TEXT[] DEFAULT '{}',
    related_entries VARCHAR(100)[] DEFAULT '{}',
    -- Source tracking
    source_type VARCHAR(50),  -- 'notion', 'document', 'manual', 'generated'
    source_id VARCHAR(200),
    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Versioning
    version INTEGER DEFAULT 1,
    previous_version_id UUID REFERENCES ckc.knowledge_entries(id),
    -- Access tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    -- Ownership
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ
);

CREATE TRIGGER knowledge_entries_update_timestamp
    BEFORE UPDATE ON ckc.knowledge_entries
    FOR EACH ROW EXECUTE FUNCTION ckc.update_timestamp();

-- ==========================================================
-- Audit Trail
-- Komplet audit log for alle ændringer
-- ==========================================================
CREATE TABLE ckc.audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Entity reference
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    -- Action details
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(100),
    actor_type VARCHAR(50),  -- 'user', 'agent', 'system'
    -- Value tracking
    old_value JSONB,
    new_value JSONB,
    -- Change summary
    changed_fields TEXT[],
    -- Metadata
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================================
-- Work Loop Sequences
-- Holder styr på hele work-loop sekvenser
-- ==========================================================
CREATE TABLE ckc.work_loop_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id VARCHAR(100) UNIQUE NOT NULL,
    context_id VARCHAR(50) REFERENCES ckc.task_contexts(context_id) ON DELETE CASCADE,
    -- Sequence details
    name VARCHAR(200),
    description TEXT,
    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    -- Execution mode
    execution_mode VARCHAR(50) DEFAULT 'sequential',  -- 'sequential', 'parallel', 'conditional'
    -- Results
    result JSONB,
    error TEXT,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER work_loop_sequences_update_timestamp
    BEFORE UPDATE ON ckc.work_loop_sequences
    FOR EACH ROW EXECUTE FUNCTION ckc.update_timestamp();

-- ==========================================================
-- Indexes for Performance
-- ==========================================================

-- Task Contexts
CREATE INDEX idx_task_contexts_task_id ON ckc.task_contexts(task_id);
CREATE INDEX idx_task_contexts_user_id ON ckc.task_contexts(user_id);
CREATE INDEX idx_task_contexts_session_id ON ckc.task_contexts(session_id);
CREATE INDEX idx_task_contexts_status ON ckc.task_contexts(status);
CREATE INDEX idx_task_contexts_created_at ON ckc.task_contexts(created_at DESC);

-- Workflow Steps
CREATE INDEX idx_workflow_steps_context ON ckc.workflow_steps(context_id);
CREATE INDEX idx_workflow_steps_agent ON ckc.workflow_steps(agent_id);
CREATE INDEX idx_workflow_steps_status ON ckc.workflow_steps(status);
CREATE INDEX idx_workflow_steps_created_at ON ckc.workflow_steps(created_at DESC);

-- Agent Memory
CREATE INDEX idx_agent_memory_agent ON ckc.agent_memory(agent_id);
CREATE INDEX idx_agent_memory_type ON ckc.agent_memory(memory_type);
CREATE INDEX idx_agent_memory_importance ON ckc.agent_memory(importance DESC);
CREATE INDEX idx_agent_memory_tags ON ckc.agent_memory USING GIN(tags);
CREATE INDEX idx_agent_memory_not_deleted ON ckc.agent_memory(is_deleted) WHERE is_deleted = FALSE;

-- Learning Events
CREATE INDEX idx_learning_events_room ON ckc.learning_events(room_id);
CREATE INDEX idx_learning_events_type ON ckc.learning_events(event_type);
CREATE INDEX idx_learning_events_created_at ON ckc.learning_events(created_at DESC);

-- ILCP Messages
CREATE INDEX idx_ilcp_messages_sender ON ckc.ilcp_messages(sender_room_id);
CREATE INDEX idx_ilcp_messages_recipient ON ckc.ilcp_messages(recipient_room_id);
CREATE INDEX idx_ilcp_messages_status ON ckc.ilcp_messages(status);
CREATE INDEX idx_ilcp_messages_type ON ckc.ilcp_messages(message_type);
CREATE INDEX idx_ilcp_messages_context ON ckc.ilcp_messages(task_context_id);
CREATE INDEX idx_ilcp_messages_created_at ON ckc.ilcp_messages(created_at DESC);

-- Knowledge Entries
CREATE INDEX idx_knowledge_entries_category ON ckc.knowledge_entries(category);
CREATE INDEX idx_knowledge_entries_tags ON ckc.knowledge_entries USING GIN(tags);
CREATE INDEX idx_knowledge_entries_source ON ckc.knowledge_entries(source_type, source_id);
CREATE INDEX idx_knowledge_entries_not_deleted ON ckc.knowledge_entries(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX idx_knowledge_entries_title_trgm ON ckc.knowledge_entries USING GIN(title gin_trgm_ops);
CREATE INDEX idx_knowledge_entries_content_trgm ON ckc.knowledge_entries USING GIN(content gin_trgm_ops);

-- Audit Trail
CREATE INDEX idx_audit_trail_entity ON ckc.audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_trail_actor ON ckc.audit_trail(actor);
CREATE INDEX idx_audit_trail_action ON ckc.audit_trail(action);
CREATE INDEX idx_audit_trail_created_at ON ckc.audit_trail(created_at DESC);

-- Work Loop Sequences
CREATE INDEX idx_work_loop_sequences_context ON ckc.work_loop_sequences(context_id);
CREATE INDEX idx_work_loop_sequences_status ON ckc.work_loop_sequences(status);

-- ==========================================================
-- Views for Common Queries
-- ==========================================================

-- Active task overview
CREATE VIEW ckc.v_active_tasks AS
SELECT
    tc.context_id,
    tc.task_id,
    tc.user_id,
    tc.original_prompt,
    tc.current_agent,
    tc.status,
    tc.created_at,
    COUNT(ws.id) as step_count,
    COUNT(ws.id) FILTER (WHERE ws.status = 'completed') as completed_steps,
    MAX(ws.completed_at) as last_activity
FROM ckc.task_contexts tc
LEFT JOIN ckc.workflow_steps ws ON tc.context_id = ws.context_id
WHERE tc.status = 'active'
GROUP BY tc.id
ORDER BY tc.created_at DESC;

-- Agent activity summary
CREATE VIEW ckc.v_agent_activity AS
SELECT
    agent_id,
    COUNT(*) as total_steps,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as avg_duration_ms,
    MAX(completed_at) as last_activity
FROM ckc.workflow_steps
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY agent_id;

-- ILCP message queue status
CREATE VIEW ckc.v_ilcp_queue_status AS
SELECT
    recipient_room_id,
    status,
    priority,
    COUNT(*) as message_count,
    MIN(created_at) as oldest_message,
    MAX(created_at) as newest_message
FROM ckc.ilcp_messages
WHERE status IN ('pending', 'delivered')
GROUP BY recipient_room_id, status, priority;

-- ==========================================================
-- Functions for Common Operations
-- ==========================================================

-- Get or create task context
CREATE OR REPLACE FUNCTION ckc.get_or_create_context(
    p_task_id VARCHAR(100),
    p_user_id VARCHAR(100) DEFAULT NULL,
    p_prompt TEXT DEFAULT NULL
) RETURNS VARCHAR(50) AS $$
DECLARE
    v_context_id VARCHAR(50);
BEGIN
    -- Check if context already exists
    SELECT context_id INTO v_context_id
    FROM ckc.task_contexts
    WHERE task_id = p_task_id AND status = 'active'
    LIMIT 1;

    -- Create new if not found
    IF v_context_id IS NULL THEN
        v_context_id := 'ctx_' || REPLACE(gen_random_uuid()::TEXT, '-', '')::VARCHAR(32);

        INSERT INTO ckc.task_contexts (context_id, task_id, user_id, original_prompt)
        VALUES (v_context_id, p_task_id, p_user_id, p_prompt);
    END IF;

    RETURN v_context_id;
END;
$$ LANGUAGE plpgsql;

-- Record audit event
CREATE OR REPLACE FUNCTION ckc.audit_log(
    p_entity_type VARCHAR(100),
    p_entity_id VARCHAR(100),
    p_action VARCHAR(100),
    p_actor VARCHAR(100) DEFAULT NULL,
    p_old_value JSONB DEFAULT NULL,
    p_new_value JSONB DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO ckc.audit_trail (entity_type, entity_id, action, actor, old_value, new_value, metadata)
    VALUES (p_entity_type, p_entity_id, p_action, p_actor, p_old_value, p_new_value, p_metadata)
    RETURNING id INTO v_audit_id;

    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- Update memory access
CREATE OR REPLACE FUNCTION ckc.touch_memory(p_memory_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE ckc.agent_memory
    SET access_count = access_count + 1,
        last_accessed = NOW()
    WHERE id = p_memory_id;
END;
$$ LANGUAGE plpgsql;

-- ==========================================================
-- Seed Data (Optional)
-- ==========================================================

-- Insert initial knowledge categories
INSERT INTO ckc.knowledge_entries (entry_id, title, content, category, tags, source_type, created_by)
VALUES
    ('ke_system_init', 'CKC System Initialization',
     'CKC Brain Database initialized successfully. This is the central knowledge repository for the Cirkelline ecosystem.',
     'system', ARRAY['initialization', 'system', 'ckc'], 'system', 'system'),
    ('ke_memory_types', 'Agent Memory Types',
     'CKC agents use three types of memory:\n1. Episodic: Specific events and experiences\n2. Semantic: General knowledge and facts\n3. Procedural: How to perform tasks and procedures',
     'documentation', ARRAY['memory', 'agents', 'architecture'], 'system', 'system');

-- ==========================================================
-- Completed
-- ==========================================================
-- Schema version tracking
CREATE TABLE IF NOT EXISTS ckc.schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT
);

INSERT INTO ckc.schema_version (version, description)
VALUES (1, 'Initial CKC Brain schema - Task Contexts, Workflow Steps, Agent Memory, ILCP Messages, Knowledge Entries, Audit Trail');
