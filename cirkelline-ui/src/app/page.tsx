'use client'
import dynamic from 'next/dynamic'
import TopBar from '@/components/TopBar'
import { ChatArea } from '@/components/chat/ChatArea'
import PageLoader from '@/components/PageLoader'
import ServicePanelContainer from '@/components/ServicePanelContainer'
import { useSidebar } from '@/hooks/useSidebar'
import { useStandaloneCalendar } from '@/hooks/useStandaloneCalendar'
import { Suspense, useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import LoginForm from '@/components/LoginForm'
import RegisterForm from '@/components/RegisterForm'

const Sidebar = dynamic(() => import('@/components/chat/Sidebar/Sidebar'), {
  ssr: false
})

type PanelType = 'email' | 'calendar' | 'tasks' | 'docs' | 'drive' | 'notion' | 'slack' | 'git' | null
type LayoutMode = 'stacked' | 'side-by-side'

export default function Home() {
  const [openPanel, setOpenPanel] = useState<PanelType>(null)
  const [panelHeight, setPanelHeight] = useState(0.5) // 50% by default
  const [panelWidth, setPanelWidth] = useState(0.4) // 40% for side-by-side (chat gets 60%)
  const [isResizing, setIsResizing] = useState(false)
  const [isPanelFullscreen, setIsPanelFullscreen] = useState(false)
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('stacked')
  const [mobilePanel, setMobilePanel] = useState<'calendar' | 'events'>('calendar')
  const [googleSyncEnabled, setGoogleSyncEnabled] = useState(false)
  const { isCollapsed } = useSidebar()

  // Calendar state for TopBar controls on mobile
  const standaloneCalendar = useStandaloneCalendar()

  // Load Google sync preference from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('cirkelline-google-calendar-sync')
    if (saved === 'true') {
      setGoogleSyncEnabled(true)
    }
  }, [])

  // Handle Google sync toggle
  const handleGoogleSyncToggle = (enabled: boolean) => {
    setGoogleSyncEnabled(enabled)
    localStorage.setItem('cirkelline-google-calendar-sync', enabled ? 'true' : 'false')
    if (enabled && standaloneCalendar.googleConnected) {
      standaloneCalendar.syncFromGoogle()
    }
  }

  // Load layout preference from localStorage
  useEffect(() => {
    const savedLayout = localStorage.getItem('cirkelline-layout-mode') as LayoutMode | null
    if (savedLayout && (savedLayout === 'stacked' || savedLayout === 'side-by-side')) {
      setLayoutMode(savedLayout)
    }
  }, [])

  // Save layout preference
  const handleLayoutChange = (mode: LayoutMode) => {
    setLayoutMode(mode)
    localStorage.setItem('cirkelline-layout-mode', mode)
  }

  // v1.3.4: Authentication check - require login for all users
  const { user } = useAuth()
  const isAnonymous = !user || user.isAnonymous
  const [, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)

  // Show login modal for anonymous users (non-dismissable)
  useEffect(() => {
    if (isAnonymous) {
      setShowLoginModal(true)
    } else {
      setShowLoginModal(false)
      setShowRegisterModal(false)
    }
  }, [isAnonymous])

  // Ensure fullscreen is always reset when panel is closed
  useEffect(() => {
    if (openPanel === null) {
      setIsPanelFullscreen(false)
    }
  }, [openPanel])

  // v1.3.4: If anonymous, render ONLY the auth screen - nothing else exists
  if (isAnonymous) {
    return (
      <div className="min-h-screen bg-light-bg dark:bg-dark-bg flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Logo/Branding */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-heading font-bold text-light-text dark:text-dark-text mb-2">
              Cirkelline
            </h1>
            <p className="text-light-text/60 dark:text-dark-text/60">
              Your personal AI assistant
            </p>
          </div>

          {/* Auth Forms - Inline, not modal */}
          {showRegisterModal ? (
            <div className="bg-light-surface dark:bg-dark-surface rounded-2xl shadow-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-heading font-semibold text-light-text dark:text-dark-text">
                  Create an account
                </h2>
              </div>
              <RegisterForm
                onSuccess={() => {}}
                onSwitchToLogin={() => {
                  setShowRegisterModal(false)
                  setShowLoginModal(true)
                }}
              />
            </div>
          ) : (
            <div className="bg-light-surface dark:bg-dark-surface rounded-2xl shadow-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-heading font-semibold text-light-text dark:text-dark-text">
                  Log in to Cirkelline
                </h2>
              </div>
              <LoginForm
                onSuccess={() => {}}
                onSwitchToRegister={() => {
                  setShowLoginModal(false)
                  setShowRegisterModal(true)
                }}
              />
            </div>
          )}
        </div>
      </div>
    )
  }

  // Authenticated users get the full app
  return (
    <>
      <PageLoader />
      <Suspense fallback={<div className="flex h-screen items-center justify-center bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text">Loading...</div>}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="relative"
        >
          {/* Sidebar */}
          <Sidebar openPanel={openPanel} onPanelChange={setOpenPanel} />

          {/* Top Bar - with calendar controls on mobile */}
          <TopBar
            showCalendarControls={openPanel === 'calendar'}
            calendarControls={openPanel === 'calendar' ? {
              activeView: standaloneCalendar.activeView,
              setActiveView: standaloneCalendar.setActiveView,
              selectedDate: standaloneCalendar.selectedDate,
              setSelectedDate: standaloneCalendar.setSelectedDate,
              onClose: () => {
                setOpenPanel(null)
                setIsPanelFullscreen(false)
              },
              onRefresh: () => {
                if (googleSyncEnabled && standaloneCalendar.googleConnected) {
                  standaloneCalendar.syncFromGoogle()
                } else {
                  standaloneCalendar.fetchCalendars()
                  standaloneCalendar.fetchEvents()
                }
              },
              onFullscreen: () => setIsPanelFullscreen(!isPanelFullscreen),
              isFullscreen: isPanelFullscreen,
              loading: standaloneCalendar.loading,
              mobilePanel: mobilePanel,
              setMobilePanel: setMobilePanel,
              googleConnected: standaloneCalendar.googleConnected,
              googleSyncEnabled: googleSyncEnabled,
              onGoogleSyncToggle: handleGoogleSyncToggle
            } : undefined}
          />

          {/* Content Area - Wraps panels and main content to handle TopBar offset */}
          <div
            className={`
              fixed top-16 bottom-0
              left-0 right-0
              ${isCollapsed ? 'md:left-0' : 'md:left-64'}
              transition-all duration-300 ease-in-out
              ${openPanel && layoutMode === 'side-by-side' ? 'flex flex-col md:flex-row side-by-side-container' : 'flex flex-col'}
            `}
          >
            {/* Stacked Layout (Mobile always, Desktop when selected) */}
            {(layoutMode === 'stacked' || !openPanel) && (
              <>
                {/* Service Panel - Top */}
                <ServicePanelContainer
                  openPanel={openPanel}
                  onClose={() => {
                    setOpenPanel(null)
                    setIsPanelFullscreen(false)
                  }}
                  panelHeight={panelHeight}
                  onPanelHeightChange={setPanelHeight}
                  onResizingChange={setIsResizing}
                  isFullscreen={isPanelFullscreen}
                  onFullscreenToggle={() => setIsPanelFullscreen(!isPanelFullscreen)}
                  layoutMode={layoutMode}
                  onLayoutChange={handleLayoutChange}
                  externalCalendarState={standaloneCalendar}
                  mobilePanel={mobilePanel}
                  googleSyncEnabled={googleSyncEnabled}
                  onGoogleSyncToggle={handleGoogleSyncToggle}
                />

                {/* Chat Area - Bottom */}
                <motion.div
                  initial={{ opacity: 1 }}
                  animate={{
                    opacity: isPanelFullscreen ? 0 : 1,
                  }}
                  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                  className="w-full bg-light-bg dark:bg-dark-bg flex-1 flex flex-col overflow-hidden"
                  style={{
                    height: openPanel ? `calc((100vh - 64px) * ${1 - panelHeight})` : 'calc(100vh - 64px)',
                    transition: isResizing ? 'none' : 'height 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    display: isPanelFullscreen ? 'none' : 'flex'
                  }}
                >
                  <ChatArea />
                </motion.div>
              </>
            )}

            {/* Side-by-Side Layout (Desktop only when panel is open) */}
            {layoutMode === 'side-by-side' && openPanel && (
              <>
                {/* Chat Area - Left */}
                <motion.div
                  initial={{ opacity: 1 }}
                  animate={{
                    opacity: isPanelFullscreen ? 0 : 1,
                  }}
                  transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                  className="hidden md:flex flex-col bg-light-bg dark:bg-dark-bg h-full overflow-hidden"
                  style={{
                    width: isPanelFullscreen ? '0%' : `${(1 - panelWidth) * 100}%`,
                    display: isPanelFullscreen ? 'none' : 'flex',
                    transition: isResizing ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  <ChatArea />
                </motion.div>

                {/* Resize Handle - Vertical divider */}
                {!isPanelFullscreen && (
                  <div
                    className="hidden md:block w-1 hover:w-1.5 bg-border-primary hover:bg-accent cursor-col-resize transition-all flex-shrink-0"
                    onMouseDown={(e) => {
                      e.preventDefault()
                      setIsResizing(true)
                      const handleMouseMove = (e: MouseEvent) => {
                        const container = document.querySelector('.side-by-side-container')
                        if (!container) return
                        const rect = container.getBoundingClientRect()
                        // Calculate width from right side (panel is on right)
                        const newPanelWidth = 1 - ((e.clientX - rect.left) / rect.width)
                        setPanelWidth(Math.max(0.25, Math.min(0.75, newPanelWidth)))
                      }
                      const handleMouseUp = () => {
                        setIsResizing(false)
                        document.removeEventListener('mousemove', handleMouseMove)
                        document.removeEventListener('mouseup', handleMouseUp)
                        document.body.style.cursor = ''
                        document.body.style.userSelect = ''
                      }
                      document.addEventListener('mousemove', handleMouseMove)
                      document.addEventListener('mouseup', handleMouseUp)
                      document.body.style.cursor = 'col-resize'
                      document.body.style.userSelect = 'none'
                    }}
                  />
                )}

                {/* Side-by-Side Container - Right (Apps, Admin, Workflows) */}
                <div
                  className="hidden md:block h-full"
                  style={{
                    width: isPanelFullscreen ? '100%' : `${panelWidth * 100}%`,
                    transition: isResizing ? 'none' : 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  <ServicePanelContainer
                    openPanel={openPanel}
                    onClose={() => {
                      setOpenPanel(null)
                      setIsPanelFullscreen(false)
                    }}
                    panelHeight={1} // Full height in side-by-side
                    onPanelHeightChange={setPanelHeight}
                    onResizingChange={setIsResizing}
                    isFullscreen={isPanelFullscreen}
                    onFullscreenToggle={() => setIsPanelFullscreen(!isPanelFullscreen)}
                    layoutMode={layoutMode}
                    onLayoutChange={handleLayoutChange}
                    panelWidth={panelWidth}
                    onPanelWidthChange={setPanelWidth}
                    externalCalendarState={standaloneCalendar}
                    mobilePanel={mobilePanel}
                    googleSyncEnabled={googleSyncEnabled}
                    onGoogleSyncToggle={handleGoogleSyncToggle}
                  />
                </div>

                {/* Mobile: Fall back to stacked layout */}
                <div className="md:hidden flex flex-col h-full">
                  <ServicePanelContainer
                    openPanel={openPanel}
                    onClose={() => {
                      setOpenPanel(null)
                      setIsPanelFullscreen(false)
                    }}
                    panelHeight={panelHeight}
                    onPanelHeightChange={setPanelHeight}
                    onResizingChange={setIsResizing}
                    isFullscreen={isPanelFullscreen}
                    onFullscreenToggle={() => setIsPanelFullscreen(!isPanelFullscreen)}
                    layoutMode="stacked"
                    onLayoutChange={handleLayoutChange}
                    externalCalendarState={standaloneCalendar}
                    mobilePanel={mobilePanel}
                    googleSyncEnabled={googleSyncEnabled}
                    onGoogleSyncToggle={handleGoogleSyncToggle}
                  />
                  <div
                    className="flex-1 flex flex-col bg-light-bg dark:bg-dark-bg overflow-hidden"
                    style={{
                      height: `calc((100vh - 64px) * ${1 - panelHeight})`,
                      display: isPanelFullscreen ? 'none' : 'flex'
                    }}
                  >
                    <ChatArea />
                  </div>
                </div>
              </>
            )}
          </div>
        </motion.div>
      </Suspense>
    </>
  )
}
