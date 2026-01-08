'use client'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface RegisterFormProps {
  onSuccess: () => void
  onSwitchToLogin: () => void
}

export default function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { register } = useAuth()

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setLoading(true)

    try {
      // Call signup API
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, display_name: name }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Registration failed. Please try again.')
        return
      }

      // Register with token (this clears chat state internally)
      register(data.token)
      onSuccess()

      // Force full page reload to clear URL params and start fresh
      window.location.href = '/'
    } catch {
      setError('An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleRegister} className="px-6 py-6 space-y-4 max-h-[calc(90vh-8rem)] overflow-y-auto">
      <p className="text-sm text-light-text/60 dark:text-dark-text/60 font-body">
        Join Cirkelline today and get started.
      </p>

      {/* Error Display */}
      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
          {error}
        </div>
      )}

      {/* Name Field */}
      <div>
        <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
          Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
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
          minLength={8}
          className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
          placeholder="********"
        />
        <p className="mt-1 text-xs text-light-text/50 dark:text-dark-text/50">
          At least 8 characters
        </p>
      </div>

      {/* Confirm Password Field */}
      <div>
        <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
          Confirm Password
        </label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-gray-300 dark:border-gray-600 focus:outline-none focus:border-accent font-body transition-colors"
          placeholder="********"
        />
      </div>

      {/* Register Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 rounded-lg bg-accent hover:bg-accent/90 text-white font-sans transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating account...' : 'Create account'}
      </button>

      {/* Switch to Login */}
      <p className="text-center text-sm text-light-text/60 dark:text-dark-text/60 font-body">
        Already have an account?{' '}
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="text-accent hover:text-accent/80 font-sans transition-colors"
        >
          Log in
        </button>
      </p>
    </form>
  )
}
