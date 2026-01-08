'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Trash2, Loader2, MessageSquare } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'

import { getSessionDetailsAPI, deleteSessionAPI } from '@/api/os'
import type { ChatMessage } from '@/types/os'

interface SessionViewModalProps {
  isOpen: boolean
  onClose: () => void
  sessionId: string | null
  endpoint: string
  onDelete?: () => void
}

interface SessionData {
  session_id: string
  session_name: string
  chat_history: ChatMessage[]
}

export default function SessionViewModal({
  isOpen,
  onClose,
  sessionId,
  endpoint,
  onDelete
}: SessionViewModalProps) {
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Fetch session data when modal opens
  useEffect(() => {
    const fetchSession = async () => {
      if (!sessionId) return

      setLoading(true)
      try {
        const data = await getSessionDetailsAPI(endpoint, sessionId)
        setSession(data)
      } catch (error) {
        console.error('Failed to fetch session:', error)
        toast.error('Failed to load session')
        onClose()
      } finally {
        setLoading(false)
      }
    }

    if (isOpen && sessionId) {
      fetchSession()
    } else {
      setSession(null)
    }
  }, [isOpen, sessionId, endpoint, onClose])

  const handleDelete = async () => {
    if (!sessionId) return

    if (!confirm('Delete this session? This cannot be undone.')) {
      return
    }

    setDeleting(true)
    try {
      await deleteSessionAPI(endpoint, '', sessionId)
      toast.success('Session deleted')
      onDelete?.()
      onClose()
    } catch (error) {
      console.error('Failed to delete session:', error)
      toast.error('Failed to delete session')
    } finally {
      setDeleting(false)
    }
  }

  // Extract all messages from chat_history
  const messages = session?.chat_history || []

  // Filter out system, tool, and delegation messages - show user and assistant messages
  // Note: AGNO uses 'user' and 'assistant' roles (not 'agent')
  // Also filter out messages without content or with "(No content)"
  const displayMessages = messages.filter(
    msg => (msg.role === 'user' || msg.role === 'assistant') &&
           msg.content &&
           msg.content.trim() !== '' &&
           msg.content !== '(No content)'
  )

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-4 md:inset-8 lg:inset-16 z-50
                     bg-light-bg dark:bg-dark-bg
                     rounded-2xl shadow-2xl
                     flex flex-col overflow-hidden
                     border border-border-primary"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4
                          border-b border-border-primary
                          bg-light-surface dark:bg-dark-surface">
              <div className="flex-1 min-w-0 mr-4">
                <h2 className="text-xl font-bold text-light-text dark:text-dark-text
                             font-heading truncate">
                  {session?.session_name || 'Loading...'}
                </h2>
                {session && (
                  <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
                    {displayMessages.length} message{displayMessages.length !== 1 ? 's' : ''}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                {/* Delete Button */}
                <button
                  onClick={handleDelete}
                  disabled={deleting || loading}
                  className="px-4 py-2 rounded-lg
                           bg-red-500 hover:bg-red-600
                           text-white font-medium
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-colors flex items-center gap-2"
                >
                  {deleting ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <Trash2 size={18} />
                      Delete
                    </>
                  )}
                </button>

                {/* Close Button */}
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg
                           hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary
                           text-light-text-secondary dark:text-dark-text-secondary
                           hover:text-light-text dark:hover:text-dark-text
                           transition-colors"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {loading ? (
                // Loading State
                <div className="flex flex-col items-center justify-center h-full">
                  <Loader2 size={48} className="animate-spin text-accent mb-4" />
                  <p className="text-light-text-secondary dark:text-dark-text-secondary">
                    Loading conversation...
                  </p>
                </div>
              ) : displayMessages.length === 0 ? (
                // Empty State
                <div className="flex flex-col items-center justify-center h-full">
                  <MessageSquare size={64} className="text-light-text-secondary dark:text-dark-text-secondary mb-4" />
                  <p className="text-lg font-semibold text-light-text dark:text-dark-text mb-2">
                    No messages
                  </p>
                  <p className="text-light-text-secondary dark:text-dark-text-secondary">
                    This session has no messages to display
                  </p>
                </div>
              ) : (
                // Messages List
                <div className="space-y-4 max-w-4xl mx-auto">
                  {displayMessages.map((message, index) => {
                    const isUser = message.role === 'user'
                    const timestamp = message.created_at
                      ? formatDistanceToNow(new Date(message.created_at * 1000), { addSuffix: true })
                      : null

                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05, duration: 0.2 }}
                        className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                      >
                        {/* Message Content */}
                        <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
                          <div
                            className={`px-4 py-3 rounded-2xl ${
                              isUser
                                ? 'bg-accent text-white rounded-br-sm'
                                : 'bg-light-surface dark:bg-dark-surface border border-border-primary rounded-bl-sm'
                            }`}
                          >
                            <p className={`text-sm whitespace-pre-wrap ${
                              isUser
                                ? 'text-white'
                                : 'text-light-text dark:text-dark-text'
                            }`}>
                              {message.content || '(No content)'}
                            </p>
                          </div>

                          {/* Timestamp */}
                          {timestamp && (
                            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1 px-1">
                              {timestamp}
                            </p>
                          )}
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
