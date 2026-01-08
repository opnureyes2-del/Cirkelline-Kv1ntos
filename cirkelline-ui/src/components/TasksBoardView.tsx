'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useStandaloneTasks } from '@/hooks/useStandaloneTasks'
import { Task, TaskList, CreateTaskRequest } from '@/types/standaloneTasks'
import TaskColumn from './TaskColumn'
import { Plus, Loader2, X } from 'lucide-react'

interface TasksByList {
  [listId: string]: Task[]
}

interface TasksBoardViewProps {
  googleSyncEnabled?: boolean
  layoutMode?: 'stacked' | 'side-by-side'
  selectedListId?: string | null
  onListChange?: (listId: string) => void
  onListsLoaded?: (lists: TaskList[]) => void
  showCompleted?: boolean
}

export default function TasksBoardView({
  googleSyncEnabled = false,
  layoutMode = 'stacked',
  selectedListId,
  onListChange,
  onListsLoaded,
  showCompleted = true
}: TasksBoardViewProps) {
  const {
    lists,
    tasks,
    loading,
    error,
    fetchLists,
    fetchTasks,
    createList,
    updateList,
    deleteList,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskComplete,
    clearError,
    hasLists
  } = useStandaloneTasks()

  const [isCreatingList, setIsCreatingList] = useState(false)
  const [newListTitle, setNewListTitle] = useState('')
  const [isInitialized, setIsInitialized] = useState(false)
  const [internalSelectedListId, setInternalSelectedListId] = useState<string | null>(null)

  // Task edit modal state
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [editNotes, setEditNotes] = useState('')
  const [editDueDate, setEditDueDate] = useState('')
  const [editPriority, setEditPriority] = useState<'low' | 'medium' | 'high' | 'urgent'>('medium')

  // Determine which list ID to use (prop or internal)
  const activeListId = selectedListId ?? internalSelectedListId ?? lists[0]?.id

  // Notify parent when lists are loaded
  useEffect(() => {
    if (lists.length > 0 && onListsLoaded) {
      onListsLoaded(lists)
    }
  }, [lists, onListsLoaded])

  // Auto-select first list when available
  useEffect(() => {
    if (lists.length > 0 && !internalSelectedListId) {
      setInternalSelectedListId(lists[0].id)
    }
  }, [lists, internalSelectedListId])

  // Group tasks by list
  const tasksByList = tasks.reduce<TasksByList>((acc, task) => {
    if (!acc[task.list_id]) {
      acc[task.list_id] = []
    }
    acc[task.list_id].push(task)
    return acc
  }, {})

  // Get current list for side-by-side view
  const currentList = lists.find(l => l.id === activeListId)

  /**
   * Handle list selection change
   */
  const handleListChange = useCallback((listId: string) => {
    setInternalSelectedListId(listId)
    if (onListChange) {
      onListChange(listId)
    }
  }, [onListChange])

  /**
   * Create a new task list
   */
  const handleCreateList = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newListTitle.trim()) return

    const newList = await createList({ name: newListTitle.trim() })
    if (newList) {
      setNewListTitle('')
      setIsCreatingList(false)
      // Select the newly created list in side-by-side mode
      if (layoutMode === 'side-by-side') {
        handleListChange(newList.id)
      }
    }
  }, [createList, newListTitle, layoutMode, handleListChange])

  /**
   * Delete a task list
   */
  const handleDeleteList = useCallback(async (listId: string) => {
    await deleteList(listId)
    // If we deleted the selected list, select another
    if (listId === activeListId && lists.length > 1) {
      const remaining = lists.filter(l => l.id !== listId)
      if (remaining.length > 0) {
        handleListChange(remaining[0].id)
      }
    }
  }, [deleteList, activeListId, lists, handleListChange])

  /**
   * Create a new task in a list
   */
  const handleCreateTask = useCallback(async (
    listId: string,
    data: { title: string; notes?: string; due_date?: string }
  ): Promise<boolean> => {
    const taskData: CreateTaskRequest = {
      list_id: listId,
      title: data.title,
      notes: data.notes,
      due_date: data.due_date
    }
    const newTask = await createTask(taskData)
    return newTask !== null
  }, [createTask])

  /**
   * Toggle task completion
   */
  const handleToggleComplete = useCallback(async (task: Task) => {
    await toggleTaskComplete(task.id)
  }, [toggleTaskComplete])


  /**
   * Rename a task list
   */
  const handleRenameList = useCallback(async (listId: string, newName: string): Promise<boolean> => {
    return await updateList(listId, { name: newName })
  }, [updateList])

  /**
   * Open task edit modal
   */
  const handleEditTask = useCallback((task: Task) => {
    setEditingTask(task)
    setEditTitle(task.title)
    setEditNotes(task.notes || '')
    setEditDueDate(task.due_date ? task.due_date.split('T')[0] : '')
    setEditPriority((task.priority as 'low' | 'medium' | 'high' | 'urgent') || 'medium')
  }, [])

  /**
   * Save task edits
   */
  const handleSaveTask = useCallback(async () => {
    if (!editingTask || !editTitle.trim()) return

    await updateTask(editingTask.id, {
      title: editTitle.trim(),
      notes: editNotes.trim() || undefined,
      due_date: editDueDate || undefined,
      priority: editPriority
    })
    setEditingTask(null)
  }, [editingTask, editTitle, editNotes, editDueDate, editPriority, updateTask])

  /**
   * Delete task from edit modal
   */
  const handleDeleteTask = useCallback(async () => {
    if (!editingTask) return
    if (confirm('Delete this task?')) {
      await deleteTask(editingTask.id)
      setEditingTask(null)
    }
  }, [editingTask, deleteTask])

  /**
   * Close edit modal
   */
  const handleCloseEditModal = useCallback(() => {
    setEditingTask(null)
  }, [])

  // Load data on mount and when sync state changes
  useEffect(() => {
    if (!isInitialized) {
      const source = googleSyncEnabled ? undefined : 'local'
      fetchLists(source)
      fetchTasks(undefined, undefined, source)
      setIsInitialized(true)
    }
  }, [fetchLists, fetchTasks, isInitialized, googleSyncEnabled])

  // Re-fetch when sync state changes (after initial load)
  useEffect(() => {
    if (isInitialized) {
      const source = googleSyncEnabled ? undefined : 'local'
      fetchLists(source)
      fetchTasks(undefined, undefined, source)
    }
  }, [googleSyncEnabled]) // Only trigger on sync state change

  // Side-by-side mode: Show single list with selector
  const isSideBySide = layoutMode === 'side-by-side'

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: 'var(--app-container-bg)' }}>
      {/* Error Message - Floating at top if present */}
      {error && (
        <div className="flex-shrink-0 mx-4 mt-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          <button
            onClick={clearError}
            className="mt-1 text-xs text-red-600 dark:text-red-400 underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Side-by-Side Mode: List selector is now in parent header */}

      {/* Board Area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {loading && lists.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 size={32} className="animate-spin text-accent" />
          </div>
        ) : !hasLists ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center px-6 py-12">
              <div className="mb-6">
                <Plus
                  size={64}
                  className="mx-auto text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                />
              </div>
              <h3 className="text-lg font-semibold text-light-text dark:text-dark-text mb-2">
                Welcome to Tasks
              </h3>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-6 max-w-sm mx-auto">
                Organize your work with task lists. Create your first list to get started.
              </p>
              <button
                onClick={() => setIsCreatingList(true)}
                className="px-6 py-2.5 bg-accent text-white rounded-md hover:bg-accent/90 transition-all hover:shadow-md focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-light-bg dark:focus:ring-offset-dark-bg"
              >
                Create your first list
              </button>
            </div>
          </div>
        ) : isSideBySide ? (
          /* Side-by-Side: Single list view */
          <div className="h-full p-4">
            {currentList && (
              <TaskColumn
                taskList={currentList}
                tasks={tasksByList[currentList.id] || []}
                loading={loading}
                onCreateTask={handleCreateTask}
                onToggleComplete={handleToggleComplete}
                onEditTask={handleEditTask}
                onDeleteList={handleDeleteList}
                onRenameList={handleRenameList}
                showCompleted={showCompleted}
                isFullWidth={true}
              />
            )}
          </div>
        ) : (
          /* Stacked: Horizontal Kanban board */
          <div className="flex gap-3 p-4 h-full min-h-0 items-stretch overflow-x-auto overflow-y-hidden tasks-board-scroll">
            {/* Existing Task Lists */}
            {lists.map((list, index) => (
              <motion.div
                key={list.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.3 }}
                className="h-full min-h-0"
              >
                <TaskColumn
                  taskList={list}
                  tasks={tasksByList[list.id] || []}
                  loading={loading}
                  onCreateTask={handleCreateTask}
                  onToggleComplete={handleToggleComplete}
                  onEditTask={handleEditTask}
                  onDeleteList={handleDeleteList}
                  onRenameList={handleRenameList}
                  showCompleted={showCompleted}
                />
              </motion.div>
            ))}

            {/* New List Column/Button */}
            <div className="flex-shrink-0 w-64 h-full flex items-start justify-center pt-0">
              {isCreatingList ? (
                <div className="w-full p-3 bg-app-container rounded-lg border border-border-primary">
                  <form onSubmit={handleCreateList} className="space-y-2">
                    <input
                      type="text"
                      value={newListTitle}
                      onChange={(e) => setNewListTitle(e.target.value)}
                      placeholder="List name"
                      className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-md focus:outline-none focus:ring-2 focus:ring-accent"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Escape') {
                          setNewListTitle('')
                          setIsCreatingList(false)
                        }
                      }}
                    />
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        disabled={!newListTitle.trim() || loading}
                        className="flex-1 px-3 py-1.5 text-xs bg-accent text-white rounded-md hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Create
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setNewListTitle('')
                          setIsCreatingList(false)
                        }}
                        className="flex-1 px-3 py-1.5 text-xs bg-app-container border border-border-primary rounded-md hover:bg-app-container transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <button
                  onClick={() => setIsCreatingList(true)}
                  className="w-full h-20 flex flex-col items-center justify-center gap-1.5 bg-app-container rounded-lg border-2 border-dashed border-border-primary hover:border-accent hover:bg-app-container transition-all group"
                >
                  <Plus size={24} className="text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors" />
                  <span className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors">
                    New List
                  </span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* New List Modal for Side-by-Side mode */}
      <AnimatePresence>
        {isSideBySide && isCreatingList && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4"
            onClick={() => {
              setIsCreatingList(false)
              setNewListTitle('')
            }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-app-container rounded-xl shadow-2xl w-full max-w-sm overflow-hidden"
            >
              <div className="px-4 py-3 border-b border-border-primary">
                <h3 className="text-sm font-semibold text-light-text dark:text-dark-text">
                  New List
                </h3>
              </div>
              <form onSubmit={handleCreateList} className="p-4 space-y-4">
                <input
                  type="text"
                  value={newListTitle}
                  onChange={(e) => setNewListTitle(e.target.value)}
                  placeholder="List name"
                  className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  autoFocus
                />
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreatingList(false)
                      setNewListTitle('')
                    }}
                    className="px-4 py-2 text-sm text-light-text-secondary hover:text-light-text transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!newListTitle.trim() || loading}
                    className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Create
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Task Edit Modal */}
      <AnimatePresence>
        {editingTask && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4"
            onClick={handleCloseEditModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-app-container rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
            >
              {/* Modal Header */}
              <div className="px-4 py-3 border-b border-border-primary flex items-center justify-between">
                <h3 className="text-sm font-semibold text-light-text dark:text-dark-text">
                  Edit Task
                </h3>
                <button
                  onClick={handleCloseEditModal}
                  className="p-1 hover:bg-app-container rounded transition-colors"
                >
                  <X size={16} className="text-light-text-secondary" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-4 space-y-4">
                {/* Title */}
                <div>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    placeholder="Task title"
                    className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                    autoFocus
                  />
                </div>

                {/* Notes */}
                <div>
                  <textarea
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    rows={3}
                    placeholder="Notes (optional)"
                    className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text resize-none"
                  />
                </div>

                {/* Due Date & Priority */}
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="block text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Due Date</label>
                    <input
                      type="date"
                      value={editDueDate}
                      onChange={(e) => setEditDueDate(e.target.value)}
                      className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Priority</label>
                    <select
                      value={editPriority}
                      onChange={(e) => setEditPriority(e.target.value as 'low' | 'medium' | 'high' | 'urgent')}
                      className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-4 py-3 border-t border-border-primary flex justify-between">
                <div>
                  <button
                    onClick={handleDeleteTask}
                    className="px-3 py-2 text-sm text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    Delete
                  </button>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleCloseEditModal}
                    className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveTask}
                    disabled={!editTitle.trim()}
                    className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
