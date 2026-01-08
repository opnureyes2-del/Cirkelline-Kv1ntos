'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronLeft,
  ChevronRight,
  BookOpen,
  List,
  Grid,
  X
} from 'lucide-react'
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth, addWeeks, subWeeks, addMonths, subMonths, eachDayOfInterval, isSameDay } from 'date-fns'

interface JournalEntry {
  id: number
  journal_date: string
  summary: string
  topics: string[]
  outcomes: string[]
  message_count: number
  created_at: string | number
}

// Format date nicely
const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T12:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// Parse journal content
const parseJournalContent = (summary: string) => {
  const lines = summary.split('\n')
  const dateHeader = lines[0]
  const journalBody = lines.slice(1).join('\n').trim()
  const dayNumber = dateHeader.split(' - ')[0] || dateHeader
  return { dayNumber, journalBody }
}

export default function JournalsPage() {
  const endpoint = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // State
  const [journals, setJournals] = useState<JournalEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<'week' | 'month'>('month')
  const [displayMode, setDisplayMode] = useState<'calendar' | 'list'>('list')
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedJournal, setSelectedJournal] = useState<JournalEntry | null>(null)

  // Load all journals
  const loadJournals = useCallback(async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setLoading(false)
        return
      }

      const res = await fetch(`${endpoint}/api/journals?limit=1000`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (res.ok) {
        const data = await res.json()
        setJournals(data.journals || [])
      }
    } catch (error) {
      console.error('Failed to fetch journals:', error)
    } finally {
      setLoading(false)
    }
  }, [endpoint])

  useEffect(() => {
    loadJournals()
  }, [loadJournals])

  // Get date range based on view mode
  const dateRange = useMemo(() => {
    if (viewMode === 'week') {
      return {
        start: startOfWeek(currentDate, { weekStartsOn: 1 }),
        end: endOfWeek(currentDate, { weekStartsOn: 1 })
      }
    } else {
      return {
        start: startOfMonth(currentDate),
        end: endOfMonth(currentDate)
      }
    }
  }, [currentDate, viewMode])

  // Get days in current range
  const daysInRange = useMemo(() => {
    return eachDayOfInterval({ start: dateRange.start, end: dateRange.end })
  }, [dateRange])

  // Map journals to dates
  const journalsByDate = useMemo(() => {
    const map = new Map<string, JournalEntry>()
    journals.forEach(journal => {
      map.set(journal.journal_date, journal)
    })
    return map
  }, [journals])

  // Journals in current range for list view
  const journalsInRange = useMemo(() => {
    return journals.filter(journal => {
      const journalDate = new Date(journal.journal_date + 'T12:00:00')
      return journalDate >= dateRange.start && journalDate <= dateRange.end
    }).sort((a, b) => new Date(b.journal_date).getTime() - new Date(a.journal_date).getTime())
  }, [journals, dateRange])

  // Navigation
  const goToPrevious = () => {
    if (viewMode === 'week') {
      setCurrentDate(subWeeks(currentDate, 1))
    } else {
      setCurrentDate(subMonths(currentDate, 1))
    }
  }

  const goToNext = () => {
    if (viewMode === 'week') {
      setCurrentDate(addWeeks(currentDate, 1))
    } else {
      setCurrentDate(addMonths(currentDate, 1))
    }
  }

  const goToToday = () => {
    setCurrentDate(new Date())
  }

  // Get journal for a specific date
  const getJournalForDate = (date: Date): JournalEntry | undefined => {
    const dateStr = format(date, 'yyyy-MM-dd')
    return journalsByDate.get(dateStr)
  }

  // Navigation in modal
  const currentIndex = journals.findIndex(j => j.id === selectedJournal?.id)
  const prevJournal = currentIndex > 0 ? journals[currentIndex - 1] : null
  const nextJournal = currentIndex < journals.length - 1 ? journals[currentIndex + 1] : null

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
            Journals
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {loading ? 'Loading...' : `${journals.length} journal${journals.length !== 1 ? 's' : ''}`}
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
        >
          {/* Left Controls */}
          <div className="flex items-center gap-3">
            {/* View Mode Toggle (Week/Month) */}
            <div className="flex items-center gap-1 bg-light-surface dark:bg-dark-surface rounded-lg p-1">
              <button
                onClick={() => setViewMode('week')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'week'
                    ? 'bg-accent text-white'
                    : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                }`}
              >
                Week
              </button>
              <button
                onClick={() => setViewMode('month')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'month'
                    ? 'bg-accent text-white'
                    : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                }`}
              >
                Month
              </button>
            </div>

            {/* Display Mode Toggle (Calendar/List) */}
            <div className="flex items-center gap-1 bg-light-surface dark:bg-dark-surface rounded-lg p-1">
              <button
                onClick={() => setDisplayMode('calendar')}
                className={`p-2 rounded-md transition-colors ${
                  displayMode === 'calendar'
                    ? 'bg-accent text-white'
                    : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                }`}
                title="Calendar View"
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setDisplayMode('list')}
                className={`p-2 rounded-md transition-colors ${
                  displayMode === 'list'
                    ? 'bg-accent text-white'
                    : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
                }`}
                title="List View"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Right Controls - Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={goToPrevious}
              className="p-2 rounded-lg bg-light-surface dark:bg-dark-surface hover:bg-light-bg dark:hover:bg-dark-elevated transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-light-text dark:text-dark-text" />
            </button>
            <button
              onClick={goToToday}
              className="px-4 py-2 rounded-lg bg-light-surface dark:bg-dark-surface hover:bg-light-bg dark:hover:bg-dark-elevated text-sm font-medium text-light-text dark:text-dark-text transition-colors"
            >
              Today
            </button>
            <button
              onClick={goToNext}
              className="p-2 rounded-lg bg-light-surface dark:bg-dark-surface hover:bg-light-bg dark:hover:bg-dark-elevated transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-light-text dark:text-dark-text" />
            </button>
          </div>
        </motion.div>

        {/* Date Range Display */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.15 }}
          className="mb-6"
        >
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading">
            {viewMode === 'week'
              ? `${format(dateRange.start, 'MMM d')} - ${format(dateRange.end, 'MMM d, yyyy')}`
              : format(currentDate, 'MMMM yyyy')
            }
          </h2>
        </motion.div>

        {/* Content */}
        {loading ? (
          <div className={displayMode === 'calendar' ? 'grid grid-cols-7 gap-3' : 'space-y-3'}>
            {Array.from({ length: displayMode === 'calendar' ? (viewMode === 'week' ? 7 : 35) : 5 }).map((_, i) => (
              <div
                key={i}
                className={`${displayMode === 'calendar' ? 'h-32' : 'h-24'} rounded-lg bg-light-surface dark:bg-dark-surface animate-pulse`}
              />
            ))}
          </div>
        ) : displayMode === 'calendar' ? (
          <>
            {/* Day Headers */}
            <div className="grid grid-cols-7 gap-3 mb-3">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                <div key={day} className="text-center text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7 gap-2">
              {daysInRange.map((date, index) => {
                const journal = getJournalForDate(date)
                const isToday = isSameDay(date, new Date())
                const { dayNumber, journalBody } = journal ? parseJournalContent(journal.summary) : { dayNumber: '', journalBody: '' }

                return (
                  <motion.div
                    key={date.toISOString()}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.02, duration: 0.2 }}
                    onClick={() => journal && setSelectedJournal(journal)}
                    className={`
                      min-h-[130px] rounded-lg transition-all overflow-hidden border border-light-text/10 dark:border-dark-text/10
                      ${isToday
                        ? 'bg-accent/10 !border-accent'
                        : journal
                          ? 'bg-light-surface dark:bg-dark-surface hover:border-accent/50 cursor-pointer'
                          : 'bg-transparent opacity-50'
                      }
                    `}
                  >
                    {/* Date Header */}
                    <div className={`px-3 py-2 ${isToday ? 'bg-accent' : journal ? 'border-b border-border-primary/50' : ''}`}>
                      <span className={`text-sm font-semibold ${
                        isToday
                          ? 'text-white'
                          : journal
                            ? 'text-light-text dark:text-dark-text'
                            : 'text-light-text-tertiary dark:text-dark-text-tertiary'
                      }`}>
                        {format(date, 'd')}
                      </span>
                      {journal && !isToday && (
                        <span className="ml-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                          {dayNumber}
                        </span>
                      )}
                      {journal && isToday && (
                        <span className="ml-2 text-xs text-white/80">
                          {dayNumber}
                        </span>
                      )}
                    </div>

                    {/* Journal Preview */}
                    {journal && (
                      <div className="px-3 py-2">
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary line-clamp-3 leading-relaxed">
                          {journalBody.substring(0, 100)}...
                        </p>
                      </div>
                    )}

                    {/* Empty state for days without journal */}
                    {!journal && !isToday && (
                      <div className="flex-1 flex items-center justify-center h-16 opacity-30">
                        <BookOpen className="w-4 h-4 text-light-text-tertiary dark:text-dark-text-tertiary" />
                      </div>
                    )}
                  </motion.div>
                )
              })}
            </div>
          </>
        ) : (
          /* List View */
          <div className="space-y-3">
            {journalsInRange.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-12 h-12 mx-auto mb-4 text-light-text-tertiary dark:text-dark-text-tertiary" />
                <p className="text-light-text-secondary dark:text-dark-text-secondary">
                  No journals in this {viewMode}
                </p>
              </div>
            ) : (
              journalsInRange.map((journal, index) => {
                const { dayNumber, journalBody } = parseJournalContent(journal.summary)
                const isToday = isSameDay(new Date(journal.journal_date + 'T12:00:00'), new Date())

                return (
                  <motion.div
                    key={journal.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.2 }}
                    onClick={() => setSelectedJournal(journal)}
                    className={`
                      bg-light-surface dark:bg-dark-surface rounded-lg p-4 cursor-pointer
                      hover:bg-light-bg dark:hover:bg-dark-elevated transition-colors
                      ${isToday ? 'ring-2 ring-accent' : ''}
                    `}
                  >
                    <div className="flex items-start gap-4">
                      {/* Date Badge */}
                      <div className={`flex-shrink-0 w-14 h-14 rounded-lg flex flex-col items-center justify-center ${
                        isToday ? 'bg-accent text-white' : 'bg-light-bg dark:bg-dark-bg'
                      }`}>
                        <span className={`text-lg font-bold ${isToday ? 'text-white' : 'text-light-text dark:text-dark-text'}`}>
                          {format(new Date(journal.journal_date + 'T12:00:00'), 'd')}
                        </span>
                        <span className={`text-xs ${isToday ? 'text-white/80' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                          {format(new Date(journal.journal_date + 'T12:00:00'), 'MMM')}
                        </span>
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-light-text dark:text-dark-text font-heading">
                            {dayNumber}
                          </h3>
                          {isToday && (
                            <span className="px-2 py-0.5 text-xs bg-accent/10 text-accent rounded-full">
                              Today
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary line-clamp-2">
                          {journalBody}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                )
              })
            )}
          </div>
        )}
      </div>

      {/* Journal Detail Modal */}
      <AnimatePresence>
        {selectedJournal && (() => {
          const { dayNumber, journalBody } = parseJournalContent(selectedJournal.summary)

          return (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
              onClick={() => setSelectedJournal(null)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ duration: 0.2 }}
                className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-border-primary flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <BookOpen className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                    <div>
                      <h3 className="font-semibold text-light-text dark:text-dark-text font-heading">
                        Daily Journal, {dayNumber}
                      </h3>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        {formatDate(selectedJournal.journal_date)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedJournal(null)}
                    className="p-2 hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5 text-light-text-secondary dark:text-dark-text-secondary" />
                  </button>
                </div>

                {/* Journal Content */}
                <div className="flex-1 overflow-y-auto p-5">
                  <p className="text-sm text-light-text dark:text-dark-text whitespace-pre-wrap font-sans leading-relaxed">
                    {journalBody}
                  </p>
                </div>

                {/* Navigation Footer */}
                <div className="flex items-center justify-between p-4 border-t border-border-primary flex-shrink-0">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => prevJournal && setSelectedJournal(prevJournal)}
                      disabled={!prevJournal}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Prev
                    </button>
                    <button
                      onClick={() => nextJournal && setSelectedJournal(nextJournal)}
                      disabled={!nextJournal}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    {currentIndex + 1} of {journals.length}
                  </span>
                </div>
              </motion.div>
            </motion.div>
          )
        })()}
      </AnimatePresence>
    </div>
  )
}
