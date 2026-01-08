'use client'

import { usePathname, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { LayoutDashboard, Users, MessageSquare, Activity, CreditCard, X } from 'lucide-react'

export default function AdminNav() {
  const pathname = usePathname()
  const router = useRouter()

  const tabs = [
    {
      name: 'Overview',
      path: '/admin',
      icon: LayoutDashboard
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
    }
  ]

  const isActive = (path: string) => {
    if (path === '/admin') {
      return pathname === '/admin'
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
                    layoutId="admin-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </button>
            )
          })}
          </div>

          {/* Close button to exit admin */}
          <button
            onClick={() => router.push('/')}
            className="p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
            title="Close Admin Panel"
          >
            <X size={16} />
          </button>
        </nav>
      </div>
    </div>
  )
}
