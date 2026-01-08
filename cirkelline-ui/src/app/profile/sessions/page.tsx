'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ArrowUpDown, Trash2, CheckSquare, Square, ChevronLeft, ChevronRight, MessageSquare, Calendar, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'

import SessionViewModal from '@/components/profile/SessionViewModal'
import DateRangePicker from '@/components/profile/DateRangePicker'
import { listUserSessionsAPI, bulkDeleteSessionsAPI, deleteSessionAPI, type SessionListItem, type SessionListFilters } from '@/api/os'

export default function SessionsPage() {
  // Use environment variable for API endpoint
  const endpoint = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // State
  const [sessions, setSessions] = useState<SessionListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [totalSessions, setTotalSessions] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [limit] = useState(18) // 18 sessions per page (3x6 grid)

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'session_name'>('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month' | 'custom'>('all')
  const [customDateFrom, setCustomDateFrom] = useState<Date | null>(null)
  const [customDateTo, setCustomDateTo] = useState<Date | null>(null)
  const [showCalendar, setShowCalendar] = useState(false)

  // Selection
  const [selectedSessions, setSelectedSessions] = useState<Set<string>>(new Set())
  const [showBulkToolbar, setShowBulkToolbar] = useState(false)

  // Modal
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Load sessions
  const loadSessions = useCallback(async () => {
    setLoading(true)
    console.log('🔄 loadSessions called - dateFilter:', dateFilter, 'customDateFrom:', customDateFrom, 'customDateTo:', customDateTo)
    try {
      const filters: SessionListFilters = {
        search: searchQuery || undefined,
        sortBy,
        sortOrder
      }

      // Date filters
      if (dateFilter === 'today') {
        const todayStart = new Date()
        todayStart.setHours(0, 0, 0, 0)
        filters.dateFrom = Math.floor(todayStart.getTime() / 1000)
      } else if (dateFilter === 'week') {
        const weekAgo = new Date()
        weekAgo.setDate(weekAgo.getDate() - 7)
        filters.dateFrom = Math.floor(weekAgo.getTime() / 1000)
      } else if (dateFilter === 'month') {
        const monthAgo = new Date()
        monthAgo.setMonth(monthAgo.getMonth() - 1)
        filters.dateFrom = Math.floor(monthAgo.getTime() / 1000)
      } else if (dateFilter === 'custom') {
        if (customDateFrom) {
          const fromDate = new Date(customDateFrom)
          fromDate.setHours(0, 0, 0, 0)
          filters.dateFrom = Math.floor(fromDate.getTime() / 1000)
          console.log('📅 Custom Date From:', customDateFrom, '→ Unix:', filters.dateFrom)
        }
        if (customDateTo) {
          const toDate = new Date(customDateTo)
          toDate.setHours(23, 59, 59, 999)
          filters.dateTo = Math.floor(toDate.getTime() / 1000)
          console.log('📅 Custom Date To:', customDateTo, '→ Unix:', filters.dateTo)
        }
        console.log('🔍 Sending date filters:', filters)
      }

      const response = await listUserSessionsAPI(endpoint, currentPage, limit, filters)
      setSessions(response.data)
      setTotalSessions(response.total)
    } catch (error) {
      console.error('Failed to load sessions:', error)
      toast.error('Failed to load sessions')
      setSessions([])
    } finally {
      setLoading(false)
    }
  }, [currentPage, searchQuery, sortBy, sortOrder, dateFilter, customDateFrom, customDateTo, endpoint, limit])

  // Load on mount and when filters change
  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // Pagination
  const totalPages = Math.ceil(totalSessions / limit)

  // Selection handlers
  const handleSelectSession = (sessionId: string, selected: boolean) => {
    const newSelected = new Set(selectedSessions)
    if (selected) {
      newSelected.add(sessionId)
    } else {
      newSelected.delete(sessionId)
    }
    setSelectedSessions(newSelected)
    setShowBulkToolbar(newSelected.size > 0)
  }

  const handleSelectAll = () => {
    if (selectedSessions.size === sessions.length) {
      // Deselect all
      setSelectedSessions(new Set())
      setShowBulkToolbar(false)
    } else {
      // Select all on current page
      const newSelected = new Set(sessions.map(s => s.session_id))
      setSelectedSessions(newSelected)
      setShowBulkToolbar(true)
    }
  }

  const allSelected = sessions.length > 0 && selectedSessions.size === sessions.length

  // Modal handlers
  const handleOpenSession = (sessionId: string) => {
    setSelectedSessionId(sessionId)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedSessionId(null)
  }

  const handleModalDelete = () => {
    loadSessions() // Reload after delete from modal
    handleCloseModal()
  }

  // Delete handlers
  const handleDeleteSingle = async (sessionId: string, sessionName: string) => {
    if (!confirm(`Delete session "${sessionName}"? This cannot be undone.`)) {
      return
    }

    try {
      await deleteSessionAPI(endpoint, '', sessionId)
      toast.success('Session deleted')
      loadSessions() // Reload
      // Remove from selection if selected
      const newSelected = new Set(selectedSessions)
      newSelected.delete(sessionId)
      setSelectedSessions(newSelected)
      setShowBulkToolbar(newSelected.size > 0)
    } catch (error) {
      console.error('Failed to delete session:', error)
      toast.error('Failed to delete session')
    }
  }

  const handleBulkDelete = async () => {
    const count = selectedSessions.size
    if (count === 0) return

    if (!confirm(`Delete ${count} selected session${count > 1 ? 's' : ''}? This cannot be undone.`)) {
      return
    }

    try {
      const sessionIds = Array.from(selectedSessions)
      await bulkDeleteSessionsAPI(endpoint, sessionIds)
      setSelectedSessions(new Set())
      setShowBulkToolbar(false)
      loadSessions() // Reload
    } catch (error) {
      console.error('Failed to delete sessions:', error)
      toast.error('Failed to delete sessions')
    }
  }

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading mb-2">
            Sessions
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {loading ? 'Loading...' : `${totalSessions} conversation${totalSessions !== 1 ? 's' : ''}`}
          </p>
        </motion.div>

        {/* Controls Bar */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="mb-6 flex flex-col sm:flex-row gap-4"
        >
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary" size={18} />
            <input
              type="text"
              placeholder="Search sessions..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setCurrentPage(1) // Reset to first page
              }}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       placeholder:text-light-text-secondary dark:placeholder:text-dark-text-secondary
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all"
            />
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [newSortBy, newSortOrder] = e.target.value.split('-') as [typeof sortBy, typeof sortOrder]
                setSortBy(newSortBy)
                setSortOrder(newSortOrder)
                setCurrentPage(1)
              }}
              className="appearance-none pl-10 pr-10 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all cursor-pointer"
            >
              <option value="updated_at-desc">Recently Updated</option>
              <option value="updated_at-asc">Least Recent</option>
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="session_name-asc">Name A-Z</option>
              <option value="session_name-desc">Name Z-A</option>
            </select>
            <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary pointer-events-none" size={18} />
          </div>

          {/* Date Filter Dropdown */}
          <div className="relative">
            <select
              value={dateFilter}
              onChange={(e) => {
                setDateFilter(e.target.value as typeof dateFilter)
                setCurrentPage(1)
              }}
              className="appearance-none pl-10 pr-10 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all cursor-pointer"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
            </select>
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary pointer-events-none" size={18} />
          </div>

          {/* Quick Calendar Access Button */}
          <button
            onClick={() => {
              setDateFilter('custom')
              setShowCalendar(true)
              setCurrentPage(1)
            }}
            className="px-4 py-2.5 rounded-lg
                     bg-light-surface dark:bg-dark-surface
                     border border-border-primary
                     hover:border-accent hover:bg-accent/5
                     text-light-text dark:text-dark-text
                     focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                     transition-all cursor-pointer
                     flex items-center gap-2 group"
            title="Select date range"
          >
            <Calendar size={18} className="text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
          </button>
        </motion.div>

        {/* Custom Date Range Calendar */}
        {dateFilter === 'custom' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-6 relative"
          >
            <button
              onClick={() => setShowCalendar(!showCalendar)}
              className="w-full px-6 py-4 rounded-xl bg-accent/5 border-2 border-accent/30
                       hover:border-accent/50 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center gap-3">
                <Calendar size={24} className="text-accent" />
                <div className="text-left">
                  <p className="text-sm font-medium text-light-text dark:text-dark-text">
                    {customDateFrom && customDateTo
                      ? `${customDateFrom.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${customDateTo.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
                      : customDateFrom
                      ? `From: ${customDateFrom.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
                      : 'Select date range'}
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    Click to {showCalendar ? 'hide' : 'open'} calendar
                  </p>
                </div>
              </div>
              <ChevronRight
                size={20}
                className={`text-accent transition-transform ${showCalendar ? 'rotate-90' : ''}`}
              />
            </button>

            {/* Calendar Picker */}
            <AnimatePresence>
              {showCalendar && (
                <DateRangePicker
                  fromDate={customDateFrom}
                  toDate={customDateTo}
                  onFromDateChange={(date) => {
                    setCustomDateFrom(date)
                    setDateFilter('custom')
                    setCurrentPage(1)
                  }}
                  onToDateChange={(date) => {
                    setCustomDateTo(date)
                    setDateFilter('custom')
                    setCurrentPage(1)
                  }}
                  onClose={() => setShowCalendar(false)}
                />
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Bulk Selection Toolbar */}
        {showBulkToolbar && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-4 p-4 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <button
                onClick={handleSelectAll}
                className="flex items-center gap-2 text-sm font-medium text-light-text dark:text-dark-text
                         hover:text-accent transition-colors"
              >
                {allSelected ? <CheckSquare size={18} /> : <Square size={18} />}
                {allSelected ? 'Deselect All' : 'Select All'}
              </button>
              <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                {selectedSessions.size} selected
              </span>
            </div>
            <button
              onClick={handleBulkDelete}
              className="flex items-center gap-2 px-4 py-2 rounded-lg
                       bg-red-500 hover:bg-red-600
                       text-white font-medium
                       transition-colors"
            >
              <Trash2 size={18} />
              Delete Selected
            </button>
          </motion.div>
        )}

        {/* Sessions List */}
        {loading ? (
          // Loading Skeletons
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-20 rounded-lg bg-light-surface/50 dark:bg-dark-surface/50
                         border border-border-primary animate-pulse"
              />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          // Empty State
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="text-center py-16"
          >
            <MessageSquare className="mx-auto mb-4 text-light-text-secondary dark:text-dark-text-secondary" size={64} />
            <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
              No sessions found
            </h3>
            <p className="text-light-text-secondary dark:text-dark-text-secondary mb-6">
              {searchQuery ? 'Try adjusting your search or filters' : 'Start a new conversation to see it here'}
            </p>
          </motion.div>
        ) : (
          // Sessions List
          <div className="space-y-3 mb-8">
            {sessions.map((session, index) => {
              const isSelected = selectedSessions.has(session.session_id)
              const updatedAt = session.updated_at
                ? formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })
                : 'Unknown'

              return (
                <motion.div
                  key={session.session_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.2 }}
                  className={`bg-light-surface dark:bg-dark-surface rounded-lg border
                           ${isSelected ? 'border-accent' : 'border-border-primary'}
                           overflow-hidden hover:border-accent/50 transition-all`}
                >
                  <div
                    onClick={() => handleOpenSession(session.session_id)}
                    className="p-2 cursor-pointer hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                  >
                    <div className="grid grid-cols-12 gap-2 items-center">
                      {/* Checkbox */}
                      <div className="col-span-1 flex items-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSelectSession(session.session_id, !isSelected)
                          }}
                          className={`w-5 h-5 rounded-lg border-2 transition-all cursor-pointer flex items-center justify-center
                            ${isSelected
                              ? 'bg-accent border-accent'
                              : 'border-border-primary hover:border-accent/70'
                            }`}
                        >
                          {isSelected && (
                            <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          )}
                        </button>
                      </div>

                      {/* Session Name */}
                      <div className="col-span-7">
                        <h3 className="text-xs font-semibold text-light-text dark:text-dark-text
                                     font-sans line-clamp-1">
                          {session.session_name || 'Untitled Session'}
                        </h3>
                        <div className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            {updatedAt}
                          </span>
                          {session.message_count !== undefined && (
                            <span className="flex items-center gap-1">
                              <MessageSquare size={12} />
                              {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Spacer */}
                      <div className="col-span-2" />

                      {/* Actions */}
                      <div className="col-span-2 flex items-center justify-end gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteSingle(session.session_id, session.session_name)
                          }}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium
                                   border border-border-primary
                                   hover:bg-red-500/10 hover:border-red-500/30
                                   text-red-600 dark:text-red-400
                                   transition-colors flex items-center gap-1.5"
                        >
                          <Trash2 size={14} />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {!loading && sessions.length > 0 && totalPages > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="flex items-center justify-center gap-2"
          >
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-border-primary
                       bg-light-surface dark:bg-dark-surface
                       text-light-text dark:text-dark-text
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-accent/10 hover:border-accent/30
                       transition-all"
            >
              <ChevronLeft size={20} />
            </button>

            <span className="px-4 py-2 text-sm text-light-text dark:text-dark-text">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-border-primary
                       bg-light-surface dark:bg-dark-surface
                       text-light-text dark:text-dark-text
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-accent/10 hover:border-accent/30
                       transition-all"
            >
              <ChevronRight size={20} />
            </button>
          </motion.div>
        )}
      </div>

      {/* Session View Modal */}
      <SessionViewModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        sessionId={selectedSessionId}
        endpoint={endpoint}
        onDelete={handleModalDelete}
      />
    </div>
  )
}
