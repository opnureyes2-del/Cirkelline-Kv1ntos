'use client'

import { MessageSquare, Upload, Settings, Link, Clock } from 'lucide-react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'

interface Activity {
  type: string
  description: string
  timestamp: number
}

interface ActivityFeedProps {
  activities: Activity[]
}

export default function ActivityFeed({ activities }: ActivityFeedProps) {
  const router = useRouter()

  // Format timestamp to relative time
  const formatRelativeTime = (timestamp: number) => {
    const now = Date.now()
    const diff = now - (timestamp * 1000) // Convert to ms

    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    return 'Just now'
  }

  // Get icon based on activity type
  const getIcon = (type: string) => {
    switch (type) {
      case 'chat_started':
        return MessageSquare
      case 'document_uploaded':
        return Upload
      case 'settings_changed':
        return Settings
      case 'integration_connected':
        return Link
      default:
        return MessageSquare
    }
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-8 border border-border-primary">
        <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-6 font-heading">
          Recent Activity
        </h2>
        <div className="text-center py-8">
          <Clock size={48} className="mx-auto mb-4 text-light-text-secondary/50 dark:text-dark-text-secondary/50" />
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            No recent activity yet. Start a conversation to see your activity here!
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary">
      <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-6 font-heading">
        Recent Activity
      </h2>

      <div className="space-y-4">
        {activities.map((activity, index) => {
          const Icon = getIcon(activity.type)

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
              className="flex items-start gap-4 pb-4 border-b border-border-primary last:border-0 last:pb-0"
            >
              {/* Icon */}
              <div className="mt-1 p-2 rounded-lg bg-accent/10 text-accent flex-shrink-0">
                <Icon size={18} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-light-text dark:text-dark-text font-medium mb-1">
                  {activity.description}
                </p>
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  {formatRelativeTime(activity.timestamp)}
                </p>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* View All Link */}
      {activities.length >= 5 && (
        <div className="mt-6 pt-4 border-t border-border-primary">
          <button
            className="text-sm text-accent hover:text-accent/80 font-medium transition-colors"
            onClick={() => router.push('/profile/activity')}
          >
            View all activity →
          </button>
        </div>
      )}
    </div>
  )
}
