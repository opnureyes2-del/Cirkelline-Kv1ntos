'use client'

import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { MessageSquare } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'

export default function AdminFeedbackBadge() {
  const { user } = useAuth()
  const router = useRouter()
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)

  // Fetch unread count
  const fetchUnreadCount = useCallback(async () => {
    if (!user || !user.is_admin) {
      setLoading(false)
      return
    }

    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/feedback/unread-count`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setUnreadCount(data.unread_count || 0)
      }
    } catch (error) {
      console.error('Failed to fetch unread feedback count:', error)
    } finally {
      setLoading(false)
    }
  }, [user])

  // Poll for updates every 30 seconds
  useEffect(() => {
    if (user && user.is_admin) {
      fetchUnreadCount()
      const interval = setInterval(fetchUnreadCount, 30000)
      return () => clearInterval(interval)
    }
  }, [user, fetchUnreadCount])

  // Don't show for non-admins
  if (!user || !user.is_admin || loading) {
    return null
  }

  return (
    <motion.button
      onClick={() => router.push('/admin/feedback')}
      className="relative p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
      title="User Feedback"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <MessageSquare className="w-5 h-5 text-light-text dark:text-dark-text" />
      {unreadCount > 0 && (
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-1 -right-1 bg-accent text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center"
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </motion.span>
      )}
    </motion.button>
  )
}
