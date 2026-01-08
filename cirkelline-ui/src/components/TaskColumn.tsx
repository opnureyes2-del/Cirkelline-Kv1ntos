'use client'

import { useState, useRef, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { TaskList, Task } from '@/types/standaloneTasks'
import TaskCard from './TaskCard'
import TaskSkeleton from './TaskSkeleton'
import {
  Plus,
  Settings,
  Trash2,
  CheckCircle2,
  Pencil
} from 'lucide-react'

interface TaskColumnProps {
  taskList: TaskList
  tasks: Task[]
  loading: boolean
  onCreateTask: (listId: string, data: { title: string; notes?: string; due_date?: string }) => Promise<boolean>
  onToggleComplete: (task: Task) => void
  onEditTask: (task: Task) => void
  onDeleteList: (listId: string) => void
  onRenameList: (listId: string, newName: string) => Promise<boolean>
  showCompleted: boolean
  isFullWidth?: boolean // For side-by-side single list view
}

export default function TaskColumn({
  taskList,
  tasks,
  loading,
  onCreateTask,
  onToggleComplete,
  onEditTask,
  onDeleteList,
  onRenameList,
  showCompleted,
  isFullWidth = false
}: TaskColumnProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [taskTitle, setTaskTitle] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [isRenaming, setIsRenaming] = useState(false)
  const [newListName, setNewListName] = useState(taskList.name)
  const settingsRef = useRef<HTMLDivElement>(null)
  const renameInputRef = useRef<HTMLInputElement>(null)

  // Filter and sort tasks based on showCompleted
  // Sort: active tasks first, then completed tasks
  const visibleTasks = tasks
    .filter(task => showCompleted || !task.completed)
    .sort((a, b) => {
      // If both have same status, maintain original order
      if (a.completed === b.completed) return 0
      // Active tasks (not completed) come first
      return a.completed ? 1 : -1
    })

  const completedCount = tasks.filter(t => t.completed).length
  const totalCount = tasks.length

  // Close settings dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setShowSettings(false)
      }
    }

    if (showSettings) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [showSettings])

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!taskTitle.trim()) return

    const success = await onCreateTask(taskList.id, {
      title: taskTitle.trim()
    })

    if (success) {
      setTaskTitle('')
      setIsAdding(false)
    }
  }

  const handleDeleteList = () => {
    if (confirm(`Delete "${taskList.name}"? All ${totalCount} task${totalCount !== 1 ? 's' : ''} will be deleted.`)) {
      onDeleteList(taskList.id)
    }
    setShowSettings(false)
  }

  const handleStartRename = () => {
    setNewListName(taskList.name)
    setIsRenaming(true)
    setShowSettings(false)
    // Focus input after render
    setTimeout(() => renameInputRef.current?.focus(), 50)
  }

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newListName.trim() || newListName.trim() === taskList.name) {
      setIsRenaming(false)
      return
    }
    const success = await onRenameList(taskList.id, newListName.trim())
    if (success) {
      setIsRenaming(false)
    }
  }

  return (
    <div className={`${isFullWidth ? 'w-full' : 'flex-shrink-0 w-64'} h-full max-h-full min-h-0 flex flex-col bg-app-container rounded-lg border border-border-primary group/column`}>
      {/* Column Header - Hidden when isFullWidth (header is in parent) */}
      {!isFullWidth && (
        <div className="flex-shrink-0 px-3 py-2 border-b border-border-primary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              {isRenaming ? (
                <form onSubmit={handleRenameSubmit} className="flex-1">
                  <input
                    ref={renameInputRef}
                    type="text"
                    value={newListName}
                    onChange={(e) => setNewListName(e.target.value)}
                    onBlur={() => setIsRenaming(false)}
                    onKeyDown={(e) => {
                      if (e.key === 'Escape') {
                        setIsRenaming(false)
                      }
                    }}
                    className="w-full text-sm font-bold font-heading text-light-text dark:text-dark-text bg-transparent border-b-2 border-accent focus:outline-none"
                  />
                </form>
              ) : (
                <>
                  <h3 className="text-sm font-bold font-heading text-light-text dark:text-dark-text truncate">
                    {taskList.name}
                  </h3>
                  {/* Task count badge */}
                  <span className="text-xs font-sans text-light-text-secondary dark:text-dark-text-secondary">
                    {tasks.filter(t => !t.completed).length}
                  </span>
                </>
              )}
            </div>

            {/* Settings Button - Only visible on hover */}
            <div className="relative flex-shrink-0" ref={settingsRef}>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="opacity-0 group-hover/column:opacity-100 p-1 rounded-md hover:bg-app-container transition-all"
                title="List settings"
              >
                <Settings
                  size={12}
                  className="text-light-text-secondary dark:text-dark-text-secondary"
                />
              </button>

              {/* Settings Dropdown */}
              {showSettings && (
                <div className="absolute right-0 top-full mt-1 w-40 bg-app-container border border-border-primary rounded-md shadow-lg z-50">
                  <button
                    onClick={handleStartRename}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm font-sans text-light-text dark:text-dark-text hover:bg-app-container transition-colors"
                  >
                    <Pencil size={14} />
                    <span>Rename List</span>
                  </button>
                  <button
                    onClick={handleDeleteList}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm font-sans text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  >
                    <Trash2 size={14} />
                    <span>Delete List</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tasks List - Scrollable */}
      <div className="flex-1 px-3 py-1.5 min-h-0 overflow-y-auto app-scroll">
        {/* Task Cards */}
        <div className="space-y-1">
          {loading && tasks.length === 0 ? (
            // Loading skeletons
            <>
              <TaskSkeleton />
              <TaskSkeleton />
              <TaskSkeleton />
            </>
          ) : visibleTasks.length === 0 ? (
            // Enhanced empty state
            <div className="flex flex-col items-center justify-center py-4 px-3">
              <CheckCircle2
                size={28}
                className={`mb-2 ${
                  tasks.length === 0
                    ? 'text-light-text-secondary dark:text-dark-text-secondary opacity-50'
                    : 'text-accent'
                }`}
              />
              <p className="text-sm font-medium text-light-text dark:text-dark-text mb-0.5">
                {tasks.length === 0 ? 'No tasks yet' : 'All done!'}
              </p>
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary text-center">
                {tasks.length === 0
                  ? 'Add a task below'
                  : completedCount === 1
                    ? '1 task completed'
                    : `${completedCount} tasks completed`}
              </p>
            </div>
          ) : (
            // Task list
            <AnimatePresence mode="popLayout">
              {visibleTasks.map((task, index) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  index={index}
                  onToggleComplete={onToggleComplete}
                  onEdit={onEditTask}
                />
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* Add Task - At bottom */}
      <div className="flex-shrink-0 px-3 py-2 border-t border-border-primary">
        {isAdding ? (
          <form onSubmit={handleCreateTask} className="space-y-2">
            <input
              type="text"
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              placeholder="Task title"
              className="w-full px-2 py-1.5 text-sm bg-app-container border border-border-primary rounded-md focus:outline-none focus:ring-2 focus:ring-accent"
              autoFocus
              onBlur={() => {
                // Only close if empty
                if (!taskTitle.trim()) {
                  setIsAdding(false)
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setTaskTitle('')
                  setIsAdding(false)
                }
              }}
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={!taskTitle.trim() || loading}
                className="flex-1 px-3 py-1.5 text-xs bg-accent text-white rounded-md hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Add Task
              </button>
              <button
                type="button"
                onClick={() => {
                  setTaskTitle('')
                  setIsAdding(false)
                }}
                className="px-3 py-1.5 text-xs bg-app-container border border-border-primary rounded-md hover:bg-app-container transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <button
            onClick={() => setIsAdding(true)}
            className="w-full flex items-center justify-center gap-1.5 px-4 py-1.5 text-xs font-medium text-light-text dark:text-dark-text rounded-lg bg-[#E4E4E2] dark:bg-[#2A2A2A] hover:bg-[#D4D4D2] dark:hover:bg-[#3A3A3A] transition-colors"
          >
            <Plus size={14} className="text-accent" />
            <span>Add task</span>
          </button>
        )}
      </div>
    </div>
  )
}
