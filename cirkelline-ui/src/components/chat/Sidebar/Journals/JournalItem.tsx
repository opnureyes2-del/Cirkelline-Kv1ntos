'use client'

import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

export interface JournalEntry {
  id: number
  journal_date: string
  summary: string
  topics: string[]
  outcomes: string[]
  message_count: number
  created_at: string
}

interface JournalItemProps {
  journal: JournalEntry
  isCollapsed?: boolean
  onClick: () => void
}

// Format date as "Wednesday December 3"
const formatJournalDateLong = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr + 'T12:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  })
}

// Parse day number from summary (e.g., "Day 40 - December 03, 2025")
const parseDayNumber = (summary: string): string => {
  if (!summary) return ''
  const match = summary.match(/^Day (\d+)/)
  return match ? `Day ${match[1]}` : ''
}

const JournalItem = ({
  journal,
  isCollapsed = false,
  onClick
}: JournalItemProps) => {
  const dayNumber = parseDayNumber(journal.summary)
  const dateFormatted = formatJournalDateLong(journal.journal_date)

  if (isCollapsed) {
    return (
      <button
        className={cn(
          'w-full flex items-center justify-center rounded-lg p-2 transition-colors duration-200',
          'bg-light-surface hover:bg-light-bg dark:bg-dark-surface dark:hover:bg-dark-bg'
        )}
        onClick={onClick}
        title={`${dayNumber}, ${dateFormatted}`}
      >
        <div className="w-2 h-2 rounded-full bg-light-text dark:bg-dark-text" />
      </button>
    )
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <motion.div
            whileHover={{ x: 2 }}
            transition={{ duration: 0.15 }}
            className={cn(
              'group/journal flex items-center w-full rounded-lg px-3 py-2 transition-colors duration-200 border border-transparent relative cursor-pointer',
              'bg-light-bg dark:bg-dark-bg hover:bg-light-surface dark:hover:bg-dark-surface'
            )}
            onClick={onClick}
          >
            {/* Single line: Day X, Date */}
            <div
              className="flex-1 overflow-hidden whitespace-nowrap text-[12px]"
              style={{
                maskImage: 'linear-gradient(to right, black 85%, transparent 100%)',
                WebkitMaskImage: 'linear-gradient(to right, black 85%, transparent 100%)'
              }}
            >
              <span className="font-semibold text-light-text dark:text-dark-text">
                {dayNumber}
              </span>
              <span className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary ml-1.5">
                {dateFormatted}
              </span>
            </div>
          </motion.div>
        </TooltipTrigger>
        <TooltipContent side="right" className="max-w-xs">
          <p className="font-semibold mb-1">{dayNumber}, {dateFormatted}</p>
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary line-clamp-3">
            {journal.summary?.split('\n').slice(1).join('\n').slice(0, 200)}...
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

export default JournalItem
