'use client'

import ProfileSidebar from '@/components/profile/ProfileSidebar'
import TopBar from '@/components/TopBar'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useSidebar } from '@/hooks/useSidebar'

export default function ProfileLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user } = useAuth()
  const router = useRouter()
  const { isCollapsed } = useSidebar()

  // Redirect if not authenticated
  useEffect(() => {
    if (user && user.isAnonymous) {
      router.push('/')
    }
  }, [user, router])

  // Don't render anything if not authenticated
  if (!user || user.isAnonymous) {
    return null
  }

  return (
    <div className="relative">
      {/* Profile Sidebar */}
      <ProfileSidebar />

      {/* Top Bar */}
      <TopBar />

      {/* Main Content Area */}
      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className={`
          min-h-screen pt-16 bg-light-bg dark:bg-dark-bg transition-all duration-300 ease-in-out overflow-y-auto
          ${isCollapsed ? 'md:ml-0' : 'md:ml-64'}
        `}
      >
        {children}
      </motion.main>
    </div>
  )
}
