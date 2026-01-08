'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Workflow,
  Brain,
  BookOpen,
  ArrowRight,
  RefreshCw,
  CheckCircle,
  Clock,
  Users,
  Activity,
  TrendingDown,
  Calendar
} from 'lucide-react'

interface WorkflowStats {
  total_runs: number
  runs_today: number
  success_rate: number
}

interface MemoryStats extends WorkflowStats {
  total_deleted: number
  total_merged: number
  avg_reduction: number
  current_memories: number
  users_with_memories: number
}

interface JournalStats extends WorkflowStats {
  total_journals: number
  journals_today: number
  users_with_journals: number
}

export default function WorkflowsOverviewPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null)
  const [journalStats, setJournalStats] = useState<JournalStats | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      // Fetch memory workflow stats
      const memoryRes = await fetch(`${apiUrl}/api/admin/workflows/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (memoryRes.ok) {
        const data = await memoryRes.json()
        setMemoryStats(data.stats)
      }

      // Fetch journal workflow stats
      const journalRes = await fetch(`${apiUrl}/api/admin/workflows/journals/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (journalRes.ok) {
        const data = await journalRes.json()
        setJournalStats(data.stats)
      }
    } catch (error) {
      console.error('Failed to fetch workflow stats:', error)
    } finally {
      setLoading(false)
    }
  }, [apiUrl])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 mb-2">
              <Workflow className="w-8 h-8 text-accent" />
              <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
                Workflows
              </h1>
            </div>
            <button
              onClick={() => { setLoading(true); fetchData(); }}
              className="flex items-center gap-2 px-4 py-2 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            Automated background workflows for memory management and daily journaling
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Memory Optimization Workflow Card */}
            <div
              onClick={() => router.push('/admin/workflows/memory')}
              className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary p-6 cursor-pointer hover:border-accent transition-colors group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <Brain className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">
                      Memory Optimization
                    </h2>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      Cleanup, merge, and optimize user memories
                    </p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Activity className="w-4 h-4 text-accent" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Total Runs</span>
                  </div>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {memoryStats?.total_runs || 0}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    {memoryStats?.runs_today || 0} today
                  </p>
                </div>

                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingDown className="w-4 h-4 text-green-500" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Avg Reduction</span>
                  </div>
                  <p className="text-xl font-bold text-green-600 dark:text-green-400">
                    {memoryStats?.avg_reduction || 0}%
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    per optimization
                  </p>
                </div>

                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Users className="w-4 h-4 text-blue-500" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Users</span>
                  </div>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {memoryStats?.users_with_memories || 0}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    with memories
                  </p>
                </div>

                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Success Rate</span>
                  </div>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {memoryStats?.success_rate || 100}%
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    completed
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-accent">
                <span>View Details</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>

            {/* Daily Journals Workflow Card */}
            <div
              onClick={() => router.push('/admin/workflows/journals')}
              className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary p-6 cursor-pointer hover:border-accent transition-colors group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                    <BookOpen className="w-6 h-6 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">
                      Daily Journals
                    </h2>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      Generate daily summaries of user interactions
                    </p>
                  </div>
                </div>
                <ArrowRight className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Activity className="w-4 h-4 text-accent" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Total Runs</span>
                  </div>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {journalStats?.total_runs || 0}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    {journalStats?.runs_today || 0} today
                  </p>
                </div>

                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <BookOpen className="w-4 h-4 text-amber-500" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Journals</span>
                  </div>
                  <p className="text-xl font-bold text-amber-600 dark:text-amber-400">
                    {journalStats?.total_journals || 0}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    {journalStats?.journals_today || 0} today
                  </p>
                </div>

                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Users className="w-4 h-4 text-blue-500" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Users</span>
                  </div>
                  <p className="text-xl font-bold text-light-text dark:text-dark-text">
                    {journalStats?.users_with_journals || 0}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    with journals
                  </p>
                </div>

                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-4 h-4 text-blue-500" />
                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Schedule</span>
                  </div>
                  <p className="text-sm font-medium text-light-text dark:text-dark-text">
                    Manual
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    admin triggered
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-accent">
                <span>View Details</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
        )}

        {/* Coming Soon - Future Workflows */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-light-text dark:text-dark-text mb-4">
            Future Workflows
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary border-dashed p-4 opacity-50">
              <div className="flex items-center gap-3 mb-2">
                <Calendar className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                <span className="font-medium text-light-text dark:text-dark-text">Activity Reports</span>
              </div>
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                Weekly/monthly usage summaries
              </p>
              <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-light-bg dark:bg-dark-bg rounded">Coming Soon</span>
            </div>

            <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary border-dashed p-4 opacity-50">
              <div className="flex items-center gap-3 mb-2">
                <Activity className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                <span className="font-medium text-light-text dark:text-dark-text">Data Cleanup</span>
              </div>
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                Automated stale data removal
              </p>
              <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-light-bg dark:bg-dark-bg rounded">Coming Soon</span>
            </div>

            <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary border-dashed p-4 opacity-50">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                <span className="font-medium text-light-text dark:text-dark-text">Health Checks</span>
              </div>
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                System health monitoring
              </p>
              <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-light-bg dark:bg-dark-bg rounded">Coming Soon</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
