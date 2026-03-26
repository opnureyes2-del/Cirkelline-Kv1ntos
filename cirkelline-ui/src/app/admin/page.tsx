'use client'

import {
  Users,
  Shield,
  Activity as ActivityIcon,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Globe,
  UserCheck,
  Clock,
  MessageSquare,
  Brain,
  BookOpen,
  Workflow,
  BarChart3,
  RefreshCw,
  ChevronRight,
  TrendingUp,
  CreditCard
} from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import type { ActivityLogStats, AdminStats } from '@/types/os'

export default function AdminOverviewPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  // Comprehensive admin stats from /api/admin/stats
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null)

  // Activity stats from /api/admin/activity
  const [activityStats, setActivityStats] = useState<ActivityLogStats>({
    total_logs: 0,
    successful_actions: 0,
    failed_actions: 0,
    admin_actions: 0,
    avg_duration_ms: 0,
    unique_users: 0,
    logs_last_24h: 0,
    failed_logins_last_hour: 0,
    action_breakdown: []
  })

  // Workflow stats
  const [workflowStats, setWorkflowStats] = useState<{
    total_runs: number
    runs_today: number
    success_rate: number
  } | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // Fetch all stats
  const fetchAllStats = useCallback(async () => {
    try {
      setError(null)
      const token = localStorage.getItem('token')
      if (!token) {
        setError('Not authenticated')
        setLoading(false)
        return
      }

      const headers = { 'Authorization': `Bearer ${token}` }

      // Fetch all endpoints in parallel
      const [statsRes, activityRes, workflowRes] = await Promise.allSettled([
        fetch(`${apiUrl}/api/admin/stats`, { headers }),
        fetch(`${apiUrl}/api/admin/activity?page=1&limit=1`, { headers }),
        fetch(`${apiUrl}/api/admin/workflows/stats`, { headers })
      ])

      // Process admin stats
      if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
        const data = await statsRes.value.json()
        setAdminStats(data.data || null)
      }

      // Process activity stats
      if (activityRes.status === 'fulfilled' && activityRes.value.ok) {
        const data = await activityRes.value.json()
        setActivityStats(data.stats || activityStats)
      }

      // Process workflow stats
      if (workflowRes.status === 'fulfilled' && workflowRes.value.ok) {
        const data = await workflowRes.value.json()
        setWorkflowStats(data.stats || null)
      }

      setLastRefresh(new Date())
    } catch (err) {
      console.error('Failed to fetch admin stats:', err)
      setError('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [apiUrl])

  useEffect(() => {
    fetchAllStats()
  }, [fetchAllStats])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAllStats()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchAllStats])

  // Calculate success rate
  const successRate = activityStats.total_logs > 0
    ? Math.round((activityStats.successful_actions / activityStats.total_logs) * 100)
    : 0

  // Format timestamp
  const formatDate = (timestamp: number | null) => {
    if (!timestamp) return 'Never'
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Format relative time
  const formatRelativeTime = (timestamp: number | null) => {
    if (!timestamp) return 'Never'
    const now = Date.now()
    const diff = now - (timestamp * 1000)
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  // Quick nav items for mobile grid
  const quickNavItems = [
    { label: 'Users', icon: Users, href: '/admin/users', color: 'text-blue-500' },
    { label: 'Activity', icon: ActivityIcon, href: '/admin/activity', color: 'text-green-500' },
    { label: 'Workflows', icon: Workflow, href: '/admin/workflows', color: 'text-purple-500' },
    { label: 'Metrics', icon: BarChart3, href: '/admin/metrics', color: 'text-amber-500' },
    { label: 'Feedback', icon: MessageSquare, href: '/admin/feedback', color: 'text-pink-500' },
    { label: 'Subscriptions', icon: CreditCard, href: '/admin/subscriptions', color: 'text-emerald-500' },
  ]

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 mb-2">
              <Shield className="w-7 h-7 sm:w-8 sm:h-8 text-accent" />
              <h1 className="text-2xl sm:text-3xl font-bold text-light-text dark:text-dark-text font-heading">
                Admin Dashboard
              </h1>
            </div>
            <button
              onClick={() => { setLoading(true); fetchAllStats(); }}
              className="flex items-center gap-2 min-h-[44px] min-w-[44px] px-3 sm:px-4 py-2 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline text-sm text-light-text dark:text-dark-text">Refresh</span>
            </button>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            System overview and management
            {lastRefresh && (
              <span className="ml-2 text-xs">
                — Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>

        {/* Error State */}
        {error && !loading && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && !adminStats && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Quick Navigation (mobile-first grid) */}
        <div className="mb-6">
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 sm:gap-3">
            {quickNavItems.map((item) => (
              <button
                key={item.label}
                onClick={() => router.push(item.href)}
                className="flex flex-col items-center gap-1.5 p-3 sm:p-4 min-h-[72px] bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary hover:border-accent active:scale-95 transition-all"
              >
                <item.icon className={`w-5 h-5 sm:w-6 sm:h-6 ${item.color}`} />
                <span className="text-xs font-medium text-light-text dark:text-dark-text">{item.label}</span>
              </button>
            ))}
          </div>
        </div>

        {(adminStats || !loading) && (
          <>
            {/* User Statistics */}
            <div className="mb-6">
              <button
                onClick={() => router.push('/admin/users')}
                className="w-full text-left mb-3"
              >
                <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading flex items-center gap-2 group">
                  <Users className="w-5 h-5" />
                  Users
                  <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
                </h2>
              </button>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Total</p>
                      <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">
                        {adminStats?.users.total ?? 0}
                      </p>
                    </div>
                    <Users className="w-7 h-7 text-light-text-secondary dark:text-dark-text-secondary" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Online</p>
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400 font-heading mt-1">
                        {adminStats?.users.online ?? 0}
                      </p>
                    </div>
                    <Globe className="w-7 h-7 text-green-600 dark:text-green-400" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">New (7d)</p>
                      <p className="text-2xl font-bold text-accent font-heading mt-1">
                        {adminStats?.users.new_week ?? 0}
                      </p>
                    </div>
                    <UserCheck className="w-7 h-7 text-accent" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Admins</p>
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 font-heading mt-1">
                        {adminStats?.users.admins ?? 0}
                      </p>
                    </div>
                    <Shield className="w-7 h-7 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* Sessions & Memories */}
            <div className="mb-6">
              <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading mb-3 flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Sessions &amp; Memories
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Total Sessions</p>
                  <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">
                    {adminStats?.sessions.total ?? 0}
                  </p>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Today</p>
                  <p className="text-2xl font-bold text-accent font-heading mt-1">
                    {adminStats?.sessions.today ?? 0}
                  </p>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">This Week</p>
                  <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">
                    {adminStats?.sessions.week ?? 0}
                  </p>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Total Memories</p>
                  <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 font-heading mt-1">
                    {adminStats?.memories.total ?? 0}
                  </p>
                </div>
              </div>
            </div>

            {/* Activity Statistics */}
            <div className="mb-6">
              <button
                onClick={() => router.push('/admin/activity')}
                className="w-full text-left mb-3"
              >
                <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading flex items-center gap-2 group">
                  <ActivityIcon className="w-5 h-5" />
                  Activity
                  <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
                </h2>
              </button>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Success Rate</p>
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400 font-heading mt-1">{successRate}%</p>
                    </div>
                    <CheckCircle className="w-7 h-7 text-green-600 dark:text-green-400" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Avg Response</p>
                      <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">{Math.round(activityStats.avg_duration_ms)}ms</p>
                    </div>
                    <Clock className="w-7 h-7 text-light-text-secondary dark:text-dark-text-secondary" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Failed Logins (1h)</p>
                      <p className={`text-2xl font-bold font-heading mt-1 ${activityStats.failed_logins_last_hour > 0 ? 'text-red-600 dark:text-red-400' : 'text-light-text dark:text-dark-text'}`}>
                        {activityStats.failed_logins_last_hour}
                      </p>
                    </div>
                    <AlertTriangle className={`w-7 h-7 ${activityStats.failed_logins_last_hour > 0 ? 'text-red-600 dark:text-red-400' : 'text-light-text-secondary dark:text-dark-text-secondary'}`} />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Failed Actions</p>
                      <p className={`text-2xl font-bold font-heading mt-1 ${activityStats.failed_actions > 0 ? 'text-red-600 dark:text-red-400' : 'text-light-text dark:text-dark-text'}`}>
                        {activityStats.failed_actions.toLocaleString()}
                      </p>
                    </div>
                    <XCircle className={`w-7 h-7 ${activityStats.failed_actions > 0 ? 'text-red-600 dark:text-red-400' : 'text-light-text-secondary dark:text-dark-text-secondary'}`} />
                  </div>
                </div>
              </div>
            </div>

            {/* Feedback Summary */}
            {adminStats?.feedback && (
              <div className="mb-6">
                <button
                  onClick={() => router.push('/admin/feedback')}
                  className="w-full text-left mb-3"
                >
                  <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading flex items-center gap-2 group">
                    <MessageSquare className="w-5 h-5" />
                    Feedback
                    {adminStats.feedback.unread > 0 && (
                      <span className="px-2 py-0.5 text-xs rounded-full bg-accent/20 text-accent font-medium">
                        {adminStats.feedback.unread} unread
                      </span>
                    )}
                    <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
                  </h2>
                </button>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Total</p>
                    <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">
                      {adminStats.feedback.total}
                    </p>
                  </div>
                  <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Unread</p>
                    <p className={`text-2xl font-bold font-heading mt-1 ${adminStats.feedback.unread > 0 ? 'text-accent' : 'text-light-text dark:text-dark-text'}`}>
                      {adminStats.feedback.unread}
                    </p>
                  </div>
                  <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Positive</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400 font-heading mt-1">
                      {adminStats.feedback.positive}
                    </p>
                  </div>
                  <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Negative</p>
                    <p className={`text-2xl font-bold font-heading mt-1 ${adminStats.feedback.negative > 0 ? 'text-red-600 dark:text-red-400' : 'text-light-text dark:text-dark-text'}`}>
                      {adminStats.feedback.negative}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Workflows Quick Status */}
            <div className="mb-6">
              <button
                onClick={() => router.push('/admin/workflows')}
                className="w-full text-left mb-3"
              >
                <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading flex items-center gap-2 group">
                  <Workflow className="w-5 h-5" />
                  Workflows
                  <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
                </h2>
              </button>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Memory Optimization Card */}
                <button
                  onClick={() => router.push('/admin/workflows/memory')}
                  className="text-left bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 hover:border-accent active:scale-[0.98] transition-all min-h-[72px]"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0">
                      <Brain className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-light-text dark:text-dark-text">Memory Optimization</p>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary truncate">
                        {workflowStats ? `${workflowStats.total_runs} runs, ${workflowStats.runs_today} today` : 'Loading...'}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary flex-shrink-0" />
                  </div>
                  {workflowStats && (
                    <div className="flex items-center gap-3 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      <span className="flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        {workflowStats.success_rate}% success
                      </span>
                    </div>
                  )}
                </button>

                {/* Daily Journals Card */}
                <button
                  onClick={() => router.push('/admin/workflows/journals')}
                  className="text-left bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 hover:border-accent active:scale-[0.98] transition-all min-h-[72px]"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-light-text dark:text-dark-text">Daily Journals</p>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary truncate">
                        Generate daily summaries
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary flex-shrink-0" />
                  </div>
                </button>
              </div>
            </div>

            {/* Recent Users */}
            {adminStats?.recent_users && adminStats.recent_users.length > 0 && (
              <div className="mb-6">
                <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading mb-3 flex items-center gap-2">
                  <UserCheck className="w-5 h-5" />
                  Recent Signups
                </h2>
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary divide-y divide-border-secondary">
                  {adminStats.recent_users.map((user) => (
                    <button
                      key={user.id}
                      onClick={() => router.push('/admin/users')}
                      className="w-full text-left p-4 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors min-h-[56px] flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                          {user.email}
                        </p>
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                          {user.display_name || 'No display name'} — {formatRelativeTime(user.created_at)}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Action Breakdown (top 6 actions) */}
            {activityStats.action_breakdown.length > 0 && (
              <div className="mb-6">
                <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading mb-3 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Top Actions
                </h2>
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="space-y-3">
                    {activityStats.action_breakdown.slice(0, 6).map((item) => {
                      const maxCount = activityStats.action_breakdown[0]?.count || 1
                      const width = Math.max((item.count / maxCount) * 100, 4)
                      return (
                        <div key={item.action}>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-light-text dark:text-dark-text">
                              {item.action.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                            </span>
                            <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary tabular-nums">
                              {item.count.toLocaleString()}
                            </span>
                          </div>
                          <div className="h-2 bg-light-bg dark:bg-dark-bg rounded-full overflow-hidden">
                            <div
                              className="h-full bg-accent rounded-full transition-all duration-500"
                              style={{ width: `${width}%` }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
