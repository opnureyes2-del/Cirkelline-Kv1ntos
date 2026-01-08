'use client'

import AdminSidebar from '@/components/admin/AdminSidebar'
import TopBar from '@/components/TopBar'
import { useSidebar } from '@/hooks/useSidebar'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { motion } from 'framer-motion'

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isCollapsed } = useSidebar()
  const { user } = useAuth()
  const router = useRouter()

  // Redirect if not admin
  useEffect(() => {
    if (user && !user.is_admin) {
      router.push('/')
    }
  }, [user, router])

  // Don't render anything if not admin
  if (!user || !user.is_admin) {
    return null
  }

  return (
    <div className="relative">
      {/* Admin Sidebar */}
      <AdminSidebar />

      {/* Top Bar */}
      <TopBar />

      {/* Main Content Area */}
      <motion.main
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.3 }}
        className={`
          min-h-screen pt-16 bg-light-bg dark:bg-dark-bg transition-all duration-300 ease-in-out
          ${isCollapsed ? 'md:ml-0' : 'md:ml-64'}
        `}
      >
        {children}
      </motion.main>
    </div>
  )
}
