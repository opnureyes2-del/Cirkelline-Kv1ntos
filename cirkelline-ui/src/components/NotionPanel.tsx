'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckSquare, FolderKanban, Building2, FileText, Plus, ChevronLeft, Loader2 } from 'lucide-react'
import { useNotionData } from '@/hooks/useNotionData'
import { CreateTaskRequest } from '@/types/notion'

interface NotionPanelProps {
  isOpen: boolean
  onClose: () => void
}

type View = 'list' | 'create_task'
type DatabaseType = 'tasks' | 'projects' | 'companies' | 'documentation'

export default function NotionPanel({ isOpen, onClose }: NotionPanelProps) {
  const {
    companies,
    projects,
    tasks,
    documentation,
    loading,
    error,
    fetchCompanies,
    fetchProjects,
    fetchTasks,
    fetchDocumentation,
    createTask,
    clearError
  } = useNotionData()

  const [view, setView] = useState<View>('list')
  const [selectedDatabase, setSelectedDatabase] = useState<DatabaseType>('tasks')
  const [taskData, setTaskData] = useState<CreateTaskRequest>({
    title: '',
    status: 'To Do',
    priority: 'Medium',
    due_date: '',
    description: '',
    project_id: ''
  })
  const panelRef = useRef<HTMLDivElement>(null)

  // Load data when panel opens
  useEffect(() => {
    if (isOpen) {
      fetchCompanies()
      fetchProjects()
      fetchTasks()
      fetchDocumentation()
      setView('list')
      setSelectedDatabase('tasks')
    }
  }, [isOpen, fetchCompanies, fetchProjects, fetchTasks, fetchDocumentation])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
    }
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Handle create task
  const handleCreateTaskClick = () => {
    setTaskData({
      title: '',
      status: 'To Do',
      priority: 'Medium',
      due_date: '',
      description: '',
      project_id: ''
    })
    setView('create_task')
  }

  // Handle task submit
  const handleTaskSubmit = async () => {
    const success = await createTask(taskData)
    if (success) {
      setView('list')
      setSelectedDatabase('tasks')
    }
  }

  // Back to list
  const handleBack = () => {
    setView('list')
    clearError()
  }

  // Format date for display
  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'No date'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Get status badge color
  const getStatusColor = (status: string = '') => {
    const statusLower = status.toLowerCase()
    if (statusLower.includes('done') || statusLower.includes('complete')) return 'bg-green-500/10 text-green-600 dark:text-green-400'
    if (statusLower.includes('progress') || statusLower.includes('doing')) return 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
    if (statusLower.includes('block')) return 'bg-red-500/10 text-red-600 dark:text-red-400'
    return 'bg-gray-500/10 text-gray-600 dark:text-gray-300'
  }

  // Get priority badge color
  const getPriorityColor = (priority: string = '') => {
    const priorityLower = priority.toLowerCase()
    if (priorityLower.includes('high') || priorityLower.includes('urgent')) return 'bg-red-500/10 text-red-600 dark:text-red-400'
    if (priorityLower.includes('medium')) return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
    return 'bg-gray-500/10 text-gray-600 dark:text-gray-300'
  }

  // Get current database items
  const getCurrentItems = () => {
    switch (selectedDatabase) {
      case 'tasks': return tasks
      case 'projects': return projects
      case 'companies': return companies
      case 'documentation': return documentation
      default: return []
    }
  }

  // Get database icon
  const getDatabaseIcon = (type: DatabaseType) => {
    switch (type) {
      case 'tasks': return CheckSquare
      case 'projects': return FolderKanban
      case 'companies': return Building2
      case 'documentation': return FileText
    }
  }

  // Get item display name - handle different property names
  const getItemDisplayName = (item: typeof getCurrentItems extends () => infer R ? R extends Array<infer T> ? T : never : never): string => {
    if ('title' in item && item.title && typeof item.title === 'string') return item.title
    if ('name' in item && item.name && typeof item.name === 'string') return item.name
    return 'Untitled'
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'calc((100vh - 64px) * 0.25)', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="
            relative
            w-full
            bg-light-surface dark:bg-dark-surface
            shadow-lg
            overflow-hidden
            flex flex-col
            border-t border-gray-200 dark:border-gray-700
          "
        >
          {/* Centered container with scroll */}
          <div className="w-full max-w-3xl mx-auto flex flex-col h-full overflow-y-scroll">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-light-bg dark:bg-dark-bg sticky top-0 z-10">
              <div className="flex items-center gap-2">
                {view !== 'list' && (
                  <button
                    onClick={handleBack}
                    className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
                    aria-label="Back"
                  >
                    <ChevronLeft size={16} />
                  </button>
                )}
                <h2 className="text-sm font-heading font-medium text-light-text dark:text-dark-text">
                  {view === 'list' && 'Notion Workspace'}
                  {view === 'create_task' && 'Create Task'}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Content */}
            <div className="flex-1">
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={32} className="animate-spin text-accent" />
                </div>
              )}

              {/* List View */}
              {!loading && view === 'list' && (
                <div>
                  {/* Database Selector & Action Button */}
                  <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
                    {/* Database Selector */}
                    <div className="flex gap-2">
                      {(['tasks', 'projects', 'companies', 'documentation'] as DatabaseType[]).map((db) => {
                        const Icon = getDatabaseIcon(db)
                        const count = db === 'tasks' ? tasks.length :
                                     db === 'projects' ? projects.length :
                                     db === 'companies' ? companies.length :
                                     documentation.length
                        return (
                          <button
                            key={db}
                            onClick={() => setSelectedDatabase(db)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-sans transition-colors ${
                              selectedDatabase === db
                                ? 'bg-accent text-white'
                                : 'text-light-text/70 dark:text-dark-text/70 hover:bg-light-surface dark:hover:bg-dark-surface'
                            }`}
                          >
                            <Icon size={14} />
                            {db.charAt(0).toUpperCase() + db.slice(1)} ({count})
                          </button>
                        )
                      })}
                    </div>

                    {/* Create Task Button (only show for tasks) */}
                    {selectedDatabase === 'tasks' && (
                      <button
                        onClick={handleCreateTaskClick}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
                      >
                        <Plus size={18} />
                        Create Task
                      </button>
                    )}
                  </div>

                  {/* Item List */}
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {getCurrentItems().length === 0 ? (
                      <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
                        No {selectedDatabase} found
                      </div>
                    ) : (
                      getCurrentItems().map((item) => (
                        <button
                          key={item.id}
                          onClick={() => window.open(item.url, '_blank')}
                          className="w-full px-6 py-4 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors text-left"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-light-text dark:text-dark-text truncate">
                                {getItemDisplayName(item)}
                              </p>

                              {/* Database-specific metadata */}
                              <div className="flex flex-wrap gap-2 mt-2">
                                {/* Tasks & Projects: Status + Priority + Date */}
                                {(selectedDatabase === 'tasks' || selectedDatabase === 'projects') && (
                                  <>
                                    {'status' in item && item.status && (
                                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getStatusColor(String(item.status))}`}>
                                        {String(item.status)}
                                      </span>
                                    )}
                                    {'priority' in item && item.priority && (
                                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${getPriorityColor(String(item.priority))}`}>
                                        {String(item.priority)}
                                      </span>
                                    )}
                                    {(selectedDatabase === 'tasks' && 'due_date' in item && item.due_date) && (
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-medium">
                                        Due: {formatDate(typeof item.due_date === 'string' ? item.due_date : null)}
                                      </span>
                                    )}
                                    {(selectedDatabase === 'projects' && 'start_date' in item && item.start_date) && (
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-medium">
                                        Start: {formatDate(typeof item.start_date === 'string' ? item.start_date : null)}
                                      </span>
                                    )}
                                  </>
                                )}

                                {/* Companies: Domain + Industry + Size */}
                                {selectedDatabase === 'companies' && (
                                  <>
                                    {'domain' in item && item.domain && (
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium">
                                        {String(item.domain)}
                                      </span>
                                    )}
                                    {'industry' in item && item.industry && (
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium">
                                        {String(item.industry)}
                                      </span>
                                    )}
                                    {'size' in item && item.size && (
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-medium">
                                        {String(item.size)}
                                      </span>
                                    )}
                                  </>
                                )}

                                {/* Documentation: Category + Tags */}
                                {selectedDatabase === 'documentation' && (
                                  <>
                                    {'category' in item && item.category && (
                                      <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium">
                                        {String(item.category)}
                                      </span>
                                    )}
                                    {'tags' in item && Array.isArray(item.tags) && item.tags.length > 0 && (item.tags as unknown[]).slice(0, 2).map((tag: unknown, index: number) => (
                                      <span key={index} className="text-xs px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-600 dark:text-teal-400 font-medium">
                                        {String(tag)}
                                      </span>
                                    ))}
                                  </>
                                )}
                              </div>

                              {/* Description */}
                              {'description' in item && item.description && (
                                <p className="text-xs text-light-text/70 dark:text-dark-text/70 mt-1 truncate">
                                  {String(item.description)}
                                </p>
                              )}
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Create Task View */}
              {!loading && view === 'create_task' && (
                <div className="p-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Task Title *
                    </label>
                    <input
                      type="text"
                      value={taskData.title}
                      onChange={(e) => setTaskData({ ...taskData, title: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      placeholder="Enter task title"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                        Status
                      </label>
                      <select
                        value={taskData.status}
                        onChange={(e) => setTaskData({ ...taskData, status: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      >
                        <option>To Do</option>
                        <option>In Progress</option>
                        <option>Done</option>
                        <option>Blocked</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                        Priority
                      </label>
                      <select
                        value={taskData.priority}
                        onChange={(e) => setTaskData({ ...taskData, priority: e.target.value })}
                        className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                      >
                        <option>Low</option>
                        <option>Medium</option>
                        <option>High</option>
                        <option>Urgent</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Due Date
                    </label>
                    <input
                      type="date"
                      value={taskData.due_date}
                      onChange={(e) => setTaskData({ ...taskData, due_date: e.target.value })}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Description
                    </label>
                    <textarea
                      value={taskData.description}
                      onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent resize-none font-body transition-colors"
                      placeholder="Task details..."
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleTaskSubmit}
                      disabled={!taskData.title}
                      className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Create Task
                    </button>
                    <button
                      onClick={handleBack}
                      className="px-4 py-2 rounded-lg hover:bg-accent/10 text-light-text dark:text-dark-text font-sans transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
