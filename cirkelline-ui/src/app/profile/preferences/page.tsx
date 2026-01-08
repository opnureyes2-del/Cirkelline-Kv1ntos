'use client'

import { useState, useEffect } from 'react'
import { Settings, Sun, Moon, Monitor, Globe } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { ACCENT_COLORS, getAccentRGB, getAccentHex, type AccentColorKey } from '@/config/colors'

export default function ProfilePreferencesPage() {
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system')
  const [accentColor, setAccentColor] = useState('purple')
  const [isDarkMode, setIsDarkMode] = useState(false)

  // Load theme and accent color on mount, track dark mode
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' || 'system'
    const savedAccent = localStorage.getItem('accentColor') || 'purple'
    setTheme(savedTheme)
    setAccentColor(savedAccent)
    setIsDarkMode(document.documentElement.classList.contains('dark'))

    // Listen for theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          setIsDarkMode(document.documentElement.classList.contains('dark'))
        }
      })
    })
    observer.observe(document.documentElement, { attributes: true })
    return () => observer.disconnect()
  }, [])

  const applyAccentColor = (color: string) => {
    const isDark = document.documentElement.classList.contains('dark')
    const rgbValue = getAccentRGB(color as AccentColorKey, isDark)
    document.documentElement.style.setProperty('--accent-rgb', rgbValue)

    // Dispatch event for components that need to update
    window.dispatchEvent(new CustomEvent('accentColorChange'))
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

    // Re-apply accent color when theme changes
    applyAccentColor(accentColor)

    // Save to backend if authenticated
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
        await fetch(`${apiUrl}/api/user/preferences`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ theme: newTheme })
        })
      }
    } catch (error) {
      console.error('Failed to save theme:', error)
    }

    toast.success(`Theme changed to ${newTheme}`)
  }

  const selectAccentColor = async (color: string) => {
    setAccentColor(color)
    localStorage.setItem('accentColor', color)
    applyAccentColor(color)

    // Save to backend if authenticated
    try {
      const token = localStorage.getItem('token')
      if (token) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
        await fetch(`${apiUrl}/api/user/preferences`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ accentColor: color })
        })
      }
    } catch (error) {
      console.error('Failed to save accent color:', error)
    }

    toast.success('Accent color updated')
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Settings className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
              Preferences
            </h1>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
            Customize your Cirkelline experience
          </p>
        </div>

        {/* Theme Settings Card */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6">
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-6 font-heading">
            Appearance
          </h2>

          {/* Theme Mode Selection */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-4">
              Theme Mode
            </label>
            <div className="grid grid-cols-3 gap-3">
              <motion.button
                onClick={() => selectTheme('light')}
                className={`flex flex-col items-center gap-3 px-4 py-6 rounded-lg transition-all ${
                  theme === 'light'
                    ? 'bg-accent/10 border-2 border-accent'
                    : 'bg-light-bg dark:bg-dark-bg border-2 border-transparent hover:border-border-primary'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Sun size={24} className={theme === 'light' ? 'text-accent' : 'text-light-text-secondary dark:text-dark-text-secondary'} />
                <span className={`text-sm font-medium ${theme === 'light' ? 'text-accent' : 'text-light-text dark:text-dark-text'}`}>
                  Light
                </span>
              </motion.button>

              <motion.button
                onClick={() => selectTheme('dark')}
                className={`flex flex-col items-center gap-3 px-4 py-6 rounded-lg transition-all ${
                  theme === 'dark'
                    ? 'bg-accent/10 border-2 border-accent'
                    : 'bg-light-bg dark:bg-dark-bg border-2 border-transparent hover:border-border-primary'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Moon size={24} className={theme === 'dark' ? 'text-accent' : 'text-light-text-secondary dark:text-dark-text-secondary'} />
                <span className={`text-sm font-medium ${theme === 'dark' ? 'text-accent' : 'text-light-text dark:text-dark-text'}`}>
                  Dark
                </span>
              </motion.button>

              <motion.button
                onClick={() => selectTheme('system')}
                className={`flex flex-col items-center gap-3 px-4 py-6 rounded-lg transition-all ${
                  theme === 'system'
                    ? 'bg-accent/10 border-2 border-accent'
                    : 'bg-light-bg dark:bg-dark-bg border-2 border-transparent hover:border-border-primary'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Monitor size={24} className={theme === 'system' ? 'text-accent' : 'text-light-text-secondary dark:text-dark-text-secondary'} />
                <span className={`text-sm font-medium ${theme === 'system' ? 'text-accent' : 'text-light-text dark:text-dark-text'}`}>
                  System
                </span>
              </motion.button>
            </div>
          </div>

          {/* Accent Color Selection */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-4">
              Accent Color
            </label>
            <div className="flex flex-wrap gap-3">
              {(['contrast', 'purple', 'orange', 'green', 'blue', 'pink'] as AccentColorKey[]).map((colorKey) => {
                const hexColor = getAccentHex(colorKey, isDarkMode)
                const isContrast = colorKey === 'contrast'
                return (
                  <motion.button
                    key={colorKey}
                    onClick={() => selectAccentColor(colorKey)}
                    className={`w-12 h-12 rounded-full transition-all ${
                      accentColor === colorKey
                        ? 'ring-4 ring-offset-2 ring-offset-light-surface dark:ring-offset-dark-surface'
                        : ''
                    } ${isContrast ? 'bg-[rgb(var(--contrast-dark-rgb))] dark:bg-[rgb(var(--contrast-light-rgb))]' : ''}`}
                    style={{
                      backgroundColor: isContrast ? undefined : hexColor,
                      ['--tw-ring-color' as string]: hexColor
                    }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    aria-label={`${ACCENT_COLORS[colorKey].name} accent`}
                  />
                )
              })}
            </div>
          </div>
        </div>

        {/* Language & Region Card (Placeholder) */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <Globe className="w-6 h-6 text-light-text-secondary dark:text-dark-text-secondary" />
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading">
              Language & Region
            </h2>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Language and region settings coming soon
          </p>
        </div>

        {/* Notifications Card (Placeholder) */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary opacity-50">
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 font-heading">
            Notifications
          </h2>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Notification preferences coming soon
          </p>
        </div>
      </div>
    </div>
  )
}
