'use client'

import { useState, useEffect } from 'react'
import { BookOpen, Check, X, Loader2, Database, FileText, ListTodo } from 'lucide-react'

interface NotionStatus {
  connected: boolean
  workspace_name: string | null
  owner_email: string | null
  workspace_icon: string | null
  created_at: string | null
}

export default function NotionConnect() {
  const [status, setStatus] = useState<NotionStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [disconnecting, setDisconnecting] = useState(false)

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/oauth/notion/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (error) {
      console.error('Failed to fetch Notion status:', error)
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
    window.location.href = `${apiUrl}/api/oauth/notion/start?token=${token}`
  }

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect your Notion workspace?')) {
      return
    }

    setDisconnecting(true)
    try {
      const token = localStorage.getItem('token')
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

      const response = await fetch(`${apiUrl}/api/oauth/notion/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        setStatus({ connected: false, workspace_name: null, owner_email: null, workspace_icon: null, created_at: null })
      } else {
        alert('Failed to disconnect Notion workspace')
      }
    } catch (error) {
      console.error('Failed to disconnect:', error)
      alert('Failed to disconnect Notion workspace')
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
            <BookOpen className="w-6 h-6 text-accent" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading">
              Connect Notion Workspace
            </h3>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
              Access your Notion databases, projects, and tasks through Cirkelline
            </p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            <Database size={16} />
            <span>View and search companies</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            <FileText size={16} />
            <span>Access projects and documents</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            <ListTodo size={16} />
            <span>Create and manage tasks</span>
          </div>
        </div>

        <button
          onClick={handleConnect}
          className="w-full px-4 py-2 bg-accent hover:bg-accent/90 text-white rounded-lg font-medium transition-colors font-sans"
        >
          Connect to Notion
        </button>

        <p className="mt-4 text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">
          Cirkelline will request permission to access your Notion workspace. You can disconnect at any time.
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
            Notion Connected
          </h3>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            {status.workspace_icon && <span className="mr-1">{status.workspace_icon}</span>}
            {status.workspace_name} • {status.owner_email}
          </p>
        </div>
      </div>

      <div className="space-y-2 mb-6">
        <p className="text-sm font-medium text-light-text dark:text-dark-text font-body">
          Connected Features:
        </p>
        <div className="grid grid-cols-3 gap-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-light-bg dark:bg-dark-bg rounded-lg">
            <Database size={16} className="text-accent" />
            <span className="text-xs font-body text-light-text dark:text-dark-text">Companies</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 bg-light-bg dark:bg-dark-bg rounded-lg">
            <FileText size={16} className="text-accent" />
            <span className="text-xs font-body text-light-text dark:text-dark-text">Projects</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-2 bg-light-bg dark:bg-dark-bg rounded-lg">
            <ListTodo size={16} className="text-accent" />
            <span className="text-xs font-body text-light-text dark:text-dark-text">Tasks</span>
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
            Disconnect Notion
          </>
        )}
      </button>

      {status.created_at && (
        <p className="mt-4 text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">
          Connected on {new Date(status.created_at).toLocaleDateString()}
        </p>
      )}
    </div>
  )
}
