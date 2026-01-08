'use client'

import { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronLeft, ChevronRight, ChevronDown, Loader2, Plus, CheckSquare, FolderKanban, Building2, FileText, Maximize2, Minimize2, Mail, SendHorizontal, SquarePen, Trash2, PencilLine, LayoutPanelTop, Columns2, Calendar, Settings, RefreshCw } from 'lucide-react'
import { useEmailData } from '@/hooks/useEmailData'
import { useCalendarData } from '@/hooks/useCalendarData'
import { useStandaloneCalendar } from '@/hooks/useStandaloneCalendar'
import { useNotionData } from '@/hooks/useNotionData'
import { useTasksData } from '@/hooks/useTasksData'
import { CreateTaskRequest } from '@/types/notion'

// Lazy load heavy panel components
const NotionTableView = dynamic(() => import('./NotionTableView'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center py-12"><Loader2 size={32} className="animate-spin text-accent" /></div>
})

const TasksPanel = dynamic(() => import('./TasksPanel'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center py-12"><Loader2 size={32} className="animate-spin text-accent" /></div>
})

const CalendarView = dynamic(() => import('./calendar/CalendarView'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center py-12"><Loader2 size={32} className="animate-spin text-accent" /></div>
})

const EmailView = dynamic(() => import('./email/EmailView'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center py-12"><Loader2 size={32} className="animate-spin text-accent" /></div>
})

type PanelType = 'email' | 'calendar' | 'notion' | 'tasks' | 'docs' | 'drive' | 'slack' | 'git' | null
type DatabaseType = 'tasks' | 'projects' | 'companies' | 'documentation'
type LayoutMode = 'stacked' | 'side-by-side'

interface ServicePanelContainerProps {
  openPanel: PanelType
  onClose: () => void
  panelHeight: number
  onPanelHeightChange: (height: number) => void
  onResizingChange: (isResizing: boolean) => void
  isFullscreen?: boolean
  onFullscreenToggle?: () => void
  layoutMode?: LayoutMode
  onLayoutChange?: (mode: LayoutMode) => void
  panelWidth?: number
  onPanelWidthChange?: (width: number) => void
  // Shared calendar state from page.tsx (for TopBar sync)
  externalCalendarState?: ReturnType<typeof useStandaloneCalendar>
  // Mobile panel switcher (calendar/events)
  mobilePanel?: 'calendar' | 'events'
  // Google sync state (shared with TopBar)
  googleSyncEnabled?: boolean
  onGoogleSyncToggle?: (enabled: boolean) => void
}

interface DatabaseInfo {
  database_type: string
  database_title: string
}

type NotionView = 'list' | 'create_task'

export default function ServicePanelContainer({
  openPanel,
  onClose,
  panelHeight,
  onPanelHeightChange,
  onResizingChange,
  isFullscreen,
  onFullscreenToggle,
  layoutMode = 'stacked',
  onLayoutChange,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  panelWidth = 0.5,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onPanelWidthChange,
  externalCalendarState,
  mobilePanel = 'calendar',
  googleSyncEnabled: externalGoogleSyncEnabled,
  onGoogleSyncToggle: externalOnGoogleSyncToggle
}: ServicePanelContainerProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  // Calculate actual pixel heights for animation
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight - 64 : 600
  const targetHeight = isFullscreen ? viewportHeight : viewportHeight * panelHeight

  // Email state
  const emailData = useEmailData()
  const [selectedEmailFolder, setSelectedEmailFolder] = useState<string>('INBOX')
  const [showEmailFolderDropdown, setShowEmailFolderDropdown] = useState(false)
  const [showEmailSettings, setShowEmailSettings] = useState(false)

  // Calendar state - use external state if provided (for TopBar sync), otherwise use local
  const internalCalendarState = useStandaloneCalendar()
  const standaloneCalendar = externalCalendarState || internalCalendarState
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const calendarData = useCalendarData() // Keep for Google sync option
  const [showViewDropdown, setShowViewDropdown] = useState(false)
  const [showCalendarSettings, setShowCalendarSettings] = useState(false)
  const [internalGoogleSyncEnabled, setInternalGoogleSyncEnabled] = useState(false)

  // Tasks state - Google Tasks sync
  const [showTasksSettings, setShowTasksSettings] = useState(false)
  const [googleTasksSyncEnabled, setGoogleTasksSyncEnabled] = useState(false)
  const [isTasksSyncing, setIsTasksSyncing] = useState(false)
  const [showCompletedTasks, setShowCompletedTasks] = useState(true)
  const [taskLists, setTaskLists] = useState<Array<{ id: string; name: string }>>([])
  const [selectedTaskListId, setSelectedTaskListId] = useState<string | null>(null)
  const [showTaskListDropdown, setShowTaskListDropdown] = useState(false)

  // Use external sync state if provided, otherwise use internal
  const googleCalendarSyncEnabled = externalGoogleSyncEnabled ?? internalGoogleSyncEnabled

  // Load Google Calendar sync preference from localStorage (only if not using external state)
  useEffect(() => {
    if (externalGoogleSyncEnabled === undefined) {
      const saved = localStorage.getItem('cirkelline-google-calendar-sync')
      if (saved === 'true') {
        setInternalGoogleSyncEnabled(true)
      }
    }
  }, [externalGoogleSyncEnabled])

  // Load Google Tasks sync preference from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('cirkelline-google-tasks-sync')
    if (saved === 'true') {
      setGoogleTasksSyncEnabled(true)
    }
  }, [])

  // Save Google Calendar sync preference
  const handleGoogleCalendarSyncToggle = (enabled: boolean) => {
    if (externalOnGoogleSyncToggle) {
      externalOnGoogleSyncToggle(enabled)
    } else {
      setInternalGoogleSyncEnabled(enabled)
      localStorage.setItem('cirkelline-google-calendar-sync', enabled ? 'true' : 'false')
    }

    // If enabling and Google is connected, trigger sync
    if (enabled && googleConnected) {
      standaloneCalendar.syncFromGoogle()
    }
  }

  // Save Google Tasks sync preference and trigger sync/disconnect
  const handleGoogleTasksSyncToggle = async (enabled: boolean) => {
    setGoogleTasksSyncEnabled(enabled)
    localStorage.setItem('cirkelline-google-tasks-sync', enabled ? 'true' : 'false')

    const token = localStorage.getItem('token')
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

    if (enabled && googleConnected) {
      // Toggle ON: Sync from Google Tasks (pull Google tasks into local DB)
      setIsTasksSyncing(true)
      try {
        await fetch(`${apiUrl}/api/tasks/sync/google`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        })
      } catch (error) {
        console.error('Failed to sync from Google Tasks:', error)
      } finally {
        setIsTasksSyncing(false)
      }
    } else if (!enabled) {
      // Toggle OFF: Remove Google tasks from local DB
      setIsTasksSyncing(true)
      try {
        await fetch(`${apiUrl}/api/tasks/sync/google`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        })
      } catch (error) {
        console.error('Failed to disconnect from Google Tasks:', error)
      } finally {
        setIsTasksSyncing(false)
      }
    }
  }

  // Notion state
  const notionData = useNotionData()
  const [notionView, setNotionView] = useState<NotionView>('list')
  const [selectedDatabase, setSelectedDatabase] = useState<DatabaseType>('tasks')
  const [isSyncing, setIsSyncing] = useState(false)
  const [databaseNames, setDatabaseNames] = useState<Partial<Record<DatabaseType, string>>>({})
  const [taskData, setTaskData] = useState<CreateTaskRequest>({
    title: '',
    status: 'To Do',
    priority: 'Medium',
    due_date: '',
    description: '',
    project_id: ''
  })

  // Connection status
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [googleConnected, setGoogleConnected] = useState(false)
  const [notionConnected, setNotionConnected] = useState(false)

  // Check login and connection status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const token = localStorage.getItem('token')
        setIsLoggedIn(!!token)

        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

        // Check Google connection
        const googleResponse = await fetch(`${apiUrl}/api/oauth/google/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (googleResponse.ok) {
          const data = await googleResponse.json()
          setGoogleConnected(data.connected)
        }

        // Check Notion connection
        const notionResponse = await fetch(`${apiUrl}/api/oauth/notion/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (notionResponse.ok) {
          const data = await notionResponse.json()
          setNotionConnected(data.connected)
        }
      } catch {
        // Silently fail - connection check is not critical
      }
    }

    checkStatus()
  }, [])

  // Initialize tasks hook (keep for Google Tasks legacy, but TasksPanel now uses standalone)
  const tasksData = useTasksData()

  // Load data when panel opens (only if connected and no data loaded)
  useEffect(() => {
    if (openPanel === 'email' && googleConnected && emailData.emails.length === 0) {
      emailData.fetchEmails(20)
    } else if (openPanel === 'calendar') {
      // Standalone calendar - always load, no connection required
      if (standaloneCalendar.calendars.length === 0) {
        standaloneCalendar.fetchCalendars()
      }
      // If Google sync is ENABLED by user AND Google is connected, sync from Google
      // Otherwise just fetch local events
      if (googleCalendarSyncEnabled && googleConnected) {
        standaloneCalendar.syncFromGoogle()
      } else if (standaloneCalendar.events.length === 0) {
        standaloneCalendar.fetchEvents()
      }
    } else if (openPanel === 'tasks') {
      // Tasks are now standalone-first (like Calendar)
      // If Google Tasks sync is ENABLED by user AND Google is connected, sync from Google
      if (googleTasksSyncEnabled && googleConnected) {
        const syncTasks = async () => {
          setIsTasksSyncing(true)
          try {
            const token = localStorage.getItem('token')
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
            await fetch(`${apiUrl}/api/tasks/sync/google`, {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${token}` }
            })
          } finally {
            setIsTasksSyncing(false)
          }
        }
        syncTasks()
      }
    } else if (openPanel === 'notion' && notionConnected && (notionData.companies.length + notionData.projects.length + notionData.tasks.length + notionData.documentation.length) === 0) {
      notionData.fetchCompanies()
      notionData.fetchProjects()
      notionData.fetchTasks()
      notionData.fetchDocumentation()
      setNotionView('list')
      setSelectedDatabase('tasks')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openPanel, googleConnected, notionConnected, googleCalendarSyncEnabled])

  // Fetch dynamic database names when Notion is connected
  useEffect(() => {
    if (notionConnected) {
      const fetchDatabaseNames = async () => {
        try {
          const token = localStorage.getItem('token')
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
          const response = await fetch(`${apiUrl}/api/notion/databases`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })

          if (!response.ok) return

          const data = await response.json()

          // Build database names from API response only
          const names: Partial<Record<DatabaseType, string>> = {}

          data.databases?.forEach((db: DatabaseInfo) => {
            if (db.database_type && db.database_title) {
              names[db.database_type as DatabaseType] = db.database_title
            }
          })

          setDatabaseNames(names)
        } catch {
          // Silently fail - database names fetch is not critical
        }
      }

      fetchDatabaseNames()
    }
  }, [notionConnected])

  // ESC key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (openPanel) {
      document.addEventListener('keydown', handleEscape)
    }
    return () => document.removeEventListener('keydown', handleEscape)
  }, [openPanel, onClose])

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('[data-dropdown]')) {
        setShowEmailFolderDropdown(false)
        setShowEmailSettings(false)
        setShowViewDropdown(false)
        setShowCalendarSettings(false)
        setShowTasksSettings(false)
        setShowTaskListDropdown(false)
      }
    }
    // Only add listener if any dropdown is open
    if (showEmailFolderDropdown || showEmailSettings || showViewDropdown || showCalendarSettings || showTasksSettings || showTaskListDropdown) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [showEmailFolderDropdown, showEmailSettings, showViewDropdown, showCalendarSettings, showTasksSettings, showTaskListDropdown])


  // Handle resize dragging
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return

      const viewportHeight = window.innerHeight - 64 // Subtract TopBar height
      const mouseY = e.clientY - 64 // Subtract TopBar height
      const newHeight = Math.max(0.2, Math.min(0.8, mouseY / viewportHeight)) // Constrain between 20% and 80%

      onPanelHeightChange(newHeight)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
      onResizingChange(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    if (isDragging) {
      onResizingChange(true)
      document.body.style.cursor = 'row-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)

      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, onPanelHeightChange, onResizingChange])

  // Notion handlers
  const handleCreateTaskClick = () => {
    setTaskData({
      title: '',
      status: 'To Do',
      priority: 'Medium',
      due_date: '',
      description: '',
      project_id: ''
    })
    setNotionView('create_task')
  }

  const handleTaskSubmit = async () => {
    const success = await notionData.createTask(taskData)
    if (success) {
      setNotionView('list')
      setSelectedDatabase('tasks')
    }
  }

  const handleNotionBack = () => {
    setNotionView('list')
    notionData.clearError()
  }

  const handleSyncDatabases = async () => {
    if (isSyncing || notionData.loading) return // Prevent double-clicking

    setIsSyncing(true)
    try {
      await notionData.syncDatabases()
    } catch {
      // Error is already handled by the hook
    } finally {
      setIsSyncing(false)
    }
  }

  // Notion utility functions
  const getCurrentItems = () => {
    switch (selectedDatabase) {
      case 'tasks': return notionData.tasks
      case 'projects': return notionData.projects
      case 'companies': return notionData.companies
      case 'documentation': return notionData.documentation
      default: return []
    }
  }

  const getDatabaseIcon = (type: DatabaseType) => {
    switch (type) {
      case 'tasks': return CheckSquare
      case 'projects': return FolderKanban
      case 'companies': return Building2
      case 'documentation': return FileText
    }
  }

  const isOpen = openPanel !== null
  const isConnected = openPanel === 'notion' ? notionConnected : googleConnected

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          initial={{ height: 0, opacity: 0 }}
          animate={{
            height: layoutMode === 'side-by-side' ? '100%' : targetHeight,
            opacity: 1
          }}
          exit={{ height: 0, opacity: 0 }}
          transition={
            isDragging
              ? { duration: 0 }
              : {
                  height: { duration: 0.6, type: 'tween', ease: [0.4, 0, 0.2, 1] },
                  opacity: { duration: 0.3 }
                }
          }
          className={`
            relative
            w-full
            shadow-lg
            flex flex-col
            z-50
            ${layoutMode === 'side-by-side' ? 'h-full border-r border-border-primary' : 'border-b border-border-primary'}
          `}
        >
          {/* Full width background layer - covers edge to edge */}
          <div className="absolute inset-0 bg-app-container z-0" />

          {/* Centered content container */}
          <div className="relative w-full max-w-7xl mx-auto flex flex-col h-full overflow-hidden">
            {/* Header - Hidden on mobile for calendar (controls are in TopBar) */}
            <div className={`${openPanel === 'calendar' ? 'hidden md:block' : ''} px-2 sm:px-4 lg:px-6 py-1 sm:py-2 border-b border-border-primary bg-app-container sticky top-0 z-10`}>
              {/* Single Row Layout - Different for Calendar vs Others */}
              {openPanel === 'calendar' ? (
                /* Calendar: Redesigned header matching mobile TopBar style */
                <div className="flex items-center justify-between gap-3">
                  {/* Left: View Dropdown - bordered style */}
                  <div className="relative flex-shrink-0" data-dropdown>
                    <button
                      onClick={() => setShowViewDropdown(!showViewDropdown)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-light-text dark:text-dark-text border border-border-primary rounded-lg bg-app-container hover:bg-app-container transition-colors"
                    >
                      <Calendar size={14} className="text-accent" />
                      <span>{standaloneCalendar.activeView.charAt(0).toUpperCase() + standaloneCalendar.activeView.slice(1)}</span>
                      <ChevronDown size={12} className={`text-light-text-secondary dark:text-dark-text-secondary transition-transform ${showViewDropdown ? 'rotate-180' : ''}`} />
                    </button>
                    {showViewDropdown && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        className="absolute top-full left-0 mt-1 bg-app-container border border-border-primary rounded-lg shadow-lg overflow-hidden z-[9999] min-w-[100px]"
                      >
                        {(['month', 'week', 'day'] as const).map((view) => (
                          <button
                            key={view}
                            onClick={() => {
                              standaloneCalendar.setActiveView(view);
                              setShowViewDropdown(false);
                            }}
                            className={`w-full px-3 py-2 text-xs text-left transition-colors ${standaloneCalendar.activeView === view ? 'bg-accent text-white' : 'text-light-text dark:text-dark-text hover:bg-accent/10'}`}
                          >
                            {view.charAt(0).toUpperCase() + view.slice(1)}
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </div>

                  {/* Center: Date Navigation - bordered style */}
                  <div className="flex items-center border border-border-primary rounded-lg overflow-hidden bg-app-container">
                    <button
                      onClick={() => {
                        const newDate = new Date(standaloneCalendar.selectedDate);
                        newDate.setMonth(newDate.getMonth() - 1);
                        standaloneCalendar.setSelectedDate(newDate);
                      }}
                      className="p-1.5 hover:bg-app-container transition-colors"
                      aria-label="Previous month"
                    >
                      <ChevronLeft size={16} className="text-light-text dark:text-dark-text" />
                    </button>
                    <span className="text-xs font-medium text-light-text dark:text-dark-text px-3 min-w-[100px] text-center border-x border-border-primary">
                      {standaloneCalendar.selectedDate.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                    </span>
                    <button
                      onClick={() => {
                        const newDate = new Date(standaloneCalendar.selectedDate);
                        newDate.setMonth(newDate.getMonth() + 1);
                        standaloneCalendar.setSelectedDate(newDate);
                      }}
                      className="p-1.5 hover:bg-app-container transition-colors"
                      aria-label="Next month"
                    >
                      <ChevronRight size={16} className="text-light-text dark:text-dark-text" />
                    </button>
                  </div>

                  {/* Right: Action Icons */}
                  <div className="flex items-center gap-0.5 flex-shrink-0">
                    {/* Settings Dropdown */}
                    <div className="relative" data-dropdown>
                      <button
                        onClick={() => setShowCalendarSettings(!showCalendarSettings)}
                        className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title="Settings"
                      >
                        <Settings size={layoutMode === 'side-by-side' ? 14 : 16} />
                      </button>
                      <AnimatePresence>
                        {showCalendarSettings && (
                          <motion.div
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -5 }}
                            className="absolute top-full right-0 mt-1 bg-app-container border border-border-primary rounded-lg shadow-lg z-[100] p-1.5"
                          >
                            <button
                              onClick={() => googleConnected && handleGoogleCalendarSyncToggle(!googleCalendarSyncEnabled)}
                              disabled={!googleConnected}
                              className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md whitespace-nowrap transition-colors ${
                                googleCalendarSyncEnabled && googleConnected
                                  ? 'bg-green-50 dark:bg-green-900/20'
                                  : 'hover:bg-app-container'
                              } ${!googleConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            >
                              {googleCalendarSyncEnabled && googleConnected && (
                                <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                              )}
                              <span className={`text-xs font-medium whitespace-nowrap ${
                                googleCalendarSyncEnabled && googleConnected
                                  ? 'text-green-700 dark:text-green-400'
                                  : 'text-light-text dark:text-dark-text'
                              }`}>Connected to Google Calendar</span>
                              <div className={`relative w-7 h-3.5 rounded-full transition-colors flex-shrink-0 ${
                                googleCalendarSyncEnabled && googleConnected ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                              }`}>
                                <span className={`absolute top-0.5 left-0.5 w-2.5 h-2.5 bg-white rounded-full transition-transform ${
                                  googleCalendarSyncEnabled && googleConnected ? 'translate-x-3.5' : 'translate-x-0'
                                }`} />
                              </div>
                            </button>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                    {/* Refresh */}
                    <button
                      onClick={async () => {
                        if (googleCalendarSyncEnabled && googleConnected) {
                          await standaloneCalendar.syncFromGoogle();
                        } else {
                          standaloneCalendar.fetchCalendars();
                          standaloneCalendar.fetchEvents();
                        }
                      }}
                      disabled={standaloneCalendar.loading || standaloneCalendar.isSyncing}
                      className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors disabled:opacity-50 ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                      title={(googleCalendarSyncEnabled && googleConnected) ? "Sync with Google Calendar" : "Refresh calendar"}
                    >
                      <RefreshCw size={layoutMode === 'side-by-side' ? 14 : 16} className={(standaloneCalendar.loading || standaloneCalendar.isSyncing) ? 'animate-spin' : ''} />
                    </button>
                    {/* Layout Toggle */}
                    {onLayoutChange && (
                      <button
                        onClick={() => onLayoutChange(layoutMode === 'stacked' ? 'side-by-side' : 'stacked')}
                        className={`hidden md:block rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title={layoutMode === 'stacked' ? 'Side by side' : 'Stacked'}
                      >
                        {layoutMode === 'stacked' ? <Columns2 size={16} /> : <LayoutPanelTop size={14} />}
                      </button>
                    )}
                    {/* Fullscreen */}
                    {onFullscreenToggle && (
                      <button
                        onClick={onFullscreenToggle}
                        className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                      >
                        {isFullscreen ? <Minimize2 size={layoutMode === 'side-by-side' ? 14 : 16} /> : <Maximize2 size={layoutMode === 'side-by-side' ? 14 : 16} />}
                      </button>
                    )}
                    {/* Close */}
                    <button
                      onClick={onClose}
                      className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-red-500 hover:bg-red-500/10 transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                      title="Close calendar"
                    >
                      <X size={layoutMode === 'side-by-side' ? 16 : 18} />
                    </button>
                  </div>
                </div>
              ) : openPanel === 'email' ? (
                /* Email: Single row header like Calendar */
                <div className="flex items-center justify-between gap-3">
                  {/* Left: Folder Dropdown */}
                  <div className="relative flex-shrink-0" data-dropdown>
                    <button
                      onClick={() => setShowEmailFolderDropdown(!showEmailFolderDropdown)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-light-text dark:text-dark-text border border-border-primary rounded-lg bg-app-container hover:bg-app-container transition-colors"
                    >
                      {selectedEmailFolder === 'INBOX' ? <Mail size={14} className="text-accent" /> :
                       selectedEmailFolder === 'SENT' ? <SendHorizontal size={14} className="text-accent" /> :
                       selectedEmailFolder === 'DRAFT' ? <SquarePen size={14} className="text-accent" /> :
                       <Trash2 size={14} className="text-accent" />}
                      <span>{selectedEmailFolder === 'INBOX' ? 'Inbox' : selectedEmailFolder === 'SENT' ? 'Sent' : selectedEmailFolder === 'DRAFT' ? 'Drafts' : 'Trash'}</span>
                      <ChevronDown size={12} className={`text-light-text-secondary dark:text-dark-text-secondary transition-transform ${showEmailFolderDropdown ? 'rotate-180' : ''}`} />
                    </button>
                    {showEmailFolderDropdown && (
                      <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        className="absolute top-full left-0 mt-1 bg-app-container border border-border-primary rounded-lg shadow-lg overflow-hidden z-[9999] min-w-[120px]"
                      >
                        {(['INBOX', 'SENT', 'DRAFT', 'TRASH'] as const).map((folder) => {
                          const FolderIcon = folder === 'INBOX' ? Mail : folder === 'SENT' ? SendHorizontal : folder === 'DRAFT' ? SquarePen : Trash2
                          const folderLabel = folder === 'INBOX' ? 'Inbox' : folder === 'SENT' ? 'Sent' : folder === 'DRAFT' ? 'Drafts' : 'Trash'
                          return (
                            <button
                              key={folder}
                              onClick={() => {
                                setSelectedEmailFolder(folder);
                                setShowEmailFolderDropdown(false);
                              }}
                              className={`w-full flex items-center gap-2 px-3 py-2 text-xs text-left transition-colors ${selectedEmailFolder === folder ? 'bg-accent text-white' : 'text-light-text dark:text-dark-text hover:bg-accent/10'}`}
                            >
                              <FolderIcon size={14} />
                              {folderLabel}
                            </button>
                          )
                        })}
                      </motion.div>
                    )}
                  </div>

                  {/* Center: Compose Button - filled grey like active sessions */}
                  <button
                    onClick={() => { const e = new CustomEvent('email-compose'); window.dispatchEvent(e); }}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-light-text dark:text-dark-text rounded-lg bg-[#E4E4E2] dark:bg-[#2A2A2A] hover:bg-[#D4D4D2] dark:hover:bg-[#3A3A3A] transition-colors"
                  >
                    <PencilLine size={14} className="text-accent" />
                    <span>Compose</span>
                  </button>

                  {/* Right: Action Icons */}
                  <div className="flex items-center gap-0.5 flex-shrink-0">
                    {/* Settings Dropdown */}
                    <div className="relative" data-dropdown>
                      <button
                        onClick={() => setShowEmailSettings(!showEmailSettings)}
                        className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title="Settings"
                      >
                        <Settings size={layoutMode === 'side-by-side' ? 14 : 16} />
                      </button>
                      <AnimatePresence>
                        {showEmailSettings && (
                          <motion.div
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -5 }}
                            className="absolute top-full right-0 mt-1 bg-app-container border border-border-primary rounded-lg shadow-lg z-[100] p-1.5"
                          >
                            {/* Gmail Connection Status */}
                            <div className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md whitespace-nowrap ${
                              googleConnected ? 'bg-green-50 dark:bg-green-900/20' : ''
                            }`}>
                              {googleConnected && (
                                <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                              )}
                              <span className={`text-xs font-medium whitespace-nowrap ${
                                googleConnected
                                  ? 'text-green-700 dark:text-green-400'
                                  : 'text-light-text-secondary dark:text-dark-text-secondary'
                              }`}>{googleConnected ? 'Connected to Gmail' : 'Gmail not connected'}</span>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                    {/* Refresh */}
                    <button
                      onClick={() => emailData.fetchEmails(20)}
                      disabled={emailData.loading}
                      className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors disabled:opacity-50 ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                      title="Refresh"
                    >
                      <RefreshCw size={layoutMode === 'side-by-side' ? 14 : 16} className={emailData.loading ? 'animate-spin' : ''} />
                    </button>
                    {/* Layout Toggle */}
                    {onLayoutChange && (
                      <button
                        onClick={() => onLayoutChange(layoutMode === 'stacked' ? 'side-by-side' : 'stacked')}
                        className={`hidden md:block rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title={layoutMode === 'stacked' ? 'Side by side' : 'Stacked'}
                      >
                        {layoutMode === 'stacked' ? <Columns2 size={16} /> : <LayoutPanelTop size={14} />}
                      </button>
                    )}
                    {/* Fullscreen */}
                    {onFullscreenToggle && (
                      <button
                        onClick={onFullscreenToggle}
                        className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                      >
                        {isFullscreen ? <Minimize2 size={layoutMode === 'side-by-side' ? 14 : 16} /> : <Maximize2 size={layoutMode === 'side-by-side' ? 14 : 16} />}
                      </button>
                    )}
                    {/* Close */}
                    <button
                      onClick={onClose}
                      className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-red-500 hover:bg-red-500/10 transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                      title="Close email"
                    >
                      <X size={layoutMode === 'side-by-side' ? 16 : 18} />
                    </button>
                  </div>
                </div>
              ) : openPanel === 'tasks' ? (
                /* Tasks Panel: Single row header like Calendar */
                <div className="flex items-center justify-between gap-3">
                  {/* Left: List selector in side-by-side, static title in stacked */}
                  {layoutMode === 'side-by-side' && taskLists.length > 0 ? (
                    <div className="relative flex-shrink-0" data-dropdown>
                      <button
                        onClick={() => setShowTaskListDropdown(!showTaskListDropdown)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-light-text dark:text-dark-text border border-border-primary rounded-lg bg-app-container hover:bg-app-container transition-colors"
                      >
                        <CheckSquare size={14} className="text-accent" />
                        <span>{taskLists.find(l => l.id === selectedTaskListId)?.name || 'Select list'}</span>
                        <ChevronDown size={12} className={`text-light-text-secondary dark:text-dark-text-secondary transition-transform ${showTaskListDropdown ? 'rotate-180' : ''}`} />
                      </button>
                      {showTaskListDropdown && (
                        <motion.div
                          initial={{ opacity: 0, y: -5 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -5 }}
                          className="absolute top-full left-0 mt-1 bg-app-container border border-border-primary rounded-lg shadow-lg overflow-hidden z-[9999] min-w-[140px]"
                        >
                          {taskLists.map((list) => (
                            <button
                              key={list.id}
                              onClick={() => {
                                setSelectedTaskListId(list.id)
                                setShowTaskListDropdown(false)
                              }}
                              className={`w-full px-3 py-2 text-xs text-left transition-colors ${selectedTaskListId === list.id ? 'bg-accent text-white' : 'text-light-text dark:text-dark-text hover:bg-accent/10'}`}
                            >
                              {list.name}
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-light-text dark:text-dark-text border border-border-primary rounded-lg bg-app-container">
                      <CheckSquare size={14} className="text-accent" />
                      <span>Tasks</span>
                    </div>
                  )}

                  {/* Right: Action Icons */}
                  <div className="flex items-center gap-0.5 flex-shrink-0">
                    {/* Settings Dropdown */}
                    <div className="relative" data-dropdown>
                      <button
                        onClick={() => setShowTasksSettings(!showTasksSettings)}
                        className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title="Settings"
                      >
                        <Settings size={layoutMode === 'side-by-side' ? 14 : 16} />
                      </button>
                      <AnimatePresence>
                        {showTasksSettings && (
                          <motion.div
                            initial={{ opacity: 0, y: -5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -5 }}
                            className="absolute top-full right-0 mt-1 bg-app-container border border-border-primary rounded-lg shadow-lg z-[100] p-1.5 min-w-[160px]"
                          >
                            {/* Settings Section */}
                            <div className="px-2.5 py-0.5 text-[8px] font-semibold text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                              Settings
                            </div>
                            <button
                              onClick={() => setShowCompletedTasks(!showCompletedTasks)}
                              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md whitespace-nowrap transition-colors ${
                                showCompletedTasks
                                  ? 'bg-accent/10'
                                  : 'hover:bg-app-container'
                              } cursor-pointer`}
                            >
                              <span className={`text-xs font-medium whitespace-nowrap ${
                                showCompletedTasks
                                  ? 'text-accent'
                                  : 'text-light-text dark:text-dark-text'
                              }`}>Show Completed</span>
                              <div className={`relative w-7 h-3.5 rounded-full transition-colors flex-shrink-0 ml-auto ${
                                showCompletedTasks ? 'bg-accent' : 'bg-gray-300 dark:bg-gray-600'
                              }`}>
                                <span className={`absolute top-0.5 left-0.5 w-2.5 h-2.5 bg-white rounded-full transition-transform ${
                                  showCompletedTasks ? 'translate-x-3.5' : 'translate-x-0'
                                }`} />
                              </div>
                            </button>

                            {/* Connect to Section */}
                            <div className="px-2.5 py-0.5 mt-1.5 text-[8px] font-semibold text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider border-t border-border-primary pt-1.5">
                              Connect to
                            </div>
                            <button
                              onClick={() => googleConnected && handleGoogleTasksSyncToggle(!googleTasksSyncEnabled)}
                              disabled={!googleConnected}
                              className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md whitespace-nowrap transition-colors ${
                                googleTasksSyncEnabled && googleConnected
                                  ? 'bg-green-50 dark:bg-green-900/20'
                                  : 'hover:bg-app-container'
                              } ${!googleConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            >
                              {googleTasksSyncEnabled && googleConnected && (
                                <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                              )}
                              <span className={`text-xs font-medium whitespace-nowrap ${
                                googleTasksSyncEnabled && googleConnected
                                  ? 'text-green-700 dark:text-green-400'
                                  : 'text-light-text dark:text-dark-text'
                              }`}>Google Tasks</span>
                              <div className={`relative w-7 h-3.5 rounded-full transition-colors flex-shrink-0 ml-auto ${
                                googleTasksSyncEnabled && googleConnected ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                              }`}>
                                <span className={`absolute top-0.5 left-0.5 w-2.5 h-2.5 bg-white rounded-full transition-transform ${
                                  googleTasksSyncEnabled && googleConnected ? 'translate-x-3.5' : 'translate-x-0'
                                }`} />
                              </div>
                            </button>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                    {/* Refresh */}
                    <button
                      onClick={async () => {
                        if (googleTasksSyncEnabled && googleConnected) {
                          setIsTasksSyncing(true)
                          try {
                            const token = localStorage.getItem('token')
                            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
                            await fetch(`${apiUrl}/api/tasks/sync/google`, {
                              method: 'POST',
                              headers: { 'Authorization': `Bearer ${token}` }
                            })
                          } finally {
                            setIsTasksSyncing(false)
                          }
                        }
                        tasksData.fetchTaskLists()
                      }}
                      disabled={tasksData.loading || isTasksSyncing}
                      className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors disabled:opacity-50 ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                      title={(googleTasksSyncEnabled && googleConnected) ? "Sync with Google Tasks" : "Refresh tasks"}
                    >
                      <RefreshCw size={layoutMode === 'side-by-side' ? 14 : 16} className={(tasksData.loading || isTasksSyncing) ? 'animate-spin' : ''} />
                    </button>
                    {/* Layout Toggle */}
                    {onLayoutChange && (
                      <button
                        onClick={() => onLayoutChange(layoutMode === 'stacked' ? 'side-by-side' : 'stacked')}
                        className={`hidden md:block rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title={layoutMode === 'stacked' ? 'Side by side' : 'Stacked'}
                      >
                        {layoutMode === 'stacked' ? <Columns2 size={16} /> : <LayoutPanelTop size={14} />}
                      </button>
                    )}
                    {/* Fullscreen */}
                    {onFullscreenToggle && (
                      <button
                        onClick={onFullscreenToggle}
                        className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-app-container transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                        title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                      >
                        {isFullscreen ? <Minimize2 size={layoutMode === 'side-by-side' ? 14 : 16} /> : <Maximize2 size={layoutMode === 'side-by-side' ? 14 : 16} />}
                      </button>
                    )}
                    {/* Close */}
                    <button
                      onClick={onClose}
                      className={`rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-red-500 hover:bg-red-500/10 transition-colors ${layoutMode === 'side-by-side' ? 'p-1' : 'p-1.5'}`}
                      title="Close tasks"
                    >
                      <X size={layoutMode === 'side-by-side' ? 16 : 18} />
                    </button>
                  </div>
                </div>
              ) : (
                /* Notion Panel: Two rows */
                <div className="space-y-2">
                  {/* First Row: Title and Action Buttons */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {notionView !== 'list' && (
                        <button onClick={handleNotionBack} className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors">
                          <ChevronLeft size={16} />
                        </button>
                      )}
                      <h2 className="text-sm font-heading font-bold text-light-text dark:text-dark-text">{notionView === 'list' ? 'Notion Workspace' : 'Create Task'}</h2>
                    </div>
                    <div className="flex items-center gap-2">
                      {notionView === 'list' && (
                        <button onClick={handleCreateTaskClick} className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-accent text-white rounded hover:bg-accent/90 transition-colors">
                          <Plus size={14} />Create {selectedDatabase === 'tasks' ? 'Task' : selectedDatabase === 'projects' ? 'Project' : selectedDatabase === 'companies' ? 'Company' : 'Document'}
                        </button>
                      )}
                      <button
                        onClick={handleSyncDatabases}
                        disabled={isSyncing || notionData.loading}
                        className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors disabled:opacity-50"
                      >
                        <RefreshCw size={13} className={isSyncing ? 'animate-spin' : ''} />
                      </button>
                      {onLayoutChange && (
                        <button onClick={() => onLayoutChange(layoutMode === 'stacked' ? 'side-by-side' : 'stacked')} className="hidden md:block p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors" title={layoutMode === 'stacked' ? 'Side by side' : 'Stacked'}>
                          {layoutMode === 'stacked' ? <Columns2 size={13} /> : <LayoutPanelTop size={13} />}
                        </button>
                      )}
                      {onFullscreenToggle && (
                        <button onClick={onFullscreenToggle} className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors">
                          {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
                        </button>
                      )}
                      <button onClick={onClose} className="p-1 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors">
                        <X size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Second Row: Tabs (only for Notion list view) */}
                  {notionView === 'list' && (
                    <div className="flex items-center gap-2">
                      {(['tasks', 'projects', 'companies', 'documentation'] as DatabaseType[]).map((db) => {
                        const Icon = getDatabaseIcon(db)
                        const count = db === 'tasks' ? notionData.tasks.length : db === 'projects' ? notionData.projects.length : db === 'companies' ? notionData.companies.length : notionData.documentation.length
                        const name = databaseNames[db]
                        return { db, Icon, count, name }
                      }).filter(({ count, name }) => count > 0 && name).map(({ db, Icon, name }) => (
                        <button key={db} onClick={() => setSelectedDatabase(db)} className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded transition-colors ${selectedDatabase === db ? 'bg-accent text-white' : 'text-light-text-secondary/60 dark:text-dark-text-secondary/60 hover:bg-accent/10 hover:text-light-text dark:hover:text-dark-text'}`}>
                          <Icon size={14} />{name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Error Display */}
            {((openPanel === 'email' && emailData.error) ||
              (openPanel === 'calendar' && standaloneCalendar.error) ||
              (openPanel === 'tasks' && tasksData.error) ||
              (openPanel === 'notion' && notionData.error)) && (
              <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
                <p className="text-sm text-red-600 dark:text-red-400">
                  {openPanel === 'email' ? emailData.error :
                   openPanel === 'calendar' ? standaloneCalendar.error :
                   openPanel === 'tasks' ? tasksData.error :
                   notionData.error}
                </p>
              </div>
            )}

            {/* Content */}
            <div className={`flex-1 ${openPanel === 'email' || openPanel === 'calendar' || openPanel === 'tasks' || openPanel === 'notion' ? 'h-0 min-h-0' : ''}`}>
              {/* Show message if not logged in or not connected (calendar is standalone, only needs login) */}
              {!isLoggedIn && openPanel === 'calendar' && (
                <div className="flex items-center justify-center py-12 px-6">
                  <div className="text-center max-w-md">
                    <p className="text-sm text-light-text/70 dark:text-dark-text/70">
                      Please login to view and manage your calendar
                    </p>
                  </div>
                </div>
              )}

              {/* Show connect prompt only for email/notion (not calendar/tasks which are standalone) */}
              {!isConnected && openPanel !== 'calendar' && openPanel !== 'tasks' && (
                <div className="flex items-center justify-center py-12 px-6">
                  <div className="text-center max-w-md">
                    <p className="text-sm text-light-text/70 dark:text-dark-text/70">
                      {!isLoggedIn
                        ? `Please login and connect to your ${openPanel === 'notion' ? 'Notion workspace' : 'Google account'} to view and manage your ${openPanel === 'email' ? 'email' : 'Notion workspace'}`
                        : `Please connect to your ${openPanel === 'notion' ? 'Notion workspace' : 'Google account'} to view and manage your ${openPanel === 'email' ? 'email' : 'Notion workspace'}`
                      }
                    </p>
                  </div>
                </div>
              )}

              {/* Tasks login prompt (standalone, only needs login) */}
              {!isLoggedIn && openPanel === 'tasks' && (
                <div className="flex items-center justify-center py-12 px-6">
                  <div className="text-center max-w-md">
                    <p className="text-sm text-light-text/70 dark:text-dark-text/70">
                      Please login to view and manage your tasks
                    </p>
                  </div>
                </div>
              )}

              {/* Loading state for panels that need connection (email, notion) */}
              {isConnected && openPanel !== 'calendar' && openPanel !== 'tasks' && (
                openPanel === 'email' ? (emailData.loading && emailData.emails.length === 0) :
                (notionData.loading && (notionData.companies.length + notionData.projects.length + notionData.tasks.length + notionData.documentation.length) === 0)
              ) && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={32} className="animate-spin text-accent" />
                </div>
              )}

              {/* Calendar loading state (standalone, only needs login) */}
              {isLoggedIn && openPanel === 'calendar' && standaloneCalendar.loading && standaloneCalendar.calendars.length === 0 && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={32} className="animate-spin text-accent" />
                </div>
              )}

              {/* Email Content */}
              {isConnected && openPanel === 'email' && !(emailData.loading && emailData.emails.length === 0) && (
                <EmailView
                  emails={emailData.emails}
                  currentEmail={emailData.currentEmail}
                  loading={emailData.loading}
                  selectedFolder={selectedEmailFolder}
                  nextPageToken={emailData.nextPageToken}
                  layoutMode={layoutMode}
                  fetchEmails={emailData.fetchEmails}
                  fetchEmailDetail={emailData.fetchEmailDetail}
                  sendEmail={emailData.sendEmail}
                  replyToEmail={emailData.replyToEmail}
                  archiveEmail={emailData.archiveEmail}
                  deleteEmail={emailData.deleteEmail}
                />
              )}

              {/* Calendar Content (Standalone - only needs login) */}
              {isLoggedIn && openPanel === 'calendar' && (
                <CalendarView
                  activeView={standaloneCalendar.activeView}
                  events={standaloneCalendar.events}
                  loading={standaloneCalendar.loading}
                  error={standaloneCalendar.error}
                  selectedDate={standaloneCalendar.selectedDate}
                  selectedEvent={standaloneCalendar.selectedEvent}
                  clearError={standaloneCalendar.clearError}
                  setSelectedDate={standaloneCalendar.setSelectedDate}
                  setSelectedEvent={standaloneCalendar.setSelectedEvent}
                  // Layout mode for side-by-side vs stacked internal layout
                  layoutMode={layoutMode}
                  // Mobile panel switcher
                  mobilePanel={mobilePanel}
                  // Standalone calendar props
                  calendars={standaloneCalendar.calendars}
                  onCreateEvent={standaloneCalendar.createEvent}
                  onUpdateEvent={standaloneCalendar.updateEvent}
                  onDeleteEvent={standaloneCalendar.deleteEvent}
                  getDefaultCalendar={standaloneCalendar.getDefaultCalendar}
                />
              )}

              {/* Tasks Content (Standalone - only needs login) */}
              {isLoggedIn && openPanel === 'tasks' && (
                <TasksPanel
                  isOpen={true}
                  googleSyncEnabled={googleTasksSyncEnabled}
                  layoutMode={layoutMode}
                  showCompleted={showCompletedTasks}
                  selectedListId={selectedTaskListId}
                  onListChange={setSelectedTaskListId}
                  onListsLoaded={(lists) => {
                    setTaskLists(lists.map(l => ({ id: l.id, name: l.name })))
                    if (!selectedTaskListId && lists.length > 0) {
                      setSelectedTaskListId(lists[0].id)
                    }
                  }}
                />
              )}

              {/* Notion Content */}
              {isConnected && openPanel === 'notion' && !(notionData.loading && (notionData.companies.length + notionData.projects.length + notionData.tasks.length + notionData.documentation.length) === 0) && (
                <>
                  {notionView === 'list' && (
                    <div className="h-full">
                      <NotionTableView
                        items={getCurrentItems()}
                        databaseType={selectedDatabase}
                      />
                    </div>
                  )}

                  {/* Create Task View */}
                  {notionView === 'create_task' && (
                    <div className="p-6 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                          Task Title *
                        </label>
                        <input
                          type="text"
                          value={taskData.title}
                          onChange={(e) => setTaskData({ ...taskData, title: e.target.value })}
                          className="w-full px-4 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-body transition-colors"
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
                            className="w-full px-4 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-body transition-colors"
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
                            className="w-full px-4 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-body transition-colors"
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
                          className="w-full px-4 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-body transition-colors"
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
                          className="w-full px-4 py-2 rounded-lg bg-app-container text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent resize-none font-body transition-colors"
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
                          onClick={handleNotionBack}
                          className="px-4 py-2 rounded-lg hover:bg-accent/10 text-light-text dark:text-dark-text font-sans transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Google Docs Placeholder */}
              {openPanel === 'docs' && (
                <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                  <FileText size={64} className="text-light-text-secondary dark:text-dark-text-secondary mb-4" />
                  <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
                    Google Docs Integration
                  </h3>
                  <p className="text-light-text-secondary dark:text-dark-text-secondary max-w-md">
                    Coming soon! Access and manage your Google Docs directly from Cirkelline.
                  </p>
                </div>
              )}

              {/* Google Drive Placeholder */}
              {openPanel === 'drive' && (
                <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                  <FileText size={64} className="text-light-text-secondary dark:text-dark-text-secondary mb-4" />
                  <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
                    Google Drive Integration
                  </h3>
                  <p className="text-light-text-secondary dark:text-dark-text-secondary max-w-md">
                    Coming soon! Browse and manage your Google Drive files directly from Cirkelline.
                  </p>
                </div>
              )}

              {/* Slack Placeholder */}
              {openPanel === 'slack' && (
                <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                  <FileText size={64} className="text-light-text-secondary dark:text-dark-text-secondary mb-4" />
                  <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
                    Slack Integration
                  </h3>
                  <p className="text-light-text-secondary dark:text-dark-text-secondary max-w-md">
                    Coming soon! Connect your Slack workspace and manage messages from Cirkelline.
                  </p>
                </div>
              )}

              {/* GitHub Placeholder */}
              {openPanel === 'git' && (
                <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                  <FileText size={64} className="text-light-text-secondary dark:text-dark-text-secondary mb-4" />
                  <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
                    GitHub Integration
                  </h3>
                  <p className="text-light-text-secondary dark:text-dark-text-secondary max-w-md">
                    Coming soon! Manage your repositories, issues, and pull requests from Cirkelline.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Resize Handle - Draggable border (hidden in fullscreen and side-by-side) */}
          {!isFullscreen && layoutMode !== 'side-by-side' && (
            <div
              onMouseDown={() => setIsDragging(true)}
              className="flex-shrink-0 w-full h-2 border-t border-border-primary hover:border-accent transition-colors cursor-row-resize"
              title="Drag to resize panel"
            />
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
