-- Migration: v1.3.0 Workflow Tables
-- Run this on production database before/after deploy

-- 1. Archive table for memory optimization workflow
CREATE TABLE IF NOT EXISTS ai.agno_memories_archive (
    id SERIAL PRIMARY KEY,
    original_memory_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    memory JSONB NOT NULL,
    topics JSONB,
    input VARCHAR,
    created_at TIMESTAMP,
    archived_at TIMESTAMP DEFAULT NOW(),
    optimization_run_id VARCHAR  -- Links all memories from same run
);

CREATE INDEX IF NOT EXISTS idx_archive_user_id ON ai.agno_memories_archive(user_id);
CREATE INDEX IF NOT EXISTS idx_archive_run_id ON ai.agno_memories_archive(optimization_run_id);
CREATE INDEX IF NOT EXISTS idx_archive_archived_at ON ai.agno_memories_archive(archived_at);

-- 2. Workflow runs table for tracking
CREATE TABLE IF NOT EXISTS ai.workflow_runs (
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

CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON ai.workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow ON ai.workflow_runs(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_user ON ai.workflow_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_started ON ai.workflow_runs(started_at);

-- Verify tables created
SELECT 'Tables created successfully' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'ai' AND table_name IN ('agno_memories_archive', 'workflow_runs');
