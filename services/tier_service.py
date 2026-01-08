"""
TierService - Business logic for user tier and subscription management.

Handles all operations related to user tiers, subscriptions, billing cycles,
upgrades, downgrades, and subscription history.
"""

from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import uuid
import json
import logging

logger = logging.getLogger(__name__)


class TierService:
    """
    Service layer for user tier and subscription management.
    Handles all business logic for tiers, subscriptions, and billing.
    """
    
    @staticmethod
    async def get_all_tiers(engine) -> List[Dict]:
        """
        Get all available tiers with pricing information.
        
        Args:
            engine: SQLAlchemy engine
            
        Returns:
            List of tier dictionaries
        """
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
        """
        Get user's active subscription with tier details.
        
        Args:
            engine: SQLAlchemy engine
            user_id: User UUID
            
        Returns:
            Subscription dictionary or None if not found
        """
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
        
        Args:
            engine: SQLAlchemy engine
            user_id: User UUID
            tier_slug: Tier identifier (member, pro, business, elite, family)
            billing_cycle: 'monthly' or 'annual'
            admin_id: Admin user ID if created by admin
            reason: Reason for subscription creation
            
        Returns:
            Tuple of (subscription_id, subscription_data)
            
        Raises:
            ValueError: If tier is invalid or inactive
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
            
            logger.info(f"Created subscription {subscription_id} for user {user_id} with tier {tier_slug}")
            
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
        
        Args:
            engine: SQLAlchemy engine
            user_id: User UUID
            new_tier_slug: New tier to upgrade to
            billing_cycle: 'monthly' or 'annual'
            admin_id: Admin user ID if upgraded by admin
            
        Returns:
            Dictionary with upgrade details
            
        Raises:
            ValueError: If no active subscription or not an upgrade
        """
        with Session(engine) as session:
            # Get current subscription
            current_sub = session.execute(
                text("""
                    SELECT s.id, s.tier_slug, t1.tier_level as current_level, t2.tier_level as new_level
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
            
            logger.info(f"Upgraded user {user_id} from {old_tier} to {new_tier_slug}")
            
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
        
        Args:
            engine: SQLAlchemy engine
            user_id: User UUID
            new_tier_slug: New tier to downgrade to
            reason: Reason for downgrade
            
        Returns:
            Dictionary with downgrade details
            
        Raises:
            ValueError: If no active subscription or not a downgrade
        """
        with Session(engine) as session:
            # Get current subscription
            current_sub = session.execute(
                text("""
                    SELECT s.id, s.tier_slug, s.current_period_end,
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
            
            logger.info(f"Scheduled downgrade for user {user_id} from {old_tier} to {new_tier_slug} on {effective_date}")
            
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
        
        Args:
            engine: SQLAlchemy engine
            user_id: User UUID
            reason: Reason for cancellation
            
        Returns:
            Dictionary with cancellation details
            
        Raises:
            ValueError: If no active subscription or trying to cancel free tier
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
            
            logger.info(f"Cancelled subscription {subscription_id} for user {user_id}")
            
            return {
                "cancelled": True,
                "remains_active_until": ends_at.isoformat(),
                "reverts_to_tier": "member"
            }
    
    @staticmethod
    async def admin_change_tier(
        engine,
        user_id: str,
        new_tier_slug: str,
        billing_cycle: str = 'monthly',
        admin_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Admin-only method to change user's tier to ANY tier (up, down, or same level).
        Bypasses upgrade/downgrade restrictions.
        
        Args:
            engine: SQLAlchemy engine
            user_id: User UUID
            new_tier_slug: New tier to assign
            billing_cycle: 'monthly' or 'annual'
            admin_id: Admin user ID performing the action
            reason: Reason for tier change
            
        Returns:
            Dictionary with tier change details
            
        Raises:
            ValueError: If tier is invalid
        """
        with Session(engine) as session:
            # Verify tier exists and is active
            new_tier = session.execute(
                text("SELECT tier_level FROM user_tiers WHERE slug = :slug AND is_active = true"),
                {"slug": new_tier_slug}
            ).fetchone()
            
            if not new_tier:
                raise ValueError(f"Invalid or inactive tier: {new_tier_slug}")
            
            new_level = new_tier[0]
            
            # Get current subscription
            current_sub = session.execute(
                text("""
                    SELECT s.id, s.tier_slug, t.tier_level
                    FROM user_subscriptions s
                    JOIN user_tiers t ON s.tier_slug = t.slug
                    WHERE s.user_id = :user_id AND s.status = 'active'
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if not current_sub:
                # No subscription - create new one
                sub_id, result = await TierService.create_subscription(
                    engine, user_id, new_tier_slug, billing_cycle,
                    admin_id=admin_id, reason=reason or "Admin tier assignment"
                )
                return {
                    "subscription_id": sub_id,
                    "old_tier": None,
                    "new_tier": new_tier_slug,
                    "action": "created",
                    "effective_immediately": True
                }
            
            subscription_id = str(current_sub[0])
            old_tier = current_sub[1]
            old_level = current_sub[2]
            
            # Determine action type
            if new_level > old_level:
                action = "upgraded"
            elif new_level < old_level:
                action = "downgraded"
            else:
                action = "tier_changed"  # Same level, different tier
            
            # Calculate new period end (only for paid tiers)
            period_end = None
            if new_tier_slug != 'member':
                if billing_cycle == 'monthly':
                    period_end = datetime.now() + timedelta(days=30)
                else:
                    period_end = datetime.now() + timedelta(days=365)
            
            # Update subscription immediately (admin override)
            session.execute(
                text("""
                    UPDATE user_subscriptions
                    SET tier_slug = :new_tier,
                        billing_cycle = :billing_cycle,
                        current_period_start = CURRENT_TIMESTAMP,
                        current_period_end = :period_end,
                        cancelled_at = NULL,
                        ends_at = NULL,
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
                    (:user_id, :subscription_id, :action, :from_tier, :to_tier,
                     :changed_by, true, :reason)
                """),
                {
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "action": action,
                    "from_tier": old_tier,
                    "to_tier": new_tier_slug,
                    "changed_by": admin_id or user_id,
                    "reason": reason or f"Admin changed tier from {old_tier} to {new_tier_slug}"
                }
            )
            
            session.commit()
            
            logger.info(f"Admin changed user {user_id} tier from {old_tier} to {new_tier_slug}")
            
            return {
                "subscription_id": subscription_id,
                "old_tier": old_tier,
                "new_tier": new_tier_slug,
                "action": action,
                "effective_immediately": True,
                "next_billing": period_end.isoformat() if period_end else None
            }
    
    @staticmethod
    async def process_expired_subscriptions(engine) -> int:
        """
        Background job: Process subscriptions that have ended.
        Returns count of processed subscriptions.
        
        Args:
            engine: SQLAlchemy engine
            
        Returns:
            Count of processed subscriptions
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
            
            if count > 0:
                logger.info(f"Processed {count} expired subscriptions")
            
            return count