'use client'

import { useSidebar } from '@/hooks/useSidebar'
import UserDropdown from './UserDropdown'
import { Menu, ChevronRight, ChevronLeft, ArrowLeft, Calendar, X, RefreshCw, Grid3X3, List, Settings, Maximize2, PanelRightClose } from 'lucide-react'
import { motion } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useRouter, usePathname } from 'next/navigation'
import { useState, useEffect, useRef } from 'react'

type CalendarViewType = 'month' | 'week' | 'day' | 'agenda';
type MobilePanel = 'calendar' | 'events';

interface CalendarControls {
  activeView: CalendarViewType;
  setActiveView: (view: CalendarViewType) => void;
  selectedDate: Date;
  setSelectedDate: (date: Date) => void;
  onClose: () => void;
  onRefresh: () => void;
  onFullscreen?: () => void;
  isFullscreen?: boolean;
  loading: boolean;
  mobilePanel: MobilePanel;
  setMobilePanel: (panel: MobilePanel) => void;
  googleConnected?: boolean;
  googleSyncEnabled?: boolean;
  onGoogleSyncToggle?: (enabled: boolean) => void;
}

interface TopBarProps {
  calendarControls?: CalendarControls;
  showCalendarControls?: boolean;
}

export default function TopBar({ calendarControls, showCalendarControls }: TopBarProps) {
  const { isCollapsed, setMobileOpen, toggle } = useSidebar()
  const router = useRouter()
  const pathname = usePathname()
  const [showViewDropdown, setShowViewDropdown] = useState(false)
  const [showSettingsDropdown, setShowSettingsDropdown] = useState(false)
  const settingsDropdownRef = useRef<HTMLDivElement>(null)

  const isProfileOrAdmin = pathname?.startsWith('/profile') || pathname?.startsWith('/admin')

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (settingsDropdownRef.current && !settingsDropdownRef.current.contains(event.target as Node)) {
        setShowSettingsDropdown(false)
      }
    }

    if (showSettingsDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      document.addEventListener('touchstart', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchstart', handleClickOutside)
    }
  }, [showSettingsDropdown])

  return (
    <>
      <motion.header
        className={`
          fixed top-0 right-0 h-16
          bg-light-surface/80 dark:bg-dark-surface/80
          backdrop-blur-md
          border-b border-border-primary
          transition-all duration-300 ease-in-out
          left-0
          ${isCollapsed ? 'md:left-0' : 'md:left-64'}
          z-30
          shadow-sm
        `}
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <div className="h-full px-4 md:px-6 flex items-center justify-between">
          {/* Left: Mobile hamburger + Logo (only when sidebar collapsed on desktop) */}
          <div className="flex items-center gap-1 md:gap-8">
            {/* Mobile hamburger menu */}
            <motion.button
              className="md:hidden p-1.5 mr-1.5 rounded-xl hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors"
              onClick={() => setMobileOpen(true)}
              aria-label="Open sidebar"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Menu size={18} />
            </motion.button>

            {/* Sidebar toggle button when collapsed - combined with logo */}
            {isCollapsed && (
              <div className="hidden md:flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <motion.button
                        onClick={toggle}
                        className="pl-0 pr-2 py-2 rounded-xl hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text-secondary dark:text-dark-text-secondary transition-colors"
                        aria-label="Expand sidebar"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <PanelRightClose size={18} className="text-light-text-secondary dark:text-dark-text-secondary" style={{ opacity: 0.5 }} />
                      </motion.button>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <p>Expand sidebar</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <motion.button
                  onClick={() => router.push('/')}
                  className="font-heading text-xl cursor-pointer bg-transparent border-none p-0 m-0 ml-[5px] leading-none flex items-center font-semibold tracking-normal text-light-text dark:text-dark-text"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, delay: 0.1 }}
                >
                  Cirkelline
                </motion.button>
              </div>
            )}

            {/* Back to Chat button for profile/admin pages */}
            {isProfileOrAdmin && (
              <motion.button
                onClick={() => router.push('/')}
                className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <ArrowLeft size={18} />
                <span className="font-heading text-sm font-semibold">Back to chat</span>
              </motion.button>
            )}
          </div>

          {/* Center: Calendar Controls (mobile only, when calendar is open) */}
          {showCalendarControls && calendarControls && (
            <div className="md:hidden flex items-center gap-1.5 flex-1 justify-center">
              {/* Panel Switcher - Simple segmented control */}
              <div className="flex items-center border border-border-primary rounded-lg overflow-hidden">
                <button
                  onClick={() => calendarControls.setMobilePanel('calendar')}
                  className={`px-2.5 py-1 text-xs font-medium transition-colors ${
                    calendarControls.mobilePanel === 'calendar'
                      ? 'bg-accent text-white'
                      : 'bg-light-surface dark:bg-dark-surface text-light-text-secondary dark:text-dark-text-secondary'
                  }`}
                >
                  <Grid3X3 size={14} />
                </button>
                <button
                  onClick={() => calendarControls.setMobilePanel('events')}
                  className={`px-2.5 py-1 text-xs font-medium transition-colors ${
                    calendarControls.mobilePanel === 'events'
                      ? 'bg-accent text-white'
                      : 'bg-light-surface dark:bg-dark-surface text-light-text-secondary dark:text-dark-text-secondary'
                  }`}
                >
                  <List size={14} />
                </button>
              </div>

              {/* View Dropdown - always rendered, disabled when on events panel */}
              <div className={`relative ${calendarControls.mobilePanel === 'events' ? 'opacity-40 pointer-events-none' : ''}`}>
                <button
                  onClick={() => setShowViewDropdown(!showViewDropdown)}
                  className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-light-text dark:text-dark-text border border-border-primary rounded-lg bg-light-surface dark:bg-dark-surface"
                >
                  <Calendar size={12} className="text-accent" />
                  <span>{calendarControls.activeView.charAt(0).toUpperCase() + calendarControls.activeView.slice(1)}</span>
                </button>
                {showViewDropdown && calendarControls.mobilePanel === 'calendar' && (
                  <div className="absolute top-full left-0 mt-1 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg shadow-lg z-50 min-w-[80px] overflow-hidden">
                    {(['month', 'week', 'day'] as const).map((view) => (
                      <button
                        key={view}
                        onClick={() => {
                          calendarControls.setActiveView(view);
                          setShowViewDropdown(false);
                        }}
                        className={`w-full px-3 py-1.5 text-xs text-left transition-colors ${calendarControls.activeView === view ? 'bg-accent text-white' : 'text-light-text dark:text-dark-text hover:bg-accent/10'}`}
                      >
                        {view.charAt(0).toUpperCase() + view.slice(1)}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Date Navigation - always rendered, disabled when on events panel */}
              <div className={`flex items-center border border-border-primary rounded-lg overflow-hidden bg-light-surface dark:bg-dark-surface ${calendarControls.mobilePanel === 'events' ? 'opacity-40 pointer-events-none' : ''}`}>
                <button
                  onClick={() => {
                    const newDate = new Date(calendarControls.selectedDate);
                    newDate.setMonth(newDate.getMonth() - 1);
                    calendarControls.setSelectedDate(newDate);
                  }}
                  className="p-1 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                >
                  <ChevronLeft size={14} className="text-light-text dark:text-dark-text" />
                </button>
                <span className="text-xs font-medium text-light-text dark:text-dark-text px-1.5 min-w-[50px] text-center border-x border-border-primary">
                  {calendarControls.selectedDate.toLocaleDateString('en-US', { month: 'short' })}
                </span>
                <button
                  onClick={() => {
                    const newDate = new Date(calendarControls.selectedDate);
                    newDate.setMonth(newDate.getMonth() + 1);
                    calendarControls.setSelectedDate(newDate);
                  }}
                  className="p-1 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                >
                  <ChevronRight size={14} className="text-light-text dark:text-dark-text" />
                </button>
              </div>
            </div>
          )}

          {/* Right: Calendar actions (mobile) or User Dropdown */}
          <div className="flex items-center gap-1 md:gap-2">
            {/* Calendar mobile actions - replaces UserDropdown on mobile */}
            {showCalendarControls && calendarControls && (
              <div className="md:hidden flex items-center gap-1">
                {/* Settings dropdown */}
                <div ref={settingsDropdownRef} className="relative">
                  <button
                    type="button"
                    onClick={() => setShowSettingsDropdown(prev => !prev)}
                    className="p-1.5 rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-light-text dark:hover:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                  >
                    <Settings size={16} />
                  </button>
                  {showSettingsDropdown && (
                    <div className="absolute top-full right-0 mt-1 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg shadow-xl min-w-[160px] overflow-hidden z-[9999]">
                      <div className="py-1">
                        {/* Google Sync Toggle */}
                        <button
                          type="button"
                          onClick={() => {
                            if (calendarControls.googleConnected && calendarControls.onGoogleSyncToggle) {
                              calendarControls.onGoogleSyncToggle(!calendarControls.googleSyncEnabled);
                            }
                          }}
                          disabled={!calendarControls.googleConnected}
                          className={`w-full flex items-center justify-between gap-2 px-3 py-2 text-xs text-left transition-colors ${
                            calendarControls.googleSyncEnabled && calendarControls.googleConnected
                              ? 'bg-green-50 dark:bg-green-900/20'
                              : ''
                          } ${!calendarControls.googleConnected ? 'opacity-50' : 'active:bg-accent/20'}`}
                        >
                          <div className="flex items-center gap-2">
                            {calendarControls.googleSyncEnabled && calendarControls.googleConnected && (
                              <div className="w-2 h-2 rounded-full bg-green-500" />
                            )}
                            <span className={calendarControls.googleSyncEnabled && calendarControls.googleConnected ? 'text-green-700 dark:text-green-400' : 'text-light-text dark:text-dark-text'}>Google Sync</span>
                          </div>
                          <div className={`relative w-7 h-3.5 rounded-full transition-colors ${
                            calendarControls.googleSyncEnabled && calendarControls.googleConnected ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                          }`}>
                            <span className={`absolute top-0.5 left-0.5 w-2.5 h-2.5 bg-white rounded-full transition-transform ${
                              calendarControls.googleSyncEnabled && calendarControls.googleConnected ? 'translate-x-3.5' : 'translate-x-0'
                            }`} />
                          </div>
                        </button>
                        {/* Refresh */}
                        <button
                          type="button"
                          onClick={() => {
                            calendarControls.onRefresh();
                            setShowSettingsDropdown(false);
                          }}
                          disabled={calendarControls.loading}
                          className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left text-light-text dark:text-dark-text active:bg-accent/20 disabled:opacity-50"
                        >
                          <RefreshCw size={14} className={calendarControls.loading ? 'animate-spin' : ''} />
                          <span>Refresh</span>
                        </button>
                        {/* Fullscreen */}
                        <button
                          type="button"
                          onClick={() => {
                            calendarControls.onFullscreen?.();
                            setShowSettingsDropdown(false);
                          }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left text-light-text dark:text-dark-text active:bg-accent/20"
                        >
                          <Maximize2 size={14} />
                          <span>Fullscreen</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                {/* Close button - separate */}
                <button
                  type="button"
                  onClick={calendarControls.onClose}
                  className="p-1.5 rounded-lg text-light-text/60 dark:text-dark-text/60 hover:text-red-500 hover:bg-red-500/10 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>
            )}
            {/* UserDropdown - hidden on mobile when calendar is open */}
            <div className={showCalendarControls ? 'hidden md:block' : ''}>
              <UserDropdown />
            </div>
          </div>
        </div>
      </motion.header>
    </>
  )
}
