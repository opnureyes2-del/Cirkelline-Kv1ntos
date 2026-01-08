'use client'

import { useState, useRef, useEffect } from 'react'
import {
  User,
  LogOut,
  LogIn,
  UserPlus,
  Sun,
  Moon,
  Monitor,
  ChevronDown,
  ChevronRight,
  Globe,
  HelpCircle,
  Shield
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useLearnMore } from '@/contexts/LearnMoreContext'
import { useRouter } from 'next/navigation'
import LoginModal from './LoginModal'
import RegisterModal from './RegisterModal'
import LearnMoreModal from './LearnMoreModal'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { ACCENT_COLORS, getAccentRGB, getAccentHex, type AccentColorKey } from '@/config/colors'

export default function UserDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  const [showRegister, setShowRegister] = useState(false)
  const { isOpen: learnMoreOpen, openLearnMore, closeLearnMore } = useLearnMore()
  const [themeExpanded, setThemeExpanded] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system')
  const [accentColor, setAccentColor] = useState<string>('purple')
  const [mounted, setMounted] = useState(false)
  const { user, logout } = useAuth()
  const router = useRouter()
  const [unreadCount, setUnreadCount] = useState(0)
  const [recentFeedback, setRecentFeedback] = useState<Array<{
    id: string
    feedback_type: string
    message_content: string
    user_email?: string
    status: string
    created_at: number
  }>>([])

  // Get current theme and accent color
  useEffect(() => {
    setMounted(true)

    console.log('👤 UserDropdown: user state:', user)
    console.log('👤 UserDropdown: isAnonymous?', user?.isAnonymous)
    console.log('👤 UserDropdown: token in localStorage?', !!localStorage.getItem('token'))

    // Load preferences from backend if logged in
    const loadPreferences = async () => {
      if (user && !user.isAnonymous) {
        try {
          const token = localStorage.getItem('token')
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

          const response = await fetch(`${apiUrl}/api/user/preferences`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })

          if (response.ok) {
            const data = await response.json()
            const prefs = data.preferences || {}

            console.log('✅ Loading preferences from backend:', prefs)

            // Apply theme from backend
            const loadedTheme = (prefs.theme as 'light' | 'dark' | 'system') || 'system'
            localStorage.setItem('theme', loadedTheme)
            setTheme(loadedTheme)
            console.log('🎨 Applied theme:', loadedTheme)

            if (loadedTheme === 'system') {
              const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
              document.documentElement.classList.toggle('dark', prefersDark)
            } else {
              document.documentElement.classList.toggle('dark', loadedTheme === 'dark')
            }

            // Apply accent color from backend
            const loadedAccent = prefs.accentColor || 'contrast'
            localStorage.setItem('accentColor', loadedAccent)
            setAccentColor(loadedAccent)
            applyAccentColor(loadedAccent)
            console.log('🎨 Applied accent color:', loadedAccent)

            // Apply sidebar states from backend
            if (prefs.sidebar) {
              console.log('📂 Applying sidebar section states from backend:', prefs.sidebar)
              Object.entries(prefs.sidebar).forEach(([key, value]) => {
                localStorage.setItem(key, JSON.stringify(value))
                console.log(`  ✅ Set ${key} = ${value}`)
              })
              // Dispatch event to notify sidebar components
              window.dispatchEvent(new CustomEvent('sidebarPreferencesLoaded'))
            } else {
              console.log('⚠️ No sidebar preferences found in backend data')
            }

            // Apply banner dismissed state from backend
            if (prefs.bannerDismissed && user?.user_id) {
              const bannerKey = `noticeBannerDismissed-${user.user_id}`
              localStorage.setItem(bannerKey, 'true')
              console.log('🎌 Applied banner dismissed state for user:', user.user_id)
              // Dispatch event to notify banner component
              window.dispatchEvent(new CustomEvent('bannerPreferencesLoaded'))
            } else {
              console.log('⚠️ Banner not dismissed or no user_id, bannerDismissed:', prefs.bannerDismissed)
            }

            // Apply sidebar collapsed state from backend
            if (prefs.sidebarCollapsed !== undefined) {
              console.log('📏 Applying sidebar collapsed state:', prefs.sidebarCollapsed)
              const sidebarState = JSON.parse(localStorage.getItem('sidebar-state') || '{}')
              sidebarState.state = { ...sidebarState.state, isCollapsed: prefs.sidebarCollapsed }
              localStorage.setItem('sidebar-state', JSON.stringify(sidebarState))
              console.log('  ✅ Updated sidebar-state in localStorage:', sidebarState)
              // Dispatch event to notify Zustand store
              window.dispatchEvent(new StorageEvent('storage', {
                key: 'sidebar-state',
                newValue: JSON.stringify(sidebarState),
                url: window.location.href
              }))
            } else {
              console.log('⚠️ No sidebarCollapsed preference found')
            }
          }
        } catch (error) {
          console.error('Failed to load preferences from backend:', error)
          // Fallback to localStorage
          const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null
          const initialTheme = savedTheme || 'system'
          setTheme(initialTheme)

          if (initialTheme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
            document.documentElement.classList.toggle('dark', prefersDark)
          } else {
            document.documentElement.classList.toggle('dark', initialTheme === 'dark')
          }

          const savedAccent = localStorage.getItem('accentColor') || 'contrast'
          setAccentColor(savedAccent)
          applyAccentColor(savedAccent)
        }
      } else {
        // Guest user or not logged in - use localStorage
        const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null
        const initialTheme = savedTheme || 'system'
        setTheme(initialTheme)

        if (initialTheme === 'system') {
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          document.documentElement.classList.toggle('dark', prefersDark)
        } else {
          document.documentElement.classList.toggle('dark', initialTheme === 'dark')
        }

        const savedAccent = localStorage.getItem('accentColor') || 'contrast'
        setAccentColor(savedAccent)
        applyAccentColor(savedAccent)
      }
    }

    loadPreferences()
  }, [user])

  // Fetch unread feedback count and recent items for admin users
  useEffect(() => {
    const fetchFeedbackData = async () => {
      if (!user || !user.is_admin) {
        setUnreadCount(0)
        setRecentFeedback([])
        return
      }

      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

        // Fetch unread count
        const countResponse = await fetch(`${apiUrl}/api/feedback/unread-count`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (countResponse.ok) {
          const countData = await countResponse.json()
          setUnreadCount(countData.unread_count || 0)
        }

        // Fetch recent unread feedback (max 3)
        const feedbackResponse = await fetch(`${apiUrl}/api/feedback?page=1&limit=3&status=unread`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (feedbackResponse.ok) {
          const feedbackData = await feedbackResponse.json()
          setRecentFeedback(feedbackData.data || [])
        }
      } catch (error) {
        console.error('Failed to fetch feedback data:', error)
      }
    }

    if (user && user.is_admin) {
      fetchFeedbackData()
      const interval = setInterval(fetchFeedbackData, 30000)

      // Listen for feedback status changes
      const handleFeedbackChange = () => {
        fetchFeedbackData()
      }
      window.addEventListener('feedbackStatusChanged', handleFeedbackChange)

      return () => {
        clearInterval(interval)
        window.removeEventListener('feedbackStatusChanged', handleFeedbackChange)
      }
    }
  }, [user])

  // Listen for system theme changes
  useEffect(() => {
    if (theme !== 'system') return

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const handleChange = (e: MediaQueryListEvent) => {
      document.documentElement.classList.toggle('dark', e.matches)
    }

    mediaQuery.addEventListener('change', handleChange)

    return () => {
      mediaQuery.removeEventListener('change', handleChange)
    }
  }, [theme])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setThemeExpanded(false) // Reset theme expansion when dropdown closes
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const applyAccentColor = (color: string) => {
    const isDark = document.documentElement.classList.contains('dark')
    const rgbValue = getAccentRGB(color as AccentColorKey, isDark)

    document.documentElement.style.setProperty('--accent-rgb', rgbValue)
  }

  const selectTheme = async (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)

    if (newTheme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      document.documentElement.classList.toggle('dark', prefersDark)
    } else {
      document.documentElement.classList.toggle('dark', newTheme === 'dark')
    }

    // ALWAYS re-apply accent color when theme changes
    // This ensures contrast colors update based on new theme
    applyAccentColor(accentColor)

    // Save to backend if user is logged in
    if (user && !user.isAnonymous) {
      try {
        const token = localStorage.getItem('token')
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

        await fetch(`${apiUrl}/api/user/preferences`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ theme: newTheme })
        })

        console.log('✅ Theme saved to backend:', newTheme)
      } catch (error) {
        console.error('Failed to save theme to backend:', error)
      }
    }
  }

  const selectAccentColor = async (color: string) => {
    setAccentColor(color)
    localStorage.setItem('accentColor', color)
    applyAccentColor(color)

    // Dispatch event to notify all components (buttons, etc.)
    window.dispatchEvent(new CustomEvent('accentColorChange'))
    console.log('🎨 Dispatched accentColorChange event for:', color)

    // Save to backend if user is logged in
    if (user && !user.isAnonymous) {
      try {
        const token = localStorage.getItem('token')
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

        await fetch(`${apiUrl}/api/user/preferences`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ accentColor: color })
        })

        console.log('✅ Accent color saved to backend:', color)
      } catch (error) {
        console.error('Failed to save accent color to backend:', error)
      }
    }
  }

  const handleLogout = () => {
    logout()
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleLanguage = () => {
    toast.info('Coming soon')
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleAdministration = () => {
    router.push('/admin')
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleLearnMore = () => {
    openLearnMore()
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleProfile = () => {
    router.push('/profile')
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleLogin = () => {
    setShowLogin(true)
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleRegister = () => {
    setShowRegister(true)
    setIsOpen(false)
    setThemeExpanded(false)
  }

  const handleSwitchToRegister = () => {
    setShowLogin(false)
    setShowRegister(true)
  }

  const handleSwitchToLogin = () => {
    setShowRegister(false)
    setShowLogin(true)
  }

  if (!mounted) return null

  const isAuthenticated = user && !user.isAnonymous

  const userName = user?.isAnonymous
    ? 'Guest'
    : (user?.display_name || user?.email?.split('@')[0] || 'User')

  const userEmail = user?.email || 'guest@cirkelline.com'

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Dropdown Trigger Button */}
      <div className="flex items-center gap-0.5">
        {/* Notification Badge (clickable) - Admin only */}
        {user?.is_admin && unreadCount > 0 && (
          <motion.button
            onClick={() => router.push('/admin/feedback')}
            className="w-5 h-5 rounded-full flex items-center justify-center transition-all hover:scale-110"
            style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            title="View feedback"
          >
            <span className="text-[10px] font-bold text-white">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          </motion.button>
        )}

        {/* User Name Button (opens dropdown) */}
        <motion.button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {/* User Name */}
          <span className="font-heading text-sm font-semibold">
            {userName}
          </span>

          {/* Chevron */}
          <motion.div
            animate={{ rotate: isOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDown size={16} className="text-light-text dark:text-dark-text" style={{ opacity: 0.5 }} />
          </motion.div>
        </motion.button>
      </div>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="absolute right-0 mt-2 w-64 bg-light-elevated dark:bg-dark-elevated border border-border-primary rounded-xl shadow-xl overflow-hidden z-50"
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -5, scale: 0.98 }}
            transition={{ duration: 0.15 }}
          >

          {isAuthenticated ? (
            <>
              {/* AUTHENTICATED USER MENU */}

              {/* User Info Section */}
              <div className="px-4 py-3 border-b border-border-secondary">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm text-light-text dark:text-dark-text truncate">
                      {userName}
                    </p>
                    {user?.is_admin && (
                      <span
                        className="px-2 py-0.5 rounded-md text-xs font-semibold text-white"
                        style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
                      >
                        Admin
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary truncate">
                    {userEmail}
                  </p>
                </div>
              </div>

              {/* Notification Preview (Admin only, when unread > 0) */}
              {user?.is_admin && unreadCount > 0 && (
                <>
                  <div className="h-2" />
                  <div className="px-4 py-2">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-light-text dark:text-dark-text font-sans">
                        Recent Feedback
                      </p>
                      <motion.button
                        onClick={() => {
                          router.push('/admin/feedback')
                          setIsOpen(false)
                        }}
                        className="text-xs text-accent hover:underline font-sans"
                        whileHover={{ x: 2 }}
                      >
                        View all →
                      </motion.button>
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto overflow-x-hidden">
                      {recentFeedback.map((item) => (
                        <div
                          key={item.id}
                          onClick={() => {
                            router.push('/admin/feedback')
                            setIsOpen(false)
                          }}
                          className="p-2 rounded-lg bg-light-bg dark:bg-dark-bg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary cursor-pointer transition-colors"
                        >
                          <div className="flex items-start gap-2">
                            {item.feedback_type === 'positive' ? (
                              <div className="w-5 h-5 rounded bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0">
                                <span className="text-xs">👍</span>
                              </div>
                            ) : (
                              <div className="w-5 h-5 rounded bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
                                <span className="text-xs">👎</span>
                              </div>
                            )}
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mb-0.5">
                                {item.user_email?.split('@')[0]}
                              </p>
                              <p className="text-xs text-light-text dark:text-dark-text font-sans line-clamp-2">
                                {item.message_content?.substring(0, 60)}...
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="h-px bg-border-secondary my-2" />
                </>
              )}

              {/* Administration Option (Admin only) - Moved to top */}
              {user?.is_admin && (
                <motion.button
                  onClick={handleAdministration}
                  className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-accent/10 text-light-text dark:text-dark-text transition-colors rounded-lg mx-1"
                  whileHover={{ x: 2 }}
                >
                  <Shield size={16} className="text-light-text dark:text-dark-text" />
                  <span className="text-sm font-sans">Administration</span>
                </motion.button>
              )}

              {/* Profile Option */}
              <motion.button
                onClick={handleProfile}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <User size={16} className="text-light-text dark:text-dark-text" />
                <span className="text-sm font-sans">Profile</span>
              </motion.button>

              {/* Language Option */}
              <motion.button
                onClick={handleLanguage}
                className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors group rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <div className="flex items-center gap-3">
                  <Globe size={16} className="text-light-text dark:text-dark-text" />
                  <span className="text-sm font-sans">Language</span>
                </div>
                <ChevronRight size={16} className="text-light-text dark:text-dark-text" />
              </motion.button>

              {/* Theme Option */}
              <div>
                <motion.button
                  onClick={() => setThemeExpanded(!themeExpanded)}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors group rounded-lg mx-1"
                  whileHover={{ x: 2 }}
                >
                  <div className="flex items-center gap-3">
                    {theme === 'light' ? (
                      <Sun size={16} className="text-light-text dark:text-dark-text" />
                    ) : theme === 'dark' ? (
                      <Moon size={16} className="text-light-text dark:text-dark-text" />
                    ) : (
                      <Monitor size={16} className="text-light-text dark:text-dark-text" />
                    )}
                    <span className="text-sm font-sans">Theme</span>
                  </div>
                  {themeExpanded ? (
                    <ChevronDown size={16} className="text-light-text dark:text-dark-text" />
                  ) : (
                    <ChevronRight size={16} className="text-light-text dark:text-dark-text" />
                  )}
                </motion.button>

                {/* Theme Options - Expanded */}
                <AnimatePresence>
                  {themeExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 py-2">
                        {/* Theme Options - Horizontal Layout */}
                        <div className="flex items-center justify-center gap-2 mb-3">
                          <motion.button
                            onClick={() => selectTheme('light')}
                            className={`flex flex-col items-center gap-2 px-4 py-3 rounded-lg transition-all flex-1 ${
                              theme === 'light'
                                ? 'bg-accent/10 text-accent'
                                : 'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Sun size={16} />
                            <span className="text-xs font-medium">Light</span>
                          </motion.button>

                          <motion.button
                            onClick={() => selectTheme('dark')}
                            className={`flex flex-col items-center gap-2 px-4 py-3 rounded-lg transition-all flex-1 ${
                              theme === 'dark'
                                ? 'bg-accent/10 text-accent'
                                : 'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Moon size={16} />
                            <span className="text-xs font-medium">Dark</span>
                          </motion.button>

                          <motion.button
                            onClick={() => selectTheme('system')}
                            className={`flex flex-col items-center gap-2 px-4 py-3 rounded-lg transition-all flex-1 ${
                              theme === 'system'
                                ? 'bg-accent/10 text-accent'
                                : 'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Monitor size={16} />
                            <span className="text-xs font-medium">System</span>
                          </motion.button>
                        </div>

                        {/* Divider */}
                        <div className="h-px bg-border-secondary my-2" />

                        {/* Accent Color Picker - Horizontal Row */}
                        <div className="px-8 py-2 flex items-center justify-center gap-2">
                          {(['contrast', 'purple', 'orange', 'green', 'blue', 'pink'] as AccentColorKey[]).map((colorKey) => {
                            const isDarkMode = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
                            const hexColor = getAccentHex(colorKey, isDarkMode)
                            const isContrast = colorKey === 'contrast'

                            return (
                              <motion.button
                                key={colorKey}
                                onClick={() => selectAccentColor(colorKey)}
                                className={`w-4 h-4 rounded-full transition-all ${
                                  isContrast ? 'bg-[#212124] dark:bg-[#E0E0E0]' : ''
                                } ${
                                  accentColor === colorKey
                                    ? 'ring-2 ring-offset-1 ring-offset-light-surface dark:ring-offset-dark-surface'
                                    : ''
                                }`}
                                style={{
                                  backgroundColor: isContrast ? undefined : hexColor,
                                  ...(accentColor === colorKey ? { boxShadow: `0 0 0 2px var(--bg-surface), 0 0 0 4px ${hexColor}` } : {})
                                }}
                                whileHover={{ scale: 1.2 }}
                                whileTap={{ scale: 0.9 }}
                                aria-label={`${ACCENT_COLORS[colorKey].name} accent`}
                              />
                            )
                          })}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Learn More Option */}
              <motion.button
                onClick={handleLearnMore}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <HelpCircle size={16} className="text-light-text dark:text-dark-text" />
                <span className="text-sm font-sans">Learn more</span>
              </motion.button>

              {/* Divider before Logout */}
              <div className="h-px bg-gray-200 dark:bg-gray-700 my-2" />

              {/* Logout Option */}
              <motion.button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-error-bg text-error transition-colors rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <LogOut size={18} className="text-error" />
                <span className="text-sm font-sans">Log out</span>
              </motion.button>
            </>
          ) : (
            <>
              {/* GUEST USER MENU */}

              {/* Guest Header */}
              <div className="px-4 py-3 border-b border-border-secondary">
                <div className="flex flex-col gap-1">
                  <p className="font-medium text-sm text-light-text dark:text-dark-text">
                    Guest
                  </p>
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary truncate">
                    Not signed in
                  </p>
                </div>
              </div>

              {/* Login */}
              <motion.button
                onClick={handleLogin}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <LogIn size={16} className="text-light-text dark:text-dark-text" />
                <span className="text-sm font-sans">Log in</span>
              </motion.button>

              {/* Register */}
              <motion.button
                onClick={handleRegister}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <UserPlus size={16} className="text-light-text dark:text-dark-text" />
                <span className="text-sm font-sans">Register</span>
              </motion.button>

              {/* Language Option */}
              <motion.button
                onClick={handleLanguage}
                className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors group rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <div className="flex items-center gap-3">
                  <Globe size={16} className="text-light-text dark:text-dark-text" />
                  <span className="text-sm font-sans">Language</span>
                </div>
                <ChevronRight size={16} className="text-light-text dark:text-dark-text" />
              </motion.button>

              {/* Theme Option */}
              <div>
                <motion.button
                  onClick={() => setThemeExpanded(!themeExpanded)}
                  className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors group rounded-lg mx-1"
                  whileHover={{ x: 2 }}
                >
                  <div className="flex items-center gap-3">
                    {theme === 'light' ? (
                      <Sun size={16} className="text-light-text dark:text-dark-text" />
                    ) : theme === 'dark' ? (
                      <Moon size={16} className="text-light-text dark:text-dark-text" />
                    ) : (
                      <Monitor size={16} className="text-light-text dark:text-dark-text" />
                    )}
                    <span className="text-sm font-sans">Theme</span>
                  </div>
                  {themeExpanded ? (
                    <ChevronDown size={16} className="text-light-text dark:text-dark-text" />
                  ) : (
                    <ChevronRight size={16} className="text-light-text dark:text-dark-text" />
                  )}
                </motion.button>

                {/* Theme Options - Expanded */}
                <AnimatePresence>
                  {themeExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="px-4 py-2">
                        {/* Theme Options - Horizontal Layout */}
                        <div className="flex items-center justify-center gap-2 mb-3">
                          <motion.button
                            onClick={() => selectTheme('light')}
                            className={`flex flex-col items-center gap-2 px-4 py-3 rounded-lg transition-all flex-1 ${
                              theme === 'light'
                                ? 'bg-accent/10 text-accent'
                                : 'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Sun size={16} />
                            <span className="text-xs font-medium">Light</span>
                          </motion.button>

                          <motion.button
                            onClick={() => selectTheme('dark')}
                            className={`flex flex-col items-center gap-2 px-4 py-3 rounded-lg transition-all flex-1 ${
                              theme === 'dark'
                                ? 'bg-accent/10 text-accent'
                                : 'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Moon size={16} />
                            <span className="text-xs font-medium">Dark</span>
                          </motion.button>

                          <motion.button
                            onClick={() => selectTheme('system')}
                            className={`flex flex-col items-center gap-2 px-4 py-3 rounded-lg transition-all flex-1 ${
                              theme === 'system'
                                ? 'bg-accent/10 text-accent'
                                : 'hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Monitor size={16} />
                            <span className="text-xs font-medium">System</span>
                          </motion.button>
                        </div>

                        {/* Divider */}
                        <div className="h-px bg-border-secondary my-2" />

                        {/* Accent Color Picker - Horizontal Row */}
                        <div className="px-8 py-2 flex items-center justify-center gap-2">
                          {(['contrast', 'purple', 'orange', 'green', 'blue', 'pink'] as AccentColorKey[]).map((colorKey) => {
                            const isDarkMode = typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
                            const hexColor = getAccentHex(colorKey, isDarkMode)
                            const isContrast = colorKey === 'contrast'

                            return (
                              <motion.button
                                key={colorKey}
                                onClick={() => selectAccentColor(colorKey)}
                                className={`w-4 h-4 rounded-full transition-all ${
                                  isContrast ? 'bg-[#212124] dark:bg-[#E0E0E0]' : ''
                                } ${
                                  accentColor === colorKey
                                    ? 'ring-2 ring-offset-1 ring-offset-light-surface dark:ring-offset-dark-surface'
                                    : ''
                                }`}
                                style={{
                                  backgroundColor: isContrast ? undefined : hexColor,
                                  ...(accentColor === colorKey ? { boxShadow: `0 0 0 2px var(--bg-surface), 0 0 0 4px ${hexColor}` } : {})
                                }}
                                whileHover={{ scale: 1.2 }}
                                whileTap={{ scale: 0.9 }}
                                aria-label={`${ACCENT_COLORS[colorKey].name} accent`}
                              />
                            )
                          })}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Learn More Option */}
              <motion.button
                onClick={handleLearnMore}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text dark:text-dark-text transition-colors rounded-lg mx-1"
                whileHover={{ x: 2 }}
              >
                <HelpCircle size={16} className="text-light-text dark:text-dark-text" />
                <span className="text-sm font-sans">Learn more</span>
              </motion.button>
            </>
          )}

          </motion.div>
        )}
      </AnimatePresence>

      {/* Modals */}
      <LoginModal
        isOpen={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToRegister={handleSwitchToRegister}
      />

      <RegisterModal
        isOpen={showRegister}
        onClose={() => setShowRegister(false)}
        onSwitchToLogin={handleSwitchToLogin}
      />

      <LearnMoreModal
        isOpen={learnMoreOpen}
        onClose={closeLearnMore}
      />
    </div>
  )
}
