'use client'

import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { X, BookOpen, ChevronLeft, ChevronRight, Grid } from 'lucide-react'
import { JournalEntry } from './JournalItem'

interface JournalDetailModalProps {
  journal: JournalEntry | null
  journals?: JournalEntry[] // Full list for navigation
  onClose: () => void
  onNavigate?: (journal: JournalEntry) => void
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

const JournalDetailModal = ({ journal, journals = [], onClose, onNavigate }: JournalDetailModalProps) => {
  const router = useRouter()

  // Find current index and prev/next journals
  const currentIndex = journals.findIndex(j => j.id === journal?.id)
  const prevJournal = currentIndex > 0 ? journals[currentIndex - 1] : null
  const nextJournal = currentIndex < journals.length - 1 ? journals[currentIndex + 1] : null

  // Close on escape key, navigate with arrow keys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft' && prevJournal && onNavigate) onNavigate(prevJournal)
      if (e.key === 'ArrowRight' && nextJournal && onNavigate) onNavigate(nextJournal)
    }
    if (journal) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [journal, onClose, prevJournal, nextJournal, onNavigate])

  if (typeof window === 'undefined') return null

  // Parse journal content - split date header from body
  const parseJournalContent = (summary: string) => {
    const lines = summary.split('\n')
    const dateHeader = lines[0] // "Day 57 - December 03, 2025"
    const journalBody = lines.slice(1).join('\n').trim()
    // Extract just "Day 57" from "Day 57 - December 03, 2025"
    const dayNumber = dateHeader.split(' - ')[0] || dateHeader
    return { dayNumber, journalBody }
  }

  const handleViewAll = () => {
    onClose()
    router.push('/profile/journals')
  }

  return createPortal(
    <AnimatePresence>
      {journal && (() => {
        const { dayNumber, journalBody } = parseJournalContent(journal.summary)

        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={onClose}
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
                      {formatDate(journal.journal_date)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
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
                {/* Prev/Next Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => prevJournal && onNavigate?.(prevJournal)}
                    disabled={!prevJournal}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Prev
                  </button>
                  <button
                    onClick={() => nextJournal && onNavigate?.(nextJournal)}
                    disabled={!nextJournal}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                {/* View All Button */}
                <button
                  onClick={handleViewAll}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg rounded-lg transition-colors"
                >
                  <Grid className="w-4 h-4" />
                  View All
                </button>
              </div>
            </motion.div>
          </motion.div>
        )
      })()}
    </AnimatePresence>,
    document.body
  )
}

export default JournalDetailModal
