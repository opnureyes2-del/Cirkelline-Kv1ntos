'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { motion } from 'framer-motion'
import { Users, TrendingUp, DollarSign, Search } from 'lucide-react'
import { TierBadge } from '@/components/TierBadge'
import type { SubscriptionListItem, SubscriptionStats, TierSlug } from '@/types/subscription'
import { toast } from 'sonner'

export default function AdminSubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionListItem[]>([])
  const [stats, setStats] = useState<SubscriptionStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [tierFilter, setTierFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [editingUserId, setEditingUserId] = useState<string | null>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const limit = 20

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setEditingUserId(null)
      }
    }

    if (editingUserId) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [editingUserId])

  const fetchSubscriptions = useCallback(async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        tier_filter: tierFilter,
        status_filter: statusFilter,
      })

      // Add search if present
      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim())
      }

      const response = await fetch(`${apiUrl}/api/admin/subscriptions?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSubscriptions(data.data)
        setTotal(data.total)
      }
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error)
      toast.error('Failed to load subscriptions')
    } finally {
      setLoading(false)
    }
  }, [page, tierFilter, statusFilter, searchTerm])

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/admin/subscription-stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data.stats)
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }, [])

  useEffect(() => {
    fetchSubscriptions()
    fetchStats()
  }, [fetchSubscriptions, fetchStats])

  const handleAssignTier = async (userId: string, tierSlug: TierSlug) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(
        `${apiUrl}/api/admin/subscriptions/${userId}/assign-tier`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            tier_slug: tierSlug,
            billing_cycle: 'monthly',
            reason: 'Admin manual assignment',
          }),
        }
      )

      if (response.ok) {
        toast.success(`Tier ${tierSlug} assigned successfully`)
        fetchSubscriptions()
        fetchStats()
      } else {
        throw new Error('Failed to assign tier')
      }
    } catch (error) {
      console.error('Failed to assign tier:', error)
      toast.error('Failed to assign tier')
    }
  }

  const paidUsers = stats ? stats.by_tier.pro + stats.by_tier.business + stats.by_tier.elite + stats.by_tier.family : 0

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
            Subscription Management
          </h1>
          <p className="mt-2 text-light-text-secondary dark:text-dark-text-secondary">
            Manage user subscriptions and tier assignments
          </p>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
            >
              <div className="flex items-center gap-3">
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    Total Subscriptions
                  </p>
                  <p className="text-2xl font-bold text-light-text dark:text-dark-text">
                    {stats.total_subscriptions}
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
            >
              <div className="flex items-center gap-3">
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    Active Subscriptions
                  </p>
                  <p className="text-2xl font-bold text-light-text dark:text-dark-text">
                    {stats.active_subscriptions}
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
            >
              <div className="flex items-center gap-3">
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <DollarSign className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    Paid Users
                  </p>
                  <p className="text-2xl font-bold text-light-text dark:text-dark-text">
                    {paidUsers}
                  </p>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
            >
              <div className="flex items-center gap-3">
                <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <Users className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    Free Users
                  </p>
                  <p className="text-2xl font-bold text-light-text dark:text-dark-text">
                    {stats.by_tier.member}
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                Search Users
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by email..."
                  className="w-full pl-10 pr-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent"
                />
              </div>
            </div>

            {/* Tier Filter */}
            <div>
              <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                Filter by Tier
              </label>
              <select
                value={tierFilter}
                onChange={(e) => setTierFilter(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent"
              >
                <option value="all">All Tiers</option>
                <option value="member">Member</option>
                <option value="pro">Pro</option>
                <option value="business">Business</option>
                <option value="elite">Elite</option>
                <option value="family">Family</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                Filter by Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="cancelled">Cancelled</option>
                <option value="expired">Expired</option>
              </select>
            </div>
          </div>
        </div>

        {/* Subscriptions Table */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-light-bg dark:bg-dark-bg border-b border-border-primary">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                    Tier (Click to Change)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                    Billing
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                    Started
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-primary">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center">
                      <div className="flex items-center justify-center">
                        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                      </div>
                    </td>
                  </tr>
                ) : subscriptions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-light-text-secondary dark:text-dark-text-secondary">
                      No subscriptions found
                    </td>
                  </tr>
                ) : (
                  subscriptions.map((sub) => (
                    <tr
                      key={sub.id}
                      className="hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-light-text dark:text-dark-text">
                            {sub.user_display_name}
                          </p>
                          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                            {sub.user_email}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="relative" ref={editingUserId === sub.user_id ? dropdownRef : null}>
                          <button
                            onClick={() => setEditingUserId(editingUserId === sub.user_id ? null : sub.user_id)}
                            className="hover:scale-110 active:scale-95 transition-all duration-200"
                            title="✨ Click to change tier"
                          >
                            <TierBadge tier={sub.tier_slug} size="sm" />
                          </button>
                          
                          {editingUserId === sub.user_id && (
                            <div className="absolute z-50 left-0 top-full mt-2 flex flex-col gap-2 p-2 bg-light-surface/95 dark:bg-dark-surface/95 backdrop-blur-sm rounded-lg shadow-lg">
                              {(['member', 'pro', 'business', 'elite', 'family'] as TierSlug[]).map((tier) => (
                                tier !== sub.tier_slug && (
                                  <button
                                    key={tier}
                                    onClick={() => {
                                      handleAssignTier(sub.user_id, tier)
                                      setEditingUserId(null)
                                    }}
                                    className="hover:scale-105 active:scale-95 transition-all"
                                    title={`Change to ${tier}`}
                                  >
                                    <TierBadge tier={tier} size="sm" />
                                  </button>
                                )
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-light-text dark:text-dark-text capitalize">
                          {sub.billing_cycle}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            sub.status === 'active'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                              : sub.status === 'cancelled'
                              ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                          }`}
                        >
                          {sub.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        {new Date(sub.started_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {total > limit && (
            <div className="px-6 py-4 bg-light-bg dark:bg-dark-bg border-t border-border-primary flex items-center justify-between">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of {total} subscriptions
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-lg bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text border border-border-primary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * limit >= total}
                  className="px-4 py-2 rounded-lg bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text border border-border-primary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Tier Breakdown */}
        {stats && (
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 font-heading">
              Tier Distribution
            </h2>
            <div className="space-y-3">
              {Object.entries(stats.by_tier).map(([tier, count]) => (
                <div key={tier} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <TierBadge tier={tier as TierSlug} size="sm" />
                    <span className="text-sm text-light-text dark:text-dark-text">
                      {tier.charAt(0).toUpperCase() + tier.slice(1)}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-light-text dark:text-dark-text">
                    {count} users
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}