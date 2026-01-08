'use client'
import { Button } from '@/components/ui/button'
import { ModeSelector } from '@/components/chat/Sidebar/ModeSelector'
import { EntitySelector } from '@/components/chat/Sidebar/EntitySelector'
import useChatActions from '@/hooks/useChatActions'
import { useStore } from '@/store'
import { useState, useEffect } from 'react'
import Icon from '@/components/ui/icon'
import { getProviderIcon } from '@/lib/modelProvider'
import Sessions from './Sessions'
import { Journals } from './Journals'
import { isValidUrl } from '@/lib/utils'
import { toast } from 'sonner'
import { useQueryState } from 'nuqs'
import { truncateText } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { useSidebar } from '@/hooks/useSidebar'
import { ChevronRight, X, ExternalLink, Mail, Calendar, CheckSquare, Layers2, MessageSquare, FolderKanban, StickyNote, ListTodo, Files, BookOpen, PanelRightOpen } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { sidebarContent } from '@/lib/animations'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { usePathname, useRouter } from 'next/navigation'

const ENDPOINT_PLACEHOLDER = 'NO ENDPOINT ADDED'

type PanelType = 'email' | 'calendar' | 'tasks' | 'docs' | 'drive' | 'notion' | 'slack' | 'git' | null

interface SidebarProps {
  openPanel?: PanelType
  onPanelChange?: (panel: PanelType) => void
}

const ModelDisplay = ({ model, isCollapsed }: { model: string; isCollapsed: boolean }) => {
  if (isCollapsed) {
    const icon = getProviderIcon(model)
    return (
      <div className="flex h-9 w-full items-center justify-center rounded-xl border border-border-primary bg-light-surface p-3 dark:bg-dark-surface transition-colors" title={model}>
        {icon && <Icon type={icon} className="shrink-0" size="xs" />}
      </div>
    )
  }

  return (
    <div className="flex h-9 w-full items-center gap-3 rounded-xl border border-border-primary bg-light-surface p-3 text-xs font-medium uppercase text-light-text dark:bg-dark-surface dark:text-dark-text transition-colors">
      {(() => {
        const icon = getProviderIcon(model)
        return icon ? <Icon type={icon} className="shrink-0" size="xs" /> : null
      })()}
      {model}
    </div>
  )
}

const Endpoint = ({ isCollapsed }: { isCollapsed: boolean }) => {
  const {
    selectedEndpoint,
    isEndpointActive,
    setSelectedEndpoint,
    setAgents,
    setSessionsData,
    setMessages
  } = useStore()
  const { initialize } = useChatActions()
  const [isEditing, setIsEditing] = useState(false)
  const [endpointValue, setEndpointValue] = useState('')
  const [isMounted, setIsMounted] = useState(false)
  const [isRotating, setIsRotating] = useState(false)
  const [, setAgentId] = useQueryState('agent')
  const [, setSessionId] = useQueryState('session')

  useEffect(() => {
    setEndpointValue(selectedEndpoint)
    setIsMounted(true)
  }, [selectedEndpoint])

  const getStatusColor = (isActive: boolean) =>
    isActive ? 'bg-positive' : 'bg-destructive'

  const handleSave = async () => {
    if (!isValidUrl(endpointValue)) {
      toast.error('Please enter a valid URL')
      return
    }
    const cleanEndpoint = endpointValue.replace(/\/$/, '').trim()
    setSelectedEndpoint(cleanEndpoint)
    setAgentId(null)
    setSessionId(null)
    setIsEditing(false)
    setAgents([])
    setSessionsData([])
    setMessages([])
  }

  const handleCancel = () => {
    setEndpointValue(selectedEndpoint)
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      handleCancel()
    }
  }

  const handleRefresh = async () => {
    setIsRotating(true)
    await initialize()
    setTimeout(() => setIsRotating(false), 500)
  }

  if (isCollapsed) {
    return (
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={handleRefresh}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-border-primary bg-light-surface text-light-text hover:bg-light-bg dark:bg-dark-surface dark:text-dark-text dark:hover:bg-dark-bg transition-colors"
          title="Refresh endpoint"
        >
          <Icon type="refresh" size="xs" className={isRotating ? 'animate-spin' : ''} />
        </button>
        <div
          className={`size-2 shrink-0 rounded-full ${getStatusColor(isEndpointActive)}`}
          title={isEndpointActive ? 'Connected' : 'Disconnected'}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col items-start gap-2">
      <div className="text-xs font-normal text-light-text/60 dark:text-dark-text/60">Connection</div>
      {isEditing ? (
        <div className="flex w-full items-center gap-1">
          <input
            type="text"
            value={endpointValue}
            onChange={(e) => setEndpointValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex h-9 w-full items-center text-ellipsis rounded-xl border border-border-primary bg-light-surface p-3 text-xs font-medium text-light-text dark:bg-dark-surface dark:text-dark-text transition-colors"
            autoFocus
          />
          <Button
            variant="ghost"
            size="icon"
            onClick={handleSave}
            className="text-light-text hover:cursor-pointer hover:bg-transparent dark:text-dark-text"
          >
            <Icon type="save" size="xs" />
          </Button>
        </div>
      ) : (
        <div className="flex w-full items-center gap-1">
          <button
            onClick={() => setIsEditing(true)}
            className="relative flex h-9 w-full cursor-pointer items-center justify-between rounded-xl border border-border-primary bg-light-surface p-3 uppercase hover:border-accent dark:bg-dark-surface transition-colors group"
          >
            <p className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary group-hover:text-accent transition-colors">
              {isMounted
                ? truncateText(selectedEndpoint, 21) || ENDPOINT_PLACEHOLDER
                : 'https://api.cirkelline.com'}
            </p>
            <div
              className={`size-2 shrink-0 rounded-full ${getStatusColor(isEndpointActive)}`}
            />
          </button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRefresh}
            className="text-light-text hover:cursor-pointer hover:bg-transparent dark:text-dark-text"
          >
            <Icon type="refresh" size="xs" className={isRotating ? 'animate-spin' : ''} />
          </Button>
        </div>
      )}
    </div>
  )
}

const Sidebar = ({ openPanel, onPanelChange }: SidebarProps) => {
  const pathname = usePathname()
  const router = useRouter()
  const { isCollapsed, isMobileOpen, toggle, setMobileOpen } = useSidebar()
  const { clearChat, focusChatInput, initialize } = useChatActions()
  const {
    messages,
    selectedEndpoint,
    isEndpointActive,
    selectedModel,
    hydrated,
    isEndpointLoading,
    mode
  } = useStore()
  const [isMounted, setIsMounted] = useState(false)
  const [agentId] = useQueryState('agent')
  const [teamId] = useQueryState('team')
  const [isMobile, setIsMobile] = useState(false)
  const [backendVersion, setBackendVersion] = useState<string | null>(null)
  const [googleConnected, setGoogleConnected] = useState(false)
  const [notionConnected, setNotionConnected] = useState(false)

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Fetch backend version from /config
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const apiUrl = selectedEndpoint || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
        const response = await fetch(`${apiUrl}/config`)
        if (response.ok) {
          const data = await response.json()
          if (data.version) {
            setBackendVersion(data.version)
          }
        }
      } catch {
        // Silently fail - will show fallback version
      }
    }
    fetchVersion()
  }, [selectedEndpoint])

  // Check Google and Notion connection status
  useEffect(() => {
    const checkConnections = async () => {
      try {
        const token = localStorage.getItem('token')
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
        // Silently fail
      }
    }

    checkConnections()
  }, [])

  const [sessionsExpanded, setSessionsExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sessions-expanded')
      return saved ? JSON.parse(saved) : true
    }
    return true
  })

  const [adminExpanded, setAdminExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('admin-expanded')
      return saved ? JSON.parse(saved) : true
    }
    return true
  })

  const [projectsExpanded, setProjectsExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('projects-expanded')
      return saved ? JSON.parse(saved) : false
    }
    return false
  })

  const [journalsExpanded, setJournalsExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('journals-expanded')
      return saved ? JSON.parse(saved) : false
    }
    return false
  })

  const [notesExpanded, setNotesExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('notes-expanded')
      return saved ? JSON.parse(saved) : false
    }
    return false
  })

  const [tasksExpanded, setTasksExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('tasks-expanded')
      return saved ? JSON.parse(saved) : false
    }
    return false
  })

  const [documentsExpanded, setDocumentsExpanded] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('documents-expanded')
      return saved ? JSON.parse(saved) : false
    }
    return false
  })


  useEffect(() => {
    setIsMounted(true)
    if (hydrated) initialize()
  }, [selectedEndpoint, initialize, hydrated, mode])

  // Listen for preferences loaded from backend
  useEffect(() => {
    const handlePreferencesLoaded = () => {
      console.log('🔄 Sidebar: Reloading section states from localStorage after backend load')

      if (typeof window !== 'undefined') {
        const sessions = localStorage.getItem('sessions-expanded')
        const admin = localStorage.getItem('admin-expanded')
        const projects = localStorage.getItem('projects-expanded')
        const journals = localStorage.getItem('journals-expanded')

        if (sessions !== null) {
          const value = JSON.parse(sessions)
          console.log('  📂 Setting sessionsExpanded:', value)
          setSessionsExpanded(value)
        }
        if (admin !== null) {
          const value = JSON.parse(admin)
          console.log('  📂 Setting adminExpanded:', value)
          setAdminExpanded(value)
        }
        if (projects !== null) {
          const value = JSON.parse(projects)
          console.log('  📂 Setting projectsExpanded:', value)
          setProjectsExpanded(value)
        }
        if (journals !== null) {
          const value = JSON.parse(journals)
          console.log('  📂 Setting journalsExpanded:', value)
          setJournalsExpanded(value)
        }

        const notes = localStorage.getItem('notes-expanded')
        const tasks = localStorage.getItem('tasks-expanded')
        const documents = localStorage.getItem('documents-expanded')

        if (notes !== null) {
          const value = JSON.parse(notes)
          setNotesExpanded(value)
        }
        if (tasks !== null) {
          const value = JSON.parse(tasks)
          setTasksExpanded(value)
        }
        if (documents !== null) {
          const value = JSON.parse(documents)
          setDocumentsExpanded(value)
        }
      }
    }

    window.addEventListener('sidebarPreferencesLoaded', handlePreferencesLoaded)

    return () => {
      window.removeEventListener('sidebarPreferencesLoaded', handlePreferencesLoaded)
    }
  }, [])

  const handleNewChat = () => {
    clearChat()
    focusChatInput()
  }

  // Helper to save all sidebar states to backend
  const saveSidebarToBackend = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      console.log('⚠️ Sidebar save skipped: No token found')
      return // Not logged in
    }

    // Read from localStorage (not state) because state updates are async
    const sidebarState = {
      'sessions-expanded': JSON.parse(localStorage.getItem('sessions-expanded') || 'true'),
      'admin-expanded': JSON.parse(localStorage.getItem('admin-expanded') || 'true'),
      'projects-expanded': JSON.parse(localStorage.getItem('projects-expanded') || 'false'),
      'journals-expanded': JSON.parse(localStorage.getItem('journals-expanded') || 'false'),
      'notes-expanded': JSON.parse(localStorage.getItem('notes-expanded') || 'false'),
      'tasks-expanded': JSON.parse(localStorage.getItem('tasks-expanded') || 'false'),
      'documents-expanded': JSON.parse(localStorage.getItem('documents-expanded') || 'false')
    }

    console.log('💾 Saving sidebar sections to backend:', sidebarState)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/user/preferences`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ sidebar: sidebarState })
      })

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Sidebar sections saved successfully:', data)
      } else {
        console.error('❌ Failed to save sidebar sections:', response.status, await response.text())
      }
    } catch (error) {
      console.error('Failed to save sidebar state:', error)
    }
  }

  const toggleSessions = () => {
    setSessionsExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('sessions-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  const toggleAdmin = () => {
    setAdminExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('admin-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  const toggleProjects = () => {
    setProjectsExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('projects-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  const toggleJournals = () => {
    setJournalsExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('journals-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  const toggleNotes = () => {
    setNotesExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('notes-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  const toggleTasks = () => {
    setTasksExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('tasks-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  const toggleDocuments = () => {
    setDocumentsExpanded((prev: boolean) => {
      const newValue = !prev
      localStorage.setItem('documents-expanded', JSON.stringify(newValue))
      saveSidebarToBackend()
      return newValue
    })
  }

  // Hide chat sidebar on profile and admin pages
  if (pathname?.startsWith('/profile') || pathname?.startsWith('/admin')) {
    return null
  }

  return (
    <>
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          group
          fixed left-0 top-0 h-screen
          bg-light-surface dark:bg-dark-surface
          transition-[width,transform,border] duration-300 ease-in-out
          z-40
          flex flex-col
          w-64
          ${isCollapsed ? 'md:w-0 md:-translate-x-full md:border-r-0' : 'md:border-r border-border-primary'}
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Header with collapse button */}
        <div className="flex items-center justify-between p-4 h-16 flex-shrink-0">
          {/* Left side: Logo + Version */}
          <div className="flex items-center gap-2">
            {/* Logo - show on mobile when open OR desktop when not collapsed */}
            <div className={`flex flex-col ml-[5px] ${isCollapsed ? 'md:hidden' : ''}`}>
              <span
                className="font-heading text-xl text-light-text dark:text-dark-text p-0 m-0 leading-none font-semibold tracking-normal"
              >
                Cirkelline
              </span>
              <span className="text-[10px] text-light-text dark:text-dark-text opacity-50">
                v{backendVersion || '1.3'} early access
              </span>
            </div>
          </div>

          {/* Right side: Collapse button (desktop) / Close button (mobile) */}
          <div className="flex items-center gap-1">
            {/* Desktop collapse button - only show when sidebar is expanded on desktop */}
            {!isCollapsed && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={toggle}
                      className="hidden md:flex p-2 rounded-lg hover:bg-accent/10 transition-colors"
                      aria-label="Collapse sidebar"
                    >
                      <PanelRightOpen size={18} className="text-light-text-secondary dark:text-dark-text-secondary" style={{ opacity: 0.5 }} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>Collapse sidebar</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}

            {/* Mobile close button */}
            <button
              onClick={() => setMobileOpen(false)}
              className="md:hidden p-2 rounded-lg hover:bg-accent/10 text-light-text-secondary dark:text-dark-text-secondary transition-colors"
              aria-label="Close sidebar"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden app-scroll" suppressHydrationWarning>

        {/* New Session Button - Show on mobile always, on desktop when not collapsed */}
        <div className="p-4">
          <Button
            onClick={handleNewChat}
            disabled={messages.length === 0}
            variant="gradient"
            className="w-full justify-center px-4"
          >
            <span className="font-heading text-sm font-semibold">New chat</span>
          </Button>
        </div>

        {/* Conversations Section - Collapsible */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`group/conversations ${isCollapsed ? 'md:hidden' : ''}`}
        >
            <div className="w-full flex items-center justify-between px-4 py-2.5">
              <button
                onClick={toggleSessions}
                className="flex items-center gap-2 rounded-lg transition-colors"
              >
                <MessageSquare
                  size={14}
                  className="text-light-text dark:text-dark-text"
                />
                <h2 className="font-heading text-sm font-semibold text-light-text dark:text-dark-text">
                  Conversations
                </h2>
                <motion.div
                  animate={{ rotate: sessionsExpanded ? 90 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="opacity-0 group-hover/conversations:opacity-100 transition-opacity duration-200"
                >
                  <ChevronRight
                    size={16}
                    className="text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                  />
                </motion.div>
              </button>
              <button
                onClick={() => router.push('/profile/sessions')}
                className="p-1 rounded hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-all opacity-0 group-hover/conversations:opacity-100"
                title="View all conversations"
              >
                <ExternalLink size={14} className="text-light-text dark:text-dark-text" />
              </button>
            </div>

            <AnimatePresence initial={false}>
              {sessionsExpanded && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: "auto" }}
                  exit={{ height: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-2 py-2">
                    <Sessions />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

        {/* Gap */}
        <div className="h-4" />

        {/* Projects Section - Collapsible */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`group/projects ${isCollapsed ? 'md:hidden' : ''}`}
        >
            <button
              onClick={toggleProjects}
              className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg transition-colors"
            >
              <FolderKanban
                size={14}
                className="text-light-text dark:text-dark-text"
              />
              <h2 className="font-heading text-sm font-semibold text-light-text dark:text-dark-text">
                Projects
              </h2>
              <motion.div
                animate={{ rotate: projectsExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
                className="opacity-0 group-hover/projects:opacity-100 transition-opacity duration-200"
              >
                <ChevronRight
                  size={16}
                  className="text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                />
              </motion.div>
            </button>

            <AnimatePresence initial={false}>
              {projectsExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-4 py-8">
                    <p className="text-sm text-center text-light-text-secondary dark:text-dark-text-secondary font-sans">
                      Coming soon
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
        </motion.div>

        {/* Notes Section - Collapsible */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`group/notes ${isCollapsed ? 'md:hidden' : ''}`}
        >
            <button
              onClick={toggleNotes}
              className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg transition-colors"
            >
              <StickyNote
                size={14}
                className="text-light-text dark:text-dark-text"
              />
              <h2 className="font-heading text-sm font-semibold text-light-text dark:text-dark-text">
                Notes
              </h2>
              <motion.div
                animate={{ rotate: notesExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
                className="opacity-0 group-hover/notes:opacity-100 transition-opacity duration-200"
              >
                <ChevronRight
                  size={16}
                  className="text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                />
              </motion.div>
            </button>

            <AnimatePresence initial={false}>
              {notesExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-4 py-8">
                    <p className="text-sm text-center text-light-text-secondary dark:text-dark-text-secondary font-sans">
                      Coming soon
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
        </motion.div>

        {/* Tasks Section - Collapsible */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`group/tasks ${isCollapsed ? 'md:hidden' : ''}`}
        >
            <button
              onClick={toggleTasks}
              className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg transition-colors"
            >
              <ListTodo
                size={14}
                className="text-light-text dark:text-dark-text"
              />
              <h2 className="font-heading text-sm font-semibold text-light-text dark:text-dark-text">
                Tasks
              </h2>
              <motion.div
                animate={{ rotate: tasksExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
                className="opacity-0 group-hover/tasks:opacity-100 transition-opacity duration-200"
              >
                <ChevronRight
                  size={16}
                  className="text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                />
              </motion.div>
            </button>

            <AnimatePresence initial={false}>
              {tasksExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-4 py-8">
                    <p className="text-sm text-center text-light-text-secondary dark:text-dark-text-secondary font-sans">
                      Coming soon
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
        </motion.div>

        {/* Documents Section - Collapsible */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`group/documents ${isCollapsed ? 'md:hidden' : ''}`}
        >
            <button
              onClick={toggleDocuments}
              className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg transition-colors"
            >
              <Files
                size={14}
                className="text-light-text dark:text-dark-text"
              />
              <h2 className="font-heading text-sm font-semibold text-light-text dark:text-dark-text">
                Documents
              </h2>
              <motion.div
                animate={{ rotate: documentsExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
                className="opacity-0 group-hover/documents:opacity-100 transition-opacity duration-200"
              >
                <ChevronRight
                  size={16}
                  className="text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                />
              </motion.div>
            </button>

            <AnimatePresence initial={false}>
              {documentsExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-4 py-8">
                    <p className="text-sm text-center text-light-text-secondary dark:text-dark-text-secondary font-sans">
                      Coming soon
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
        </motion.div>

        {/* Journals Section - Collapsible */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`group/journals ${isCollapsed ? 'md:hidden' : ''}`}
        >
            <div className="w-full flex items-center justify-between px-4 py-2.5">
              <button
                onClick={toggleJournals}
                className="flex items-center gap-2 rounded-lg transition-colors"
              >
                <BookOpen
                  size={14}
                  className="text-light-text dark:text-dark-text"
                />
                <h2 className="font-heading text-sm font-semibold text-light-text dark:text-dark-text">
                  Journals
                </h2>
                <motion.div
                  animate={{ rotate: journalsExpanded ? 90 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="opacity-0 group-hover/journals:opacity-100 transition-opacity duration-200"
                >
                  <ChevronRight
                    size={16}
                    className="text-light-text-secondary dark:text-dark-text-secondary opacity-50"
                  />
                </motion.div>
              </button>
              <button
                onClick={() => router.push('/profile/journals')}
                className="p-1 rounded hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-all opacity-0 group-hover/journals:opacity-100"
                title="View all journals"
              >
                <ExternalLink size={14} className="text-light-text dark:text-dark-text" />
              </button>
            </div>

            <AnimatePresence initial={false}>
              {journalsExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="overflow-hidden"
                >
                  <div className="px-2 py-2">
                    <Journals />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
        </motion.div>

        {/* Admin Section - Collapsible - HIDDEN FOR NOW */}
        {false && !isCollapsed && isMounted && (
          <div>
            <button
              onClick={toggleAdmin}
              className="w-full flex items-center justify-between px-4 py-2.5 transition-colors"
            >
              <h2 className="font-heading text-sm font-bold text-light-text dark:text-dark-text">
                Admin
              </h2>
              <ChevronRight
                size={16}
                className={`text-light-text/50 dark:text-dark-text/50 transition-transform duration-300 ${
                  adminExpanded ? 'rotate-90' : ''
                }`}
                style={{ opacity: 0.5 }}
              />
            </button>

            {adminExpanded && (
              <div className="px-4 py-3 space-y-4 animate-slide-down">
                {/* Endpoint Connection */}
                <Endpoint isCollapsed={isCollapsed} />

                {/* Mode & Entity Selection */}
                {isEndpointActive && (
                  <div className="flex w-full flex-col items-start gap-2">
                    <div className="text-xs font-normal text-light-text/60 dark:text-dark-text/60">
                      Mode
                    </div>
                    {isEndpointLoading ? (
                      <div className="flex w-full flex-col gap-2">
                        {Array.from({ length: 3 }).map((_, index) => (
                          <Skeleton
                            key={index}
                            className="h-9 w-full rounded-xl bg-light-surface dark:bg-dark-surface"
                          />
                        ))}
                      </div>
                    ) : (
                      <>
                        <ModeSelector />
                        <EntitySelector />
                        {selectedModel && (agentId || teamId) && (
                          <ModelDisplay model={selectedModel} isCollapsed={isCollapsed} />
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        </div>
        {/* End Scrollable Content Area */}

        {/* Service Icons - Fixed at Bottom */}
        <div className={`flex-shrink-0 border-t border-border-primary px-4 py-3 ${isCollapsed ? 'md:hidden' : ''}`}>
          <TooltipProvider>
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <Tooltip>
              <TooltipTrigger asChild>
                <motion.button
                  onClick={() => onPanelChange?.(openPanel === 'calendar' ? null : 'calendar')}
                  className={`flex-shrink-0 rounded-full p-2 transition-all duration-200 ${openPanel === 'calendar' ? 'text-white' : 'bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text'}`}
                  style={{ backgroundColor: openPanel === 'calendar' ? 'rgb(var(--accent-rgb))' : undefined }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Calendar className="w-4 h-4" strokeWidth={2} />
                </motion.button>
              </TooltipTrigger>
              <TooltipContent side="top"><p>Calendar</p></TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <motion.button
                  onClick={() => onPanelChange?.(openPanel === 'email' ? null : 'email')}
                  className={`flex-shrink-0 rounded-full p-2 transition-all duration-200 ${openPanel === 'email' ? 'text-white' : !googleConnected ? 'bg-light-bg dark:bg-dark-bg text-light-text/25 dark:text-dark-text/25 cursor-not-allowed' : 'bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text'}`}
                  style={{ backgroundColor: openPanel === 'email' ? 'rgb(var(--accent-rgb))' : undefined }}
                  disabled={!googleConnected}
                  whileHover={googleConnected ? { scale: 1.1 } : {}}
                  whileTap={googleConnected ? { scale: 0.95 } : {}}
                >
                  <Mail className="w-4 h-4" strokeWidth={2} />
                </motion.button>
              </TooltipTrigger>
              <TooltipContent side="top"><p>{googleConnected ? 'Email' : 'Connect Google'}</p></TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <motion.button
                  onClick={() => onPanelChange?.(openPanel === 'tasks' ? null : 'tasks')}
                  className={`flex-shrink-0 rounded-full p-2 transition-all duration-200 ${openPanel === 'tasks' ? 'text-white' : 'bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text'}`}
                  style={{ backgroundColor: openPanel === 'tasks' ? 'rgb(var(--accent-rgb))' : undefined }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <CheckSquare className="w-4 h-4" strokeWidth={2} />
                </motion.button>
              </TooltipTrigger>
              <TooltipContent side="top"><p>Tasks</p></TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <motion.button
                  onClick={() => onPanelChange?.(openPanel === 'notion' ? null : 'notion')}
                  className={`flex-shrink-0 rounded-full p-2 transition-all duration-200 ${openPanel === 'notion' ? 'text-white' : !notionConnected ? 'bg-light-bg dark:bg-dark-bg text-light-text/25 dark:text-dark-text/25 cursor-not-allowed' : 'bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text'}`}
                  style={{ backgroundColor: openPanel === 'notion' ? 'rgb(var(--accent-rgb))' : undefined }}
                  disabled={!notionConnected}
                  whileHover={notionConnected ? { scale: 1.1 } : {}}
                  whileTap={notionConnected ? { scale: 0.95 } : {}}
                >
                  <Layers2 className="w-4 h-4" strokeWidth={2} />
                </motion.button>
              </TooltipTrigger>
              <TooltipContent side="top"><p>{notionConnected ? 'Notion' : 'Connect Notion'}</p></TooltipContent>
            </Tooltip>
          </div>
          </TooltipProvider>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
