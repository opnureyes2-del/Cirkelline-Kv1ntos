-- ============================================================================
-- Cirkelline KV1NTOS: Create ALL missing public schema tables
-- ============================================================================
-- Generated from code analysis of my_os.py, cirkelline/endpoints/*,
-- cirkelline/admin/*, cirkelline/middleware/*, cirkelline/integrations/*,
-- services/tier_service.py, and cirkelline/shared/jwt_utils.py
--
-- Existing tables: users, notion_tokens, alembic_version (3)
-- This script creates: 12 missing tables + 3 missing columns on users
-- ============================================================================

BEGIN;

-- ============================================================================
-- 0. ADD MISSING COLUMNS TO EXISTING users TABLE
-- ============================================================================
-- The code in preferences.py, tier_service.py, and auth.py expects these columns

ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_tier_slug VARCHAR(50) DEFAULT 'member';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_id UUID;

-- ============================================================================
-- 1. google_tokens
-- ============================================================================
-- Used by: integrations/google/oauth_endpoints.py, google_oauth.py, my_os.py, auth.py
-- Stores encrypted Google OAuth tokens per user (one-to-one with users)

CREATE TABLE IF NOT EXISTS google_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,           -- Encrypted OAuth access token (AES-256-GCM)
    refresh_token TEXT,                   -- Encrypted OAuth refresh token
    token_expiry TIMESTAMP,              -- When the access token expires
    scopes TEXT,                          -- Granted OAuth scopes
    email VARCHAR(255),                   -- Google account email
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_google_tokens_user_id ON google_tokens(user_id);

-- Auto-update trigger
CREATE TRIGGER update_google_tokens_updated_at
    BEFORE UPDATE ON google_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 2. admin_profiles
-- ============================================================================
-- Used by: shared/jwt_utils.py (load_admin_profile), all admin/* endpoints
-- Stores admin-specific profile data (name, role, personal context)

CREATE TABLE IF NOT EXISTS admin_profiles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) DEFAULT 'Admin',
    personal_context TEXT,
    preferences JSONB DEFAULT '{}',
    custom_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_profiles_user_id ON admin_profiles(user_id);

CREATE TRIGGER update_admin_profiles_updated_at
    BEFORE UPDATE ON admin_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 3. notion_user_databases
-- ============================================================================
-- Used by: integrations/notion/notion_helpers.py, database_endpoints.py, notion_tools.py
-- Registry of Notion databases discovered for each user via OAuth

CREATE TABLE IF NOT EXISTS notion_user_databases (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    database_id VARCHAR(255) NOT NULL,    -- Notion database UUID
    database_title VARCHAR(500),
    database_type VARCHAR(100),           -- Classified type (tasks, projects, contacts, etc.)
    schema JSONB DEFAULT '{}',            -- Full Notion database schema/properties
    property_order JSONB DEFAULT '[]',    -- Ordered list of property keys for UX
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, database_id)
);

CREATE INDEX IF NOT EXISTS idx_notion_user_databases_user_id ON notion_user_databases(user_id);
CREATE INDEX IF NOT EXISTS idx_notion_user_databases_type ON notion_user_databases(database_type);

CREATE TRIGGER update_notion_user_databases_updated_at
    BEFORE UPDATE ON notion_user_databases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 4. user_tiers
-- ============================================================================
-- Used by: services/tier_service.py, admin/subscriptions.py, shared/jwt_utils.py
-- Defines available subscription tiers (member, pro, business, elite, family)

CREATE TABLE IF NOT EXISTS user_tiers (
    slug VARCHAR(50) PRIMARY KEY,         -- e.g. 'member', 'pro', 'business', 'elite', 'family'
    name VARCHAR(100) NOT NULL,           -- Display name
    description TEXT,
    tier_level INTEGER NOT NULL DEFAULT 1, -- Numeric level for comparison (1=free, 2=pro, etc.)
    monthly_price_cents INTEGER DEFAULT 0,
    annual_price_cents INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    features JSONB DEFAULT '{}',          -- Feature flags/limits for this tier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_user_tiers_updated_at
    BEFORE UPDATE ON user_tiers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed default tiers
INSERT INTO user_tiers (slug, name, description, tier_level, monthly_price_cents, annual_price_cents, is_active, features) VALUES
    ('member', 'Member', 'Free tier with basic access', 1, 0, 0, true, '{"max_sessions": 10, "max_documents": 5}'),
    ('pro', 'Pro', 'Professional tier with advanced features', 2, 999, 9990, true, '{"max_sessions": 100, "max_documents": 50, "deep_research": true}'),
    ('business', 'Business', 'Business tier with team features', 3, 2999, 29990, true, '{"max_sessions": -1, "max_documents": -1, "deep_research": true, "team_features": true}'),
    ('elite', 'Elite', 'Elite tier with all features', 4, 4999, 49990, true, '{"max_sessions": -1, "max_documents": -1, "deep_research": true, "team_features": true, "priority_support": true}'),
    ('family', 'Family', 'Family plan with shared access', 3, 3999, 39990, true, '{"max_sessions": -1, "max_documents": -1, "deep_research": true, "family_sharing": true}')
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- 5. user_subscriptions
-- ============================================================================
-- Used by: services/tier_service.py, admin/subscriptions.py, shared/jwt_utils.py
-- Tracks active user subscriptions (one active per user)

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier_slug VARCHAR(50) NOT NULL REFERENCES user_tiers(slug),
    billing_cycle VARCHAR(20) DEFAULT 'monthly',  -- 'monthly' or 'annual'
    status VARCHAR(30) DEFAULT 'active',          -- 'active', 'cancelled', 'expired'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_period_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_period_end TIMESTAMP,
    cancelled_at TIMESTAMP,
    ends_at TIMESTAMP,
    payment_provider VARCHAR(50),                  -- e.g. 'stripe', 'manual'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_tier ON user_subscriptions(tier_slug);

CREATE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add FK from users.subscription_id to user_subscriptions.id
-- (only after user_subscriptions exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_users_subscription_id'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT fk_users_subscription_id
            FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- 6. subscription_history
-- ============================================================================
-- Used by: services/tier_service.py
-- Audit log of all subscription changes (upgrades, downgrades, cancellations)

CREATE TABLE IF NOT EXISTS subscription_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES user_subscriptions(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,              -- 'created', 'upgraded', 'downgraded', 'cancelled', 'expired', 'admin_assigned', 'tier_changed'
    from_tier_slug VARCHAR(50),
    to_tier_slug VARCHAR(50),
    changed_by_user_id UUID,                  -- Who initiated the change
    is_admin_action BOOLEAN DEFAULT false,
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscription_history_user_id ON subscription_history(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_history_subscription_id ON subscription_history(subscription_id);

-- ============================================================================
-- 7. activity_logs
-- ============================================================================
-- Used by: cirkelline/middleware/middleware.py (log_activity), admin/activity.py
-- Universal activity logging for ALL user-facing actions

CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),                     -- Text because it may contain 'unknown' or anon IDs
    action_type VARCHAR(100) NOT NULL,        -- e.g. 'user_login', 'document_upload', 'feedback_submit'
    endpoint VARCHAR(500),
    http_method VARCHAR(10),
    status_code INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    error_type VARCHAR(100),
    target_user_id VARCHAR(255),              -- For admin actions targeting another user
    target_resource_id VARCHAR(255),          -- Document ID, feedback ID, etc.
    resource_type VARCHAR(100),               -- 'document', 'feedback', etc.
    details JSONB,                            -- Additional details
    duration_ms INTEGER,
    ip_address VARCHAR(45),                   -- IPv4 or IPv6
    user_agent VARCHAR(500),
    is_admin BOOLEAN DEFAULT false,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action_type ON activity_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_success ON activity_logs(success);

-- ============================================================================
-- 8. feedback_submissions
-- ============================================================================
-- Used by: cirkelline/endpoints/feedback.py, admin/users.py
-- User feedback on AI messages (positive/negative with optional comments)

CREATE TABLE IF NOT EXISTS feedback_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),                  -- Reference to agno session
    message_content TEXT NOT NULL,            -- The AI message being rated (max 5000 chars)
    feedback_type VARCHAR(20) NOT NULL,       -- 'positive' or 'negative'
    user_comments TEXT,                       -- Optional user explanation (max 2000 chars)
    status VARCHAR(20) DEFAULT 'unread',      -- 'unread', 'seen', 'done'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_submissions_user_id ON feedback_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_submissions_status ON feedback_submissions(status);
CREATE INDEX IF NOT EXISTS idx_feedback_submissions_type ON feedback_submissions(feedback_type);

CREATE TRIGGER update_feedback_submissions_updated_at
    BEFORE UPDATE ON feedback_submissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 9. calendars
-- ============================================================================
-- Used by: cirkelline/endpoints/calendar.py
-- User calendars (local + Google Calendar sync)

CREATE TABLE IF NOT EXISTS calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    is_visible BOOLEAN DEFAULT true,
    source VARCHAR(50) DEFAULT 'local',       -- 'local' or 'google'
    external_id VARCHAR(255),                 -- Google Calendar ID
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendars_user ON calendars(user_id);

-- ============================================================================
-- 10. calendar_events
-- ============================================================================
-- Used by: cirkelline/endpoints/calendar.py
-- Calendar events (local + synced from Google Calendar)

CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID NOT NULL REFERENCES calendars(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    location VARCHAR(500),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    all_day BOOLEAN DEFAULT false,
    recurrence_rule TEXT,                     -- iCal RRULE format
    color VARCHAR(7),
    external_id VARCHAR(255),                -- Google Event ID
    external_link VARCHAR(500),              -- Link to Google Calendar event
    source VARCHAR(50) DEFAULT 'local',      -- 'local' or 'google'
    sync_status VARCHAR(50) DEFAULT 'local', -- 'local', 'synced', 'pending'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_user ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_calendar ON calendar_events(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_external ON calendar_events(external_id);

-- ============================================================================
-- 11. task_lists
-- ============================================================================
-- Used by: cirkelline/endpoints/tasks.py
-- Task lists (local + Google Tasks sync)

CREATE TABLE IF NOT EXISTS task_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    source VARCHAR(50) DEFAULT 'local',       -- 'local' or 'google'
    external_id VARCHAR(255),                 -- Google TaskList ID
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_task_lists_user ON task_lists(user_id);

-- ============================================================================
-- 12. tasks
-- ============================================================================
-- Used by: cirkelline/endpoints/tasks.py
-- Individual tasks within task lists

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    notes TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(20) DEFAULT 'medium',    -- 'low', 'medium', 'high', 'urgent'
    position INTEGER DEFAULT 0,
    parent_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    external_id VARCHAR(255),                 -- Google Task ID
    source VARCHAR(50) DEFAULT 'local',       -- 'local' or 'google'
    sync_status VARCHAR(50) DEFAULT 'local',  -- 'local', 'synced', 'pending'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_list ON tasks(list_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);

-- ============================================================================
-- DONE
-- ============================================================================
-- Total: 12 new tables created + 3 columns added to users
--
-- Tables created:
--   1. google_tokens
--   2. admin_profiles
--   3. notion_user_databases
--   4. user_tiers (with seed data: member, pro, business, elite, family)
--   5. user_subscriptions
--   6. subscription_history
--   7. activity_logs
--   8. feedback_submissions
--   9. calendars
--  10. calendar_events
--  11. task_lists
--  12. tasks
--
-- Columns added to users:
--   - preferences JSONB DEFAULT '{}'
--   - current_tier_slug VARCHAR(50) DEFAULT 'member'
--   - subscription_id UUID (FK to user_subscriptions)

COMMIT;
