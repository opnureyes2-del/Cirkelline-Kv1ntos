'use client'
import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import GoogleConnect from '@/components/GoogleConnect'
import { useSearchParams } from 'next/navigation'

interface ProfileModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const { user } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [bio, setBio] = useState('')
  const modalRef = useRef<HTMLDivElement>(null)
  const searchParams = useSearchParams()

  // Initialize with user data
  useEffect(() => {
    if (user) {
      setName(user.isAnonymous ? 'Guest' : (user.display_name || user.email?.split('@')[0] || 'User'))
      setEmail(user.email || 'guest@cirkelline.com')
    }
  }, [user])

  // Handle OAuth callback redirect
  useEffect(() => {
    const googleStatus = searchParams?.get('google')
    if (googleStatus === 'connected') {
      // Show success notification
      alert('Google account connected successfully!')
      // Remove query parameter
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [searchParams])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden' // Prevent background scroll
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
      onClose()
    }
  }

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        console.error('No auth token found')
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
      const response = await fetch(`${apiUrl}/api/user/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          display_name: name
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update profile')
      }

      const data = await response.json()

      // Store new token
      localStorage.setItem('token', data.token)

      // Reload page to update UI everywhere
      window.location.reload()

    } catch (err) {
      console.error('Profile update error:', err)
      alert('Failed to update profile. Please try again.')
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6 bg-black/50 backdrop-blur-sm overflow-y-auto"
      onClick={handleBackdropClick}
    >
      {/* Modal Container */}
      <div
        ref={modalRef}
        className="w-full max-w-md bg-light-surface dark:bg-dark-surface rounded-2xl shadow-2xl overflow-hidden animate-modal my-auto"
      >

        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-heading font-semibold text-light-text dark:text-dark-text">
            Profile Settings
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-accent/10 text-light-text/60 dark:text-dark-text/60 transition-colors"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="px-4 sm:px-6 py-6 space-y-6 max-h-[calc(90vh-12rem)] overflow-y-auto">

          {/* Name Field */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
              placeholder="Your name"
            />
          </div>

          {/* Email Field */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
              placeholder="your@email.com"
            />
          </div>

          {/* Bio Field */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
              Bio
            </label>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value.slice(0, 200))}
              rows={3}
              className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent resize-none font-body transition-colors"
              placeholder="Tell us about yourself..."
              maxLength={200}
            />
            <p className="mt-1 text-xs text-light-text/50 dark:text-dark-text/50">
              {bio.length}/200 characters
            </p>
          </div>

          {/* Google Services Section */}
          <div>
            <h3 className="text-sm font-medium text-light-text dark:text-dark-text mb-3">
              Google Services
            </h3>
            <GoogleConnect />
          </div>

        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-4 sm:px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg hover:bg-accent/10 text-light-text dark:text-dark-text font-sans transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors"
          >
            Save changes
          </button>
        </div>

      </div>
    </div>,
    document.body
  )
}
