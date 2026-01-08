'use client'

import { motion } from 'framer-motion'
import { Task } from '@/types/standaloneTasks'
import {
  CheckSquare,
  Square,
  Calendar as CalendarIcon,
  Edit2,
  AlertCircle
} from 'lucide-react'

interface TaskCardProps {
  task: Task
  onToggleComplete: (task: Task) => void
  onEdit: (task: Task) => void
  index?: number
}

// Priority colors
const priorityColors = {
  low: 'text-green-500 dark:text-green-400',
  medium: 'text-yellow-500 dark:text-yellow-400',
  high: 'text-orange-500 dark:text-orange-400',
  urgent: 'text-red-500 dark:text-red-400'
}

export default function TaskCard({ task, onToggleComplete, onEdit, index = 0 }: TaskCardProps) {
  const isCompleted = task.completed

  // Check if task is overdue
  const isOverdue = task.due_date && !isCompleted && new Date(task.due_date) < new Date()

  // Check if task is due today
  const isDueToday = task.due_date && !isCompleted &&
    new Date(task.due_date).toDateString() === new Date().toDateString()

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25, delay: index * 0.05 }}
      className={`
        group/task p-2 rounded-md
        bg-app-container
        border border-transparent
        hover:border-border-primary
        hover:shadow-sm
        transition-all duration-200
        ${isCompleted ? 'opacity-70' : ''}
      `}
    >
      <div className="flex items-start gap-2">
        {/* Checkbox */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggleComplete(task)
          }}
          className="mt-0.5 flex-shrink-0 hover:scale-110 transition-transform focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-light-bg dark:focus:ring-offset-dark-bg rounded"
          aria-label={isCompleted ? 'Mark as incomplete' : 'Mark as complete'}
        >
          {isCompleted ? (
            <CheckSquare
              size={16}
              className="text-accent animate-in zoom-in duration-200"
            />
          ) : (
            <Square
              size={16}
              className="text-light-text-secondary dark:text-dark-text-secondary hover:text-accent transition-colors"
            />
          )}
        </button>

        {/* Task Content */}
        <div
          className="flex-1 min-w-0 cursor-pointer rounded focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-light-bg dark:focus:ring-offset-dark-bg"
          onClick={() => onEdit(task)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onEdit(task)
            }
          }}
          role="button"
          tabIndex={0}
          aria-label={`Edit task: ${task.title}`}
        >
          {/* Title */}
          <p
            className={`text-xs font-medium font-sans mb-0.5 transition-all ${
              isCompleted
                ? 'line-through text-light-text-secondary dark:text-dark-text-secondary'
                : 'text-light-text dark:text-dark-text'
            }`}
          >
            {task.title}
          </p>

          {/* Notes Preview */}
          {task.notes && !isCompleted && (
            <p className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary line-clamp-2 mb-1.5">
              {task.notes}
            </p>
          )}

          {/* Meta info: Due Date + Priority */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Due Date */}
            {task.due_date && (
              <div className="flex items-center gap-1">
                <CalendarIcon
                  size={12}
                  className={`flex-shrink-0 ${
                    isOverdue
                      ? 'text-red-600 dark:text-red-400'
                      : isDueToday
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-light-text-secondary dark:text-dark-text-secondary'
                  }`}
                />
                <span
                  className={`text-[10px] ${
                    isOverdue
                      ? 'text-red-600 dark:text-red-400 font-medium'
                      : isDueToday
                      ? 'text-yellow-600 dark:text-yellow-400 font-medium'
                      : 'text-light-text-secondary dark:text-dark-text-secondary'
                  }`}
                >
                  {new Date(task.due_date).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric'
                  })}
                </span>
              </div>
            )}

            {/* Priority indicator (only for high/urgent) */}
            {(task.priority === 'high' || task.priority === 'urgent') && !isCompleted && (
              <div className={`flex items-center gap-0.5 ${priorityColors[task.priority]}`}>
                <AlertCircle size={10} />
                <span className="text-[10px] capitalize">{task.priority}</span>
              </div>
            )}
          </div>
        </div>

        {/* Edit Button - Visible on hover */}
        <button
          onClick={(e) => {
            e.stopPropagation()
            onEdit(task)
          }}
          className="opacity-0 group-hover/task:opacity-100 flex-shrink-0 p-1 rounded hover:bg-app-container focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-accent transition-all"
          title="Edit task"
          aria-label="Edit task"
        >
          <Edit2
            size={12}
            className="text-light-text-secondary dark:text-dark-text-secondary"
          />
        </button>
      </div>
    </motion.div>
  )
}
