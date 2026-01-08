'use client'

import { useEffect, useState, useCallback } from 'react'
import type { FeedbackSubmission } from '@/types/os'
import { ThumbsUp, ThumbsDown, ChevronLeft, ChevronRight, Filter, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'

export default function AdminFeedbackPage() {
  const [feedback, setFeedback] = useState<FeedbackSubmission[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [unreadCount, setUnreadCount] = useState(0)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const limit = 20

  // Fetch feedback
  const fetchFeedback = useCallback(async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const statusParam = statusFilter !== 'all' ? `&status=${statusFilter}` : ''
      const response = await fetch(
        `${apiUrl}/api/feedback?page=${page}&limit=${limit}${statusParam}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setFeedback(data.data || [])
        setTotal(data.total || 0)
        setUnreadCount(data.unread_count || 0)
      } else {
        toast.error('Failed to load feedback')
      }
    } catch (error) {
      console.error('Feedback fetch error:', error)
      toast.error('Failed to load feedback')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter])

  useEffect(() => {
    fetchFeedback()
  }, [fetchFeedback])

  // Update feedback status
  const updateStatus = async (feedbackId: string, newStatus: 'unread' | 'seen' | 'done') => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/feedback/${feedbackId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      })

      if (response.ok) {
        toast.success(`Marked as ${newStatus}`)
        fetchFeedback() // Refresh list
        // Notify UserDropdown to refresh count
        window.dispatchEvent(new CustomEvent('feedbackStatusChanged'))
      } else {
        toast.error('Failed to update status')
      }
    } catch (error) {
      console.error('Status update error:', error)
      toast.error('Failed to update status')
    }
  }

  // Format timestamp
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Truncate text
  const truncate = (text: string, length: number) => {
    if (text.length <= length) return text
    return text.substring(0, length) + '...'
  }

  // Status badge colors
  const getStatusBadge = (status: string) => {
    const colors = {
      unread: 'bg-accent/20 text-accent',
      seen: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
      done: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
    }
    return colors[status as keyof typeof colors] || colors.unread
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-light-text dark:text-dark-text font-heading">
              User Feedback
            </h1>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans mt-1">
              {unreadCount > 0 && (
                <span className="font-semibold text-accent">{unreadCount} unread</span>
              )}
              {unreadCount > 0 && total > 0 && ' • '}
              {total > 0 && `${total} total`}
            </p>
          </div>

          {/* Filter */}
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="px-3 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="all">All Status</option>
              <option value="unread">Unread</option>
              <option value="seen">Seen</option>
              <option value="done">Done</option>
            </select>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Empty State */}
        {!loading && feedback.length === 0 && (
          <div className="text-center py-12">
            <MessageSquare className="w-16 h-16 mx-auto text-light-text-secondary dark:text-dark-text-secondary mb-4" />
            <p className="text-lg text-light-text dark:text-dark-text font-heading mb-2">
              No feedback yet
            </p>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
              Feedback submitted by users will appear here
            </p>
          </div>
        )}

        {/* Feedback Table */}
        {!loading && feedback.length > 0 && (
          <div className="space-y-3">
            {feedback.map((item) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary overflow-hidden"
              >
                {/* Row Header */}
                <div
                  onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  className="p-4 cursor-pointer hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                >
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                    {/* Feedback Type Icon */}
                    <div className="md:col-span-1 flex items-center">
                      {item.feedback_type === 'positive' ? (
                        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                          <ThumbsUp className="w-5 h-5 text-green-600 dark:text-green-400" />
                        </div>
                      ) : (
                        <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
                          <ThumbsDown className="w-5 h-5 text-red-600 dark:text-red-400" />
                        </div>
                      )}
                    </div>

                    {/* User & Message */}
                    <div className="md:col-span-7">
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mb-1">
                        {item.user_email} • {formatDate(item.created_at)}
                      </p>
                      <p className="text-sm text-light-text dark:text-dark-text font-sans">
                        {truncate(item.message_content, 150)}
                      </p>
                      {item.user_comments && (
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mt-2 italic">
                          Comment: {truncate(item.user_comments, 100)}
                        </p>
                      )}
                    </div>

                    {/* Status Badge */}
                    <div className="md:col-span-2 flex items-center">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(item.status)}`}>
                        {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="md:col-span-2 flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setExpandedId(expandedId === item.id ? null : item.id)
                        }}
                        className="text-xs px-3 py-1.5 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg text-light-text dark:text-dark-text transition-colors font-sans"
                      >
                        {expandedId === item.id ? 'Collapse' : 'Expand'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                <AnimatePresence>
                  {expandedId === item.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="border-t border-border-secondary overflow-hidden"
                    >
                      <div className="p-4 space-y-4">
                        {/* Full Message */}
                        <div>
                          <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">
                            Full Message:
                          </h4>
                          <div className="bg-accent/10 p-3 rounded-lg max-h-48 overflow-y-auto">
                            <p className="text-sm text-light-text dark:text-dark-text font-sans whitespace-pre-wrap">
                              {item.message_content}
                            </p>
                          </div>
                        </div>

                        {/* User Comments */}
                        {item.user_comments && (
                          <div>
                            <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">
                              User Comments:
                            </h4>
                            <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                              <p className="text-sm text-light-text dark:text-dark-text font-sans whitespace-pre-wrap">
                                {item.user_comments}
                              </p>
                            </div>
                          </div>
                        )}

                        {/* Metadata */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                          <div>
                            <span className="font-semibold">Session ID:</span> {item.session_id || 'None'}
                          </div>
                          <div>
                            <span className="font-semibold">Feedback ID:</span> {item.id.substring(0, 8)}...
                          </div>
                        </div>

                        {/* Status Change Buttons */}
                        <div className="flex items-center gap-2 pt-2 border-t border-border-secondary">
                          <p className="text-xs font-semibold text-light-text dark:text-dark-text font-sans">
                            Mark as:
                          </p>
                          <button
                            onClick={() => updateStatus(item.id, 'unread')}
                            disabled={item.status === 'unread'}
                            className="text-xs px-3 py-1.5 rounded-lg bg-accent/20 text-accent hover:bg-accent/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-sans"
                          >
                            Unread
                          </button>
                          <button
                            onClick={() => updateStatus(item.id, 'seen')}
                            disabled={item.status === 'seen'}
                            className="text-xs px-3 py-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-sans"
                          >
                            Seen
                          </button>
                          <button
                            onClick={() => updateStatus(item.id, 'done')}
                            disabled={item.status === 'done'}
                            className="text-xs px-3 py-1.5 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-sans"
                          >
                            Done
                          </button>
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
        {!loading && feedback.length > 0 && totalPages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
              Page {page} of {totalPages}
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
                className="p-2 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed text-light-text dark:text-dark-text transition-colors"
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
