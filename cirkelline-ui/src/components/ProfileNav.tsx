'use client'

import { usePathname, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { User, Link, Settings, Shield, X, Activity, MessageSquare, Brain } from 'lucide-react'

export default function ProfileNav() {
  const pathname = usePathname()
  const router = useRouter()

  const tabs = [
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

  return (
    <div className="bg-light-surface/80 dark:bg-dark-surface/80 backdrop-blur-md border-b border-border-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex gap-1 justify-between items-center">
          <div className="flex gap-1 overflow-x-auto flex-nowrap scrollbar-none" style={{ WebkitOverflowScrolling: 'touch' }}>
          {tabs.map((tab) => {
            const Icon = tab.icon
            const active = isActive(tab.path)

            return (
              <button
                key={tab.path}
                onClick={() => router.push(tab.path)}
                className="relative px-4 py-3 flex items-center gap-2 text-sm font-medium transition-colors flex-shrink-0"
              >
                <Icon
                  size={18}
                  className={active
                    ? 'text-accent'
                    : 'text-light-text-secondary dark:text-dark-text-secondary'
                  }
                />
                <span
                  className={active
                    ? 'text-accent font-semibold'
                    : 'text-light-text dark:text-dark-text'
                  }
                >
                  {tab.name}
                </span>

                {/* Active indicator */}
                {active && (
                  <motion.div
                    layoutId="profile-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </button>
            )
          })}
          </div>

          {/* Close button to exit profile */}
          <button
            onClick={() => router.push('/')}
            className="p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
            title="Close Profile"
          >
            <X size={18} />
          </button>
        </nav>
      </div>
    </div>
  )
}
