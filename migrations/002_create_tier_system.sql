-- ════════════════════════════════════════════════════════════════
-- Migration: Create User Tier & Subscription System
-- Date: 2025-10-28
-- Phase: 1 - Foundation
-- Description: Add tier system with subscriptions, billing, and history
-- ════════════════════════════════════════════════════════════════

BEGIN;

-- ════════════════════════════════════════════════════════════════
-- STEP 1: Create user_tiers table (master tier definitions)
-- ════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS user_tiers (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    tier_level INTEGER NOT NULL UNIQUE,
    monthly_price_cents INTEGER DEFAULT 0,
    annual_price_cents INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    features JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE user_tiers IS 'Master tier definitions with pricing and features';
COMMENT ON COLUMN user_tiers.slug IS 'Unique identifier (member, pro, business, elite, family)';
COMMENT ON COLUMN user_tiers.tier_level IS 'Hierarchy level (1=lowest, 5=highest)';
COMMENT ON COLUMN user_tiers.monthly_price_cents IS 'Monthly price in cents (0 for free)';
COMMENT ON COLUMN user_tiers.features IS 'Feature flags and limits (Phase 2)';

-- ════════════════════════════════════════════════════════════════
-- STEP 2: Seed tier data
-- ════════════════════════════════════════════════════════════════

INSERT INTO user_tiers (slug, name, description, tier_level, monthly_price_cents, annual_price_cents, features) VALUES
('member', 'Member', 'Free tier with access to basic features', 1, 0, 0, '{"type": "free"}'),
('pro', 'Pro', 'Access to paid features with enhanced limits', 2, NULL, NULL, '{"type": "paid"}'),
('business', 'Business', 'Pro features plus business-specific capabilities', 3, NULL, NULL, '{"type": "paid", "includes": ["pro"]}'),
('elite', 'Elite', 'All paid features with premium support', 4, NULL, NULL, '{"type": "paid", "includes": ["pro", "business"]}'),
('family', 'Family', 'Elite features plus special family benefits', 5, NULL, NULL, '{"type": "paid", "includes": ["elite"], "special": "family"}')
ON CONFLICT (slug) DO NOTHING;

-- ════════════════════════════════════════════════════════════════
-- STEP 3: Create user_subscriptions table
-- ════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tier_slug VARCHAR(50) NOT NULL REFERENCES user_tiers(slug),
    
    -- Billing information
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    
    -- Subscription lifecycle timestamps
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_period_start TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_period_end TIMESTAMP,
    cancelled_at TIMESTAMP,
    ends_at TIMESTAMP,
    
    -- Payment provider integration (Phase 2)
    payment_provider VARCHAR(50),
    external_subscription_id VARCHAR(255),
    
    -- Metadata for extensibility
    metadata JSONB DEFAULT '{}',
    
    -- Standard timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_billing_cycle CHECK (billing_cycle IN ('monthly', 'annual')),
    CONSTRAINT chk_status CHECK (status IN ('active', 'cancelled', 'expired', 'pending')),
    CONSTRAINT unique_active_subscription EXCLUDE USING btree (user_id WITH =) WHERE (status = 'active')
);

COMMENT ON TABLE user_subscriptions IS 'User subscription records with billing and lifecycle tracking';
COMMENT ON COLUMN user_subscriptions.status IS 'active=current, cancelled=ending, expired=ended, pending=awaiting payment';
COMMENT ON COLUMN user_subscriptions.ends_at IS 'When subscription ends (for scheduled downgrades/cancellations)';
COMMENT ON CONSTRAINT unique_active_subscription ON user_subscriptions IS 'Ensures user can only have one active subscription';

-- Indexes for performance
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_tier ON user_subscriptions(tier_slug);
CREATE INDEX idx_user_subscriptions_period_end ON user_subscriptions(current_period_end) WHERE current_period_end IS NOT NULL;
CREATE INDEX idx_user_subscriptions_external_id ON user_subscriptions(external_subscription_id) WHERE external_subscription_id IS NOT NULL;

-- ════════════════════════════════════════════════════════════════
-- STEP 4: Create subscription_history table
-- ════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS subscription_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES user_subscriptions(id) ON DELETE CASCADE,
    
    -- Change details
    action VARCHAR(50) NOT NULL,
    from_tier_slug VARCHAR(50) REFERENCES user_tiers(slug),
    to_tier_slug VARCHAR(50) REFERENCES user_tiers(slug),
    
    -- Who made the change
    changed_by_user_id UUID REFERENCES users(id),
    is_admin_action BOOLEAN DEFAULT false,
    
    -- Context
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_action CHECK (action IN ('created', 'upgraded', 'downgraded', 'cancelled', 'renewed', 'expired', 'reactivated', 'admin_assigned'))
);

COMMENT ON TABLE subscription_history IS 'Complete audit trail of all subscription changes';
COMMENT ON COLUMN subscription_history.action IS 'Type of change: created, upgraded, downgraded, cancelled, renewed, expired, reactivated, admin_assigned';
COMMENT ON COLUMN subscription_history.changed_by_user_id IS 'User who made change (NULL for system-initiated changes)';

-- Indexes for querying history
CREATE INDEX idx_subscription_history_user_id ON subscription_history(user_id);
CREATE INDEX idx_subscription_history_subscription_id ON subscription_history(subscription_id);
CREATE INDEX idx_subscription_history_created_at ON subscription_history(created_at DESC);
CREATE INDEX idx_subscription_history_action ON subscription_history(action);

-- ════════════════════════════════════════════════════════════════
-- STEP 5: Update users table
-- ════════════════════════════════════════════════════════════════

-- Add tier tracking columns to existing users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS current_tier_slug VARCHAR(50) REFERENCES user_tiers(slug) DEFAULT 'member',
ADD COLUMN IF NOT EXISTS subscription_id UUID REFERENCES user_subscriptions(id);

COMMENT ON COLUMN users.current_tier_slug IS 'User''s current tier (denormalized for performance)';
COMMENT ON COLUMN users.subscription_id IS 'Reference to active subscription (denormalized for performance)';

-- Index for tier-based queries
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(current_tier_slug);

-- ════════════════════════════════════════════════════════════════
-- STEP 6: Create default subscriptions for all existing users
-- ════════════════════════════════════════════════════════════════

-- Insert Member tier subscriptions for all existing users who don't have one
INSERT INTO user_subscriptions (user_id, tier_slug, billing_cycle, status, started_at, current_period_start)
SELECT 
    id,
    'member',
    'monthly',
    'active',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM users
WHERE current_tier_slug IS NULL OR subscription_id IS NULL
ON CONFLICT DO NOTHING;

-- ════════════════════════════════════════════════════════════════
-- STEP 7: Update users table with their new subscription IDs
-- ════════════════════════════════════════════════════════════════

UPDATE users u
SET 
    subscription_id = s.id,
    current_tier_slug = 'member'
FROM user_subscriptions s
WHERE u.id = s.user_id 
  AND s.status = 'active'
  AND s.tier_slug = 'member'
  AND u.subscription_id IS NULL;

-- ════════════════════════════════════════════════════════════════
-- STEP 8: Create history entries for initial subscriptions
-- ════════════════════════════════════════════════════════════════

INSERT INTO subscription_history (user_id, subscription_id, action, to_tier_slug, reason, metadata)
SELECT 
    s.user_id,
    s.id,
    'created',
    'member',
    'Initial tier assignment during system migration',
    '{"migration": "002_create_tier_system", "auto_assigned": true}'
FROM user_subscriptions s
WHERE s.tier_slug = 'member' 
  AND s.status = 'active'
  AND NOT EXISTS (
      SELECT 1 FROM subscription_history sh 
      WHERE sh.subscription_id = s.id
  );

-- ════════════════════════════════════════════════════════════════
-- STEP 9: Create trigger for auto-updating updated_at
-- ════════════════════════════════════════════════════════════════

-- Trigger for user_tiers
CREATE OR REPLACE TRIGGER update_user_tiers_updated_at
    BEFORE UPDATE ON user_tiers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_subscriptions
CREATE OR REPLACE TRIGGER update_user_subscriptions_updated_at
    BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ════════════════════════════════════════════════════════════════
-- STEP 10: Create helper functions
-- ════════════════════════════════════════════════════════════════

-- Function to get user's current tier
CREATE OR REPLACE FUNCTION get_user_tier(p_user_id UUID)
RETURNS TABLE (
    tier_slug VARCHAR,
    tier_name VARCHAR,
    tier_level INTEGER,
    subscription_status VARCHAR,
    subscription_ends_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.slug,
        t.name,
        t.tier_level,
        s.status,
        s.ends_at
    FROM users u
    JOIN user_subscriptions s ON u.subscription_id = s.id
    JOIN user_tiers t ON s.tier_slug = t.slug
    WHERE u.id = p_user_id AND s.status = 'active'
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_tier IS 'Get user''s current tier and subscription details';

-- Function to check if user can access tier (helper for Phase 2)
CREATE OR REPLACE FUNCTION user_has_tier_level(p_user_id UUID, p_required_level INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_level INTEGER;
    v_is_admin BOOLEAN;
BEGIN
    -- Admins always have access
    SELECT EXISTS(SELECT 1 FROM admin_profiles WHERE user_id = p_user_id) INTO v_is_admin;
    IF v_is_admin THEN
        RETURN true;
    END IF;
    
    -- Get user's tier level
    SELECT t.tier_level INTO v_user_level
    FROM users u
    JOIN user_subscriptions s ON u.subscription_id = s.id
    JOIN user_tiers t ON s.tier_slug = t.slug
    WHERE u.id = p_user_id AND s.status = 'active';
    
    -- Check access
    RETURN COALESCE(v_user_level, 1) >= p_required_level;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION user_has_tier_level IS 'Check if user''s tier meets minimum level requirement';

-- ════════════════════════════════════════════════════════════════
-- STEP 11: Create view for easy subscription queries
-- ════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW user_subscription_details AS
SELECT 
    u.id as user_id,
    u.email,
    u.display_name,
    t.slug as tier_slug,
    t.name as tier_name,
    t.tier_level,
    t.monthly_price_cents,
    t.annual_price_cents,
    s.id as subscription_id,
    s.billing_cycle,
    s.status as subscription_status,
    s.started_at,
    s.current_period_start,
    s.current_period_end,
    s.cancelled_at,
    s.ends_at,
    s.payment_provider,
    s.external_subscription_id,
    -- Calculate days remaining
    CASE 
        WHEN s.current_period_end IS NOT NULL 
        THEN EXTRACT(DAYS FROM (s.current_period_end - CURRENT_TIMESTAMP))::INTEGER
        ELSE NULL
    END as days_remaining,
    -- Is subscription ending?
    (s.status = 'cancelled' OR s.ends_at IS NOT NULL) as is_ending,
    -- Check if admin
    EXISTS(SELECT 1 FROM admin_profiles WHERE user_id = u.id) as is_admin
FROM users u
LEFT JOIN user_subscriptions s ON u.subscription_id = s.id AND s.status = 'active'
LEFT JOIN user_tiers t ON s.tier_slug = t.slug;

COMMENT ON VIEW user_subscription_details IS 'Complete view of user subscriptions with calculated fields';

COMMIT;

-- ════════════════════════════════════════════════════════════════
-- Migration Complete!
-- ════════════════════════════════════════════════════════════════
-- 
-- Verification queries (run separately):
-- 
-- -- Check tier data
-- SELECT * FROM user_tiers ORDER BY tier_level;
-- 
-- -- Check all users have subscriptions
-- SELECT COUNT(*) FROM users WHERE subscription_id IS NULL;
-- 
-- -- Check subscription counts by tier
-- SELECT tier_slug, COUNT(*) as user_count 
-- FROM user_subscriptions 
-- WHERE status = 'active' 
-- GROUP BY tier_slug;
-- 
-- -- Test view
-- SELECT * FROM user_subscription_details LIMIT 5;
-- ════════════════════════════════════════════════════════════════