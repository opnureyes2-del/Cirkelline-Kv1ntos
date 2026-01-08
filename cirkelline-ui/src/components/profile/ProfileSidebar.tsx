'use client'

import { usePathname, useRouter } from 'next/navigation'
import { User, Link, Settings, Shield, Activity, MessageSquare, Brain, X, FileText, BookOpen, PanelRightOpen } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useSidebar } from '@/hooks/useSidebar'
import { sidebarContent } from '@/lib/animations'

const ProfileSidebar = () => {
  const pathname = usePathname()
  const router = useRouter()
  const { isCollapsed, isMobileOpen, toggle, setMobileOpen } = useSidebar()
  const [isMobile, setIsMobile] = useState(false)

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const navigationItems = [
    {
      name: 'Account',
      path: '/profile',
      icon: User
    },
    {
      name: 'Activity',
      path: '/profile/activity',
      icon: Activity
    },
    {
      name: 'Sessions',
      path: '/profile/sessions',
      icon: MessageSquare
    },
    {
      name: 'Memories',
      path: '/profile/memories',
      icon: Brain
    },
    {
      name: 'Journals',
      path: '/profile/journals',
      icon: BookOpen
    },
    {
      name: 'Documents',
      path: '/profile/documents',
      icon: FileText
    },
    {
      name: 'Integrations',
      path: '/profile/integrations',
      icon: Link
    },
    {
      name: 'Preferences',
      path: '/profile/preferences',
      icon: Settings
    },
    {
      name: 'Security',
      path: '/profile/security',
      icon: Shield
    }
  ]

  const isActive = (path: string) => {
    if (path === '/profile') {
      return pathname === '/profile'
    }
    return pathname.startsWith(path)
  }

  const handleNavClick = (path: string) => {
    router.push(path)
    if (isMobile) {
      setMobileOpen(false)
    }
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
          fixed left-0 top-0 h-screen
          bg-light-surface dark:bg-dark-surface
          transition-all duration-300 ease-in-out
          z-40
          flex flex-col
          w-64
          ${isCollapsed ? 'md:w-0 md:-translate-x-full md:border-r-0' : 'md:border-r border-border-primary'}
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Header */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`flex items-center justify-between p-4 h-16 flex-shrink-0 border-b border-border-primary ${isCollapsed ? 'md:hidden' : ''}`}
        >
          <div className="flex items-center">
            {/* Desktop collapse button - aligned with nav icons */}
            {!isCollapsed && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={toggle}
                      className="hidden md:flex py-2 pl-4 pr-2 mr-2 rounded-lg hover:bg-accent/10 transition-colors"
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

            <button
              onClick={() => router.push('/')}
              className="font-heading text-xl text-light-text dark:text-dark-text cursor-pointer bg-transparent border-none p-0 m-0 font-semibold tracking-normal"
            >
              Cirkelline
            </button>
          </div>

          {/* Mobile close button */}
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden p-2 rounded-lg hover:bg-accent/10 text-light-text-secondary dark:text-dark-text-secondary transition-colors"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </motion.div>

        {/* Navigation Items */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`flex-1 overflow-y-auto overflow-x-hidden p-4 ${isCollapsed ? 'md:hidden' : ''}`}
        >
          <nav className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.path)

              return (
                <button
                  key={item.path}
                  onClick={() => handleNavClick(item.path)}
                  className={`
                    w-full px-4 py-3 rounded-lg transition-colors flex items-center gap-3
                    ${active
                      ? 'bg-accent/10 text-accent font-medium'
                      : 'text-light-text dark:text-dark-text hover:bg-light-bg dark:hover:bg-dark-bg'
                    }
                  `}
                >
                  <Icon size={20} className={active ? 'text-accent' : 'text-light-text-secondary dark:text-dark-text-secondary'} />
                  <span className="text-sm">{item.name}</span>
                </button>
              )
            })}
          </nav>
        </motion.div>

      </aside>
    </>
  )
}

export default ProfileSidebar
