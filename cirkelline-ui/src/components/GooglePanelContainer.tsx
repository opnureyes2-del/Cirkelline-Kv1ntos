'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronLeft, Loader2 } from 'lucide-react'
import { useEmailData } from '@/hooks/useEmailData'
import { useCalendarData } from '@/hooks/useCalendarData'
import { Email } from '@/types/email'
import { CalendarEvent } from '@/types/calendar'

type PanelType = 'email' | 'calendar' | null

interface GooglePanelContainerProps {
  openPanel: PanelType
  onClose: () => void
}

type EmailView = 'list' | 'detail' | 'compose' | 'reply'
type CalendarView = 'list' | 'detail' | 'create' | 'edit'

export default function GooglePanelContainer({ openPanel, onClose }: GooglePanelContainerProps) {
  const panelRef = useRef<HTMLDivElement>(null)

  // Email state
  const emailData = useEmailData()
  const [emailView, setEmailView] = useState<EmailView>('list')

  // Calendar state
  const calendarData = useCalendarData()
  const [calendarView, setCalendarView] = useState<CalendarView>('list')

  // Connection status
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [googleConnected, setGoogleConnected] = useState(false)

  // Check login and Google connection status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const token = localStorage.getItem('token')
        setIsLoggedIn(!!token)

        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
        const response = await fetch(`${apiUrl}/api/oauth/google/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (response.ok) {
          const data = await response.json()
          setGoogleConnected(data.connected)
        }
      } catch (error) {
        console.error('Failed to check Google connection:', error)
      }
    }

    checkStatus()
  }, [])

  // Load data when panel opens (only if connected)
  useEffect(() => {
    if (!googleConnected) return

    if (openPanel === 'email') {
      emailData.fetchEmails(20)
      setEmailView('list')
    } else if (openPanel === 'calendar') {
      calendarData.fetchEvents()
      setCalendarView('list')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openPanel, googleConnected])

  // ESC key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (openPanel) {
      document.addEventListener('keydown', handleEscape)
    }
    return () => document.removeEventListener('keydown', handleEscape)
  }, [openPanel, onClose])

  // Email handlers
  const handleEmailClick = async (email: Email) => {
    await emailData.fetchEmailDetail(email.id)
    setEmailView('detail')
  }

  // TODO: Implement compose view
  // const handleCompose = () => {
  //   setComposeData({ to: '', subject: '', body: '' })
  //   setEmailView('compose')
  // }

  // TODO: Implement compose/reply views
  // const handleSend = async () => {
  //   const success = await emailData.sendEmail(composeData)
  //   if (success) {
  //     setEmailView('list')
  //     emailData.fetchEmails(20)
  //   }
  // }

  // const handleReplyClick = () => {
  //   setReplyBody('')
  //   setEmailView('reply')
  // }

  // const handleReplySubmit = async () => {
  //   if (!emailData.currentEmail) return
  //   const success = await emailData.replyToEmail(emailData.currentEmail.id, { body: replyBody })
  //   if (success) {
  //     setEmailView('list')
  //     emailData.clearCurrentEmail()
  //     emailData.fetchEmails(20)
  //   }
  // }

  const handleEmailBack = () => {
    setEmailView('list')
    emailData.clearCurrentEmail()
    emailData.clearError()
  }

  // Calendar handlers
  const handleEventClick = async (event: CalendarEvent) => {
    await calendarData.fetchEventDetail(event.id)
    setCalendarView('detail')
  }

  // TODO: Implement create event view
  // const handleCreateEvent = () => {
  //   setEventFormData({
  //     summary: '',
  //     description: '',
  //     location: '',
  //     start: '',
  //     end: '',
  //     attendees: ''
  //   })
  //   setCalendarView('create')
  // }

  // TODO: Implement create/edit views
  // const handleEventSubmit = async () => {
  //   const attendeeList = eventFormData.attendees
  //     .split(',')
  //     .map(e => e.trim())
  //     .filter(e => e.length > 0)

  //   const eventData = {
  //     summary: eventFormData.summary,
  //     description: eventFormData.description || undefined,
  //     location: eventFormData.location || undefined,
  //     start: eventFormData.start,
  //     end: eventFormData.end,
  //     attendees: attendeeList.length > 0 ? attendeeList : undefined
  //   }

  //   const success = await calendarData.createEvent(eventData)
  //   if (success) {
  //     setCalendarView('list')
  //     calendarData.fetchEvents()
  //   }
  // }

  const handleCalendarBack = () => {
    setCalendarView('list')
    calendarData.clearCurrentEvent()
    calendarData.clearError()
  }

  const isOpen = openPanel !== null

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'calc((100vh - 64px) * 0.25)', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="
            relative
            w-full
            bg-light-surface dark:bg-dark-surface
            shadow-lg
            overflow-hidden
            flex flex-col
            border-b border-gray-200 dark:border-gray-700
          "
        >
          {/* Centered container with scroll */}
          <div className="w-full max-w-3xl mx-auto flex flex-col h-full overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-light-bg dark:bg-dark-bg sticky top-0 z-10">
              <div className="flex items-center gap-2">
                {((openPanel === 'email' && emailView !== 'list') ||
                  (openPanel === 'calendar' && calendarView !== 'list')) && (
                  <button
                    onClick={openPanel === 'email' ? handleEmailBack : handleCalendarBack}
                    className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
                    aria-label="Back"
                  >
                    <ChevronLeft size={16} />
                  </button>
                )}
                {openPanel === 'email' ? (
                  <h2 className="text-sm font-heading font-medium text-light-text dark:text-dark-text">
                    {emailView === 'list' && 'Inbox'}
                    {emailView === 'detail' && 'Email'}
                    {emailView === 'compose' && 'Compose Email'}
                    {emailView === 'reply' && 'Reply'}
                  </h2>
                ) : (
                  <h2 className="text-sm font-heading font-medium text-light-text dark:text-dark-text">
                    {calendarView === 'list' && 'Upcoming Events'}
                    {calendarView === 'detail' && 'Event Details'}
                    {calendarView === 'create' && 'Create Event'}
                    {calendarView === 'edit' && 'Edit Event'}
                  </h2>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Error Display */}
            {(openPanel === 'email' ? emailData.error : calendarData.error) && (
              <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                <p className="text-sm text-red-600 dark:text-red-400">
                  {openPanel === 'email' ? emailData.error : calendarData.error}
                </p>
              </div>
            )}

            {/* Content - Smoothly transition between email and calendar */}
            <div className="flex-1 overflow-y-auto">
              {/* Show message if not logged in or not connected */}
              {!googleConnected && (
                <div className="flex items-center justify-center py-12 px-6">
                  <div className="text-center max-w-md">
                    <p className="text-sm text-light-text/70 dark:text-dark-text/70">
                      {!isLoggedIn
                        ? `Please login and connect to your Google account to view and manage your ${openPanel === 'email' ? 'email' : 'calendar'}`
                        : `Please connect to your Google account to view and manage your ${openPanel === 'email' ? 'email' : 'calendar'}`
                      }
                    </p>
                  </div>
                </div>
              )}

              {googleConnected && (openPanel === 'email' ? emailData.loading : calendarData.loading) && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={32} className="animate-spin text-accent" />
                </div>
              )}

              {/* Email Content */}
              {googleConnected && openPanel === 'email' && !emailData.loading && (
                <>
                  {emailView === 'list' && (
                    <div>
                      {/* TODO: Implement Compose button when compose view is ready */}
                      <div className="divide-y divide-gray-200 dark:divide-gray-700">
                        {emailData.emails.length === 0 ? (
                          <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
                            No emails found
                          </div>
                        ) : (
                          emailData.emails.map((email) => (
                            <button
                              key={email.id}
                              onClick={() => handleEmailClick(email)}
                              className="w-full px-6 py-4 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors text-left"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <p className={`text-sm font-medium truncate ${email.is_unread ? 'text-light-text dark:text-dark-text' : 'text-light-text/70 dark:text-dark-text/70'}`}>
                                      {email.from}
                                    </p>
                                    {email.is_unread && (
                                      <span className="w-2 h-2 rounded-full bg-accent" />
                                    )}
                                  </div>
                                  <p className={`text-sm mt-1 truncate ${email.is_unread ? 'font-medium text-light-text dark:text-dark-text' : 'text-light-text/70 dark:text-dark-text/70'}`}>
                                    {email.subject}
                                  </p>
                                  <p className="text-xs text-light-text/50 dark:text-dark-text/50 mt-1 truncate">
                                    {email.snippet}
                                  </p>
                                </div>
                                <span className="text-xs text-light-text/50 dark:text-dark-text/50 whitespace-nowrap">
                                  {new Date(email.date).toLocaleDateString()}
                                </span>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                  {/* Add other email views (detail, compose, reply) here - abbreviated for space */}
                </>
              )}

              {/* Calendar Content */}
              {googleConnected && openPanel === 'calendar' && !calendarData.loading && (
                <>
                  {calendarView === 'list' && (
                    <div>
                      {/* TODO: Implement Create Event button when create view is ready */}
                      <div className="divide-y divide-gray-200 dark:divide-gray-700">
                        {calendarData.events.length === 0 ? (
                          <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
                            No upcoming events
                          </div>
                        ) : (
                          calendarData.events.map((event) => (
                            <button
                              key={event.id}
                              onClick={() => handleEventClick(event)}
                              className="w-full px-6 py-4 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors text-left"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                                    {event.summary}
                                  </p>
                                  {event.description && (
                                    <p className="text-xs text-light-text/70 dark:text-dark-text/70 mt-1 truncate">
                                      {event.description}
                                    </p>
                                  )}
                                  <p className="text-xs text-light-text/50 dark:text-dark-text/50 mt-1">
                                    {new Date(event.start).toLocaleString()}
                                  </p>
                                </div>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                  {/* Add other calendar views here - abbreviated for space */}
                </>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
