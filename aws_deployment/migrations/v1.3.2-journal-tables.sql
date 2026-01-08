-- ============================================================
-- Migration: v1.3.2 - Daily Journal Workflow Tables
-- Date: 2025-12-12
-- Description: Creates tables for the daily journal workflow
-- ============================================================

-- Run this on AWS RDS before deploying v1.3.2
-- Connect: psql -h cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com -U postgres -d cirkelline_system

-- ============================================================
-- 1. Create ai.user_journals table
-- ============================================================

CREATE TABLE IF NOT EXISTS ai.user_journals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    journal_date DATE NOT NULL,
    summary TEXT NOT NULL,
    topics JSONB,
    outcomes JSONB,
    sessions_processed JSONB,
    message_count INTEGER,
    created_at BIGINT NOT NULL,
    UNIQUE(user_id, journal_date)
);

-- Indexes for user_journals
CREATE INDEX IF NOT EXISTS idx_user_journals_user_id ON ai.user_journals(user_id);
CREATE INDEX IF NOT EXISTS idx_user_journals_date ON ai.user_journals(journal_date);
CREATE INDEX IF NOT EXISTS idx_user_journals_topics ON ai.user_journals USING GIN(topics);

-- Verify
-- \d ai.user_journals

-- ============================================================
-- 2. Create ai.journal_queue table
-- ============================================================

CREATE TABLE IF NOT EXISTS ai.journal_queue (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    target_date DATE NOT NULL,
    status VARCHAR DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITHOUT TIME ZONE,
    UNIQUE(user_id, target_date)
);

-- Indexes for journal_queue
CREATE INDEX IF NOT EXISTS idx_journal_queue_status ON ai.journal_queue(status);
CREATE INDEX IF NOT EXISTS idx_journal_queue_priority ON ai.journal_queue(priority DESC, created_at);

-- Verify
-- \d ai.journal_queue

-- ============================================================
-- 3. Ensure ai.workflow_runs table exists (from v1.3.0)
-- ============================================================

CREATE TABLE IF NOT EXISTS ai.workflow_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR UNIQUE NOT NULL,
    workflow_name VARCHAR NOT NULL,
    user_id VARCHAR,
    status VARCHAR NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    current_step VARCHAR,
    steps_completed JSONB DEFAULT '[]'::jsonb,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    metrics JSONB
);

-- Indexes for workflow_runs
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON ai.workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow ON ai.workflow_runs(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_user ON ai.workflow_runs(user_id);

-- Verify
-- \d ai.workflow_runs

-- ============================================================
-- 4. Verification Queries
-- ============================================================

-- Check all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'ai'
  AND table_name IN ('user_journals', 'journal_queue', 'workflow_runs');

-- Should return 3 rows

-- ============================================================
-- DONE! Ready for v1.3.2 deployment
-- ============================================================
