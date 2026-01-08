'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Calendar, Plus, ChevronLeft, Loader2, Edit2, Trash2, MapPin, Users } from 'lucide-react'
import { useCalendarData } from '@/hooks/useCalendarData'
import { CalendarEvent, CreateEventRequest } from '@/types/calendar'

interface CalendarPanelProps {
  isOpen: boolean
  onClose: () => void
}

type View = 'list' | 'detail' | 'create' | 'edit'

export default function CalendarPanel({ isOpen, onClose }: CalendarPanelProps) {
  const {
    events,
    currentEvent,
    loading,
    error,
    fetchEvents,
    fetchEventDetail,
    createEvent,
    updateEvent,
    deleteEvent,
    clearError,
    clearCurrentEvent
  } = useCalendarData()

  const [view, setView] = useState<View>('list')
  const [eventData, setEventData] = useState<CreateEventRequest>({
    summary: '',
    description: '',
    location: '',
    start: '',
    end: '',
    attendees: []
  })
  const [attendeeInput, setAttendeeInput] = useState('')
  const panelRef = useRef<HTMLDivElement>(null)

  // Get sidebar state from localStorage (same as TopBar)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)

  useEffect(() => {
    const checkSidebar = () => {
      const collapsed = localStorage.getItem('sidebarCollapsed') === 'true'
      setSidebarCollapsed(collapsed)
    }
    checkSidebar()
    window.addEventListener('storage', checkSidebar)
    return () => window.removeEventListener('storage', checkSidebar)
  }, [])

  // Load events when panel opens (next 7 days)
  useEffect(() => {
    if (isOpen) {
      const now = new Date()
      const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
      fetchEvents(now.toISOString(), weekFromNow.toISOString(), 50)
      setView('list')
    }
  }, [isOpen, fetchEvents])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  // Handle event click
  const handleEventClick = async (event: CalendarEvent) => {
    await fetchEventDetail(event.id)
    setView('detail')
  }

  // Handle create new event
  const handleCreateClick = () => {
    const now = new Date()
    const oneHourLater = new Date(now.getTime() + 60 * 60 * 1000)

    setEventData({
      summary: '',
      description: '',
      location: '',
      start: now.toISOString().slice(0, 16),
      end: oneHourLater.toISOString().slice(0, 16),
      attendees: []
    })
    setAttendeeInput('')
    setView('create')
  }

  // Handle edit event
  const handleEditClick = () => {
    if (!currentEvent) return

    setEventData({
      summary: currentEvent.summary,
      description: currentEvent.description || '',
      location: currentEvent.location || '',
      start: currentEvent.start.slice(0, 16),
      end: currentEvent.end.slice(0, 16),
      attendees: currentEvent.attendees?.map(a => a.email) || []
    })
    setAttendeeInput('')
    setView('edit')
  }

  // Handle create submit
  const handleCreateSubmit = async () => {
    const success = await createEvent({
      ...eventData,
      start: new Date(eventData.start).toISOString(),
      end: new Date(eventData.end).toISOString()
    })
    if (success) {
      setView('list')
    }
  }

  // Handle update submit
  const handleUpdateSubmit = async () => {
    if (!currentEvent) return

    const success = await updateEvent(currentEvent.id, {
      ...eventData,
      start: new Date(eventData.start).toISOString(),
      end: new Date(eventData.end).toISOString()
    })
    if (success) {
      setView('list')
      clearCurrentEvent()
    }
  }

  // Handle delete
  const handleDelete = async (eventId: string) => {
    if (!confirm('Are you sure you want to delete this event?')) return
    const success = await deleteEvent(eventId)
    if (success) {
      setView('list')
      clearCurrentEvent()
    }
  }

  // Add attendee
  const handleAddAttendee = () => {
    if (!attendeeInput.trim()) return
    if (eventData.attendees?.includes(attendeeInput.trim())) return

    setEventData({
      ...eventData,
      attendees: [...(eventData.attendees || []), attendeeInput.trim()]
    })
    setAttendeeInput('')
  }

  // Remove attendee
  const handleRemoveAttendee = (email: string) => {
    setEventData({
      ...eventData,
      attendees: eventData.attendees?.filter(a => a !== email) || []
    })
  }

  // Back to list
  const handleBack = () => {
    setView('list')
    clearCurrentEvent()
    clearError()
  }

  // Format date for display
  const formatEventDate = (start: string, end: string) => {
    const startDate = new Date(start)
    const endDate = new Date(end)

    const dateStr = startDate.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
    const startTime = startDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    })
    const endTime = endDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    })

    return `${dateStr}, ${startTime} - ${endTime}`
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'calc((100vh - 64px) * 0.25)', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`
            relative
            bg-light-surface dark:bg-dark-surface
            shadow-lg
            overflow-y-auto overflow-x-hidden
            flex flex-col
            border-b border-gray-200 dark:border-gray-700
            transition-all duration-300 ease-in-out
            ${sidebarCollapsed ? 'ml-16 mr-0' : 'ml-64 mr-0'}
            md:ml-0 md:mr-0
          `}
          style={{
            marginLeft: typeof window !== 'undefined' && window.innerWidth >= 768
              ? (sidebarCollapsed ? '4rem' : '16rem')
              : '0',
            marginRight: '0'
          }}
        >
          {/* Centered container */}
          <div className="w-full max-w-3xl mx-auto flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-light-bg dark:bg-dark-bg">
              <div className="flex items-center gap-3">
                {view !== 'list' && (
                  <button
                    onClick={handleBack}
                    className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
                    aria-label="Back"
                  >
                    <ChevronLeft size={20} />
                  </button>
                )}
                <Calendar size={20} className="text-accent" />
                <h2 className="text-lg font-heading font-semibold text-light-text dark:text-dark-text">
                  {view === 'list' && 'Upcoming Events'}
                  {view === 'detail' && 'Event Details'}
                  {view === 'create' && 'Create Event'}
                  {view === 'edit' && 'Edit Event'}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
                aria-label="Close"
              >
                <X size={20} />
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={32} className="animate-spin text-accent" />
                </div>
              )}

              {/* List View */}
              {!loading && view === 'list' && (
                <div>
                  {/* Create Button */}
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <button
                      onClick={handleCreateClick}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
                    >
                      <Plus size={18} />
                      Create Event
                    </button>
                  </div>

                  {/* Event List */}
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {events.length === 0 ? (
                      <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
                        No upcoming events
                      </div>
                    ) : (
                      events.map((event) => (
                        <button
                          key={event.id}
                          onClick={() => handleEventClick(event)}
                          className="w-full px-6 py-4 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors text-left"
                        >
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-light-text dark:text-dark-text">
                              {event.summary}
                            </p>
                            <p className="text-xs text-light-text/60 dark:text-dark-text/60">
                              {formatEventDate(event.start, event.end)}
                            </p>
                            {event.location && (
                              <div className="flex items-center gap-1 text-xs text-light-text/50 dark:text-dark-text/50">
                                <MapPin size={12} />
                                {event.location}
                              </div>
                            )}
                            {event.attendees && event.attendees.length > 0 && (
                              <div className="flex items-center gap-1 text-xs text-light-text/50 dark:text-dark-text/50">
                                <Users size={12} />
                                {event.attendees.length} attendee{event.attendees.length !== 1 ? 's' : ''}
                              </div>
                            )}
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Detail View */}
              {!loading && view === 'detail' && currentEvent && (
                <div className="p-6 space-y-4">
                  {/* Event Title */}
                  <h3 className="text-lg font-semibold text-light-text dark:text-dark-text">
                    {currentEvent.summary}
                  </h3>

                  {/* Event Time */}
                  <div className="flex items-start gap-2 text-sm text-light-text/70 dark:text-dark-text/70">
                    <Calendar size={16} className="mt-0.5" />
                    <span>{formatEventDate(currentEvent.start, currentEvent.end)}</span>
                  </div>

                  {/* Location */}
                  {currentEvent.location && (
                    <div className="flex items-start gap-2 text-sm text-light-text/70 dark:text-dark-text/70">
                      <MapPin size={16} className="mt-0.5" />
                      <span>{currentEvent.location}</span>
                    </div>
                  )}

                  {/* Attendees */}
                  {currentEvent.attendees && currentEvent.attendees.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-light-text dark:text-dark-text">
                        <Users size={16} />
                        Attendees
                      </div>
                      <div className="space-y-1">
                        {currentEvent.attendees.map((attendee, index) => (
                          <div key={index} className="text-sm text-light-text/70 dark:text-dark-text/70 pl-6">
                            {attendee.displayName || attendee.email}
                            {attendee.responseStatus && (
                              <span className="ml-2 text-xs text-light-text/50 dark:text-dark-text/50">
                                ({attendee.responseStatus})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Description */}
                  {currentEvent.description && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-light-text dark:text-dark-text">
                        Description
                      </p>
                      <p className="text-sm text-light-text/70 dark:text-dark-text/70 whitespace-pre-wrap">
                        {currentEvent.description}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                      onClick={handleEditClick}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
                    >
                      <Edit2 size={16} />
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(currentEvent.id)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-300 dark:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 font-sans transition-colors"
                    >
                      <Trash2 size={16} />
                      Delete
                    </button>
                  </div>
                </div>
              )}

              {/* Create/Edit Form */}
              {!loading && (view === 'create' || view === 'edit') && (
                <div className="p-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Event Title *
                    </label>
                    <input
                      type="text"
                      value={eventData.summary}
                      onChange={(e) => setEventData({ ...eventData, summary: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      placeholder="Meeting with team"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                        Start Time *
                      </label>
                      <input
                        type="datetime-local"
                        value={eventData.start}
                        onChange={(e) => setEventData({ ...eventData, start: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                        End Time *
                      </label>
                      <input
                        type="datetime-local"
                        value={eventData.end}
                        onChange={(e) => setEventData({ ...eventData, end: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      value={eventData.location}
                      onChange={(e) => setEventData({ ...eventData, location: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      placeholder="Conference Room A"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Description
                    </label>
                    <textarea
                      value={eventData.description}
                      onChange={(e) => setEventData({ ...eventData, description: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent resize-none font-body transition-colors"
                      placeholder="Event details..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Attendees
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="email"
                        value={attendeeInput}
                        onChange={(e) => setAttendeeInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddAttendee())}
                        className="flex-1 px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                        placeholder="email@example.com"
                      />
                      <button
                        onClick={handleAddAttendee}
                        className="px-4 py-2 rounded-lg bg-accent/10 hover:bg-accent/20 text-accent font-sans transition-colors"
                      >
                        Add
                      </button>
                    </div>
                    {eventData.attendees && eventData.attendees.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {eventData.attendees.map((email, index) => (
                          <div
                            key={index}
                            className="flex items-center gap-1 px-3 py-1 rounded-full bg-light-bg dark:bg-dark-bg border border-gray-300 dark:border-gray-600 text-sm"
                          >
                            <span className="text-light-text dark:text-dark-text">{email}</span>
                            <button
                              onClick={() => handleRemoveAttendee(email)}
                              className="ml-1 text-light-text/50 dark:text-dark-text/50 hover:text-red-500"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                      onClick={view === 'create' ? handleCreateSubmit : handleUpdateSubmit}
                      disabled={!eventData.summary || !eventData.start || !eventData.end}
                      className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {view === 'create' ? 'Create Event' : 'Save Changes'}
                    </button>
                    <button
                      onClick={handleBack}
                      className="px-4 py-2 rounded-lg hover:bg-accent/10 text-light-text dark:text-dark-text font-sans transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
