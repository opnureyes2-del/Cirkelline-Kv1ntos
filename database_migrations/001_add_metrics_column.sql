-- Migration: Add metrics tracking to agno_sessions
-- Version: 001
-- Date: 2025-11-26
-- Purpose: Enable comprehensive token usage tracking for all agents/teams

-- Add metrics column to store array of metric objects
-- Each metric object contains: timestamp, agent_id, agent_name, tokens, costs
ALTER TABLE ai.agno_sessions
ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '[]'::jsonb;

-- Create GIN index for fast JSONB queries (filter by agent, date range, etc.)
CREATE INDEX IF NOT EXISTS idx_agno_sessions_metrics
ON ai.agno_sessions USING GIN (metrics);

-- Add comment explaining the column
COMMENT ON COLUMN ai.agno_sessions.metrics IS
'Array of metric objects tracking token usage per message. Each object contains:
{
    "timestamp": "ISO 8601 datetime",
    "agent_id": "unique agent/team identifier",
    "agent_name": "human-readable name",
    "agent_type": "agent or team",
    "input_tokens": int,
    "output_tokens": int,
    "total_tokens": int,
    "model": "model identifier",
    "message_preview": "first 100 chars",
    "response_preview": "first 100 chars",
    "input_cost": float (USD),
    "output_cost": float (USD),
    "total_cost": float (USD)
}';

-- Verify migration
SELECT
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'ai'
AND table_name = 'agno_sessions'
AND column_name = 'metrics';
