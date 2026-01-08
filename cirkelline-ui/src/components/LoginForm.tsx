'use client'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

interface LoginFormProps {
  onSuccess: () => void
  onSwitchToRegister: () => void
}

export default function LoginForm({ onSuccess, onSwitchToRegister }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { login } = useAuth()

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
          placeholder="********"
        />
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
  )
}
