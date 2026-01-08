'use client'

import { useState } from 'react'
import { Calendar, CreateCalendarRequest } from '@/types/calendar'
import { cn } from '@/lib/utils'
import { Plus, Check, MoreVertical, Trash2, Edit2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

// Default calendar colors
const CALENDAR_COLORS = [
  '#8E0B83', // Purple (default)
  '#EC4B13', // Orange
  '#13EC81', // Green
  '#1380EC', // Blue
  '#EC1380', // Pink
  '#F59E0B', // Amber
  '#10B981', // Emerald
  '#6366F1', // Indigo
]

interface CalendarSidebarProps {
  calendars: Calendar[]
  selectedCalendarIds: string[]
  onToggleCalendar: (id: string) => void
  onCreateCalendar: (data: CreateCalendarRequest) => Promise<Calendar | null>
  onDeleteCalendar: (id: string) => Promise<boolean>
  onUpdateCalendar: (id: string, data: { name?: string; color?: string }) => Promise<boolean>
  loading?: boolean
}

export default function CalendarSidebar({
  calendars,
  selectedCalendarIds,
  onToggleCalendar,
  onCreateCalendar,
  onDeleteCalendar,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onUpdateCalendar,
  loading = false,
}: CalendarSidebarProps) {
  const [isAddingCalendar, setIsAddingCalendar] = useState(false)
  const [newCalendarName, setNewCalendarName] = useState('')
  const [newCalendarColor, setNewCalendarColor] = useState(CALENDAR_COLORS[0])
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null)
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null)

  const handleCreateCalendar = async () => {
    if (!newCalendarName.trim()) return

    const result = await onCreateCalendar({
      name: newCalendarName.trim(),
      color: newCalendarColor,
    })

    if (result) {
      setNewCalendarName('')
      setNewCalendarColor(CALENDAR_COLORS[0])
      setIsAddingCalendar(false)
    }
  }

  const handleDeleteCalendar = async (id: string) => {
    if (window.confirm('Delete this calendar and all its events?')) {
      await onDeleteCalendar(id)
    }
    setMenuOpenId(null)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border-primary">
        <span className="text-sm font-semibold text-light-text dark:text-dark-text">
          My Calendars
        </span>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setIsAddingCalendar(true)}
                className="p-1 rounded hover:bg-accent/10 transition-colors"
                disabled={loading}
              >
                <Plus size={16} className="text-light-text dark:text-dark-text" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Add calendar</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Calendar List */}
      <div className="flex-1 overflow-y-auto py-2">
        {calendars.length === 0 && !isAddingCalendar && !loading && (
          <div className="px-3 py-8 text-center">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
              No calendars yet
            </p>
            <button
              onClick={() => setIsAddingCalendar(true)}
              className="mt-2 text-sm text-accent hover:underline"
            >
              Create your first calendar
            </button>
          </div>
        )}

        <AnimatePresence>
          {calendars.map((calendar) => (
            <motion.div
              key={calendar.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="group relative"
            >
              <div
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-app-container transition-colors',
                  !selectedCalendarIds.includes(calendar.id) && 'opacity-50'
                )}
                onClick={() => onToggleCalendar(calendar.id)}
              >
                {/* Checkbox with calendar color */}
                <div
                  className={cn(
                    'w-4 h-4 rounded flex items-center justify-center border-2 transition-colors',
                    selectedCalendarIds.includes(calendar.id)
                      ? 'border-transparent'
                      : 'border-light-text-secondary dark:border-dark-text-secondary'
                  )}
                  style={{
                    backgroundColor: selectedCalendarIds.includes(calendar.id)
                      ? calendar.color
                      : 'transparent',
                  }}
                >
                  {selectedCalendarIds.includes(calendar.id) && (
                    <Check size={12} className="text-white" strokeWidth={3} />
                  )}
                </div>

                {/* Calendar name */}
                <span className="flex-1 text-sm text-light-text dark:text-dark-text truncate">
                  {calendar.name}
                </span>

                {/* Source indicator */}
                {calendar.source === 'google' && (
                  <span className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary bg-app-container px-1 rounded">
                    Google
                  </span>
                )}

                {/* Menu button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setMenuOpenId(menuOpenId === calendar.id ? null : calendar.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-app-container transition-opacity"
                >
                  <MoreVertical size={14} className="text-light-text-secondary dark:text-dark-text-secondary" />
                </button>
              </div>

              {/* Dropdown menu */}
              <AnimatePresence>
                {menuOpenId === calendar.id && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="absolute right-2 top-full z-50 mt-1 w-36 py-1 bg-app-container border border-border-primary rounded-lg shadow-lg"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => {
                        setEditingCalendarId(calendar.id)
                        setMenuOpenId(null)
                      }}
                      className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-light-text dark:text-dark-text hover:bg-app-container"
                    >
                      <Edit2 size={14} />
                      <span>Edit</span>
                    </button>
                    {calendar.source === 'local' && (
                      <button
                        onClick={() => handleDeleteCalendar(calendar.id)}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-error hover:bg-error/10"
                      >
                        <Trash2 size={14} />
                        <span>Delete</span>
                      </button>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Add Calendar Form */}
        <AnimatePresence>
          {isAddingCalendar && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="px-3 py-2 border-t border-border-primary"
            >
              <input
                type="text"
                value={newCalendarName}
                onChange={(e) => setNewCalendarName(e.target.value)}
                placeholder="Calendar name"
                className="w-full px-2 py-1.5 text-sm bg-app-container border border-border-primary rounded focus:outline-none focus:border-accent"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreateCalendar()
                  if (e.key === 'Escape') {
                    setIsAddingCalendar(false)
                    setNewCalendarName('')
                  }
                }}
              />

              {/* Color picker */}
              <div className="flex gap-1 mt-2">
                {CALENDAR_COLORS.map((color) => (
                  <button
                    key={color}
                    onClick={() => setNewCalendarColor(color)}
                    className={cn(
                      'w-5 h-5 rounded-full transition-transform',
                      newCalendarColor === color && 'ring-2 ring-offset-1 ring-light-text dark:ring-dark-text scale-110'
                    )}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2 mt-2">
                <button
                  onClick={() => {
                    setIsAddingCalendar(false)
                    setNewCalendarName('')
                  }}
                  className="px-2 py-1 text-xs text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCalendar}
                  disabled={!newCalendarName.trim() || loading}
                  className="px-2 py-1 text-xs bg-accent text-white rounded disabled:opacity-50"
                >
                  Create
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer - Integration hint */}
      <div className="px-3 py-2 border-t border-border-primary">
        <p className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary text-center">
          Connect Google Calendar in Settings
        </p>
      </div>
    </div>
  )
}
