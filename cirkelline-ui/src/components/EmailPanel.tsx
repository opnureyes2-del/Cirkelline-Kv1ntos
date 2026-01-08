'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Mail, Send, Reply, Archive, Trash2, ChevronLeft, Loader2 } from 'lucide-react'
import { useEmailData } from '@/hooks/useEmailData'
import { Email } from '@/types/email'

interface EmailPanelProps {
  isOpen: boolean
  onClose: () => void
}

type View = 'list' | 'detail' | 'compose' | 'reply'

export default function EmailPanel({ isOpen, onClose }: EmailPanelProps) {
  const {
    emails,
    currentEmail,
    loading,
    error,
    fetchEmails,
    fetchEmailDetail,
    sendEmail,
    replyToEmail,
    archiveEmail,
    deleteEmail,
    clearError,
    clearCurrentEmail
  } = useEmailData()

  const [view, setView] = useState<View>('list')
  const [composeData, setComposeData] = useState({ to: '', subject: '', body: '' })
  const [replyBody, setReplyBody] = useState('')
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

  // Load emails when panel opens
  useEffect(() => {
    if (isOpen) {
      fetchEmails(20)
      setView('list')
    }
  }, [isOpen, fetchEmails])

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

  // Handle email click
  const handleEmailClick = async (email: Email) => {
    await fetchEmailDetail(email.id)
    setView('detail')
  }

  // Handle compose
  const handleCompose = () => {
    setComposeData({ to: '', subject: '', body: '' })
    setView('compose')
  }

  // Handle send
  const handleSend = async () => {
    const success = await sendEmail(composeData)
    if (success) {
      setView('list')
      fetchEmails(20) // Refresh list
    }
  }

  // Handle reply
  const handleReplyClick = () => {
    setReplyBody('')
    setView('reply')
  }

  // Handle reply submit
  const handleReplySubmit = async () => {
    if (!currentEmail) return
    const success = await replyToEmail(currentEmail.id, { body: replyBody })
    if (success) {
      setView('list')
      clearCurrentEmail()
      fetchEmails(20) // Refresh list
    }
  }

  // Handle archive
  const handleArchive = async (emailId: string) => {
    const success = await archiveEmail(emailId)
    if (success) {
      setView('list')
      clearCurrentEmail()
    }
  }

  // Handle delete
  const handleDelete = async (emailId: string) => {
    if (!confirm('Are you sure you want to delete this email permanently?')) return
    const success = await deleteEmail(emailId)
    if (success) {
      setView('list')
      clearCurrentEmail()
    }
  }

  // Back to list
  const handleBack = () => {
    setView('list')
    clearCurrentEmail()
    clearError()
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
                <Mail size={20} className="text-accent" />
                <h2 className="text-lg font-heading font-semibold text-light-text dark:text-dark-text">
                  {view === 'list' && 'Inbox'}
                  {view === 'detail' && 'Email'}
                  {view === 'compose' && 'Compose Email'}
                  {view === 'reply' && 'Reply'}
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
                  {/* Compose Button */}
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <button
                      onClick={handleCompose}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
                    >
                      <Send size={18} />
                      Compose
                    </button>
                  </div>

                  {/* Email List */}
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {emails.length === 0 ? (
                      <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
                        No emails found
                      </div>
                    ) : (
                      emails.map((email) => (
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

              {/* Detail View */}
              {!loading && view === 'detail' && currentEmail && (
                <div className="p-6 space-y-4">
                  {/* Email Header */}
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold text-light-text dark:text-dark-text">
                      {currentEmail.subject}
                    </h3>
                    <div className="text-sm text-light-text/70 dark:text-dark-text/70">
                      <p><span className="font-medium">From:</span> {currentEmail.from}</p>
                      <p><span className="font-medium">To:</span> {currentEmail.to}</p>
                      <p><span className="font-medium">Date:</span> {new Date(currentEmail.date).toLocaleString()}</p>
                    </div>
                  </div>

                  {/* Email Body */}
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {currentEmail.body_html ? (
                      <div dangerouslySetInnerHTML={{ __html: currentEmail.body_html }} />
                    ) : (
                      <pre className="whitespace-pre-wrap font-body text-light-text dark:text-dark-text">
                        {currentEmail.body_text}
                      </pre>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <button
                      onClick={handleReplyClick}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
                    >
                      <Reply size={16} />
                      Reply
                    </button>
                    <button
                      onClick={() => handleArchive(currentEmail.id)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-light-bg dark:hover:bg-dark-bg text-light-text dark:text-dark-text font-sans transition-colors"
                    >
                      <Archive size={16} />
                      Archive
                    </button>
                    <button
                      onClick={() => handleDelete(currentEmail.id)}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-300 dark:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 font-sans transition-colors"
                    >
                      <Trash2 size={16} />
                      Delete
                    </button>
                  </div>
                </div>
              )}

              {/* Compose View */}
              {!loading && view === 'compose' && (
                <div className="p-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      To
                    </label>
                    <input
                      type="email"
                      value={composeData.to}
                      onChange={(e) => setComposeData({ ...composeData, to: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      placeholder="recipient@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Subject
                    </label>
                    <input
                      type="text"
                      value={composeData.subject}
                      onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      placeholder="Email subject"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Message
                    </label>
                    <textarea
                      value={composeData.body}
                      onChange={(e) => setComposeData({ ...composeData, body: e.target.value })}
                      rows={12}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent resize-none font-body transition-colors"
                      placeholder="Write your message..."
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSend}
                      disabled={!composeData.to || !composeData.subject}
                      className="flex items-center gap-2 px-6 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send size={16} />
                      Send
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

              {/* Reply View */}
              {!loading && view === 'reply' && currentEmail && (
                <div className="p-6 space-y-4">
                  <div className="p-4 rounded-lg bg-light-bg dark:bg-dark-bg border border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-light-text/70 dark:text-dark-text/70">
                      <span className="font-medium">Replying to:</span> {currentEmail.subject}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Your Reply
                    </label>
                    <textarea
                      value={replyBody}
                      onChange={(e) => setReplyBody(e.target.value)}
                      rows={12}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent resize-none font-body transition-colors"
                      placeholder="Write your reply..."
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleReplySubmit}
                      disabled={!replyBody.trim()}
                      className="flex items-center gap-2 px-6 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Reply size={16} />
                      Send Reply
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
