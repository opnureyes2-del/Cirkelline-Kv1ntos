'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import type { ActivityLog } from '@/types/os'
import {
  Activity,
  Search,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Users,
  AlertTriangle,
  Calendar,
  Globe,
  Server,
  ChevronDown,
  X,
  RefreshCw
} from 'lucide-react'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'

export default function AdminActivityPage() {
  const [logs, setLogs] = useState<ActivityLog[]>([])
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState<string>('all')
  const [successFilter, setSuccessFilter] = useState<string>('all')
  const [userSearch, setUserSearch] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<string>('timestamp')
  const [sortOrder, setSortOrder] = useState<string>('desc')
  const [sseConnected, setSseConnected] = useState(false)
  const [currentTime, setCurrentTime] = useState(Date.now())
  const limit = 20
  const eventSourceRef = useRef<EventSource | null>(null)

  // Available action types for filter
  const actionTypes = [
    'all',
    // User Actions
    'user_login',
    'user_signup',
    // AI Interactions
    'chat_message',
    // Session Management
    'session_create',
    'session_rename',
    'session_delete',
    // Document Operations
    'document_upload',
    'document_delete',
    'document_list',
    // Memories
    'memories_get',
    // Preferences
    'preferences_get',
    'preferences_update',
    // Admin Actions
    'admin_list_users',
    'admin_view_activity_logs',
    'admin_list_feedback',
    // Feedback
    'feedback_unread_count'
  ]

  // Fetch activity logs
  const fetchLogs = useCallback(async () => {
    setLoading(true)

    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const actionParam = actionFilter !== 'all' ? `&action_filter=${actionFilter}` : ''
      const successParam = successFilter !== 'all' ? `&success_filter=${successFilter}` : ''
      const userParam = userSearch ? `&user_search=${encodeURIComponent(userSearch)}` : ''
      const sortByParam = `&sort_by=${sortBy}`
      const sortOrderParam = `&sort_order=${sortOrder}`

      const response = await fetch(
        `${apiUrl}/api/admin/activity?page=${page}&limit=${limit}${actionParam}${successParam}${userParam}${sortByParam}${sortOrderParam}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setLogs(data.data || [])
        setTotal(data.total || 0)
      } else {
        toast.error('Failed to load activity logs')
      }
    } catch (error) {
      console.error('Activity logs fetch error:', error)
      toast.error('Failed to load activity logs')
    } finally {
      setLoading(false)
    }
  }, [page, actionFilter, successFilter, userSearch, sortBy, sortOrder])

  // Initial fetch
  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  // SSE connection for real-time updates
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

    // Create EventSource for SSE (note: EventSource doesn't support custom headers)
    // We'll use a workaround by including the token in the URL as a query param
    const eventSource = new EventSource(
      `${apiUrl}/api/admin/activity/stream?token=${token}`,
      {
        withCredentials: false
      }
    )

    eventSource.onopen = () => {
      console.log('✅ SSE connected - Real-time activity logs enabled')
      setSseConnected(true)
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'connected') {
          console.log('SSE connection established')
          return
        }

        if (data.type === 'new_activity') {
          const newLog = data.data

          // Only add to logs if on page 1 (most recent page)
          if (page === 1) {
            setLogs((prevLogs) => {
              // Check if log already exists (prevent duplicates)
              if (prevLogs.some(log => log.id === newLog.id)) {
                return prevLogs
              }

              // Add new log to the beginning
              const updatedLogs = [newLog, ...prevLogs]

              // Keep only the limit number of logs
              return updatedLogs.slice(0, limit)
            })

            // Update total count
            setTotal((prevTotal) => prevTotal + 1)

            // Show toast notification
            const actionName = formatActionType(newLog.action_type)
            toast.success(`New activity: ${actionName}`, {
              duration: 2000,
              position: 'bottom-right'
            })
          }
        }
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('❌ SSE connection error:', error)
      setSseConnected(false)
      eventSource.close()
    }

    eventSourceRef.current = eventSource

    return () => {
      console.log('Closing SSE connection')
      eventSource.close()
      setSseConnected(false)
    }
  }, [page, limit])

  // Update current time every 30 seconds to refresh relative timestamps
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now())
    }, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  // Handle search
  const handleSearch = () => {
    setPage(1)
    fetchLogs()
  }

  // Format timestamp
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // Format relative time
  const formatRelativeTime = (timestamp: number) => {
    const diff = currentTime - (timestamp * 1000)
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (seconds < 60) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  // Format action type for display
  const formatActionType = (action: string) => {
    return action.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }

  // Get status badge colors
  const getStatusBadge = (success: boolean, statusCode: number) => {
    if (success && statusCode >= 200 && statusCode < 300) {
      return 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
    } else if (statusCode >= 400 && statusCode < 500) {
      return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400'
    } else if (statusCode >= 500) {
      return 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
    }
    return 'bg-gray-100 dark:bg-gray-900/30 text-gray-600 dark:text-gray-400'
  }

  // Get method badge color
  const getMethodBadge = (method: string) => {
    const colors: Record<string, string> = {
      GET: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
      POST: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
      PUT: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400',
      PATCH: 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400',
      DELETE: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
    }
    return colors[method] || 'bg-gray-100 dark:bg-gray-900/30 text-gray-600 dark:text-gray-400'
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-light-text dark:text-dark-text font-heading">
                Activity Logs
              </h1>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans mt-1">
                Monitor all system activity and user actions
              </p>
            </div>

            {/* Auto-Refresh Controls */}
            <div className="flex items-center gap-3">
              {/* Last Refresh Time */}
              {/* Real-time Connection Status */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all ${
                sseConnected
                  ? 'border-green-500 bg-green-500/10 text-green-600 dark:text-green-400'
                  : 'border-yellow-500 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
              }`}>
                <motion.div
                  animate={sseConnected ? { scale: [1, 1.2, 1] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <div className={`w-2 h-2 rounded-full ${
                    sseConnected ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                </motion.div>
                <span className="text-xs font-medium">
                  {sseConnected ? 'Live' : 'Connecting...'}
                </span>
              </div>

              {/* Manual Refresh Button */}
              <button
                onClick={() => fetchLogs()}
                disabled={loading}
                className="p-2 rounded-lg border border-border-primary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary disabled:opacity-50 transition-colors"
                title="Refresh now"
              >
                <RefreshCw
                  size={18}
                  className={`text-light-text dark:text-dark-text ${loading ? 'animate-spin' : ''}`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* User Search */}
            <div>
              <label className="block text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">
                Search User
              </label>
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary" />
                  <input
                    type="text"
                    placeholder="Email or ID..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    className="w-full pl-9 pr-8 py-2 rounded-lg border border-border-primary bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                  {userSearch && (
                    <button
                      onClick={() => {
                        setUserSearch('')
                        setPage(1)
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-light-text-secondary hover:text-light-text dark:hover:text-dark-text"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Action Filter */}
            <div>
              <label className="block text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">
                Action Type
              </label>
              <select
                value={actionFilter}
                onChange={(e) => {
                  setActionFilter(e.target.value)
                  setPage(1)
                }}
                className="w-full px-3 py-2 rounded-lg border border-border-primary bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
              >
                {actionTypes.map(action => (
                  <option key={action} value={action}>
                    {action === 'all' ? 'All Actions' : formatActionType(action)}
                  </option>
                ))}
              </select>
            </div>

            {/* Success Filter */}
            <div>
              <label className="block text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">
                Status
              </label>
              <select
                value={successFilter}
                onChange={(e) => {
                  setSuccessFilter(e.target.value)
                  setPage(1)
                }}
                className="w-full px-3 py-2 rounded-lg border border-border-primary bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <option value="all">All Status</option>
                <option value="success">Success Only</option>
                <option value="failure">Failures Only</option>
              </select>
            </div>

            {/* Sort Options */}
            <div>
              <label className="block text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">
                Sort By
              </label>
              <div className="flex gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg border border-border-primary bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="timestamp">Time</option>
                  <option value="action_type">Action</option>
                  <option value="duration_ms">Duration</option>
                  <option value="status_code">Status</option>
                </select>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 rounded-lg border border-border-primary hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors"
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </button>
              </div>
            </div>
          </div>

          {/* Filter Summary */}
          <div className="mt-4 pt-4 border-t border-border-secondary flex items-center justify-between">
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
              Showing {logs.length} of {total.toLocaleString()} results
              {actionFilter !== 'all' && ` • Filter: ${formatActionType(actionFilter)}`}
              {successFilter !== 'all' && ` • ${successFilter === 'success' ? 'Success' : 'Failures'} only`}
              {userSearch && ` • User: "${userSearch}"`}
            </p>
            {(actionFilter !== 'all' || successFilter !== 'all' || userSearch) && (
              <button
                onClick={() => {
                  setActionFilter('all')
                  setSuccessFilter('all')
                  setUserSearch('')
                  setPage(1)
                }}
                className="text-xs px-3 py-1 rounded-lg bg-accent/20 text-accent hover:bg-accent/30 transition-colors font-sans"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Empty State */}
        {!loading && logs.length === 0 && (
          <div className="text-center py-12">
            <Activity className="w-16 h-16 mx-auto text-light-text-secondary dark:text-dark-text-secondary mb-4" />
            <p className="text-lg text-light-text dark:text-dark-text font-heading mb-2">
              No activity logs found
            </p>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
              {actionFilter !== 'all' || successFilter !== 'all' || userSearch
                ? 'Try adjusting your filters'
                : 'Activity logs will appear here as users interact with the system'}
            </p>
          </div>
        )}

        {/* Logs Table */}
        {!loading && logs.length > 0 && (
          <div className="space-y-3">
            {logs.map((log) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary overflow-hidden"
              >
                {/* Row Header */}
                <div
                  onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                  className="p-4 cursor-pointer hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                >
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                    {/* Status Icon */}
                    <div className="md:col-span-1 flex items-center">
                      <div className={`p-2 rounded-lg ${log.success ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                        {log.success ? (
                          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                        )}
                      </div>
                    </div>

                    {/* Main Info */}
                    <div className="md:col-span-7">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getMethodBadge(log.http_method)}`}>
                          {log.http_method}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(log.success, log.status_code)}`}>
                          {log.status_code}
                        </span>
                        {log.is_admin && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                            Admin
                          </span>
                        )}
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                          {formatRelativeTime(log.timestamp)}
                        </p>
                      </div>
                      <p className="text-sm font-semibold text-light-text dark:text-dark-text font-sans mb-1">
                        {formatActionType(log.action_type)}
                      </p>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-mono">
                        {log.endpoint}
                      </p>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mt-1">
                        {log.user_email || log.user_id || 'Unknown user'}
                        {log.duration_ms && ` • ${log.duration_ms}ms`}
                      </p>
                    </div>

                    {/* Quick Info */}
                    <div className="md:col-span-3">
                      <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                        <div className="flex items-center gap-1 mb-1">
                          <Globe size={12} />
                          <span className="font-mono">{log.ip_address || 'N/A'}</span>
                        </div>
                        {log.error_message && (
                          <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
                            <AlertTriangle size={12} />
                            <span className="truncate">{log.error_message.substring(0, 30)}...</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Expand Button */}
                    <div className="md:col-span-1 flex items-center justify-end">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setExpandedId(expandedId === log.id ? null : log.id)
                        }}
                        className="p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                      >
                        <ChevronDown
                          size={18}
                          className={`text-light-text-secondary dark:text-dark-text-secondary transition-transform ${expandedId === log.id ? 'rotate-180' : ''}`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                <AnimatePresence>
                  {expandedId === log.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="border-t border-border-secondary overflow-hidden"
                    >
                      <div className="p-4 space-y-4">
                        {/* Timestamp Details */}
                        <div>
                          <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                            <Calendar size={14} /> Timestamp
                          </h4>
                          <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                            <p className="text-sm text-light-text dark:text-dark-text font-sans">
                              {formatDate(log.timestamp)}
                            </p>
                          </div>
                        </div>

                        {/* User Details */}
                        <div>
                          <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                            <Users size={14} /> User Information
                          </h4>
                          <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2 text-xs font-sans">
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Email:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">{log.user_email || 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Display Name:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">{log.user_display_name || 'N/A'}</span>
                              </div>
                              <div className="col-span-2">
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">User ID:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text font-mono">{log.user_id || 'N/A'}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Request Details */}
                        <div>
                          <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                            <Server size={14} /> Request Details
                          </h4>
                          <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2 text-xs font-sans">
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Method:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text font-mono">{log.http_method}</span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Status:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">{log.status_code}</span>
                              </div>
                              <div className="col-span-2">
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Endpoint:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text font-mono break-all">{log.endpoint}</span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Duration:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">{log.duration_ms ? `${log.duration_ms}ms` : 'N/A'}</span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">IP Address:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text font-mono">{log.ip_address || 'N/A'}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Error Details (if applicable) */}
                        {log.error_message && (
                          <div>
                            <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                              <AlertTriangle size={14} className="text-red-600 dark:text-red-400" /> Error Details
                            </h4>
                            <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg space-y-2">
                              <div>
                                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mb-1">Error Type:</p>
                                <p className="text-sm text-red-600 dark:text-red-400 font-mono">{log.error_type || 'Unknown'}</p>
                              </div>
                              <div>
                                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mb-1">Error Message:</p>
                                <p className="text-sm text-red-600 dark:text-red-400 font-sans">{log.error_message}</p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Additional Details (JSONB) */}
                        {log.details && Object.keys(log.details).length > 0 && (
                          <div>
                            <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">Additional Details</h4>
                            <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg max-h-64 overflow-y-auto">
                              <pre className="text-xs text-light-text dark:text-dark-text font-mono overflow-x-auto">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}

                        {/* User Agent */}
                        {log.user_agent && (
                          <div>
                            <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">User Agent</h4>
                            <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                              <p className="text-xs text-light-text dark:text-dark-text font-mono break-all">{log.user_agent}</p>
                            </div>
                          </div>
                        )}

                        {/* Resource Info (if applicable) */}
                        {(log.target_user_id || log.target_resource_id || log.resource_type) && (
                          <div>
                            <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">Resource Information</h4>
                            <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2 text-xs font-sans">
                              {log.resource_type && (
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Type:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text">{log.resource_type}</span>
                                </div>
                              )}
                              {log.target_resource_id && (
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Resource ID:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text font-mono">{log.target_resource_id}</span>
                                </div>
                              )}
                              {log.target_user_id && (
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Target User:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text font-mono">{log.target_user_id}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Log ID */}
                        <div className="pt-2 border-t border-border-secondary">
                          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                            Log ID: <span className="font-mono">{log.id}</span>
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {!loading && logs.length > 0 && totalPages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
              Page {page} of {totalPages} • Showing {logs.length} of {total.toLocaleString()} logs
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed text-light-text dark:text-dark-text transition-colors"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg border border-primary hover:bg-light-bg dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed text-light-text dark:text-dark-text transition-colors"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
