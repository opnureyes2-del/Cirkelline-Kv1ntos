'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { MessageSquare, Trash2, ExternalLink, MoreVertical } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

import type { SessionListItem } from '@/api/os'

interface SessionCardProps {
  session: SessionListItem
  isSelected: boolean
  onSelect: (sessionId: string, selected: boolean) => void
  onDelete: (sessionId: string) => void
  delay?: number
}

export default function SessionCard({
  session,
  isSelected,
  onSelect,
  onDelete,
  delay = 0
}: SessionCardProps) {
  const router = useRouter()
  const [showActions, setShowActions] = useState(false)

  // Format dates
  const updatedAt = session.updated_at
    ? formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })
    : 'Unknown'

  // Handle card click - navigate to chat
  const handleCardClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking checkbox or actions
    if ((e.target as HTMLElement).closest('.session-actions, .session-checkbox')) {
      return
    }
    router.push(`/chat?session=${session.session_id}`)
  }

  // Handle delete with confirmation
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm(`Delete session "${session.session_name}"?`)) {
      onDelete(session.session_id)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      onClick={handleCardClick}
      className={`
        relative overflow-hidden
        bg-light-surface dark:bg-dark-surface
        rounded-xl p-4
        border ${isSelected ? 'border-accent' : 'border-border-primary'}
        hover:border-accent/50
        transition-all duration-300
        cursor-pointer
        group
      `}
    >
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-20 h-20 bg-accent/5 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Header: Checkbox + Session Name + Actions */}
      <div className="relative flex items-start gap-3 mb-3">
        {/* Selection Checkbox */}
        <div className="session-checkbox flex items-center pt-1">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => {
              e.stopPropagation()
              onSelect(session.session_id, e.target.checked)
            }}
            className="w-4 h-4 rounded border-border-primary bg-light-bg dark:bg-dark-bg
                     text-accent focus:ring-accent focus:ring-offset-0 cursor-pointer"
          />
        </div>

        {/* Session Name */}
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-light-text dark:text-dark-text
                       font-heading line-clamp-2 group-hover:text-accent transition-colors">
            {session.session_name || 'Untitled Session'}
          </h3>
        </div>

        {/* Actions Menu */}
        <div className="session-actions relative flex-shrink-0">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowActions(!showActions)
            }}
            className="p-1.5 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg
                     text-light-text-secondary dark:text-dark-text-secondary
                     hover:text-light-text dark:hover:text-dark-text transition-colors"
            title="Actions"
          >
            <MoreVertical size={16} />
          </button>

          {/* Actions Dropdown */}
          {showActions && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-40"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowActions(false)
                }}
              />

              {/* Dropdown Menu */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-8 z-50 w-48
                         bg-light-surface dark:bg-dark-surface
                         border border-border-primary
                         rounded-lg shadow-lg overflow-hidden"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowActions(false)
                    router.push(`/chat?session=${session.session_id}`)
                  }}
                  className="w-full px-4 py-2.5 text-left flex items-center gap-3
                           hover:bg-light-bg dark:hover:bg-dark-bg
                           text-light-text dark:text-dark-text
                           text-sm transition-colors"
                >
                  <ExternalLink size={16} />
                  Open in Chat
                </button>

                <button
                  onClick={handleDelete}
                  className="w-full px-4 py-2.5 text-left flex items-center gap-3
                           hover:bg-red-500/10 dark:hover:bg-red-500/20
                           text-red-600 dark:text-red-400
                           text-sm transition-colors"
                >
                  <Trash2 size={16} />
                  Delete
                </button>
              </motion.div>
            </>
          )}
        </div>
      </div>

      {/* Footer: Updated Time + Message Count */}
      <div className="relative flex items-center justify-between text-xs
                    text-light-text-secondary dark:text-dark-text-secondary">
        <span>Updated {updatedAt}</span>

        {session.message_count !== undefined && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-full
                        bg-accent/10 text-accent">
            <MessageSquare size={12} />
            <span className="font-medium">{session.message_count}</span>
          </div>
        )}
      </div>
    </motion.div>
  )
}
