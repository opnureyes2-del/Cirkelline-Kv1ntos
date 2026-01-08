'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  RefreshCw,
  X,
  AlertTriangle,
  Loader2,
  Search,
  ArrowUpDown,
  Zap,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  History,
  Trash2,
  GitMerge,
  TrendingDown,
  Activity,
  ArrowLeft,
  Brain
} from 'lucide-react'

interface WorkflowRun {
  run_id: string
  workflow_name: string
  user_id: string
  user_email: string | null
  archived_count: number
  current_count: number
  started_at: string | null
  completed_at: string | null
  status: string
}

interface WorkflowStats {
  total_runs: number
  runs_today: number
  total_deleted: number
  total_merged: number
  avg_reduction: number
  success_rate: number
  current_memories: number
  users_with_memories: number
}

interface RunHistoryItem {
  run_id: string
  status: string
  started_at: string | null
  completed_at: string | null
  before_count: number | null
  after_count: number | null
  reduction_percent: number | null
}

interface UserStats {
  user_id: string
  email: string
  memory_count: number
  topic_count: number
  last_optimization: string | null
  // New fields for intelligent triggering
  total_runs: number
  post_optimization_count: number | null
  growth: number | null
  should_trigger: boolean
  run_history: RunHistoryItem[]
}

interface ActiveRun {
  run_id: string
  user_id: string
  step: number
  current_step: string  // Backend uses "current_step"
  total_steps: number
  progress: number
  started_at: string
  stats: {
    decisions_made?: number
    delete_count?: number
    merge_count?: number
    keep_count?: number
  }
}

interface WorkflowConfig {
  memory_optimization: {
    enabled: boolean
    threshold: number
    cooldown_hours: number
  }
}

interface Memory {
  memory_id: string
  memory: string
  topics: string[]
  created_at: string | null
  updated_at?: string | null
}

interface Changes {
  summary: {
    before: number
    after: number
    net_change: number
  }
  deleted: Memory[]
  new_or_merged: Memory[]
  topics: {
    removed: string[]
    added: string[]
  }
}

interface RunDetails {
  run_id: string
  workflow_name: string
  user_id: string
  user_email: string | null
  status: string
  started_at: string | null
  completed_at: string | null
  stats: {
    memories_before: number
    memories_after: number
    reduction_percent: number
    topics_before: number
    topics_after: number
    topics_removed: number
  }
  changes?: Changes
  before: {
    memories: Memory[]
    topics: string[]
  }
  after: {
    memories: Memory[]
    topics: string[]
  }
}

export default function MemoryWorkflowPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<WorkflowStats | null>(null)
  const [runs, setRuns] = useState<WorkflowRun[]>([])
  const [triggerLoading, setTriggerLoading] = useState<string | null>(null)
  const [, setTriggerResult] = useState<{success: boolean, message: string, runId?: string} | null>(null)

  // New state for enhanced features
  const [userStats, setUserStats] = useState<UserStats[]>([])
  const [activeRuns, setActiveRuns] = useState<ActiveRun[]>([])
  const [, setConfig] = useState<WorkflowConfig | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'memory_count' | 'topic_count' | 'last_optimization' | 'growth' | 'total_runs'>('memory_count')
  const [sortDesc, setSortDesc] = useState(true)
  const [expandedUsers, setExpandedUsers] = useState<Set<string>>(new Set())
  const [expandedActiveRuns, setExpandedActiveRuns] = useState<Set<string>>(new Set())
  const [growthThreshold, setGrowthThreshold] = useState(100)

  // Modal state for run details
  const [selectedRun, setSelectedRun] = useState<RunDetails | null>(null)
  const [modalLoading, setModalLoading] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      // Fetch stats, runs, user stats, active runs, and config in parallel
      // Filter by workflow_name to only show Memory Optimization data
      const [statsRes, runsRes, userStatsRes, activeRes, configRes] = await Promise.all([
        fetch(`${apiUrl}/api/admin/workflows/stats?workflow_name=${encodeURIComponent('Memory Optimization')}`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/runs?limit=20`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/users-stats`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/active?workflow_name=${encodeURIComponent('Memory Optimization')}`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/config`, { headers: { 'Authorization': `Bearer ${token}` }})
      ])

      if (statsRes.ok) {
        const data = await statsRes.json()
        setStats(data.stats)
      }

      if (runsRes.ok) {
        const data = await runsRes.json()
        setRuns(data.runs)
      }

      if (userStatsRes.ok) {
        const data = await userStatsRes.json()
        setUserStats(data.users || [])
        if (data.growth_threshold) {
          setGrowthThreshold(data.growth_threshold)
        }
      }

      if (activeRes.ok) {
        const data = await activeRes.json()
        setActiveRuns(data.active_runs || [])
      }

      if (configRes.ok) {
        const data = await configRes.json()
        setConfig(data.config)
      }
    } catch (error) {
      console.error('Failed to fetch workflow data:', error)
    } finally {
      setLoading(false)
    }
  }, [apiUrl])

  // Fetch only active runs (for polling) - filtered to Memory Optimization only
  const fetchActiveRuns = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/active?workflow_name=${encodeURIComponent('Memory Optimization')}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        setActiveRuns(data.active_runs || [])
      }
    } catch (error) {
      console.error('Failed to fetch active runs:', error)
    }
  }, [apiUrl])

  useEffect(() => {
    setLoading(true)
    fetchData()
  }, [fetchData])

  // Poll for active runs when there are any
  useEffect(() => {
    if (activeRuns.length > 0) {
      const interval = setInterval(async () => {
        await fetchActiveRuns()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeRuns.length, fetchActiveRuns])

  // Detect when all active runs complete and refresh data
  const prevActiveRunsRef = useRef(activeRuns.length)
  useEffect(() => {
    // If we had active runs before but now have none, refresh all data
    if (prevActiveRunsRef.current > 0 && activeRuns.length === 0) {
      fetchData()
    }
    prevActiveRunsRef.current = activeRuns.length
  }, [activeRuns.length, fetchData])

  // Trigger workflow for user
  const triggerWorkflow = async (userId: string, userEmail: string) => {
    setTriggerLoading(userId)
    setTriggerResult(null)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const response = await fetch(
        `${apiUrl}/api/admin/workflows/memory-optimization/run?target_user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      const data = await response.json()

      if (data.success) {
        // Workflow started in background - immediately fetch active runs to show progress
        setTriggerResult({
          success: true,
          message: `Optimization started for ${userEmail}. Watch progress above!`,
          runId: data.run_id
        })

        // Immediately fetch active runs to show the new run
        await fetchActiveRuns()

        // If we don't see active runs yet (race condition), add a placeholder
        if (activeRuns.length === 0) {
          setActiveRuns([{
            run_id: data.run_id,
            user_id: userId,
            step: 1,
            current_step: 'Starting...',
            total_steps: 6,
            progress: 0,
            started_at: new Date().toISOString(),
            stats: {}
          }])
        }
      } else {
        setTriggerResult({
          success: false,
          message: data.error || 'Workflow failed to start'
        })
      }
    } catch {
      setTriggerResult({
        success: false,
        message: 'Failed to trigger workflow'
      })
    } finally {
      setTriggerLoading(null)
    }
  }

  // Fetch run details for modal
  const fetchRunDetails = async (runId: string) => {
    setModalLoading(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/runs/${runId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        setSelectedRun(data.run)
      }
    } catch (error) {
      console.error('Failed to fetch run details:', error)
    } finally {
      setModalLoading(false)
    }
  }

  // Format date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  // Toggle user expansion
  const toggleUserExpanded = (userId: string) => {
    setExpandedUsers(prev => {
      const next = new Set(prev)
      if (next.has(userId)) {
        next.delete(userId)
      } else {
        next.add(userId)
      }
      return next
    })
  }

  // Toggle active run expansion
  const toggleActiveRunExpanded = (runId: string) => {
    setExpandedActiveRuns(prev => {
      const next = new Set(prev)
      if (next.has(runId)) {
        next.delete(runId)
      } else {
        next.add(runId)
      }
      return next
    })
  }

  // Sort and filter users
  const filteredUsers = userStats
    .filter(u => u.email.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      let aVal: number = 0
      let bVal: number = 0

      if (sortBy === 'memory_count') {
        aVal = a.memory_count
        bVal = b.memory_count
      } else if (sortBy === 'topic_count') {
        aVal = a.topic_count
        bVal = b.topic_count
      } else if (sortBy === 'growth') {
        aVal = a.growth ?? -1
        bVal = b.growth ?? -1
      } else if (sortBy === 'total_runs') {
        aVal = a.total_runs
        bVal = b.total_runs
      } else {
        aVal = a.last_optimization ? new Date(a.last_optimization).getTime() : 0
        bVal = b.last_optimization ? new Date(b.last_optimization).getTime() : 0
      }

      return sortDesc ? bVal - aVal : aVal - bVal
    })

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/admin/workflows')}
            className="flex items-center gap-2 text-light-text-secondary dark:text-dark-text-secondary hover:text-accent mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Workflows
          </button>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                <Brain className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
                  Memory Optimization
                </h1>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
                  Automatic memory cleanup, merging, and optimization workflow
                </p>
              </div>
            </div>
            <button
              onClick={() => { setLoading(true); fetchData(); }}
              className="flex items-center gap-2 px-4 py-2 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && (
          <>
            {/* Stats Cards - Full Width */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
              <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Total Runs</p>
                    <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">
                      {stats?.total_runs || 0}
                    </p>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5">
                      {stats?.runs_today || 0} today
                    </p>
                  </div>
                  <Activity className="w-8 h-8 text-accent" />
                </div>
              </div>

              <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Deleted</p>
                    <p className="text-2xl font-bold text-red-600 dark:text-red-400 font-heading mt-1">
                      {stats?.total_deleted?.toLocaleString() || 0}
                    </p>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5">
                      memories removed
                    </p>
                  </div>
                  <Trash2 className="w-8 h-8 text-red-500" />
                </div>
              </div>

              <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Merged</p>
                    <p className="text-2xl font-bold text-amber-600 dark:text-amber-400 font-heading mt-1">
                      {stats?.total_merged?.toLocaleString() || 0}
                    </p>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5">
                      duplicates combined
                    </p>
                  </div>
                  <GitMerge className="w-8 h-8 text-amber-500" />
                </div>
              </div>

              <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Avg Reduction</p>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400 font-heading mt-1">
                      {stats?.avg_reduction || 0}%
                    </p>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-0.5">
                      per optimization
                    </p>
                  </div>
                  <TrendingDown className="w-8 h-8 text-green-500" />
                </div>
              </div>
            </div>


            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - 2/3 width */}
              <div className="lg:col-span-2 space-y-6">
                {/* Active Runs Section */}
                <div>
                  <h2 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading mb-3 flex items-center gap-2">
                    {activeRuns.length > 0 ? (
                      <Loader2 className="w-5 h-5 animate-spin text-accent" />
                    ) : (
                      <Play className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                    )}
                    Active Runs ({activeRuns.length})
                  </h2>
                  <div className="rounded-lg border overflow-hidden bg-light-surface dark:bg-dark-surface border-border-primary">
                    {activeRuns.length > 0 ? (
                      <div className="divide-y divide-border-primary">
                        {activeRuns.map((run) => {
                          const isExpanded = expandedActiveRuns.has(run.run_id)
                          const user = userStats.find(u => u.user_id === run.user_id)
                          return (
                            <div key={run.run_id} className="bg-[#E4E4E2] dark:bg-[#2A2A2A]">
                              <div
                                onClick={() => toggleActiveRunExpanded(run.run_id)}
                                className="p-4 cursor-pointer transition-colors"
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    {isExpanded ? (
                                      <ChevronDown className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                                    ) : (
                                      <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                                    )}
                                    <div>
                                      <p className="font-medium text-light-text dark:text-dark-text">
                                        {user?.email || run.user_id}
                                      </p>
                                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                                        Step {run.step}/{run.total_steps}: {run.current_step}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <Loader2 className="w-4 h-4 animate-spin text-accent" />
                                    <div className="text-right text-sm text-light-text-secondary dark:text-dark-text-secondary">
                                      {formatDate(run.started_at)}
                                    </div>
                                  </div>
                                </div>
                                <div className="w-full bg-light-bg dark:bg-dark-bg rounded-full h-2.5 mb-2">
                                  <div
                                    className="bg-accent h-2.5 rounded-full transition-all duration-500"
                                    style={{ width: `${run.progress}%` }}
                                  />
                                </div>
                                <div className="flex justify-between text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                  <span>{run.progress}% complete</span>
                                  {run.stats && Object.keys(run.stats).length > 0 && (
                                    <span>
                                      {run.stats.delete_count !== undefined && `${run.stats.delete_count} delete`}
                                      {run.stats.merge_count !== undefined && `, ${run.stats.merge_count} merge`}
                                      {run.stats.keep_count !== undefined && `, ${run.stats.keep_count} keep`}
                                    </span>
                                  )}
                                </div>
                              </div>
                              {/* Expanded Details */}
                              {isExpanded && (
                                <div className="px-4 pb-4 bg-[#E4E4E2] dark:bg-[#2A2A2A] border-t border-border-primary">
                                  <div className="pt-3 grid grid-cols-2 gap-4">
                                    <div>
                                      <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-1">Run ID</p>
                                      <p className="text-xs text-light-text dark:text-dark-text font-mono">{run.run_id.slice(0, 12)}...</p>
                                    </div>
                                    <div>
                                      <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-1">User ID</p>
                                      <p className="text-xs text-light-text dark:text-dark-text font-mono">{run.user_id.slice(0, 12)}...</p>
                                    </div>
                                    <div>
                                      <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-1">Started</p>
                                      <p className="text-xs text-light-text dark:text-dark-text">{new Date(run.started_at).toLocaleString()}</p>
                                    </div>
                                    <div>
                                      <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-1">User Memories</p>
                                      <p className="text-xs text-light-text dark:text-dark-text">{user?.memory_count || 'N/A'} memories, {user?.topic_count || 'N/A'} topics</p>
                                    </div>
                                    {run.stats && Object.keys(run.stats).length > 0 && (
                                      <>
                                        <div className="col-span-2">
                                          <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-2">Decisions So Far</p>
                                          <div className="flex gap-4">
                                            {run.stats.delete_count !== undefined && (
                                              <div className="flex items-center gap-1.5">
                                                <div className="w-2 h-2 rounded-full bg-red-500" />
                                                <span className="text-xs text-light-text dark:text-dark-text">{run.stats.delete_count} delete</span>
                                              </div>
                                            )}
                                            {run.stats.merge_count !== undefined && (
                                              <div className="flex items-center gap-1.5">
                                                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                                                <span className="text-xs text-light-text dark:text-dark-text">{run.stats.merge_count} merge</span>
                                              </div>
                                            )}
                                            {run.stats.keep_count !== undefined && (
                                              <div className="flex items-center gap-1.5">
                                                <div className="w-2 h-2 rounded-full bg-green-500" />
                                                <span className="text-xs text-light-text dark:text-dark-text">{run.stats.keep_count} keep</span>
                                              </div>
                                            )}
                                          </div>
                                        </div>
                                      </>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="p-6 text-center">
                        <Play className="w-10 h-10 text-light-text-secondary dark:text-dark-text-secondary mx-auto mb-2 opacity-30" />
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                          No workflows currently running
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Scheduled Runs Section - Now using should_trigger */}
                <div>
                  <h2 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading mb-3 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                    Pending Triggers
                  </h2>
                  <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary overflow-hidden">
                    {(() => {
                      // Use the intelligent should_trigger from backend
                      const usersShouldTrigger = userStats.filter(u => u.should_trigger)
                      const usersNearTrigger = userStats.filter(u => {
                        if (u.should_trigger) return false
                        const growth = u.growth ?? u.memory_count // For new users, growth = memory_count
                        return growth >= growthThreshold * 0.7
                      })

                      if (usersShouldTrigger.length === 0 && usersNearTrigger.length === 0) {
                        return (
                          <div className="p-6 text-center">
                            <Clock className="w-10 h-10 text-light-text-secondary dark:text-dark-text-secondary mx-auto mb-2 opacity-30" />
                            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                              No pending triggers (threshold: +{growthThreshold} new memories)
                            </p>
                          </div>
                        )
                      }

                      return (
                        <div className="divide-y divide-border-primary">
                          {usersShouldTrigger.map((user) => (
                            <div key={user.user_id} className="p-3 bg-amber-50/50 dark:bg-amber-900/10">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="w-7 h-7 rounded-full bg-amber-500 flex items-center justify-center">
                                    <AlertTriangle className="w-3.5 h-3.5 text-white" />
                                  </div>
                                  <div>
                                    <p className="text-sm font-medium text-light-text dark:text-dark-text">
                                      {user.email}
                                    </p>
                                    <p className="text-xs text-amber-600 dark:text-amber-400">
                                      {user.growth !== null ? (
                                        <>+{user.growth} new ({user.memory_count} total)</>
                                      ) : (
                                        <>{user.memory_count} memories (never optimized)</>
                                      )}
                                    </p>
                                  </div>
                                </div>
                                <button
                                  onClick={() => triggerWorkflow(user.user_id, user.email)}
                                  disabled={triggerLoading === user.user_id}
                                  className="px-3 py-1 text-xs font-medium rounded-lg bg-amber-500 hover:bg-amber-600 text-white transition-colors"
                                >
                                  {triggerLoading === user.user_id ? 'Starting...' : 'Run Now'}
                                </button>
                              </div>
                            </div>
                          ))}
                          {usersNearTrigger.map((user) => {
                            const growth = user.growth ?? user.memory_count
                            const progress = (growth / growthThreshold) * 100
                            return (
                              <div key={user.user_id} className="p-3">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-3">
                                    <div className="w-7 h-7 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                      <TrendingUp className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                                    </div>
                                    <div>
                                      <p className="text-sm font-medium text-light-text dark:text-dark-text">
                                        {user.email}
                                      </p>
                                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                        +{growth} / +{growthThreshold} ({Math.round(progress)}%)
                                      </p>
                                    </div>
                                  </div>
                                  <div className="w-24">
                                    <div className="w-full bg-light-bg dark:bg-dark-bg rounded-full h-1.5">
                                      <div
                                        className="bg-blue-500 h-1.5 rounded-full"
                                        style={{ width: `${Math.min(100, progress)}%` }}
                                      />
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )
                    })()}
                  </div>
                </div>

                {/* All Users Table - Enhanced with Growth and Runs */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading flex items-center gap-2">
                      <Users className="w-5 h-5" />
                      All Users ({userStats.length})
                    </h2>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                      <input
                        type="text"
                        placeholder="Search..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 pr-3 py-1.5 text-sm border border-border-primary rounded-lg bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text w-48"
                      />
                    </div>
                  </div>

                  <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary overflow-hidden">
                    <div className="grid grid-cols-12 gap-2 p-3 border-b border-border-primary bg-light-bg dark:bg-dark-bg text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
                      <div className="col-span-3">Email</div>
                      <div
                        className="col-span-1 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('memory_count'); setSortDesc(sortBy === 'memory_count' ? !sortDesc : true); }}
                      >
                        Mem
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div
                        className="col-span-1 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('topic_count'); setSortDesc(sortBy === 'topic_count' ? !sortDesc : true); }}
                      >
                        Topics
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div
                        className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('growth'); setSortDesc(sortBy === 'growth' ? !sortDesc : true); }}
                      >
                        Growth
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div
                        className="col-span-1 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('total_runs'); setSortDesc(sortBy === 'total_runs' ? !sortDesc : true); }}
                      >
                        Runs
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div
                        className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('last_optimization'); setSortDesc(sortBy === 'last_optimization' ? !sortDesc : true); }}
                      >
                        Last Run
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div className="col-span-2 text-right">Action</div>
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                      {filteredUsers.map((user) => {
                        const shouldTrigger = user.should_trigger
                        const isLoading = triggerLoading === user.user_id
                        const isExpanded = expandedUsers.has(user.user_id)
                        const hasHistory = user.run_history && user.run_history.length > 0

                        return (
                          <div key={user.user_id}>
                            <div
                              className={`grid grid-cols-12 gap-2 p-3 border-b border-border-primary items-center transition-colors ${
                                shouldTrigger ? 'bg-amber-50/50 dark:bg-amber-900/10' : 'hover:bg-light-bg dark:hover:bg-dark-bg'
                              }`}
                            >
                              {/* Email with expand toggle */}
                              <div className="col-span-3 truncate flex items-center gap-2">
                                {hasHistory ? (
                                  <button
                                    onClick={() => toggleUserExpanded(user.user_id)}
                                    className="p-0.5 hover:bg-light-bg dark:hover:bg-dark-bg rounded"
                                  >
                                    {isExpanded ? (
                                      <ChevronDown className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                                    ) : (
                                      <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                                    )}
                                  </button>
                                ) : (
                                  <div className="w-5" />
                                )}
                                <span className="text-sm text-light-text dark:text-dark-text truncate">
                                  {user.email}
                                </span>
                              </div>
                              {/* Memory Count */}
                              <div className="col-span-1">
                                <span className="text-sm font-medium text-light-text dark:text-dark-text">
                                  {user.memory_count}
                                </span>
                              </div>
                              {/* Topic Count */}
                              <div className="col-span-1">
                                <span className="text-sm text-light-text dark:text-dark-text">
                                  {user.topic_count}
                                </span>
                              </div>
                              {/* Growth */}
                              <div className="col-span-2">
                                {user.growth !== null ? (
                                  <span className={`text-sm font-medium ${
                                    shouldTrigger ? 'text-amber-600 dark:text-amber-400' :
                                    user.growth > 0 ? 'text-green-600 dark:text-green-400' : 'text-light-text dark:text-dark-text'
                                  }`}>
                                    +{user.growth}
                                    {user.post_optimization_count !== null && (
                                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary ml-1">
                                        (from {user.post_optimization_count})
                                      </span>
                                    )}
                                  </span>
                                ) : (
                                  <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary italic">
                                    New user
                                  </span>
                                )}
                              </div>
                              {/* Total Runs */}
                              <div className="col-span-1">
                                <span className="text-sm text-light-text dark:text-dark-text">
                                  {user.total_runs}
                                </span>
                              </div>
                              {/* Last Optimization */}
                              <div className="col-span-2">
                                <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                  {formatDate(user.last_optimization)}
                                </span>
                              </div>
                              {/* Action */}
                              <div className="col-span-2 text-right">
                                <button
                                  onClick={() => triggerWorkflow(user.user_id, user.email)}
                                  disabled={isLoading || user.memory_count === 0}
                                  className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg transition-colors ${
                                    user.memory_count === 0
                                      ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                                      : shouldTrigger
                                        ? 'bg-amber-500 hover:bg-amber-600 text-white'
                                        : 'bg-[#E4E4E2] hover:bg-[#D4D4D2] dark:bg-[#2A2A2A] dark:hover:bg-[#3A3A3A] text-black dark:text-white'
                                  }`}
                                >
                                  {isLoading ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Zap className="w-3 h-3" />
                                  )}
                                  {isLoading ? '...' : 'Run'}
                                </button>
                              </div>
                            </div>
                            {/* Expandable Run History */}
                            {isExpanded && hasHistory && (
                              <div className="bg-light-bg/50 dark:bg-dark-bg/50 border-b border-border-primary">
                                <div className="px-4 py-2">
                                  <div className="flex items-center gap-2 mb-2">
                                    <History className="w-3.5 h-3.5 text-light-text-secondary dark:text-dark-text-secondary" />
                                    <span className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
                                      Run History
                                    </span>
                                  </div>
                                  <div className="space-y-1.5">
                                    {user.run_history.map((run) => (
                                      <div
                                        key={run.run_id}
                                        className="flex items-center justify-between p-2 rounded bg-light-surface dark:bg-dark-surface cursor-pointer hover:bg-light-bg dark:hover:bg-dark-bg"
                                        onClick={() => fetchRunDetails(run.run_id)}
                                      >
                                        <div className="flex items-center gap-2">
                                          {run.status === 'completed' ? (
                                            <CheckCircle className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                                          ) : run.status === 'failed' ? (
                                            <XCircle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                                          ) : (
                                            <Clock className="w-3.5 h-3.5 text-yellow-600 dark:text-yellow-400" />
                                          )}
                                          <span className="text-xs text-light-text dark:text-dark-text">
                                            {formatDate(run.started_at)}
                                          </span>
                                        </div>
                                        {run.before_count !== null && run.after_count !== null && (
                                          <div className="text-xs">
                                            <span className="text-light-text-secondary dark:text-dark-text-secondary">
                                              {run.before_count} → {run.after_count}
                                            </span>
                                            {run.reduction_percent !== null && (
                                              <span className="ml-1 text-green-600 dark:text-green-400">
                                                (-{run.reduction_percent.toFixed(1)}%)
                                              </span>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>

                    {filteredUsers.length === 0 && (
                      <div className="p-6 text-center text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        No users found
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column - 1/3 width */}
              <div className="lg:col-span-1 space-y-6">
                {/* Recent Runs */}
                <div>
                  <h2 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading mb-3">
                    Recent Runs
                  </h2>

                  {runs.length === 0 ? (
                    <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6 text-center">
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        No runs yet
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {runs.slice(0, 10).map((run) => (
                        <div
                          key={run.run_id}
                          className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-3 hover:border-accent transition-colors cursor-pointer"
                          onClick={() => fetchRunDetails(run.run_id)}
                        >
                          <div className="flex items-start gap-2">
                            <div className="mt-0.5">
                              {run.status === 'completed' ? (
                                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                              ) : run.status === 'failed' ? (
                                <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                              ) : (
                                <Clock className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                                {run.user_email || run.user_id.slice(0, 8)}
                              </p>
                              <div className="flex items-center justify-between text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                <span>{formatDate(run.started_at)}</span>
                                {run.archived_count > 0 && run.archived_count > run.current_count && (
                                  <span className="text-green-600 dark:text-green-400">
                                    -{Math.round((1 - run.current_count / run.archived_count) * 100)}%
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Run Details Modal */}
      {(selectedRun || modalLoading) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedRun(null)}>
          <div
            className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary max-w-2xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {modalLoading ? (
              <div className="p-8 flex justify-center items-center">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
              </div>
            ) : selectedRun && (
              <>
                {/* Modal Header */}
                <div className="flex items-center justify-between p-4 border-b border-border-primary">
                  <div className="flex items-center gap-3">
                    {selectedRun.status === 'completed' ? (
                      <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                        <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                    ) : selectedRun.status === 'failed' ? (
                      <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                        <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                        <Clock className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold text-light-text dark:text-dark-text">
                        {selectedRun.workflow_name}
                      </h3>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        {selectedRun.user_email || selectedRun.user_id.slice(0, 8)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedRun(null)}
                    className="p-2 hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                  </button>
                </div>

                {/* Modal Body */}
                <div className="p-4 overflow-y-auto max-h-[calc(80vh-80px)]">
                  {/* Summary Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 text-center">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <span className="text-xl font-bold text-light-text dark:text-dark-text">{selectedRun.stats?.memories_before || 0}</span>
                        <ArrowUpDown className="w-4 h-4 text-accent" />
                        <span className="text-xl font-bold text-green-600 dark:text-green-400">{selectedRun.stats?.memories_after || 0}</span>
                      </div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Memories</p>
                      <p className="text-sm font-medium text-accent">{selectedRun.stats?.reduction_percent || 0}% reduction</p>
                    </div>

                    <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 text-center">
                      <div className="flex items-center justify-center gap-2 mb-1">
                        <span className="text-xl font-bold text-light-text dark:text-dark-text">{selectedRun.stats?.topics_before || 0}</span>
                        <ArrowUpDown className="w-4 h-4 text-accent" />
                        <span className="text-xl font-bold text-green-600 dark:text-green-400">{selectedRun.stats?.topics_after || 0}</span>
                      </div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Topics</p>
                      <p className="text-sm font-medium text-accent">{selectedRun.stats?.topics_removed || 0} removed</p>
                    </div>
                  </div>

                  {/* DELETED MEMORIES */}
                  {selectedRun.changes && selectedRun.changes.deleted && selectedRun.changes.deleted.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800 p-4 mb-4">
                      <h3 className="font-bold text-red-800 dark:text-red-200 mb-3 flex items-center gap-2">
                        <Trash2 className="w-4 h-4" />
                        DELETED ({selectedRun.changes.deleted.length} memories)
                      </h3>
                      <div className="space-y-3 max-h-60 overflow-y-auto">
                        {selectedRun.changes.deleted.map((mem) => (
                          <div key={mem.memory_id} className="bg-white dark:bg-dark-surface rounded p-3 border border-red-200 dark:border-red-900/30">
                            <p className="text-sm text-light-text dark:text-dark-text mb-2">{mem.memory}</p>
                            <div className="flex flex-wrap gap-1">
                              {mem.topics?.map((topic, idx) => (
                                <span key={idx} className="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-xs">
                                  {topic}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* NEW/MERGED MEMORIES */}
                  {selectedRun.changes && selectedRun.changes.new_or_merged && selectedRun.changes.new_or_merged.length > 0 && (
                    <div className="bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800 p-4 mb-4">
                      <h3 className="font-bold text-green-800 dark:text-green-200 mb-3 flex items-center gap-2">
                        <GitMerge className="w-4 h-4" />
                        NEW/MERGED ({selectedRun.changes.new_or_merged.length} memories)
                      </h3>
                      <div className="space-y-3 max-h-60 overflow-y-auto">
                        {selectedRun.changes.new_or_merged.map((mem) => (
                          <div key={mem.memory_id} className="bg-white dark:bg-dark-surface rounded p-3 border border-green-200 dark:border-green-900/30">
                            <p className="text-sm text-light-text dark:text-dark-text mb-2">{mem.memory}</p>
                            <div className="flex flex-wrap gap-1">
                              {mem.topics?.map((topic, idx) => (
                                <span key={idx} className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs">
                                  {topic}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* TOPIC CHANGES */}
                  {selectedRun.changes && selectedRun.changes.topics && ((selectedRun.changes.topics.removed?.length || 0) > 0 || (selectedRun.changes.topics.added?.length || 0) > 0) && (
                    <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 mb-4">
                      <h3 className="font-bold text-light-text dark:text-dark-text mb-3 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        TOPIC CHANGES
                      </h3>

                      {selectedRun.changes.topics.removed && selectedRun.changes.topics.removed.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs font-medium text-red-600 dark:text-red-400 mb-1">
                            REMOVED ({selectedRun.changes.topics.removed.length})
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {selectedRun.changes.topics.removed.map((topic, idx) => (
                              <span key={idx} className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-sm line-through">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {selectedRun.changes.topics.added && selectedRun.changes.topics.added.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">
                            ADDED ({selectedRun.changes.topics.added.length})
                          </p>
                          <div className="flex flex-wrap gap-1">
                            {selectedRun.changes.topics.added.map((topic, idx) => (
                              <span key={idx} className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-sm">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* No changes message */}
                  {selectedRun.changes && (!selectedRun.changes.deleted || selectedRun.changes.deleted.length === 0) && (!selectedRun.changes.new_or_merged || selectedRun.changes.new_or_merged.length === 0) && (!selectedRun.changes.topics?.removed || selectedRun.changes.topics.removed.length === 0) && (!selectedRun.changes.topics?.added || selectedRun.changes.topics.added.length === 0) && (
                    <div className="bg-gray-50 dark:bg-gray-900/10 rounded-lg border border-gray-200 dark:border-gray-800 p-4 mb-4">
                      <p className="text-center text-gray-600 dark:text-gray-400">No changes detected in this run</p>
                    </div>
                  )}

                  {/* Timestamps */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Started</p>
                      <p className="text-sm text-light-text dark:text-dark-text">
                        {selectedRun.started_at ? new Date(selectedRun.started_at).toLocaleString() : 'N/A'}
                      </p>
                    </div>
                    <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Completed</p>
                      <p className="text-sm text-light-text dark:text-dark-text">
                        {selectedRun.completed_at ? new Date(selectedRun.completed_at).toLocaleString() : 'N/A'}
                      </p>
                    </div>
                  </div>

                  {/* Run ID Footer */}
                  <div className="pt-4 border-t border-border-primary">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      Run ID: <code className="bg-light-bg dark:bg-dark-bg px-1 rounded">{selectedRun.run_id}</code>
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
