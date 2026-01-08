'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useLearnMore } from '@/contexts/LearnMoreContext'
import { useAuth } from '@/hooks/useAuth'

const NoticeBanner = () => {
  const [isVisible, setIsVisible] = useState(false)
  const [hasAppeared, setHasAppeared] = useState(false)
  const { openLearnMore } = useLearnMore()
  const { user } = useAuth()

  useEffect(() => {
    // Only check after we have user info (or confirmed anonymous)
    if (typeof window === 'undefined') return

    const checkBannerState = () => {
      // GUEST USERS: Always show banner (no persistence)
      if (!user?.user_id) {
        setIsVisible(true)
        return
      }

      // LOGGED-IN USERS: Check localStorage for dismiss state
      const userId = user.user_id
      const bannerKey = `noticeBannerDismissed-${userId}`
      const bannerDismissed = localStorage.getItem(bannerKey)

      // Set visibility based on dismiss state
      if (!bannerDismissed) {
        setIsVisible(true)
      } else {
        setIsVisible(false)
      }
    }

    checkBannerState()

    // Listen for preferences loaded from backend
    const handlePreferencesLoaded = () => {
      checkBannerState()
    }

    window.addEventListener('bannerPreferencesLoaded', handlePreferencesLoaded)

    return () => {
      window.removeEventListener('bannerPreferencesLoaded', handlePreferencesLoaded)
    }
  }, [user])

  const handleClose = async () => {
    if (typeof window === 'undefined') return

    setIsVisible(false)

    // Save to backend if user is logged in
    if (user?.user_id) {
      const userId = user.user_id
      const bannerKey = `noticeBannerDismissed-${userId}`
      localStorage.setItem(bannerKey, 'true')

      // Save to backend
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

        await fetch(`${apiUrl}/api/user/preferences`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ bannerDismissed: true })
        })
      } catch {
        // Silently fail - banner dismiss is not critical
      }
    }
  }

  const handleFeedback = () => {
    openLearnMore('contact')
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{
            duration: 0.3,
            ease: 'easeOut',
            delay: !hasAppeared ? 7 : 0
          }}
          onAnimationComplete={() => setHasAppeared(true)}
          className="absolute top-4 left-0 right-0 z-40 flex justify-center px-4 pointer-events-none"
        >
          <div className="max-w-2xl w-full pointer-events-auto">
            <div
              className="border border-border-primary rounded-xl p-4 shadow-lg backdrop-blur-sm relative bg-[rgb(var(--contrast-dark-rgb))] dark:bg-[rgb(var(--contrast-light-rgb))]"
            >
              <p className="text-sm font-medium text-center pr-8 text-[rgb(var(--contrast-light-rgb))] dark:text-[rgb(var(--contrast-dark-rgb))]">
                We are still in <span className="font-semibold">early stages</span> of development.
                <br />
                Report any issues or give us your suggestions{' '}
                <button
                  onClick={handleFeedback}
                  className="text-accent font-semibold hover:underline focus:outline-none"
                >
                  here
                </button>
              </p>
              <button
                onClick={handleClose}
                className="absolute top-3 right-3 transition-colors p-0.5 rounded-lg hover:opacity-70 text-[rgb(var(--contrast-light-rgb))] dark:text-[rgb(var(--contrast-dark-rgb))]"
                aria-label="Close banner"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default NoticeBanner
