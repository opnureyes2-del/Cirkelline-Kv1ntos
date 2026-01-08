
# User Tier & Subscription System - Architecture Plan

**Version:** 1.0.0  
**Date:** 2025-10-28  
**Status:** ✅ Planning Complete - Ready for Implementation  
**Implementation:** Phase 1 (Foundation)

---

## Table of Contents

1. [Overview](#overview)
2. [Tier Structure](#tier-structure)
3. [Database Schema](#database-schema)
4. [SQL Migration Scripts](#sql-migration-scripts)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Implementation](#frontend-implementation)
7. [Migration Strategy](#migration-strategy)
8. [Future Enhancements (Phase 2)](#future-enhancements-phase-2)
9. [Technical Decisions](#technical-decisions)
10. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Goals

Create a robust, scalable user tier system that:
- ✅ Supports 5 distinct user tiers (Member, Pro, Business, Elite, Family)
- ✅ Tracks subscription status and billing cycles
- ✅ Maintains backward compatibility with existing users
- ✅ Provides foundation for future payment integration
- ✅ Keeps admins separate from tier restrictions

### Current State Analysis

**Existing User Types:**
- **Anonymous/Guest users:** Temporary session-based (ID: `anon-{uuid}`)
- **Registered users:** Stored in [`users`](../my_os.py:2868-2910) table
- **Admin users:** Identified via [`admin_profiles`](../docs/04-DATABASE-REFERENCE.md:129-161) table + hardcoded emails

**Current User Flow:**
```
Signup → users table → JWT with user_type → Middleware extracts user info
```

**What We're Adding:**
```
Signup → users table + user_subscriptions table → JWT with tier info → Tier-aware endpoints
```

### Key Requirements

Based on user input:
- ✅ 5 tiers: Member, Pro, Business, Elite, Family
- ✅ Both monthly and annual billing cycles
- ✅ No trial periods
- ✅ Downgrades take effect at end of billing cycle
- ✅ All existing users default to Member (free)
- ✅ Admins remain separate from tier system
- ⏸️ No feature gating in Phase 1 (all features available to all tiers initially)
- ⏸️ Payment integration deferred to Phase 2

---

## Tier Structure

### Tier Definitions

| Tier | Slug | Level | Base Price | Target Audience | Key Benefits |
|------|------|-------|------------|-----------------|--------------|
| **Member** | `member` | 1 | Free | All new users | Basic features, community access |
| **Pro** | `pro` | 2 | TBD | Individual power users | Paid features, enhanced limits |
| **Business** | `business` | 3 | TBD | Companies, teams | Pro + business features, API access |
| **Elite** | `elite` | 4 | TBD | Premium users | All paid features, priority support |
| **Family** | `family` | 5 | TBD | Friends, families | Elite + special family features |

### Tier Hierarchy

```
Level 1: Member (Free, Default)
         ↓ Upgrade
Level 2: Pro (Paid)
         ↓ Upgrade
Level 3: Business (Paid, includes Pro features)
         ↓ Upgrade
Level 4: Elite (Paid, includes all Business features)
         ↓ Special Tier
Level 5: Family (Paid, Elite + unique family features)
```

**Notes:**
- **Tier Level** determines hierarchy (higher = more features)
- **Business** includes all Pro features
- **Elite** includes all Business features
- **Family** is parallel to Elite with unique family-specific features

### Feature Matrix (Phase 2 - Placeholder)

```json
{
  "member": {
    "max_documents": 10,
    "max_sessions_per_month": 50,
    "google_integration": false,
    "api_access": false,
    "support_level": "community"
  },
  "pro": {
    "max_documents": 100,
    "max_sessions_per_month": -1,
    "google_integration": true,
    "api_access": false,
    "support_level": "email"
  },
  "business": {
    "max_documents": 1000,
    "max_sessions_per_month": -1,
    "google_integration": true,
    "api_access": true,
    "team_features": true,
    "support_level": "priority"
  },
  "elite": {
    "max_documents": -1,
    "max_sessions_per_month": -1,
    "google_integration": true,
    "api_access": true,
    "team_features": true,
    "white_label": true,
    "support_level": "dedicated"
  },
  "family": {
    "max_documents": -1,
    "max_sessions_per_month": -1,
    "google_integration": true,
    "api_access": true,
    "shared_accounts": 5,
    "family_sharing": true,
    "support_level": "dedicated"
  }
}
```

---

## Database Schema

### ER Diagram

```
┌─────────────────────┐
│    user_tiers       │
│ (Master tier data)  │
├─────────────────────┤
│ id (PK)            │
│ slug (UNIQUE)      │◄──────────┐
│ name               │           │
│ tier_level         │           │ FK
│ monthly_price      │           │
│ annual_price       │           │
│ features (JSONB)   │           │
└─────────────────────┘           │
                                  │
┌─────────────────────┐           │
│       users         │           │
│  (Existing table)   │           │
├─────────────────────┤           │
│ id (PK)            │◄──┐       │
│ email              │   │       │
│ hashed_password    │   │       │
│ display_name       │   │       │
│ current_tier_slug ─┼───┼───────┘
│ subscription_id ───┼───┼───────┐
│ preferences        │   │       │
│ created_at         │   │       │
│ last_login         │   │       │
└─────────────────────┘   │       │
                          │       │
                          │ FK    │ FK
                          │       │
┌─────────────────────────┼───────┘
│  user_subscriptions     │
│ (Subscription records)  │
├─────────────────────────┤
│ id (PK)            │◄───┘
│ user_id (FK) ──────┘
│ tier_slug (FK)      
│ billing_cycle       
│ status              
│ started_at          
│ current_period_start
│ current_period_end  
│ cancelled_at        
│ ends_at            │◄────────────┐
│ payment_provider    │             │
│ external_sub_id     │             │
└─────────────────────┘             │
          │                         │
          │ FK                      │ FK
          │                         │
          ├─────────────────────────┤
          ▼                         │
┌─────────────────────┐             │
│ subscription_history│             │
│ (Audit trail)       │             │
├─────────────────────┤             │
│ id (PK)            │             │
│ user_id (FK) ──────┼─────────────┘
│ subscription_id (FK)
│ action              
│ from_tier_slug      
│ to_tier_slug        
│ changed_by_user_id  
│ is_admin_action     
│ reason              
│ created_at          
└─────────────────────┘
```

---

## SQL Migration Scripts

### Migration File: `002_create_tier_system.sql`

**Purpose:** Create complete tier and subscription infrastructure

```sql
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
CREATE TRIGGER update_user_tiers_updated_at
    BEFORE UPDATE ON user_tiers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for user_subscriptions
CREATE TRIGGER update_user_subscriptions_updated_at
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
-- VERIFICATION QUERIES (Run separately after migration)
-- ════════════════════════════════════════════════════════════════

-- Verify tables created
-- \dt user_tiers
-- \dt user_subscriptions
-- \dt subscription_history

-- Check tier data
-- SELECT * FROM user_tiers ORDER BY tier_level;

-- Check all users have subscriptions
-- SELECT COUNT(*) FROM users WHERE subscription_id IS NULL;
-- Should return 0

-- Check subscription counts by tier
-- SELECT tier_slug, COUNT(*) as user_count 
-- FROM user_subscriptions 
-- WHERE status = 'active' 
-- GROUP BY tier_slug;

-- Test helper function
-- SELECT * FROM get_user_tier('YOUR-USER-ID-HERE');

-- Test view
-- SELECT * FROM user_subscription_details WHERE email = 'opnureyes2@gmail.com';
```

### Migration File: `003_add_tier_preferences.sql` (Optional Enhancement)

**Purpose:** Add tier-specific preferences storage

```sql
-- Optional: Add tier-specific preferences to users table
BEGIN;

-- Update users.preferences JSONB to include tier preferences
-- Structure: {"theme": "dark", "tier_preferences": {"auto_renew": true, "upgrade_notifications": true}}

-- This is already supported by existing preferences column
-- No schema change needed, just documentation

COMMIT;
```

---

## Backend Implementation

### 1. New Backend Files

#### `services/tier_service.py`

**Purpose:** Business logic for tier management

```python
# /services/tier_service.py

from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import uuid
import json

class TierService:
    """
    Service layer for user tier and subscription management.
    Handles all business logic for tiers, subscriptions, and billing.
    """
    
    @staticmethod
    async def get_all_tiers(engine) -> List[Dict]:
        """Get all available tiers"""
        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT slug, name, description, tier_level,
                           monthly_price_cents, annual_price_cents, 
                           is_active, features
                    FROM user_tiers
                    WHERE is_active = true
                    ORDER BY tier_level
                """)
            )
            
            tiers = []
            for row in result.fetchall():
                tiers.append({
                    "slug": row[0],
                    "name": row[1],
                    "description": row[2],
                    "tier_level": row[3],
                    "monthly_price_cents": row[4],
                    "annual_price_cents": row[5],
                    "is_active": row[6],
                    "features": row[7]
                })
            
            return tiers
    
    @staticmethod
    async def get_user_subscription(engine, user_id: str) -> Optional[Dict]:
        """Get user's active subscription with tier details"""
        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT 
                        s.id, s.tier_slug, s.billing_cycle, s.status,
                        s.started_at, s.current_period_start, s.current_period_end,
                        s.cancelled_at, s.ends_at,
                        t.name as tier_name, t.tier_level, t.description,
                        t.monthly_price_cents, t.annual_price_cents
                    FROM user_subscriptions s
                    JOIN user_tiers t ON s.tier_slug = t.slug
                    WHERE s.user_id = :user_id AND s.status = 'active'
                    LIMIT 1
                """),
                {"user_id": user_id}
            )
            
            row = result.fetchone()
            if not row:
                return None
            
            return {
                "id": str(row[0]),
                "tier": {
                    "slug": row[1],
                    "name": row[9],
                    "level": row[10],
                    "description": row[11],
                    "monthly_price_cents": row[12],
                    "annual_price_cents": row[13]
                },
                "billing_cycle": row[2],
                "status": row[3],
                "started_at": row[4].isoformat() if row[4] else None,
                "current_period_start": row[5].isoformat() if row[5] else None,
                "current_period_end": row[6].isoformat() if row[6] else None,
                "cancelled_at": row[7].isoformat() if row[7] else None,
                "ends_at": row[8].isoformat() if row[8] else None
            }
    
    @staticmethod
    async def create_subscription(
        engine, 
        user_id: str, 
        tier_slug: str,
        billing_cycle: str = 'monthly',
        admin_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Create new subscription for user.
        Returns (subscription_id, subscription_data)
        """
        with Session(engine) as session:
            # Verify tier exists
            tier_check = session.execute(
                text("SELECT tier_level FROM user_tiers WHERE slug = :slug AND is_active = true"),
                {"slug": tier_slug}
            )
            if not tier_check.fetchone():
                raise ValueError(f"Invalid or inactive tier: {tier_slug}")
            
            # Create subscription
            subscription_id = str(uuid.uuid4())
            
            # Calculate period end (only for paid tiers)
            period_end = None
            if tier_slug != 'member':
                if billing_cycle == 'monthly':
                    period_end = datetime.now() + timedelta(days=30)
                else:  # annual
                    period_end = datetime.now() + timedelta(days=365)
            
            session.execute(
                text("""
                    INSERT INTO user_subscriptions 
                    (id, user_id, tier_slug, billing_cycle, status, 
                     current_period_start, current_period_end)
                    VALUES 
                    (:id, :user_id, :tier_slug, :billing_cycle, 'active',
                     CURRENT_TIMESTAMP, :period_end)
                """),
                {
                    "id": subscription_id,
                    "user_id": user_id,
                    "tier_slug": tier_slug,
                    "billing_cycle": billing_cycle,
                    "period_end": period_end
                }
            )
            
            # Update user's current tier
            session.execute(
                text("""
                    UPDATE users 
                    SET current_tier_slug = :tier_slug,
                        subscription_id = :subscription_id
                    WHERE id = :user_id
                """),
                {
                    "tier_slug": tier_slug,
                    "subscription_id": subscription_id,
                    "user_id": user_id
                }
            )
            
            # Create history entry
            session.execute(
                text("""
                    INSERT INTO subscription_history 
                    (user_id, subscription_id, action, to_tier_slug, 
                     changed_by_user_id, is_admin_action, reason, metadata)
                    VALUES 
                    (:user_id, :subscription_id, :action, :to_tier,
                     :changed_by, :is_admin, :reason, :metadata)
                """),
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "action": "admin_assigned" if admin_id else "created",
                    "to_tier": tier_slug,
                    "changed_by": admin_id or user_id,
                    "is_admin": admin_id is not None,
                    "reason": reason or "Subscription created",
                    "metadata": json.dumps({"created_by": "system"})
                }
            )
            
            session.commit()
            
            # Return subscription data
            return subscription_id, {
                "id": subscription_id,
                "user_id": user_id,
                "tier_slug": tier_slug,
                "status": "active"
            }
    
    @staticmethod
    async def upgrade_subscription(
        engine,
        user_id: str,
        new_tier_slug: str,
        billing_cycle: str = 'monthly',
        admin_id: Optional[str] = None
    ) -> Dict:
        """
        Upgrade user to higher tier (immediate effect).
        Returns updated subscription data.
        """
        with Session(engine) as session:
            # Get current subscription
            current_sub = session.execute(
                text("""
                    SELECT id, tier_slug, s.tier_level as current_level, t.tier_level as new_level
                    FROM user_subscriptions s
                    JOIN user_tiers t ON s.tier_slug = t.slug
                    JOIN user_tiers nt ON nt.slug = :new_tier
                    WHERE s.user_id = :user_id AND s.status = 'active'
                """),
                {"user_id": user_id, "new_tier": new_tier_slug}
            ).fetchone()
            
            if not current_sub:
                raise ValueError("No active subscription found")
            
            subscription_id = str(current_sub[0])
            old_tier = current_sub[1]
            current_level = current_sub[2]
            new_level = current_sub[3]
            
            # Verify it's an upgrade
            if new_level <= current_level:
                raise ValueError("New tier must be higher level than current tier")
            
            # Calculate new period end
            if billing_cycle == 'monthly':
                period_end = datetime.now() + timedelta(days=30)
            else:
                period_end = datetime.now() + timedelta(days=365)
            
            # Update subscription
            session.execute(
                text("""
                    UPDATE user_subscriptions
                    SET tier_slug = :new_tier,
                        billing_cycle = :billing_cycle,
                        current_period_start = CURRENT_TIMESTAMP,
                        current_period_end = :period_end,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :subscription_id
                """),
                {
                    "new_tier": new_tier_slug,
                    "billing_cycle": billing_cycle,
                    "period_end": period_end,
                    "subscription_id": subscription_id
                }
            )
            
            # Update user's current tier
            session.execute(
                text("UPDATE users SET current_tier_slug = :tier WHERE id = :user_id"),
                {"tier": new_tier_slug, "user_id": user_id}
            )
            
            # Log to history
            session.execute(
                text("""
                    INSERT INTO subscription_history 
                    (user_id, subscription_id, action, from_tier_slug, to_tier_slug,
                     changed_by_user_id, is_admin_action, reason)
                    VALUES 
                    (:user_id, :subscription_id, 'upgraded', :from_tier, :to_tier,
                     :changed_by, :is_admin, :reason)
                """),
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "from_tier": old_tier,
                    "to_tier": new_tier_slug,
                    "changed_by": admin_id or user_id,
                    "is_admin": admin_id is not None,
                    "reason": f"Upgraded from {old_tier} to {new_tier_slug}"
                }
            )
            
            session.commit()
            
            return {
                "subscription_id": subscription_id,
                "old_tier": old_tier,
                "new_tier": new_tier_slug,
                "effective_immediately": True,
                "next_billing": period_end.isoformat()
            }
    
    @staticmethod
    async def downgrade_subscription(
        engine,
        user_id: str,
        new_tier_slug: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Schedule downgrade to lower tier at end of current billing period.
        Returns effective date and details.
        """
        with Session(engine) as session:
            # Get current subscription
            current_sub = session.execute(
                text("""
                    SELECT id, tier_slug, current_period_end,
                           t1.tier_level as current_level,
                           t2.tier_level as new_level
                    FROM user_subscriptions s
                    JOIN user_tiers t1 ON s.tier_slug = t1.slug
                    JOIN user_tiers t2 ON t2.slug = :new_tier
                    WHERE s.user_id = :user_id AND s.status = 'active'
                """),
                {"user_id": user_id, "new_tier": new_tier_slug}
            ).fetchone()
            
            if not current_sub:
                raise ValueError("No active subscription found")
            
            subscription_id = str(current_sub[0])
            old_tier = current_sub[1]
            period_end = current_sub[2]
            current_level = current_sub[3]
            new_level = current_sub[4]
            
            # Verify it's a downgrade
            if new_level >= current_level:
                raise ValueError("New tier must be lower level than current tier")
            
            # Set ends_at to current period end (or now + 30 days if free tier)
            effective_date = period_end or (datetime.now() + timedelta(days=30))
            
            # Schedule downgrade
            session.execute(
                text("""
                    UPDATE user_subscriptions
                    SET ends_at = :effective_date,
                        metadata = jsonb_set(
                            COALESCE(metadata, '{}'),
                            '{scheduled_downgrade}',
                            to_jsonb(:new_tier::text)
                        )
                    WHERE id = :subscription_id
                """),
                {
                    "effective_date": effective_date,
                    "new_tier": new_tier_slug,
                    "subscription_id": subscription_id
                }
            )
            
            # Log to history
            session.execute(
                text("""
                    INSERT INTO subscription_history 
                    (user_id, subscription_id, action, from_tier_slug, to_tier_slug,
                     changed_by_user_id, is_admin_action, reason, metadata)
                    VALUES 
                    (:user_id, :subscription_id, 'downgraded', :from_tier, :to_tier,
                     :changed_by, false, :reason, :metadata)
                """),
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "from_tier": old_tier,
                    "to_tier": new_tier_slug,
                    "changed_by": user_id,
                    "reason": reason or f"Downgrade scheduled from {old_tier} to {new_tier_slug}",
                    "metadata": json.dumps({"effective_date": effective_date.isoformat()})
                }
            )
            
            session.commit()
            
            return {
                "subscription_id": subscription_id,
                "old_tier": old_tier,
                "new_tier": new_tier_slug,
                "effective_date": effective_date.isoformat(),
                "remains_active_until": effective_date.isoformat()
            }
    
    @staticmethod
    async def cancel_subscription(engine, user_id: str, reason: Optional[str] = None) -> Dict:
        """
        Cancel subscription (remains active until period end).
        Free tier cannot be cancelled.
        """
        with Session(engine) as session:
            # Get current subscription
            current_sub = session.execute(
                text("""
                    SELECT id, tier_slug, current_period_end
                    FROM user_subscriptions
                    WHERE user_id = :user_id AND status = 'active'
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if not current_sub:
                raise ValueError("No active subscription found")
            
            subscription_id = str(current_sub[0])
            tier_slug = current_sub[1]
            period_end = current_sub[2]
            
            if tier_slug == 'member':
                raise ValueError("Cannot cancel free tier")
            
            # Calculate when subscription ends (reverts to member)
            ends_at = period_end or (datetime.now() + timedelta(days=30))
            
            # Mark as cancelled
            session.execute(
                text("""
                    UPDATE user_subscriptions
                    SET status = 'cancelled',
                        cancelled_at = CURRENT_TIMESTAMP,
                        ends_at = :ends_at,
                        metadata = jsonb_set(
                            COALESCE(metadata, '{}'),
                            '{reverts_to_tier}',
                            to_jsonb('member'::text)
                        )
                    WHERE id = :subscription_id
                """),
                {
                    "ends_at": ends_at,
                    "subscription_id": subscription_id
                }
            )
            
            # Log cancellation
            session.execute(
                text("""
                    INSERT INTO subscription_history 
                    (user_id, subscription_id, action, from_tier_slug, to_tier_slug,
                     changed_by_user_id, reason, metadata)
                    VALUES 
                    (:user_id, :subscription_id, 'cancelled', :from_tier, 'member',
                     :user_id, :reason, :metadata)
                """),
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "from_tier": tier_slug,
                    "reason": reason or "User cancelled subscription",
                    "metadata": json.dumps({"ends_at": ends_at.isoformat()})
                }
            )
            
            session.commit()
            
            return {
                "cancelled": True,
                "remains_active_until": ends_at.isoformat(),
                "reverts_to_tier": "member"
            }
    
    @staticmethod
    async def process_expired_subscriptions(engine) -> int:
        """
        Background job: Process subscriptions that have ended.
        Returns count of processed subscriptions.
        """
        with Session(engine) as session:
            # Find subscriptions past their end date
            expired = session.execute(
                text("""
                    SELECT id, user_id, tier_slug, metadata
                    FROM user_subscriptions
                    WHERE status = 'cancelled' 
                      AND ends_at IS NOT NULL 
                      AND ends_at < CURRENT_TIMESTAMP
                """)
            ).fetchall()
            
            count = 0
            for row in expired:
                subscription_id = str(row[0])
                user_id = str(row[1])
                old_tier = row[2]
                metadata = row[3] or {}
                
                # Get target tier (default to member)
                target_tier = metadata.get('reverts_to_tier', 'member')
                scheduled_tier = metadata.get('scheduled_downgrade', target_tier)
                
                # Create new member subscription
                new_sub_id = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO user_subscriptions
                        (id, user_id, tier_slug, billing_cycle, status)
                        VALUES (:id, :user_id, :tier, 'monthly', 'active')
                    """),
                    {"id": new_sub_id, "user_id": user_id, "tier": scheduled_tier}
                )
                
                # Expire old subscription
                session.execute(
                    text("UPDATE user_subscriptions SET status = 'expired' WHERE id = :id"),
                    {"id": subscription_id}
                )
                
                # Update user
                session.execute(
                    text("""
                        UPDATE users 
                        SET current_tier_slug = :tier,
                            subscription_id = :new_sub_id
                        WHERE id = :user_id
                    """),
                    {"tier": scheduled_tier, "new_sub_id": new_sub_id, "user_id": user_id}
                )
                
                # Log expiration
                session.execute(
                    text("""
                        INSERT INTO subscription_history 
                        (user_id, subscription_id, action, from_tier_slug, to_tier_slug, reason)
                        VALUES 
                        (:user_id, :old_sub_id, 'expired', :from_tier, :to_tier, :reason)
                    """),
                    {
                        "user_id": user_id,
                        "old_sub_id": subscription_id,
                        "from_tier": old_tier,
                        "to_tier": scheduled_tier,
                        "reason": "Subscription period ended"
                    }
                )
                
                count += 1
            
            session.commit()
            return count
```

### 2. API Endpoint Implementations

**Add to [`my_os.py`](../my_os.py) after existing endpoints (around line 5000+)**

#### Public Tier Information

```python
@app.get("/api/tiers")
async def get_available_tiers():
    """
    Get all available tiers with pricing information.
    Public endpoint - no authentication required.
    """
    try:
        from services.tier_service import TierService
        
        tiers = await TierService.get_all_tiers(_shared_engine)
        
        return {
            "success": True,
            "tiers": tiers
        }
    except Exception as e:
        logger.error(f"Error fetching tiers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### User Subscription Endpoints

```python
@app.get("/api/user/subscription")
async def get_user_subscription_info(request: Request):
    """Get current user's subscription and tier information"""
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        from services.tier_service import TierService
        
        subscription = await TierService.get_user_subscription(_shared_engine, user_id)
        all_tiers = await TierService.get_all_tiers(_shared_engine)
        
        # Determine which tiers user can upgrade to
        current_level = subscription['tier']['level'] if subscription else 1
        available_upgrades = [
            tier for tier in all_tiers 
            if tier['tier_level'] > current_level
        ]
        
        return {
            "success": True,
            "subscription": subscription,
            "available_tiers": all_tiers,
            "available_upgrades": available_upgrades,
            "can_upgrade": len(available_upgrades) > 0
        }
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/subscription/upgrade")
async def request_tier_upgrade(request: Request):
    """
    Request tier upgrade.
    Phase 1: Creates subscription, requires admin approval for payment
    Phase 2: Will redirect to payment processor
    """
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        data = await request.json()
        new_tier = data.get('tier_slug')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not new_tier:
            raise HTTPException(status_code=400, detail="tier_slug required")
        
        from services.tier_service import TierService
        
        result = await TierService.upgrade_subscription(
            _shared_engine, user_id, new_tier, billing_cycle
        )
        
        # Log upgrade request
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="tier_upgrade_request",
            success=True,
            status_code=200,
            details={"new_tier": new_tier, "billing_cycle": billing_cycle}
        )
        
        return {
            "success": True,
            "message": "Upgrade request created. Contact admin for payment setup.",
            "upgrade": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/subscription/downgrade")
async def request_tier_downgrade(request: Request):
    """Schedule tier downgrade at end of billing cycle"""
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        data = await request.json()
        new_tier = data.get('tier_slug')
        reason = data.get('reason', '')
        
        if not new_tier:
            raise HTTPException(status_code=400, detail="tier_slug required")
        
        from services.tier_service import TierService
        
        result = await TierService.downgrade_subscription(
            _shared_engine, user_id, new_tier, reason
        )
        
        # Log downgrade request
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="tier_downgrade_request",
            success=True,
            status_code=200,
            details={"new_tier": new_tier, "effective_date": result['effective_date']}
        )
        
        return {
            "success": True,
            "message": f"Downgrade scheduled for {result['effective_date']}",
            "downgrade": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error downgrading subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/user/subscription/cancel")
async def cancel_user_subscription(request: Request):
    """Cancel subscription (reverts to free tier at period end)"""
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        data = await request.json()
        reason = data.get('reason', '')
        
        from services.tier_service import TierService
        
        result = await TierService.cancel_subscription(_shared_engine, user_id, reason)
        
        # Log cancellation
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="subscription_cancel",
            success=True,
            status_code=200,
            details={"reason": reason}
        )
        
        return {
            "success": True,
            "message": "Subscription cancelled",
            "cancellation": result
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Admin Subscription Management

```python
@app.get("/api/admin/subscriptions")
async def list_all_subscriptions(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    tier_filter: str = Query("all"),
    status_filter: str = Query("all")
):
    """List all subscriptions with filters (admin only)"""
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check admin
    with Session(_shared_engine) as session:
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Build query with filters
        query = """
            SELECT 
                s.id, s.user_id, u.email, u.display_name,
                s.tier_slug, t.name as tier_name, t.tier_level,
                s.billing_cycle, s.status,
                s.started_at, s.current_period_end, s.cancelled_at,
                s.payment_provider
            FROM user_subscriptions s
            JOIN users u ON s.user_id = u.id
            JOIN user_tiers t ON s.tier_slug = t.slug
            WHERE 1=1
        """
        
        params = {}
        
        if tier_filter != 'all':
            query += " AND s.tier_slug = :tier"
            params['tier'] = tier_filter
        
        if status_filter != 'all':
            query += " AND s.status = :status"
            params['status'] = status_filter
        
        # Count total
        count_query = query.replace("SELECT s.id,", "SELECT COUNT(*) FROM (SELECT s.id,") + ") as count_query"
        
        with Session(_shared_engine) as session:
            total = session.execute(text(count_query), params).scalar()
            
            # Get paginated results
            query += " ORDER BY s.created_at DESC LIMIT :limit OFFSET :offset"
            params['limit'] = limit
            params['offset'] = (page - 1) * limit
            
            result = session.execute(text(query), params).fetchall()
            
            subscriptions = []
            for row in result:
                subscriptions.append({
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "user_email": row[2],
                    "user_display_name": row[3],
                    "tier_slug": row[4],
                    "tier_name": row[5],
                    "tier_level": row[6],
                    "billing_cycle": row[7],
                    "status": row[8],
                    "started_at": row[9].isoformat() if row[9] else None,
                    "current_period_end": row[10].isoformat() if row[10] else None,
                    "cancelled_at": row[11].isoformat() if row[11] else None,
                    "payment_provider": row[12]
                })
        
        return {
            "success": True,
            "data": subscriptions,
            "total": total,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/subscriptions/{target_user_id}/assign-tier")
async def admin_assign_tier(target_user_id: str, request: Request):
    """
    Admin assigns tier to user (bypasses payment).
    Used for promotions, manual upgrades, special cases.
    """
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check admin
    with Session(_shared_engine) as session:
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        data = await request.json()
        tier_slug = data.get('tier_slug')
        billing_cycle = data.get('billing_cycle', 'monthly')
        reason = data.get('reason', 'Admin assignment')
        
        if not tier_slug:
            raise HTTPException(status_code=400, detail="tier_slug required")
        
        from services.tier_service import TierService
        
        # Check if user has active subscription
        current_sub = await TierService.get_user_subscription(_shared_engine, target_user_id)
        
        if current_sub:
            # Upgrade existing subscription
            result = await TierService.upgrade_subscription(
                _shared_engine, target_user_id, tier_slug, billing_cycle, admin_id=user_id
            )
        else:
            # Create new subscription
            sub_id, result = await TierService.create_subscription(
                _shared_engine, target_user_id, tier_slug, billing_cycle, 
                admin_id=user_id, reason=reason
            )
        
        # Log admin action
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="admin_assign_tier",
            success=True,
            status_code=200,
            target_user_id=target_user_id,
            details={"tier": tier_slug, "reason": reason},
            is_admin=True
        )
        
        return {
            "success": True,
            "message": f"Tier {tier_slug} assigned to user",
            "subscription": result
        }
    except Exception as e:
        logger.error(f"Error assigning tier: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/subscription-stats")
async def get_subscription_stats(request: Request):
    """Get subscription statistics (admin only)"""
    user_id = getattr(request.state, 'user_id', None)
    
    if not user_id or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check admin
    with Session(_shared_engine) as session:
        admin_check = session.execute(
            text("SELECT 1 FROM admin_profiles WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if not admin_check:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get statistics
        stats_query = """
            SELECT
                COUNT(*) as total_subscriptions,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_subscriptions,
                COUNT(CASE WHEN tier_slug = 'member' THEN 1 END) as free_users,
                COUNT(CASE WHEN tier_slug = 'pro' THEN 1 END) as pro_users,
                COUNT(CASE WHEN tier_slug = 'business' THEN 1 END) as business_users,
                COUNT(CASE WHEN tier_slug = 'elite' THEN 1 END) as elite_users,
                COUNT(CASE WHEN tier_slug = 'family' THEN 1 END) as family_users,
                COUNT(CASE WHEN billing_cycle = 'monthly' THEN 1 END) as monthly_billing,
                COUNT(CASE WHEN billing_cycle = 'annual' THEN 1 END) as annual_billing
            FROM user_subscriptions
            WHERE status = 'active'
        """
        
        result = session.execute(text(stats_query)).fetchone()
        
        return {
            "success": True,
            "stats": {
                "total_subscriptions": result[0],
                "active_subscriptions": result[1],
                "by_tier": {
                    "member": result[2],
                    "pro": result[3],
                    "business": result[4],
                    "elite": result[5],
                    "family": result[6]
                },
                "by_billing_cycle": {
                    "monthly": result[7],
                    "annual": result[8]
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching subscription stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. JWT Token Updates

**Update JWT generation in 3 places:**

#### A. Signup Endpoint (my_os.py ~line 2974)

```python
# BEFORE (current)
jwt_payload = {
    "user_id": str(new_user[0]),
    "email": new_user[1],
    "display_name": new_user[2],
    "user_type": "Regular",
    "is_admin": False
}

# AFTER (with tier info)
# Get user's subscription info
with Session(engine) as session:
    tier_info = session.execute(
        text("""
            SELECT s.tier_slug, t.tier_level, s.status
            FROM user_subscriptions s
            JOIN user_tiers t ON s.tier_slug = t.slug
            WHERE s.user_id = :user_id AND s.status = 'active'
        """),
        {"user_id": str(new_user[0])}
    ).fetchone()

jwt_payload = {
    "user_id": str(new_user[0]),
    "email": new_user[1],
    "display_name": new_user[2],
    "user_type": "Regular",
    "is_admin": False,
    # NEW: Tier information
    "tier_slug": tier_info[0] if tier_info else "member",
    "tier_level": tier_info[1] if tier_info else 1,
    "subscription_status": tier_info[2] if tier_info else "active"
}
```

#### B. Login Endpoint (my_os.py ~line 3158)

```python
# Same pattern as signup - add tier query before JWT generation
```

#### C. Profile Update Endpoint (my_os.py ~line 2112)

```python
# When generating new JWT after profile update, include current tier
```

---

## Frontend Implementation

### 1. TypeScript Types

**File:** `cirkelline-ui/src/types/subscription.ts` (new file)

```typescript
export interface UserTier {
  id: number
  slug: 'member' | 'pro' | 'business' | 'elite' | 'family'
  name: string
  description: string
  tier_level: number
  monthly_price_cents: number
  annual_price_cents: number
  is_active: boolean
  features: Record<string, any>
}

export interface UserSubscription {
  id: string
  tier: {
    slug: string
    name: string
    level: number
    description: string
    monthly_price_cents: number
    annual_price_cents: number
  }
  billing_cycle: 'monthly' | 'annual'
  status: 'active' | 'cancelled' | 'expired' | 'pending'
  started_at: string
  current_period_start: string
  current_period_end: string | null
  cancelled_at: string | null
  ends_at: string | null
}

export interface SubscriptionHistory {
  id: string
  action: 'created' | 'upgraded' | 'downgraded' | 'cancelled' | 'renewed' | 'expired' | 'reactivated' | 'admin_assigned'
  from_tier_slug: string | null
  to_tier_slug: string | null
  changed_by_user_id: string | null
  is_admin_action: boolean
  reason: string | null
  created_at: string
}

export interface SubscriptionStats {
  total_subscriptions: number
  active_subscriptions: number
  by_tier: {
    member: number
    pro: number
    business: number
    elite: number
    family: number
  }
  by_billing_cycle: {
    monthly: number
    annual: number
  }
}
```

### 2. Update AuthContext

**File:** `cirkelline-ui/src/contexts/AuthContext.tsx`

```typescript
// Update User interface
interface User {
  user_id: string