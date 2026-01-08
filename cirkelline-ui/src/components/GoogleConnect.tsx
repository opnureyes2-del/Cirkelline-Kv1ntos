'use client'

import { useState, useEffect } from 'react'
import { Mail, Calendar, Sheet, Check, X, Loader2 } from 'lucide-react'

interface GoogleStatus {
  connected: boolean
  email: string | null
  scopes: string[]
  connected_at: string | null
}

export default function GoogleConnect() {
  const [status, setStatus] = useState<GoogleStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [disconnecting, setDisconnecting] = useState(false)

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/oauth/google/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (error) {
      console.error('Failed to fetch Google status:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleConnect = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
    const token = localStorage.getItem('token')

    // Redirect to OAuth start endpoint
    window.location.href = `${apiUrl}/api/oauth/google/start?token=${token}`
  }

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your Google account?')) {
      return
    }

    setDisconnecting(true)
    try {
      const token = localStorage.getItem('token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

      const response = await fetch(`${apiUrl}/api/oauth/google/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        setStatus({ connected: false, email: null, scopes: [], connected_at: null })
      } else {
        alert('Failed to disconnect Google account')
      }
    } catch (error) {
      console.error('Failed to disconnect:', error)
      alert('Failed to disconnect Google account')
    } finally {
      setDisconnecting(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6">
        <div className="flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-accent" />
        </div>
      </div>
    )
  }

  if (!status?.connected) {
    return (
      <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-accent/10 rounded-lg">
            <Mail className="w-6 h-6 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading">
              Connect Google Account
            </h3>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
              Access Gmail, Calendar, and Sheets through Cirkelline
            </p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            <Mail size={16} />
            <span>Read and send emails</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            <Calendar size={16} />
            <span>View and create calendar events</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            <Sheet size={16} />
            <span>Access and update spreadsheets</span>
          </div>
        </div>

        <button
          onClick={handleConnect}
          className="w-full px-4 py-2 bg-accent hover:bg-accent/90 text-white rounded-lg font-medium transition-colors font-sans"
        >
          Connect to Google
        </button>

        <p className="mt-4 text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">
          Cirkelline will request permission to access your Google services. You can disconnect at any time.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-green-500/10 rounded-lg">
          <Check className="w-6 h-6 text-green-600 dark:text-green-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading">
            Google Connected
          </h3>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            {status.email}
          </p>
        </div>
      </div>

      <div className="space-y-2 mb-6">
        <p className="text-sm font-medium text-light-text dark:text-dark-text font-body">
          Connected Services:
        </p>
        <div className="grid grid-cols-3 gap-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-light-bg dark:bg-dark-bg rounded-lg">
            <Mail size={16} className="text-accent" />
            <span className="text-xs font-body text-light-text dark:text-dark-text">Gmail</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 bg-light-bg dark:bg-dark-bg rounded-lg">
            <Calendar size={16} className="text-accent" />
            <span className="text-xs font-body text-light-text dark:text-dark-text">Calendar</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 bg-light-bg dark:bg-dark-bg rounded-lg">
            <Sheet size={16} className="text-accent" />
            <span className="text-xs font-body text-light-text dark:text-dark-text">Sheets</span>
          </div>
        </div>
      </div>

      <button
        onClick={handleDisconnect}
        disabled={disconnecting}
        className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors font-sans disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {disconnecting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Disconnecting...
          </>
        ) : (
          <>
            <X size={16} />
            Disconnect Google
          </>
        )}
      </button>

      {status.connected_at && (
        <p className="mt-4 text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">
          Connected on {new Date(status.connected_at).toLocaleDateString()}
        </p>
      )}
    </div>
  )
}
