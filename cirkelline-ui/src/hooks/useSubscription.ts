/**
 * useSubscription Hook
 * 
 * Fetches and manages user subscription data
 */

import { useState, useEffect, useCallback } from 'react'
import type { 
  UserSubscription, 
  UserTier, 
  GetUserSubscriptionResponse 
} from '@/types/subscription'

interface UseSubscriptionResult {
  subscription: UserSubscription | null
  availableTiers: UserTier[]
  availableUpgrades: UserTier[]
  canUpgrade: boolean
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useSubscription(): UseSubscriptionResult {
  const [subscription, setSubscription] = useState<UserSubscription | null>(null)
  const [availableTiers, setAvailableTiers] = useState<UserTier[]>([])
  const [availableUpgrades, setAvailableUpgrades] = useState<UserTier[]>([])
  const [canUpgrade, setCanUpgrade] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSubscription = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setIsLoading(false)
      return
    }

    try {
      setIsLoading(true)
      setError(null)

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/user/subscription`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch subscription: ${response.statusText}`)
      }

      const data: GetUserSubscriptionResponse = await response.json()

      setSubscription(data.subscription)
      setAvailableTiers(data.available_tiers)
      setAvailableUpgrades(data.available_upgrades)
      setCanUpgrade(data.can_upgrade)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription')
      console.error('Error fetching subscription:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSubscription()
  }, [fetchSubscription])

  return {
    subscription,
    availableTiers,
    availableUpgrades,
    canUpgrade,
    isLoading,
    error,
    refetch: fetchSubscription,
  }
}