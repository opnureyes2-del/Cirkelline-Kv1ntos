/**
 * User Tier & Subscription System Types
 * 
 * Defines TypeScript interfaces for tier and subscription data
 * used throughout the Cirkelline frontend.
 */

export type TierSlug = 'member' | 'pro' | 'business' | 'elite' | 'family'
export type BillingCycle = 'monthly' | 'annual'
export type SubscriptionStatus = 'active' | 'cancelled' | 'expired' | 'pending'
export type SubscriptionAction = 
  | 'created' 
  | 'upgraded' 
  | 'downgraded' 
  | 'cancelled' 
  | 'renewed' 
  | 'expired' 
  | 'reactivated' 
  | 'admin_assigned'

/**
 * User Tier Definition
 * Master tier data with pricing and features
 */
export interface UserTier {
  id: number
  slug: TierSlug
  name: string
  description: string
  tier_level: number
  monthly_price_cents: number | null
  annual_price_cents: number | null
  is_active: boolean
  features: Record<string, unknown>
}

/**
 * User Subscription
 * Current active subscription for a user
 */
export interface UserSubscription {
  id: string
  tier: {
    slug: TierSlug
    name: string
    level: number
    description: string
    monthly_price_cents: number | null
    annual_price_cents: number | null
  }
  billing_cycle: BillingCycle
  status: SubscriptionStatus
  started_at: string
  current_period_start: string
  current_period_end: string | null
  cancelled_at: string | null
  ends_at: string | null
}

/**
 * Subscription History Entry
 * Audit trail of subscription changes
 */
export interface SubscriptionHistory {
  id: string
  action: SubscriptionAction
  from_tier_slug: TierSlug | null
  to_tier_slug: TierSlug | null
  changed_by_user_id: string | null
  is_admin_action: boolean
  reason: string | null
  created_at: string
}

/**
 * Subscription Statistics (Admin)
 * Aggregate stats for admin dashboard
 */
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

/**
 * Subscription List Item (Admin)
 * Used in admin subscription management list
 */
export interface SubscriptionListItem {
  id: string
  user_id: string
  user_email: string
  user_display_name: string
  tier_slug: TierSlug
  tier_name: string
  tier_level: number
  billing_cycle: BillingCycle
  status: SubscriptionStatus
  started_at: string
  current_period_end: string | null
  cancelled_at: string | null
  payment_provider: string | null
}

/**
 * Tier Upgrade Request
 * Payload for requesting tier upgrade
 */
export interface TierUpgradeRequest {
  tier_slug: TierSlug
  billing_cycle: BillingCycle
}

/**
 * Tier Downgrade Request
 * Payload for requesting tier downgrade
 */
export interface TierDowngradeRequest {
  tier_slug: TierSlug
  reason?: string
}

/**
 * Subscription Cancel Request
 * Payload for cancelling subscription
 */
export interface SubscriptionCancelRequest {
  reason?: string
}

/**
 * Admin Tier Assignment Request
 * Payload for admin assigning tier to user
 */
export interface AdminTierAssignmentRequest {
  tier_slug: TierSlug
  billing_cycle: BillingCycle
  reason?: string
}

/**
 * API Response: Get User Subscription
 */
export interface GetUserSubscriptionResponse {
  success: boolean
  subscription: UserSubscription | null
  available_tiers: UserTier[]
  available_upgrades: UserTier[]
  can_upgrade: boolean
}

/**
 * API Response: Get All Tiers
 */
export interface GetTiersResponse {
  success: boolean
  tiers: UserTier[]
}

/**
 * API Response: Upgrade Subscription
 */
export interface UpgradeSubscriptionResponse {
  success: boolean
  message: string
  upgrade: {
    subscription_id: string
    old_tier: TierSlug
    new_tier: TierSlug
    effective_immediately: boolean
    next_billing: string
  }
}

/**
 * API Response: Downgrade Subscription
 */
export interface DowngradeSubscriptionResponse {
  success: boolean
  message: string
  downgrade: {
    subscription_id: string
    old_tier: TierSlug
    new_tier: TierSlug
    effective_date: string
    remains_active_until: string
  }
}

/**
 * API Response: Cancel Subscription
 */
export interface CancelSubscriptionResponse {
  success: boolean
  message: string
  cancellation: {
    cancelled: boolean
    remains_active_until: string
    reverts_to_tier: TierSlug
  }
}

/**
 * API Response: List Subscriptions (Admin)
 */
export interface ListSubscriptionsResponse {
  success: boolean
  data: SubscriptionListItem[]
  total: number
  page: number
  limit: number
}

/**
 * API Response: Get Subscription Stats (Admin)
 */
export interface GetSubscriptionStatsResponse {
  success: boolean
  stats: SubscriptionStats
}

/**
 * Tier Badge Props
 * For displaying tier badges in UI
 */
export interface TierBadgeProps {
  tier: TierSlug
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
}

/**
 * Subscription Card Props
 * For displaying subscription details
 */
export interface SubscriptionCardProps {
  subscription: UserSubscription
  onUpgrade?: () => void
  onManage?: () => void
}