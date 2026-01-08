'use client'

import { X, MessageSquare, ThumbsUp, ThumbsDown, Send } from 'lucide-react'
import { useState } from 'react'
import type { ChatMessage } from '@/types/os'
import { toast } from 'sonner'

interface FeedbackModalProps {
  message: ChatMessage
  feedbackType: 'positive' | 'negative'
  sessionId: string | null
  onClose: () => void
}

export default function FeedbackModal({ message, feedbackType, sessionId, onClose }: FeedbackModalProps) {
  const [userComments, setUserComments] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (isSubmitting) return

    setIsSubmitting(true)

    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Please log in to submit feedback')
        onClose()
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message_content: message.content,
          feedback_type: feedbackType,
          user_comments: userComments.trim() || null,
          session_id: sessionId
        })
      })

      if (response.ok) {
        toast.success('Feedback submitted! Thank you.')
        onClose()
      } else {
        const error = await response.json()
        toast.error(error.detail || 'Failed to submit feedback')
      }
    } catch (error) {
      console.error('Feedback submission error:', error)
      toast.error('Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  const FeedbackIcon = feedbackType === 'positive' ? ThumbsUp : ThumbsDown
  const feedbackColor = feedbackType === 'positive'
    ? 'text-green-600 dark:text-green-400'
    : 'text-red-600 dark:text-red-400'
  const feedbackBgColor = feedbackType === 'positive'
    ? 'bg-green-100 dark:bg-green-900/30'
    : 'bg-red-100 dark:bg-red-900/30'

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-[100] animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[101] w-[95vw] sm:w-[85vw] md:w-[75vw] lg:w-[65vw] max-w-3xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto animate-in zoom-in-95 duration-200">
        <div className="bg-light-surface dark:bg-dark-surface rounded-lg shadow-xl border border-border-primary">
          {/* Header */}
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-border-secondary">
            <div className="flex items-center gap-2 sm:gap-3">
              <MessageSquare className="w-5 h-5 sm:w-6 sm:h-6 text-accent" />
              <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading">
                Submit Feedback
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text-secondary dark:text-dark-text-secondary transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
            {/* Feedback Type */}
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-lg ${feedbackBgColor}`}>
                <FeedbackIcon className={`w-5 h-5 ${feedbackColor}`} />
              </div>
              <div>
                <p className="text-sm font-semibold text-light-text dark:text-dark-text font-body">
                  {feedbackType === 'positive' ? 'Positive Feedback' : 'Negative Feedback'}
                </p>
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">
                  {feedbackType === 'positive'
                    ? 'Tell us what you liked'
                    : 'Help us improve'}
                </p>
              </div>
            </div>

            {/* Cirkelline's Message (Read-only) */}
            <div>
              <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-2 font-body">
                Cirkelline&apos;s Message:
              </h3>
              <div className="bg-accent/10 p-4 rounded-lg max-h-48 overflow-y-auto">
                <p className="text-sm text-light-text dark:text-dark-text leading-relaxed font-body whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>
            </div>

            {/* User Comments */}
            <div>
              <label htmlFor="comments" className="text-sm font-semibold text-light-text dark:text-dark-text mb-2 block font-body">
                Additional Comments (Optional):
              </label>
              <textarea
                id="comments"
                value={userComments}
                onChange={(e) => setUserComments(e.target.value)}
                placeholder={feedbackType === 'positive'
                  ? "What did you find helpful? (optional)"
                  : "What could be improved? (optional)"}
                maxLength={2000}
                rows={4}
                className="w-full p-3 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text placeholder:text-light-text-secondary dark:placeholder:text-dark-text-secondary focus:outline-none focus:ring-2 focus:ring-accent transition-colors font-body text-sm resize-none"
              />
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1 text-right font-body">
                {userComments.length} / 2000
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end gap-3 pt-4 border-t border-border-secondary">
              <button
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg border border-border-primary text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg transition-colors disabled:opacity-50 font-sans text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg bg-accent text-white hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2 font-sans text-sm"
              >
                {isSubmitting ? (
                  <>Submitting...</>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Submit Feedback
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
