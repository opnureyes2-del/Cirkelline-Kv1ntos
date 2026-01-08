import { useQueryState } from 'nuqs'
import { SessionEntry } from '@/types/os'
import useSessionLoader from '@/hooks/useSessionLoader'
import { useStore } from '@/store'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { deleteSessionAPI } from '@/api/os'
import { toast } from 'sonner'
import useChatActions from '@/hooks/useChatActions'
import DeleteSessionModal from './DeleteSessionModal'
import Icon from '@/components/ui/icon'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

type SessionItemProps = SessionEntry & {
  isSelected: boolean
  currentSessionId: string | null
  onSessionClick: () => void
  isCollapsed?: boolean
}

// Format relative time (e.g., "1min ago", "Yesterday", "10 days ago")
const formatRelativeTime = (timestamp: number): string => {
  if (!timestamp || isNaN(timestamp)) return ''

  const now = Date.now()
  const timestampMs = timestamp * 1000 // Convert to milliseconds
  const diff = now - timestampMs
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (seconds < 0) return 'Just now' // Handle future timestamps
  if (seconds < 60) return 'Just now'
  if (minutes < 60) return `${minutes}min ago`
  if (hours < 24) return `${hours}h ago`
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`
  if (days < 365) return `${Math.floor(days / 30)} months ago`
  return `${Math.floor(days / 365)} years ago`
}

const SessionItem = ({
  session_name: title,
  session_id,
  created_at,
  isSelected,
  currentSessionId,
  onSessionClick,
  isCollapsed = false
}: SessionItemProps) => {
  const [agentId] = useQueryState('agent')
  const [teamId] = useQueryState('team')
  const [dbId] = useQueryState('db_id')
  const [, setSessionId] = useQueryState('session')
  const { getSession } = useSessionLoader()
  const { selectedEndpoint, sessionsData, setSessionsData, mode } = useStore()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 })
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const { clearChat } = useChatActions()

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isDropdownOpen])

  const handleGetSession = async () => {
    if (!(agentId || teamId || dbId)) return

    onSessionClick()
    await getSession(
      {
        entityType: mode,
        agentId,
        teamId,
        dbId: dbId ?? ''
      },
      session_id
    )
    setSessionId(session_id)
  }

  const handleDeleteSession = async () => {
    if (!(agentId || teamId || dbId)) return
    setIsDeleting(true)
    try {
      const response = await deleteSessionAPI(
        selectedEndpoint,
        dbId ?? '',
        session_id
      )

      if (response?.ok && sessionsData) {
        setSessionsData(sessionsData.filter((s) => s.session_id !== session_id))
        // If the deleted session was the active one, clear the chat
        if (currentSessionId === session_id) {
          setSessionId(null)
          clearChat()
        }
        toast.success('Session deleted')
      } else {
        const errorMsg = await response?.text()
        toast.error(
          `Failed to delete session: ${response?.statusText || 'Unknown error'} ${errorMsg || ''}`
        )
      }
    } catch (error) {
      toast.error(
        `Failed to delete session: ${error instanceof Error ? error.message : String(error)}`
      )
    } finally {
      setIsDeleteModalOpen(false)
      setIsDeleting(false)
    }
  }
  if (isCollapsed) {
    return (
      <button
        className={cn(
          'w-full flex items-center justify-center rounded-lg p-2 transition-colors duration-200',
          isSelected
            ? 'bg-accent/10'
            : 'bg-light-surface hover:bg-light-bg dark:bg-dark-surface dark:hover:bg-dark-bg'
        )}
        onClick={handleGetSession}
        title={title}
      >
        {/* Simple collapsed view - no icon needed */}
        <div className="w-2 h-2 rounded-full bg-light-text dark:bg-dark-text" />
      </button>
    )
  }

  return (
    <>
      <motion.div
        whileHover={!isSelected ? { x: 2 } : undefined}
        transition={{ duration: 0.15 }}
        className={cn(
          'group/session flex flex-col w-full rounded-lg px-3 py-2 transition-colors duration-200 border border-transparent relative',
          isSelected
            ? 'cursor-default bg-[#E4E4E2] dark:bg-[#2A2A2A]'
            : 'cursor-pointer bg-light-bg dark:bg-dark-bg',
          isDropdownOpen && 'z-[9999]'
        )}
        onClick={handleGetSession}
      >
        {/* Title row - full width without truncation */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="w-full pr-1 flex items-center gap-2">
                <div
                  className="relative flex-1 overflow-hidden text-[12px]"
                  style={{
                    maskImage: 'linear-gradient(to right, black 85%, transparent 100%)',
                    WebkitMaskImage: 'linear-gradient(to right, black 85%, transparent 100%)'
                  }}
                >
                  <span className="whitespace-nowrap font-semibold text-light-text dark:text-dark-text">
                    {title}
                  </span>
                </div>
              </div>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>{title}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Timestamp row */}
        {created_at && (
          <div className="text-[11px] font-body text-light-text-secondary dark:text-dark-text-secondary">
            {formatRelativeTime(created_at)}
          </div>
        )}

        {/* Hover-only settings icon - absolutely positioned in vertical center */}
        <div className="absolute top-1/2 -translate-y-1/2 right-[3px] opacity-0 group-hover/session:opacity-100 transition-opacity duration-200 z-[9999]" ref={dropdownRef}>
          <button
            ref={buttonRef}
            className="text-light-text dark:text-dark-text p-0.5 flex items-center justify-center"
            onClick={(e) => {
              e.stopPropagation()
              if (buttonRef.current) {
                const rect = buttonRef.current.getBoundingClientRect()
                setDropdownPosition({
                  top: rect.bottom + 4,
                  left: rect.left - 176 + rect.width
                })
              }
              setIsDropdownOpen(!isDropdownOpen)
            }}
            title="Session options"
          >
            <Icon type="more-vertical" size="xs" className="text-inherit" />
          </button>

        </div>
      </motion.div>

      {/* Dropdown Menu - Rendered via Portal */}
      {typeof window !== 'undefined' && createPortal(
        <AnimatePresence>
          {isDropdownOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -5 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -5 }}
              transition={{ duration: 0.1 }}
              className="fixed w-44 bg-light-elevated dark:bg-dark-elevated border border-border-primary rounded-lg shadow-lg overflow-hidden z-[9999]"
              style={{ top: `${dropdownPosition.top}px`, left: `${dropdownPosition.left}px` }}
              onClick={(e) => e.stopPropagation()}
            >
                {/* Rename */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toast.info('Coming soon')
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-light-text dark:text-dark-text hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                  title="Coming soon"
                >
                  <Icon type="edit" size="xs" />
                  <span>Rename</span>
                </button>

                {/* Archive */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toast.info('Coming soon')
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-light-text dark:text-dark-text hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                  title="Coming soon"
                >
                  <Icon type="archive" size="xs" />
                  <span>Archive</span>
                </button>

                {/* Export */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toast.info('Coming soon')
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-light-text dark:text-dark-text hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                  title="Coming soon"
                >
                  <Icon type="download" size="xs" />
                  <span>Export</span>
                </button>

                {/* More info */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toast.info('Coming soon')
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-light-text dark:text-dark-text hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                  title="Coming soon"
                >
                  <Icon type="info" size="xs" />
                  <span>More info</span>
                </button>

                {/* Divider */}
                <div className="h-px bg-border-secondary my-1" />

                {/* Delete */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setIsDropdownOpen(false)
                    setIsDeleteModalOpen(true)
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-error hover:bg-error/10 transition-colors"
                >
                  <Icon type="trash" size="xs" />
                  <span>Delete</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>,
        document.body
      )}

      <DeleteSessionModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onDelete={handleDeleteSession}
        isDeleting={isDeleting}
      />
    </>
  )
}

export default SessionItem
