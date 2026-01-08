'use client'

import { usePathname, useRouter } from 'next/navigation'
import { LayoutDashboard, Users, MessageSquare, Activity, CreditCard, BarChart3, X, ChevronLeft, Workflow, FolderOpen } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { useSidebar } from '@/hooks/useSidebar'
import { sidebarContent } from '@/lib/animations'
import { FolderSwitcher } from '@/components/ckc'

const AdminSidebar = () => {
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
      name: 'Overview',
      path: '/admin',
      icon: LayoutDashboard
    },
    {
      name: 'Metrics',
      path: '/admin/metrics',
      icon: BarChart3
    },
    {
      name: 'CKC Folders',
      path: '/admin/ckc',
      icon: FolderOpen
    },
    {
      name: 'Users',
      path: '/admin/users',
      icon: Users
    },
    {
      name: 'Subscriptions',
      path: '/admin/subscriptions',
      icon: CreditCard
    },
    {
      name: 'Feedback',
      path: '/admin/feedback',
      icon: MessageSquare
    },
    {
      name: 'Activity',
      path: '/admin/activity',
      icon: Activity
    },
    {
      name: 'Workflows',
      path: '/admin/workflows',
      icon: Workflow
    }
  ]

  const isActive = (path: string) => {
    if (path === '/admin') {
      return pathname === '/admin'
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
          <div className="flex items-center gap-2">
            {/* Desktop collapse button */}
            {!isCollapsed && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={toggle}
                      className="hidden md:flex p-2 rounded-lg hover:bg-accent/10 transition-colors"
                      aria-label="Collapse sidebar"
                    >
                      <ChevronLeft size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
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
              className="font-heading text-xl text-light-text dark:text-dark-text cursor-pointer bg-transparent border-none p-0 m-0 -ml-1"
              style={{ fontWeight: 600, letterSpacing: '0' }}
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

        {/* CKC Folder Switcher */}
        <motion.div
          initial={false}
          animate={(isCollapsed && !isMobile) ? "collapsed" : "expanded"}
          variants={sidebarContent}
          className={`p-4 border-b border-border-primary ${isCollapsed ? 'md:hidden' : ''}`}
        >
          <div className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary mb-2 px-1">
            CKC Context
          </div>
          <FolderSwitcher variant="dropdown" showFavorites={true} />
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

export default AdminSidebar
