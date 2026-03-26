'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

interface Stats {
  conversations_started: number
  messages_sent: number
  messages_received: number
  documents_uploaded: number
  memories_captured: number
}

interface Session {
  session_id: string
  created_at: number
  session_name: string | null
}

interface Memory {
  id: string
  content: string
  created_at: string
  category: string
}

async function apiFetch(path: string, token: string) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Authorization': `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}

export default function DashboardPage() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [userName, setUserName] = useState('')
  const [stats, setStats] = useState<Stats | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [memories, setMemories] = useState<Memory[]>([])
  const [subscription, setSubscription] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const t = localStorage.getItem('token')
    if (!t) { router.push('/login'); return }
    setToken(t)
    try {
      const payload = JSON.parse(atob(t.split('.')[1]))
      setUserName(payload.display_name || payload.user_name || payload.email || '')
    } catch {}
  }, [router])

  useEffect(() => {
    if (!token) return
    const load = async () => {
      try {
        const [statsData, sessionsData, memoriesData, subData] = await Promise.all([
          apiFetch('/api/user/statistics', token),
          apiFetch('/sessions', token),
          apiFetch('/api/user/memories', token),
          apiFetch('/api/user/subscription', token),
        ])
        setStats(statsData.statistics)
        setSessions(statsData.recent_activity?.length ? [] : (sessionsData.data || sessionsData || []))
        setMemories((memoriesData.memories || []).slice(0, 5))
        setSubscription(subData.subscription)
      } catch (err: any) {
        if (err.message === '401') { localStorage.removeItem('token'); router.push('/login') }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token, router])

  if (!token) return null

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 6) return 'God nat'
    if (h < 12) return 'God morgen'
    if (h < 18) return 'God eftermiddag'
    return 'God aften'
  }

  return (
    <div className="min-h-[100dvh] bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 py-4">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              {greeting()}, {userName || 'bruger'}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {subscription?.tier?.name || 'Member'} — {stats?.conversations_started || 0} samtaler
            </p>
          </div>
          <Link href="/profile" className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold text-sm">
            {(userName || '?')[0].toUpperCase()}
          </Link>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-3">
          <Link href="/chat" className="flex items-center gap-3 p-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            <div>
              <p className="font-semibold text-sm">Ny chat</p>
              <p className="text-xs text-blue-200">Start samtale</p>
            </div>
          </Link>
          <Link href="/profile/documents" className="flex items-center gap-3 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-gray-300 transition-colors">
            <svg className="w-6 h-6 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            <div>
              <p className="font-semibold text-sm text-gray-900 dark:text-white">Dokumenter</p>
              <p className="text-xs text-gray-500">{stats?.documents_uploaded || 0} uploadet</p>
            </div>
          </Link>
        </div>

        {/* Stats */}
        {loading ? (
          <div className="grid grid-cols-2 gap-3">
            {[1,2,3,4].map(i => <div key={i} className="h-20 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse" />)}
          </div>
        ) : stats && (
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.messages_sent}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Beskeder sendt</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.conversations_started}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Samtaler</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.documents_uploaded}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Dokumenter</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.memories_captured}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Minder gemt</p>
            </div>
          </div>
        )}

        {/* Recent Sessions */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h2 className="font-semibold text-sm text-gray-900 dark:text-white">Seneste sessioner</h2>
            <Link href="/profile/sessions" className="text-xs text-blue-600 hover:text-blue-700">Se alle</Link>
          </div>
          {sessions.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500">
              Ingen sessioner endnu — <Link href="/chat" className="text-blue-600 underline">start en chat</Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {sessions.slice(0, 5).map((s, i) => (
                <div key={i} className="px-4 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {s.session_name || `Session ${s.session_id.slice(0, 8)}`}
                    </p>
                    <p className="text-xs text-gray-500">{new Date(s.created_at * 1000).toLocaleDateString('da-DK')}</p>
                  </div>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Memories */}
        {memories.length > 0 && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
              <h2 className="font-semibold text-sm text-gray-900 dark:text-white">Minder</h2>
              <Link href="/profile/memories" className="text-xs text-blue-600 hover:text-blue-700">Se alle</Link>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {memories.map((m, i) => (
                <div key={i} className="px-4 py-3">
                  <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">{m.content}</p>
                  <p className="text-xs text-gray-400 mt-1">{m.category}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Nav */}
        <nav className="grid grid-cols-3 gap-2 pt-2 pb-8">
          {[
            { href: '/profile/preferences', label: 'Indstillinger', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
            { href: '/profile/integrations', label: 'Google', icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1' },
            { href: '/profile/security', label: 'Sikkerhed', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
          ].map(({ href, label, icon }) => (
            <Link key={href} href={href} className="flex flex-col items-center gap-1.5 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-gray-300 transition-colors">
              <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={icon} /></svg>
              <span className="text-xs text-gray-600 dark:text-gray-400">{label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </div>
  )
}
