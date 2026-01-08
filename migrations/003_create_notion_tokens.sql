-- ════════════════════════════════════════════════════════════════
-- Migration: Create Notion OAuth Integration Table
-- Date: 2025-11-02
-- Phase: Notion Integration - Per-User OAuth
-- Description: Add notion_tokens table for storing user Notion OAuth credentials
-- ════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════
-- STEP 1: Create notion_tokens table
-- ════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS notion_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Notion workspace identification
    workspace_id VARCHAR(255) NOT NULL,
    workspace_name VARCHAR(255),
    workspace_icon VARCHAR(255),

    -- OAuth credentials (ENCRYPTED with AES-256-GCM)
    access_token TEXT NOT NULL,

    -- Notion integration details
    bot_id VARCHAR(255),
    owner_email VARCHAR(255),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(user_id)  -- One Notion workspace per user
);

COMMENT ON TABLE notion_tokens IS 'Per-user Notion OAuth credentials (encrypted) matching Google services pattern';
COMMENT ON COLUMN notion_tokens.user_id IS 'FK to users table - enforces user isolation';
COMMENT ON COLUMN notion_tokens.workspace_id IS 'Notion workspace ID from OAuth response';
COMMENT ON COLUMN notion_tokens.access_token IS 'Encrypted OAuth access token (AES-256-GCM)';
COMMENT ON COLUMN notion_tokens.bot_id IS 'Notion bot/integration ID';
COMMENT ON CONSTRAINT notion_tokens_user_id_key ON notion_tokens IS 'Ensures one Notion workspace per user';

-- ════════════════════════════════════════════════════════════════
-- STEP 2: Create indexes for performance
-- ════════════════════════════════════════════════════════════════

CREATE INDEX idx_notion_tokens_user_id ON notion_tokens(user_id);
CREATE INDEX idx_notion_tokens_workspace_id ON notion_tokens(workspace_id);

COMMENT ON INDEX idx_notion_tokens_user_id IS 'Fast lookups for user-specific Notion credentials';
COMMENT ON INDEX idx_notion_tokens_workspace_id IS 'Fast lookups by workspace ID';

-- ════════════════════════════════════════════════════════════════
-- STEP 3: Create trigger for auto-updating updated_at
-- ════════════════════════════════════════════════════════════════

-- Create trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for notion_tokens
CREATE TRIGGER update_notion_tokens_updated_at
    BEFORE UPDATE ON notion_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON FUNCTION update_updated_at_column IS 'Auto-update updated_at timestamp on row changes';

-- ════════════════════════════════════════════════════════════════
-- STEP 4: Grant appropriate permissions
-- ════════════════════════════════════════════════════════════════

-- Grant access to the cirkelline user (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cirkelline') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON notion_tokens TO cirkelline;
        GRANT USAGE, SELECT ON SEQUENCE notion_tokens_id_seq TO cirkelline;
    END IF;
END $$;

COMMIT;

-- ════════════════════════════════════════════════════════════════
-- Migration Complete!
-- ════════════════════════════════════════════════════════════════
--
-- Verification queries (run separately):
--
-- -- Check table exists
-- \d notion_tokens
--
-- -- Check indexes
-- \di notion_tokens*
--
-- -- Check constraints
-- SELECT conname, contype, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE conrelid = 'notion_tokens'::regclass;
--
-- -- Test cascade deletion
-- -- (Should delete notion_tokens row when user is deleted)
--
-- ════════════════════════════════════════════════════════════════
