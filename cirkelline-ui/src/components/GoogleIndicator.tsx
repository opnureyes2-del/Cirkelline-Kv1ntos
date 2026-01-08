'use client'

import { useState, useEffect } from 'react'
import { Mail } from 'lucide-react'

export default function GoogleIndicator() {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
        const response = await fetch(`${apiUrl}/api/oauth/google/status`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })

        if (response.ok) {
          const data = await response.json()
          setConnected(data.connected)
        }
      } catch (error) {
        console.error('Failed to check Google status:', error)
      }
    }

    checkStatus()
  }, [])

  if (!connected) return null

  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 rounded-full border border-green-500/20"
      title="Google account connected"
    >
      <Mail size={14} className="text-green-600 dark:text-green-400" />
      <span className="text-xs font-medium text-green-600 dark:text-green-400 font-sans">
        Google Connected
      </span>
    </div>
  )
}
