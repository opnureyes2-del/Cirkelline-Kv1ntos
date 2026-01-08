'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  ArrowRight,
  Tag,
  Loader2,
  RefreshCw
} from 'lucide-react'

interface Memory {
  memory_id: string
  memory: string
  topics: string[]
  created_at: string | null
  updated_at?: string | null
}

interface ActiveRunInfo {
  run_id: string
  user_id: string
  step: number
  current_step: string
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
  current_step?: string
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

export default function WorkflowRunDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params.runId as string

  const [loading, setLoading] = useState(true)
  const [run, setRun] = useState<RunDetails | null>(null)
  const [activeInfo, setActiveInfo] = useState<ActiveRunInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  const fetchActiveStatus = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return null

      const response = await fetch(`${apiUrl}/api/admin/workflows/active`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        const activeRun = data.active_runs?.find((r: ActiveRunInfo) => r.run_id === runId)
        return activeRun || null
      }
      return null
    } catch {
      return null
    }
  }, [apiUrl, runId])

  const fetchRunDetails = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setError('Not authenticated')
        return
      }

      const response = await fetch(`${apiUrl}/api/admin/workflows/runs/${runId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) {
        const activeRun = await fetchActiveStatus()
        if (activeRun) {
          setActiveInfo(activeRun)
          setRun(null)
          return
        }
        throw new Error('Failed to fetch run details')
      }

      const data = await response.json()
      setRun(data.run)

      if (data.run?.status === 'running') {
        const activeRun = await fetchActiveStatus()
        setActiveInfo(activeRun)
      } else {
        setActiveInfo(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [apiUrl, runId, fetchActiveStatus])

  useEffect(() => {
    if (runId) {
      setLoading(true)
      setError(null)
      fetchRunDetails()
    }
  }, [runId, fetchRunDetails])

  useEffect(() => {
    if (activeInfo || (run?.status === 'running')) {
      const interval = setInterval(async () => {
        const activeRun = await fetchActiveStatus()
        if (activeRun) {
          setActiveInfo(activeRun)
        } else {
          setActiveInfo(null)
          fetchRunDetails()
        }
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [activeInfo, run?.status, fetchActiveStatus, fetchRunDetails])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  if (loading) {
    return (
      <div className="p-8 flex justify-center items-center">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error && !activeInfo) {
    return (
      <div className="p-8">
        <button
          onClick={() => router.push('/admin/workflows')}
          className="flex items-center gap-2 text-light-text-secondary dark:text-dark-text-secondary hover:text-accent mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Workflows
        </button>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      </div>
    )
  }

  // Active run view (workflow in progress)
  if (activeInfo && !run) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => router.push('/admin/workflows')}
            className="flex items-center gap-2 text-light-text-secondary dark:text-dark-text-secondary hover:text-accent mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Workflows
          </button>

          <div className="flex items-center gap-3 mb-6">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
            <h1 className="text-2xl font-bold text-light-text dark:text-dark-text font-heading">
              Memory Optimization Running...
            </h1>
          </div>

          <div className="bg-accent/5 border-2 border-accent rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Step {activeInfo.step}/{activeInfo.total_steps}: {activeInfo.current_step}
              </p>
              <div className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                <RefreshCw className="w-3 h-3 animate-spin" />
                Live
              </div>
            </div>

            <div className="w-full bg-light-bg dark:bg-dark-bg rounded-full h-3 mb-2">
              <div
                className="bg-accent h-3 rounded-full transition-all duration-500"
                style={{ width: `${activeInfo.progress}%` }}
              />
            </div>
            <p className="text-sm text-center text-light-text-secondary dark:text-dark-text-secondary">
              {activeInfo.progress}% complete
            </p>
          </div>

          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
            <h3 className="font-medium text-light-text dark:text-dark-text mb-3">Steps</h3>
            <div className="space-y-2">
              {['Fetch Memories', 'Classify', 'Resolve Merges', 'Normalize Topics', 'Save', 'Report'].map((stepName, idx) => {
                const stepNum = idx + 1
                const isCompleted = stepNum < activeInfo.step
                const isCurrent = stepNum === activeInfo.step

                return (
                  <div key={stepNum} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                      isCompleted ? 'bg-green-500 text-white' :
                      isCurrent ? 'bg-accent text-white' :
                      'bg-light-bg dark:bg-dark-bg text-light-text-secondary'
                    }`}>
                      {isCompleted ? <CheckCircle className="w-4 h-4" /> : stepNum}
                    </div>
                    <span className={`text-sm ${
                      isCompleted ? 'text-green-600 dark:text-green-400' :
                      isCurrent ? 'text-accent font-medium' :
                      'text-light-text-secondary dark:text-dark-text-secondary'
                    }`}>
                      {stepName}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="p-8 flex justify-center items-center">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const changes = run.changes

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <button
          onClick={() => router.push('/admin/workflows')}
          className="flex items-center gap-2 text-light-text-secondary dark:text-dark-text-secondary hover:text-accent mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Workflows
        </button>

        <div className="flex items-center gap-3 mb-2">
          {run.status === 'completed' ? (
            <CheckCircle className="w-7 h-7 text-green-600 dark:text-green-400" />
          ) : (
            <XCircle className="w-7 h-7 text-red-600 dark:text-red-400" />
          )}
          <h1 className="text-2xl font-bold text-light-text dark:text-dark-text font-heading">
            {run.workflow_name}
          </h1>
        </div>
        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-6">
          {run.user_email} • {formatDate(run.completed_at)}
        </p>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <span className="text-xl font-bold text-light-text dark:text-dark-text">{run.stats.memories_before}</span>
              <ArrowRight className="w-4 h-4 text-accent" />
              <span className="text-xl font-bold text-green-600 dark:text-green-400">{run.stats.memories_after}</span>
            </div>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Memories</p>
            <p className="text-sm font-medium text-accent">{run.stats.reduction_percent}% reduction</p>
          </div>

          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <span className="text-xl font-bold text-light-text dark:text-dark-text">{run.stats.topics_before}</span>
              <ArrowRight className="w-4 h-4 text-accent" />
              <span className="text-xl font-bold text-green-600 dark:text-green-400">{run.stats.topics_after}</span>
            </div>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Topics</p>
            <p className="text-sm font-medium text-accent">{run.stats.topics_removed} removed</p>
          </div>
        </div>

        {/* DELETED MEMORIES */}
        {changes && changes.deleted && changes.deleted.length > 0 && (
          <div className="bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800 p-4 mb-4">
            <h3 className="font-bold text-red-800 dark:text-red-200 mb-3">
              DELETED ({changes.deleted.length} memories)
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {changes.deleted.map((mem) => (
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
        {changes && changes.new_or_merged && changes.new_or_merged.length > 0 && (
          <div className="bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800 p-4 mb-4">
            <h3 className="font-bold text-green-800 dark:text-green-200 mb-3">
              NEW/MERGED ({changes.new_or_merged.length} memories)
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {changes.new_or_merged.map((mem) => (
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
        {changes && changes.topics && ((changes.topics.removed?.length || 0) > 0 || (changes.topics.added?.length || 0) > 0) && (
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 mb-4">
            <h3 className="font-bold text-light-text dark:text-dark-text mb-3 flex items-center gap-2">
              <Tag className="w-5 h-5" />
              TOPIC CHANGES
            </h3>

            {changes.topics.removed && changes.topics.removed.length > 0 && (
              <div className="mb-3">
                <p className="text-xs font-medium text-red-600 dark:text-red-400 mb-1">
                  REMOVED ({changes.topics.removed.length})
                </p>
                <div className="flex flex-wrap gap-1">
                  {changes.topics.removed.map((topic, idx) => (
                    <span key={idx} className="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-sm line-through">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {changes.topics.added && changes.topics.added.length > 0 && (
              <div>
                <p className="text-xs font-medium text-green-600 dark:text-green-400 mb-1">
                  ADDED ({changes.topics.added.length})
                </p>
                <div className="flex flex-wrap gap-1">
                  {changes.topics.added.map((topic, idx) => (
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
        {changes && (!changes.deleted || changes.deleted.length === 0) && (!changes.new_or_merged || changes.new_or_merged.length === 0) && (!changes.topics?.removed || changes.topics.removed.length === 0) && (!changes.topics?.added || changes.topics.added.length === 0) && (
          <div className="bg-gray-50 dark:bg-gray-900/10 rounded-lg border border-gray-200 dark:border-gray-800 p-4 mb-4">
            <p className="text-center text-gray-600 dark:text-gray-400">No changes detected in this run</p>
          </div>
        )}


        {/* Run ID Footer */}
        <div className="mt-6 pt-4 border-t border-border-primary">
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
            Run ID: <code className="bg-light-bg dark:bg-dark-bg px-1 rounded">{run.run_id}</code>
          </p>
        </div>
      </div>
    </div>
  )
}
