'use client'
import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
  onSwitchToRegister: () => void
}

export default function LoginModal({ isOpen, onClose, onSwitchToRegister }: LoginModalProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  const { login } = useAuth()

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Call login API
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Invalid email or password')
        return
      }

      // Login with token (this clears chat state internally)
      login(data.token)
      onClose()

      // Force full page reload to clear URL params and start fresh
      window.location.href = '/'
    } catch {
      setError('An error occurred. Please try again.')
    } finally {
      setLoading(false)
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
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-heading font-semibold text-light-text dark:text-dark-text">
            Log in to Cirkelline
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
        <form onSubmit={handleLogin} className="px-6 py-6 space-y-4">

          <p className="text-sm text-light-text/60 dark:text-dark-text/60 font-body">
            Welcome back! Please enter your credentials.
          </p>

          {/* Error Display */}
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
              {error}
            </div>
          )}

          {/* Email Field */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
              placeholder="your@email.com"
            />
          </div>

          {/* Password Field */}
          <div>
            <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
              placeholder="••••••••"
            />
          </div>

          {/* Forgot Password Link */}
          <div className="text-right">
            <button
              type="button"
              className="text-sm text-accent hover:text-accent/80 font-sans transition-colors"
            >
              Forgot password?
            </button>
          </div>

          {/* Login Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Logging in...' : 'Log in'}
          </button>

          {/* Switch to Register */}
          <p className="text-center text-sm text-light-text/60 dark:text-dark-text/60 font-body">
            Don&apos;t have an account?{' '}
            <button
              type="button"
              onClick={onSwitchToRegister}
              className="text-accent hover:text-accent/80 font-sans transition-colors"
            >
              Register
            </button>
          </p>

        </form>

      </div>
    </div>,
    document.body
  )
}
