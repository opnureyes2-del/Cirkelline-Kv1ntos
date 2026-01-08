'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
  BookOpen,
  ArrowLeft,
  RefreshCw,
  Play,
  Users,
  Calendar,
  Clock,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Loader2,
  CheckCircle,
  XCircle,
  MessageSquare,
  Search,
  ArrowUpDown,
  X,
  Database
} from 'lucide-react'

interface JournalEntry {
  id: number
  user_id: string
  user_email?: string
  journal_date: string
  summary: string
  topics: string[]
  outcomes: string[]
  message_count: number
  created_at: string
}

interface UserStats {
  user_id: string
  email: string
  created_at: string | null
  days_on_platform: number
  journal_count: number
  expected_journals: number
  last_journal: string | null
  total_sessions: number
}

interface WorkflowRun {
  run_id: string
  workflow_name: string
  user_id: string
  user_email: string | null
  target_date: string | null
  started_at: string | null
  completed_at: string | null
  status: string
  current_step?: string
  error_message?: string | null
  metrics?: {
    step?: number
    progress?: number
    journal_id?: number
    messages?: number
    sessions_fetched?: number
  }
  output_data?: {
    summary?: string
    topics?: string[]
    outcomes?: string[]
    message_count?: number
    report?: string
  }
}

interface ActiveRun {
  run_id: string
  user_id: string
  user_email?: string
  step: number
  current_step: string
  total_steps: number
  progress: number
  started_at: string
  target_date?: string
}

interface RunDetails {
  run_id: string
  workflow_name: string
  user_id: string
  user_email: string | null
  target_date: string | null
  status: string
  started_at: string | null
  completed_at: string | null
  current_step?: string
  error_message?: string | null
  error?: string
  metrics?: {
    step?: number
    progress?: number
    journal_id?: number
    messages?: number
    sessions_fetched?: number
  }
  journal_entry?: {
    content: string
    topics: string[]
    outcomes: string[]
    date: string | null
  }
  output_data?: {
    summary?: string
    topics?: string[]
    outcomes?: string[]
    message_count?: number
    session_count?: number
    report?: string
  }
}

interface CalendarDay {
  date: string
  has_activity: boolean
  session_count: number
  message_count: number
  sessions: { id: string; name: string }[]
  has_journal: boolean
  journal: {
    id: number
    topics: string[]
    summary_preview: string
  } | null
  status: 'complete' | 'gap' | 'no_activity'
}

interface CalendarData {
  user_id: string
  email: string
  registered_at: string
  days: CalendarDay[]
  summary: {
    total_days: number
    days_with_activity: number
    days_with_journals: number
    gap_days: number
  }
}

interface QueueItem {
  id: number
  user_id: string
  email: string | null
  target_date: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  priority: number
  error_message: string | null
  created_at: string
  processed_at: string | null
}

interface QueueStats {
  pending: number
  processing: number
  completed: number
  failed: number
  total: number
}

interface QueueData {
  stats: QueueStats
  items: QueueItem[]
  worker: {
    running: boolean
    current_job_id: number | null
    jobs_processed: number
    jobs_failed: number
  }
  scheduler: {
    running: boolean
    jobs: { id: string; name: string; next_run: string | null }[]
  }
}

export default function JournalsWorkflowPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [userStats, setUserStats] = useState<UserStats[]>([])
  const [runs, setRuns] = useState<WorkflowRun[]>([])
  const [activeRuns, setActiveRuns] = useState<ActiveRun[]>([])
  const [triggerLoading, setTriggerLoading] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'journal_count' | 'last_journal' | 'total_sessions'>('journal_count')
  const [sortDesc, setSortDesc] = useState(true)

  // Run Details Modal state
  const [selectedRun, setSelectedRun] = useState<RunDetails | null>(null)
  const [modalLoading, setModalLoading] = useState(false)

  // Calendar Modal state
  const [calendarData, setCalendarData] = useState<CalendarData | null>(null)
  const [calendarLoading, setCalendarLoading] = useState(false)
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week')
  const [viewOffset, setViewOffset] = useState(0) // 0 = current week/month, 1 = previous, etc.
  const [expandedDays, setExpandedDays] = useState<Set<string>>(new Set())
  const [dayJournalLoading, setDayJournalLoading] = useState<string | null>(null)

  // Queue state
  const [queueData, setQueueData] = useState<QueueData | null>(null)
  const [backfillLoading, setBackfillLoading] = useState<string | null>(null)
  const [backfillAllLoading, setBackfillAllLoading] = useState(false)
  const [cancellingRun, setCancellingRun] = useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [cancellingJob, setCancellingJob] = useState<number | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [cancellingAllPending, setCancellingAllPending] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      // Fetch all data in parallel
      const [usersRes, runsRes, activeRes, queueRes] = await Promise.all([
        fetch(`${apiUrl}/api/admin/workflows/journals/users`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/journals/runs?limit=10`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/journals/active`, { headers: { 'Authorization': `Bearer ${token}` }}),
        fetch(`${apiUrl}/api/admin/workflows/journals/queue`, { headers: { 'Authorization': `Bearer ${token}` }})
      ])

      if (usersRes.ok) {
        const data = await usersRes.json()
        setUserStats(data.users || [])
      }

      if (runsRes.ok) {
        const data = await runsRes.json()
        setRuns(data.runs || [])
      }

      if (activeRes.ok) {
        const data = await activeRes.json()
        setActiveRuns(data.active_runs || [])
      }

      if (queueRes.ok) {
        const data = await queueRes.json()
        setQueueData(data)
      }
    } catch (error) {
      console.error('Failed to fetch journal data:', error)
    } finally {
      setLoading(false)
    }
  }, [apiUrl])

  // Fetch only active runs (for polling)
  const fetchActiveRuns = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/active`, {
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
    fetchData()
  }, [fetchData])

  // Always poll for active runs (every 3 seconds)
  useEffect(() => {
    const interval = setInterval(async () => {
      await fetchActiveRuns()
    }, 3000)
    return () => clearInterval(interval)
  }, [fetchActiveRuns])

  // Detect when all active runs complete and refresh data
  const prevActiveRunsRef = useRef(activeRuns.length)
  useEffect(() => {
    if (prevActiveRunsRef.current > 0 && activeRuns.length === 0) {
      fetchData()
    }
    prevActiveRunsRef.current = activeRuns.length
  }, [activeRuns.length, fetchData])

  // Trigger workflow for user
  const triggerWorkflow = async (userId: string, userEmail: string, targetDate?: string) => {
    setTriggerLoading(userId)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      let url = `${apiUrl}/api/admin/workflows/daily-journal/run?target_user_id=${userId}`
      if (targetDate) {
        url += `&target_date=${targetDate}`
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      const data = await response.json()

      if (data.success) {
        // Immediately fetch active runs
        await fetchActiveRuns()

        // If no active runs yet, add placeholder
        if (activeRuns.length === 0) {
          setActiveRuns([{
            run_id: data.run_id,
            user_id: userId,
            user_email: userEmail,
            step: 1,
            current_step: 'Starting...',
            total_steps: 4,
            progress: 0,
            started_at: new Date().toISOString(),
            target_date: targetDate
          }])
        }
      } else {
        console.error('Failed to trigger workflow:', data.error)
      }
    } catch (error) {
      console.error('Failed to trigger workflow:', error)
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

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/runs/${runId}`, {
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

  // Fetch calendar data for a user
  const fetchCalendarData = async (userId: string) => {
    setCalendarLoading(true)
    setCalendarData(null)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/user/${userId}/calendar`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        if (data.success) {
          setCalendarData(data)
        }
      }
    } catch (error) {
      console.error('Failed to fetch calendar data:', error)
    } finally {
      setCalendarLoading(false)
    }
  }

  // Close calendar modal
  const closeCalendarModal = () => {
    setCalendarData(null)
    setViewMode('week')
    setViewOffset(0)
    setExpandedDays(new Set())
  }

  // Toggle day expanded state
  const toggleDayExpanded = (date: string) => {
    setExpandedDays(prev => {
      const next = new Set(prev)
      if (next.has(date)) {
        next.delete(date)
      } else {
        next.add(date)
      }
      return next
    })
  }

  // Create journal for a specific day
  const createJournalForDay = async (userId: string, date: string) => {
    setDayJournalLoading(date)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const response = await fetch(`${apiUrl}/api/admin/workflows/daily-journal/run?target_user_id=${userId}&target_date=${date}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      const data = await response.json()
      if (data.success) {
        alert(`Journal workflow started for ${date}`)
        // Refresh calendar data
        fetchCalendarData(userId)
        // Also refresh main data to show in active runs
        fetchData()
      } else {
        alert(`Failed to start journal: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to create journal:', error)
      alert('Failed to start journal workflow')
    } finally {
      setDayJournalLoading(null)
    }
  }

  // View journal details - fetch from runs by date
  const viewJournalForDay = async (userId: string, journalId: number) => {
    // Find a run that matches this journal, or just show the journal data
    // For now, we'll use the existing run details modal by finding the run
    setModalLoading(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      // Fetch the journal details directly
      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/entries?user_id=${userId}&limit=100`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        const journal = (data.journals || data.entries || []).find((j: JournalEntry) => j.id === journalId)
        if (journal) {
          // Create a pseudo-run object to display in modal
          // Include journal_entry field so the modal shows the full content
          setSelectedRun({
            run_id: `journal-${journal.id}`,
            workflow_name: 'daily_journal',
            user_id: journal.user_id,
            user_email: journal.user_email || null,
            target_date: journal.journal_date,
            status: 'completed',
            started_at: journal.created_at,
            completed_at: journal.created_at,
            // Include journal_entry for the actual journal content display
            journal_entry: {
              content: journal.summary,
              topics: journal.topics,
              outcomes: journal.outcomes,
              date: journal.journal_date
            },
            // Metrics for the stats display
            metrics: {
              messages: journal.message_count,
              sessions_fetched: 0 // Not tracked per-journal
            },
            output_data: {
              summary: journal.summary,
              topics: journal.topics,
              outcomes: journal.outcomes,
              message_count: journal.message_count
            }
          })
        }
      }
    } catch (error) {
      console.error('Failed to fetch journal:', error)
    } finally {
      setModalLoading(false)
    }
  }

  // Backfill user journals
  const backfillUser = async (userId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setBackfillLoading(userId)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/backfill/${userId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        alert(`Backfill queued: ${data.jobs_added} jobs added (${data.gaps_found} gaps found)`)
        fetchData()
      }
    } catch (error) {
      console.error('Failed to backfill user:', error)
    } finally {
      setBackfillLoading(null)
    }
  }

  // Backfill all users
  const backfillAllUsers = async () => {
    if (!confirm('This will queue journal jobs for ALL users with gaps. Continue?')) return
    setBackfillAllLoading(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/backfill-all`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        alert(`Global backfill: ${data.total_jobs_added} jobs added for ${data.total_users} users`)
        fetchData()
      }
    } catch (error) {
      console.error('Failed to backfill all users:', error)
    } finally {
      setBackfillAllLoading(false)
    }
  }

  // Retry failed queue jobs (future UI implementation)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const retryFailedJobs = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/queue/retry-failed`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        alert(`Reset ${data.reset_count} failed jobs to pending`)
        fetchData()
      }
    } catch (error) {
      console.error('Failed to retry failed jobs:', error)
    }
  }

  // Cancel a single active run
  const cancelRun = async (runId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    if (!confirm('Cancel this workflow run?')) return

    setCancellingRun(runId)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/runs/${runId}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        await fetchActiveRuns()
        fetchData()
      } else {
        const data = await res.json()
        alert(`Failed to cancel: ${data.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to cancel run:', error)
    } finally {
      setCancellingRun(null)
    }
  }

  // Cancel a single queue job (future UI implementation)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const cancelQueueJob = async (jobId: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setCancellingJob(jobId)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/queue/${jobId}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        fetchData()
      } else {
        const data = await res.json()
        alert(`Failed to cancel: ${data.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to cancel job:', error)
    } finally {
      setCancellingJob(null)
    }
  }

  // Cancel all pending jobs (future UI implementation)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const cancelAllPendingJobs = async () => {
    if (!confirm('Cancel ALL pending jobs? This cannot be undone.')) return

    setCancellingAllPending(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const res = await fetch(`${apiUrl}/api/admin/workflows/journals/queue/cancel-pending`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.ok) {
        const data = await res.json()
        alert(`Cancelled ${data.cancelled_count} pending jobs`)
        fetchData()
      }
    } catch (error) {
      console.error('Failed to cancel pending jobs:', error)
    } finally {
      setCancellingAllPending(false)
    }
  }

  // Get filtered days based on view mode
  const getFilteredDays = () => {
    if (!calendarData) return { days: [], label: '', hasNext: false, hasPrev: false }

    const today = new Date()
    let startDate: Date
    let endDate: Date
    let label: string

    if (viewMode === 'week') {
      // Get start of current week (Monday) minus offset weeks
      const dayOfWeek = today.getDay()
      const diff = dayOfWeek === 0 ? 6 : dayOfWeek - 1 // Days since Monday
      endDate = new Date(today)
      endDate.setDate(today.getDate() - diff - (viewOffset * 7) + 6) // End of week (Sunday)
      startDate = new Date(endDate)
      startDate.setDate(endDate.getDate() - 6) // Start of week (Monday)

      // Format label
      const startStr = startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      const endStr = endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      label = `${startStr} - ${endStr}`
    } else {
      // Month view
      const targetMonth = new Date(today.getFullYear(), today.getMonth() - viewOffset, 1)
      startDate = new Date(targetMonth.getFullYear(), targetMonth.getMonth(), 1)
      endDate = new Date(targetMonth.getFullYear(), targetMonth.getMonth() + 1, 0)
      label = targetMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    }

    const startStr = startDate.toISOString().split('T')[0]
    const endStr = endDate.toISOString().split('T')[0]

    const filteredDays = calendarData.days.filter(day => {
      return day.date >= startStr && day.date <= endStr
    })

    // Check if there's data before/after
    const registeredDate = new Date(calendarData.registered_at)
    const hasPrev = startDate > registeredDate
    const hasNext = viewOffset > 0

    return { days: filteredDays, label, hasNext, hasPrev }
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

  // Format registration date (short format)
  const formatRegistrationDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  // Sort and filter users
  const filteredUsers = userStats
    .filter(u => u.email.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      let aVal: number = 0
      let bVal: number = 0

      if (sortBy === 'journal_count') {
        aVal = a.journal_count
        bVal = b.journal_count
      } else if (sortBy === 'total_sessions') {
        aVal = a.expected_journals
        bVal = b.expected_journals
      } else {
        aVal = a.last_journal ? new Date(a.last_journal).getTime() : 0
        bVal = b.last_journal ? new Date(b.last_journal).getTime() : 0
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
              <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
                  Daily Journals
                </h1>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
                  Generate daily summaries of user interactions
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={backfillAllUsers}
                disabled={backfillAllLoading}
                className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {backfillAllLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Database className="w-4 h-4" />
                )}
                Backfill All
              </button>
              <button
                onClick={() => { setLoading(true); fetchData(); }}
                className="flex items-center gap-2 px-4 py-2 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
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
            {/* Two Column Layout - Flat structure for mobile reordering */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Active Runs Section - Mobile: 1st, Desktop: Left column row 1 */}
              <div className="order-1 lg:col-span-2 lg:row-start-1">
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
                          const user = userStats.find(u => u.user_id === run.user_id)
                          // Format date as "20th November 2025"
                          const formatOrdinalDate = (dateStr: string | null) => {
                            if (!dateStr) return 'Today'
                            const date = new Date(dateStr + 'T12:00:00')
                            const day = date.getDate()
                            const suffix = day === 1 || day === 21 || day === 31 ? 'st' : day === 2 || day === 22 ? 'nd' : day === 3 || day === 23 ? 'rd' : 'th'
                            return `${day}${suffix} ${date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`
                          }
                          const targetDateStr = formatOrdinalDate(run.target_date || null)
                          const isCancelling = cancellingRun === run.run_id
                          const userEmail = run.user_email || user?.email || ''
                          const userName = userEmail.split('@')[0] || run.user_id.slice(0, 8)

                          return (
                            <div key={run.run_id} className="bg-[#E4E4E2] dark:bg-[#2A2A2A] p-4">
                              {/* Header with Cancel button */}
                              <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2">
                                  <Loader2 className="w-5 h-5 animate-spin text-blue-500 flex-shrink-0" />
                                  <div>
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Journal:</span>
                                      <span className="text-sm font-semibold text-blue-700 dark:text-blue-300">
                                        {targetDateStr}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">User:</span>
                                      <span className="text-sm text-light-text dark:text-dark-text">
                                        {userName}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                                <button
                                  onClick={(e) => cancelRun(run.run_id, e)}
                                  disabled={isCancelling}
                                  className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/40 rounded transition-colors disabled:opacity-50"
                                  title="Cancel this run"
                                >
                                  {isCancelling ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <X className="w-3 h-3" />
                                  )}
                                  Cancel
                                </button>
                              </div>

                              {/* Progress bar */}
                              <div className="w-full bg-light-bg dark:bg-dark-bg rounded-full h-2 mb-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                                  style={{ width: `${run.progress}%` }}
                                />
                              </div>

                              {/* Step info */}
                              <div className="flex justify-between text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                <span>Step {run.step}/{run.total_steps}: {run.current_step}</span>
                                <span>{run.progress}%</span>
                              </div>
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

              {/* Queue Status - Mobile: 2nd, Desktop: Right column row 1 */}
              <div className="order-2 lg:col-span-1 lg:row-start-1">
                <h2 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading mb-3 flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Queue Status
                </h2>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 space-y-4">
                  {/* Stats */}
                  {queueData && (
                    <>
                      <div className="grid grid-cols-4 gap-2">
                        <div className="text-center p-2 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg">
                          <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">{queueData.stats.pending}</p>
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Pending</p>
                        </div>
                        <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/10 rounded-lg">
                          <p className="text-lg font-bold text-blue-600 dark:text-blue-400">{queueData.stats.processing}</p>
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Processing</p>
                        </div>
                        <div className="text-center p-2 bg-green-50 dark:bg-green-900/10 rounded-lg">
                          <p className="text-lg font-bold text-green-600 dark:text-green-400">{queueData.stats.completed}</p>
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Done</p>
                        </div>
                        <div className="text-center p-2 bg-red-50 dark:bg-red-900/10 rounded-lg">
                          <p className="text-lg font-bold text-red-600 dark:text-red-400">{queueData.stats.failed}</p>
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Failed</p>
                        </div>
                      </div>

                      {/* Worker Status */}
                      <div className="flex items-center gap-2 text-xs">
                        <span className={`w-2 h-2 rounded-full ${queueData.worker.running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                        <span className="text-light-text-secondary dark:text-dark-text-secondary">
                          Worker: {queueData.worker.running ? 'Running' : 'Stopped'}
                          {queueData.worker.running && queueData.worker.current_job_id && (
                            <span className="text-blue-500 ml-1">(Processing job #{queueData.worker.current_job_id})</span>
                          )}
                        </span>
                      </div>

                      {/* Scheduler Status */}
                      <div className="flex items-center gap-2 text-xs">
                        <span className={`w-2 h-2 rounded-full ${queueData.scheduler.running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                        <span className="text-light-text-secondary dark:text-dark-text-secondary">
                          Scheduler: {queueData.scheduler.running ? 'Running' : 'Stopped'}
                          {queueData.scheduler.jobs?.[0]?.next_run && (
                            <span className="text-light-text-secondary dark:text-dark-text-secondary ml-1">
                              (Next: {new Date(queueData.scheduler.jobs[0].next_run).toLocaleTimeString()})
                            </span>
                          )}
                        </span>
                      </div>
                    </>
                  )}

                </div>
              </div>

              {/* Users Table - Mobile: 3rd, Desktop: Left column row 2 */}
              <div className="order-3 lg:col-span-2 lg:row-start-2">
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
                      <div className="col-span-4">Email</div>
                      <div className="col-span-2">Registered</div>
                      <div
                        className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('journal_count'); setSortDesc(sortBy === 'journal_count' ? !sortDesc : true); }}
                      >
                        Journals
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div
                        className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('total_sessions'); setSortDesc(sortBy === 'total_sessions' ? !sortDesc : true); }}
                      >
                        Active Days
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                      <div
                        className="col-span-2 flex items-center gap-1 cursor-pointer hover:text-accent"
                        onClick={() => { setSortBy('last_journal'); setSortDesc(sortBy === 'last_journal' ? !sortDesc : true); }}
                      >
                        Last Journal
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </div>

                    <div className="max-h-96 overflow-y-auto">
                      {filteredUsers.map((user) => {
                        const journalGap = (user.expected_journals || 0) - (user.journal_count || 0)
                        const isComplete = journalGap <= 0

                        return (
                          <div
                            key={user.user_id}
                            className="grid grid-cols-12 gap-2 p-3 border-b border-border-primary items-center hover:bg-light-bg dark:hover:bg-dark-bg cursor-pointer"
                            onClick={() => fetchCalendarData(user.user_id)}
                          >
                            <div className="col-span-4 truncate text-sm text-light-text dark:text-dark-text hover:text-accent">
                              {user.email}
                            </div>
                            <div className="col-span-2">
                              <div className="text-xs text-light-text dark:text-dark-text">
                                {formatRegistrationDate(user.created_at)}
                              </div>
                              <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                {user.days_on_platform || 0} day{(user.days_on_platform || 0) !== 1 ? 's' : ''}
                              </div>
                            </div>
                            <div className="col-span-2">
                              <span className={`text-sm font-medium ${
                                isComplete
                                  ? 'text-green-600 dark:text-green-400'
                                  : 'text-amber-600 dark:text-amber-400'
                              }`}>
                                {user.journal_count || 0}/{user.expected_journals || 0}
                              </span>
                              {!isComplete && journalGap > 0 && (
                                <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary ml-1">
                                  (-{journalGap})
                                </span>
                              )}
                            </div>
                            <div className="col-span-2">
                              <span className="text-sm text-light-text dark:text-dark-text">
                                {user.expected_journals || 0}
                              </span>
                            </div>
                            <div className="col-span-2">
                              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                {formatDate(user.last_journal)}
                              </span>
                            </div>
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

              {/* Recent Runs - Mobile: 4th, Desktop: Right column row 2 */}
              <div className="order-4 lg:col-span-1 lg:row-start-2">
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
                      {runs.slice(0, 8).map((run) => {
                        // Format date as ordinal (e.g., "19th November 2025")
                        const formatOrdinalDate = (dateStr: string | null) => {
                          if (!dateStr) return 'Unknown date'
                          const date = new Date(dateStr + 'T12:00:00')
                          const day = date.getDate()
                          const suffix = day === 1 || day === 21 || day === 31 ? 'st' : day === 2 || day === 22 ? 'nd' : day === 3 || day === 23 ? 'rd' : 'th'
                          return `${day}${suffix} ${date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`
                        }

                        // Format timestamp as absolute time
                        const formatTimestamp = (dateStr: string | null) => {
                          if (!dateStr) return 'N/A'
                          const date = new Date(dateStr)
                          return date.toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true
                          })
                        }

                        const userName = run.user_email?.split('@')[0] || run.user_id.slice(0, 8)

                        return (
                          <div
                            key={run.run_id}
                            className={`bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-3 hover:border-accent transition-colors cursor-pointer ${
                              run.status === 'completed' ? 'border-l-2 border-l-green-500' :
                              run.status === 'failed' ? 'border-l-2 border-l-red-500' :
                              'border-l-2 border-l-yellow-500'
                            }`}
                            onClick={() => fetchRunDetails(run.run_id)}
                          >
                            {/* Header with status icon */}
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                {run.status === 'completed' ? (
                                  <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                                ) : run.status === 'failed' ? (
                                  <XCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" />
                                ) : (
                                  <Clock className="w-4 h-4 text-yellow-600 dark:text-yellow-400 animate-pulse flex-shrink-0" />
                                )}
                                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                                  run.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                                  run.status === 'failed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                                  'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                                }`}>
                                  {run.status === 'completed' ? 'Completed' : run.status === 'failed' ? 'Failed' : 'Running'}
                                </span>
                              </div>
                              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                {formatTimestamp(run.completed_at || run.started_at)}
                              </span>
                            </div>

                            {/* Journal and User info */}
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-12">Journal:</span>
                                <span className="text-sm font-medium text-light-text dark:text-dark-text">
                                  {formatOrdinalDate(run.target_date)}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-12">User:</span>
                                <span className="text-sm text-light-text dark:text-dark-text">
                                  {userName}
                                </span>
                              </div>
                            </div>

                            {/* Metrics */}
                            {run.metrics && (
                              <div className="mt-2 pt-2 border-t border-border-primary flex gap-4 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                <span>{run.metrics.messages || 0} messages</span>
                                <span>{run.metrics.sessions_fetched || 0} sessions</span>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Calendar Timeline Modal */}
      {(calendarData || calendarLoading) && (() => {
        const { days: filteredDays, label: periodLabel, hasNext, hasPrev } = getFilteredDays()
        return (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={closeCalendarModal}>
            <div
              className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {calendarLoading ? (
                <div className="p-8 flex justify-center items-center">
                  <Loader2 className="w-8 h-8 animate-spin text-accent" />
                </div>
              ) : calendarData && (
                <>
                  {/* Modal Header */}
                  <div className="flex items-center justify-between p-4 border-b border-border-primary flex-shrink-0">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-light-text dark:text-dark-text">
                          {calendarData.email}
                        </h3>
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                          Registered: {new Date(calendarData.registered_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Backfill button - only show if there are gaps */}
                      {calendarData.summary.gap_days > 0 && (
                        <button
                          onClick={() => backfillUser(calendarData.user_id)}
                          disabled={backfillLoading === calendarData.user_id}
                          className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors disabled:opacity-50"
                        >
                          {backfillLoading === calendarData.user_id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Database className="w-4 h-4" />
                          )}
                          Backfill {calendarData.summary.gap_days} Gap{calendarData.summary.gap_days !== 1 ? 's' : ''}
                        </button>
                      )}
                      <button
                        onClick={closeCalendarModal}
                        className="p-2 hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors"
                      >
                        <X className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                      </button>
                    </div>
                  </div>

                  {/* Controls Bar: View Toggle + Pagination */}
                  <div className="px-4 py-3 bg-light-bg dark:bg-dark-bg border-b border-border-primary flex-shrink-0">
                    <div className="flex items-center justify-between">
                      {/* View Toggle */}
                      <div className="flex items-center gap-1 bg-light-surface dark:bg-dark-surface rounded-lg p-1 border border-border-primary">
                        <button
                          onClick={() => { setViewMode('week'); setViewOffset(0); }}
                          className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                            viewMode === 'week'
                              ? 'bg-accent text-white'
                              : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                          }`}
                        >
                          Week
                        </button>
                        <button
                          onClick={() => { setViewMode('month'); setViewOffset(0); }}
                          className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                            viewMode === 'month'
                              ? 'bg-accent text-white'
                              : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                          }`}
                        >
                          Month
                        </button>
                      </div>

                      {/* Period Navigation */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setViewOffset(prev => prev + 1)}
                          disabled={!hasPrev}
                          className={`p-1.5 rounded transition-colors ${
                            hasPrev
                              ? 'hover:bg-light-surface dark:hover:bg-dark-surface text-light-text dark:text-dark-text'
                              : 'text-light-text-secondary/30 dark:text-dark-text-secondary/30 cursor-not-allowed'
                          }`}
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="text-sm font-medium text-light-text dark:text-dark-text min-w-[140px] text-center">
                          {periodLabel}
                        </span>
                        <button
                          onClick={() => setViewOffset(prev => prev - 1)}
                          disabled={!hasNext}
                          className={`p-1.5 rounded transition-colors ${
                            hasNext
                              ? 'hover:bg-light-surface dark:hover:bg-dark-surface text-light-text dark:text-dark-text'
                              : 'text-light-text-secondary/30 dark:text-dark-text-secondary/30 cursor-not-allowed'
                          }`}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Summary Stats */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-light-text-secondary dark:text-dark-text-secondary">
                          <span className="font-medium text-light-text dark:text-dark-text">{calendarData.summary.total_days}</span> total
                        </span>
                        <span className="text-green-600 dark:text-green-400 font-medium">
                          {calendarData.summary.days_with_journals} journals
                        </span>
                        {calendarData.summary.gap_days > 0 && (
                          <span className="text-amber-600 dark:text-amber-400 font-medium">
                            {calendarData.summary.gap_days} gaps
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Timeline List */}
                  <div className="flex-1 overflow-y-auto p-4">
                    <div className="space-y-2">
                      {filteredDays.length === 0 ? (
                        <div className="text-center py-8 text-light-text-secondary dark:text-dark-text-secondary">
                          No data for this period
                        </div>
                      ) : (
                        filteredDays.map((day) => {
                          const dateObj = new Date(day.date + 'T12:00:00')
                          const isExpanded = expandedDays.has(day.date)
                          const isCreatingJournal = dayJournalLoading === day.date

                          return (
                            <div
                              key={day.date}
                              className={`rounded-lg border border-border-primary overflow-hidden ${
                                day.status === 'gap' ? 'bg-amber-50/50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-800' :
                                day.status === 'complete' ? 'bg-green-50/30 dark:bg-green-900/10 border-green-200 dark:border-green-800' :
                                ''
                              }`}
                            >
                              {/* Day Header - Clickable */}
                              <div
                                onClick={() => day.has_activity && toggleDayExpanded(day.date)}
                                className={`flex items-center gap-3 p-3 ${day.has_activity ? 'cursor-pointer hover:bg-light-bg/50 dark:hover:bg-dark-bg/50' : ''}`}
                              >
                                {/* Expand Icon */}
                                {day.has_activity ? (
                                  <div className="w-4 h-4 flex items-center justify-center flex-shrink-0">
                                    {isExpanded ? (
                                      <ChevronDown className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                                    ) : (
                                      <ChevronRight className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                                    )}
                                  </div>
                                ) : (
                                  <div className="w-4 h-4 flex-shrink-0" />
                                )}

                                {/* Status Icon */}
                                <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                                  {day.status === 'complete' ? (
                                    <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                                  ) : day.status === 'gap' ? (
                                    <div className="w-5 h-5 rounded-full bg-amber-500 flex items-center justify-center">
                                      <span className="text-white text-xs font-bold">!</span>
                                    </div>
                                  ) : (
                                    <div className="w-5 h-5 rounded-full bg-gray-200 dark:bg-gray-700" />
                                  )}
                                </div>

                                {/* Date */}
                                <div className="w-28 flex-shrink-0">
                                  <p className={`text-sm font-medium ${
                                    day.status === 'no_activity'
                                      ? 'text-light-text-secondary dark:text-dark-text-secondary'
                                      : 'text-light-text dark:text-dark-text'
                                  }`}>
                                    {dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                                  </p>
                                </div>

                                {/* Summary Content */}
                                <div className="flex-1 min-w-0">
                                  {day.has_activity ? (
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                        {day.session_count} session{day.session_count !== 1 ? 's' : ''}
                                      </span>
                                      {day.journal ? (
                                        <span className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                                          <CheckCircle className="w-3 h-3" />
                                          Journal created
                                        </span>
                                      ) : (
                                        <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                                          No journal
                                        </span>
                                      )}
                                    </div>
                                  ) : (
                                    <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                                      No activity
                                    </span>
                                  )}
                                </div>

                                {/* Quick Action Buttons (visible without expanding) */}
                                {day.has_activity && (
                                  <div className="flex-shrink-0 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                                    {day.journal ? (
                                      <button
                                        onClick={() => viewJournalForDay(calendarData!.user_id, day.journal!.id)}
                                        className="px-2 py-1 text-xs bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
                                      >
                                        View Journal
                                      </button>
                                    ) : (
                                      <button
                                        onClick={() => createJournalForDay(calendarData!.user_id, day.date)}
                                        disabled={isCreatingJournal}
                                        className="px-2 py-1 text-xs bg-amber-500 hover:bg-amber-600 text-white rounded transition-colors disabled:opacity-50 flex items-center gap-1"
                                      >
                                        {isCreatingJournal ? (
                                          <>
                                            <Loader2 className="w-3 h-3 animate-spin" />
                                            Creating...
                                          </>
                                        ) : (
                                          <>
                                            <Play className="w-3 h-3" />
                                            Create Journal
                                          </>
                                        )}
                                      </button>
                                    )}
                                  </div>
                                )}
                              </div>

                              {/* Expanded Content */}
                              {isExpanded && day.has_activity && (
                                <div className="px-4 pb-4 border-t border-border-primary bg-light-bg/30 dark:bg-dark-bg/30">
                                  {/* Sessions List */}
                                  <div className="pt-3">
                                    <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-2">
                                      Sessions ({day.session_count})
                                    </p>
                                    <div className="space-y-1">
                                      {(day.sessions || []).map((sess, idx) => (
                                        <div
                                          key={idx}
                                          className="flex items-center gap-2 p-2 bg-light-surface dark:bg-dark-surface rounded border border-border-primary"
                                        >
                                          <MessageSquare className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary flex-shrink-0" />
                                          <span className="text-sm text-light-text dark:text-dark-text truncate">
                                            {sess.name || 'Untitled Session'}
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>

                                  {/* Journal Info (if exists) */}
                                  {day.journal && (
                                    <div className="pt-3 mt-3 border-t border-border-primary">
                                      <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-2">
                                        Journal Entry
                                      </p>
                                      {/* Topics */}
                                      {(day.journal.topics || []).length > 0 && (
                                        <div className="flex flex-wrap gap-1 mb-2">
                                          {day.journal.topics.map((topic, idx) => (
                                            <span
                                              key={idx}
                                              className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded text-xs"
                                            >
                                              {topic}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                      {/* Summary Preview */}
                                      {day.journal.summary_preview && (
                                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary line-clamp-3">
                                          {day.journal.summary_preview}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )
                        })
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )
      })()}

      {/* Run Details Modal */}
      {(selectedRun || modalLoading) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedRun(null)}>
          <div
            className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {modalLoading ? (
              <div className="p-8 flex justify-center items-center">
                <Loader2 className="w-8 h-8 animate-spin text-accent" />
              </div>
            ) : selectedRun && (
              <>
                {/* TOP: Workflow Information */}
                <div className="p-4 border-b border-border-primary flex-shrink-0 bg-light-bg dark:bg-dark-bg">
                  {/* Title row with close button */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {selectedRun.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : selectedRun.status === 'failed' ? (
                        <XCircle className="w-5 h-5 text-red-500" />
                      ) : (
                        <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                      )}
                      <h2 className="text-lg font-semibold text-light-text dark:text-dark-text">
                        {selectedRun.target_date
                          ? new Date(selectedRun.target_date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
                          : 'Daily Journal'
                        }
                      </h2>
                    </div>
                    <button
                      onClick={() => setSelectedRun(null)}
                      className="p-1.5 hover:bg-light-surface dark:hover:bg-dark-surface rounded-lg transition-colors"
                    >
                      <X className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                    </button>
                  </div>

                  {/* Info grid - compact */}
                  <div className="grid grid-cols-4 gap-x-4 gap-y-2 text-sm">
                    <div>
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">User</span>
                      <p className="text-light-text dark:text-dark-text truncate">{selectedRun.user_email || selectedRun.user_id.slice(0, 8)}</p>
                    </div>
                    <div>
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">Messages</span>
                      <p className="text-light-text dark:text-dark-text font-medium">{selectedRun.metrics?.messages || selectedRun.output_data?.message_count || 0}</p>
                    </div>
                    <div>
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">Sessions</span>
                      <p className="text-light-text dark:text-dark-text font-medium">{selectedRun.metrics?.sessions_fetched || selectedRun.output_data?.session_count || 0}</p>
                    </div>
                    <div>
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">Status</span>
                      <p className={`font-medium capitalize ${
                        selectedRun.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                        selectedRun.status === 'failed' ? 'text-red-600 dark:text-red-400' :
                        'text-blue-600 dark:text-blue-400'
                      }`}>{selectedRun.status}</p>
                    </div>
                    <div>
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">Started</span>
                      <p className="text-light-text dark:text-dark-text">{selectedRun.started_at ? new Date(selectedRun.started_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">Completed</span>
                      <p className="text-light-text dark:text-dark-text">{selectedRun.completed_at ? new Date(selectedRun.completed_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'N/A'}</p>
                    </div>
                    <div className="col-span-2">
                      <span className="text-light-text-secondary dark:text-dark-text-secondary text-xs">Run ID</span>
                      <p className="text-light-text dark:text-dark-text font-mono text-xs">{selectedRun.run_id}</p>
                    </div>
                  </div>
                </div>

                {/* MIDDLE: Journal Entry + Topics + Outcomes */}
                <div className="p-4 overflow-y-auto flex-1">
                  {/* Error Message */}
                  {selectedRun.status === 'failed' && (selectedRun.error || selectedRun.error_message) && (
                    <div className="bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800 p-4 mb-4">
                      <p className="text-sm text-red-700 dark:text-red-300">{selectedRun.error || selectedRun.error_message}</p>
                    </div>
                  )}

                  {/* Journal Entry */}
                  {selectedRun.status === 'completed' && selectedRun.journal_entry?.content && (() => {
                    // Split content into date header and body
                    const content = selectedRun.journal_entry.content
                    const lines = content.split('\n')
                    const dateHeader = lines[0] // "Day 57 - December 03, 2025"
                    const journalBody = lines.slice(1).join('\n').trim()

                    return (
                      <div className="bg-[#E4E4E2] dark:bg-[#2A2A2A] rounded-lg overflow-hidden mb-4">
                        {/* Date Header */}
                        <div className="px-5 pt-5 pb-3">
                          <h3 className="text-base font-semibold text-light-text dark:text-dark-text font-heading">
                            {dateHeader}
                          </h3>
                        </div>
                        {/* Divider */}
                        <div className="mx-5 border-b border-light-text/20 dark:border-dark-text/20" />
                        {/* Journal Body */}
                        <div className="px-5 pt-4 pb-5">
                          <p className="text-sm text-light-text dark:text-dark-text whitespace-pre-wrap font-sans leading-relaxed">
                            {journalBody}
                          </p>
                        </div>
                      </div>
                    )
                  })()}

                  {/* Topics */}
                  {selectedRun.status === 'completed' && ((selectedRun.journal_entry?.topics && selectedRun.journal_entry.topics.length > 0) ||
                    (selectedRun.output_data?.topics && selectedRun.output_data.topics.length > 0)) && (
                    <div className="mb-4">
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-2">Topics</p>
                      <div className="flex flex-wrap gap-1.5">
                        {(selectedRun.journal_entry?.topics || selectedRun.output_data?.topics || []).map((topic, idx) => (
                          <span key={idx} className="px-2 py-1 bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text rounded text-xs">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Outcomes */}
                  {selectedRun.status === 'completed' && ((selectedRun.journal_entry?.outcomes && selectedRun.journal_entry.outcomes.length > 0) ||
                    (selectedRun.output_data?.outcomes && selectedRun.output_data.outcomes.length > 0)) && (
                    <div className="mb-4">
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-2">Key Outcomes</p>
                      <ul className="space-y-1">
                        {(selectedRun.journal_entry?.outcomes || selectedRun.output_data?.outcomes || []).map((outcome, idx) => (
                          <li key={idx} className="text-sm text-light-text dark:text-dark-text flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            {outcome}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* BOTTOM: Workflow Report + Re-run */}
                <div className="p-4 border-t border-border-primary flex-shrink-0 bg-light-bg dark:bg-dark-bg">
                  {/* Workflow Report */}
                  {selectedRun.output_data?.report && (
                    <details className="mb-3">
                      <summary className="text-xs text-light-text-secondary dark:text-dark-text-secondary cursor-pointer hover:text-light-text dark:hover:text-dark-text flex items-center gap-1">
                        <ChevronRight className="w-3 h-3 group-open:rotate-90 transition-transform" />
                        View Workflow Report
                      </summary>
                      <pre className="mt-2 text-xs text-light-text-secondary dark:text-dark-text-secondary bg-light-surface dark:bg-dark-surface rounded-lg p-3 whitespace-pre-wrap overflow-auto max-h-32">
                        {selectedRun.output_data.report}
                      </pre>
                    </details>
                  )}

                  {/* Re-run button */}
                  {selectedRun.target_date && (
                    <div className="flex justify-end">
                      <button
                        onClick={() => {
                          triggerWorkflow(selectedRun.user_id, selectedRun.user_email || '', selectedRun.target_date || undefined)
                          setSelectedRun(null)
                        }}
                        disabled={triggerLoading === selectedRun.user_id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-accent hover:bg-accent/90 text-white rounded-lg transition-colors disabled:opacity-50"
                      >
                        {triggerLoading === selectedRun.user_id ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Re-running...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4" />
                            Re-run Workflow
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
