'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  processing_ms?: number
  message_id?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [connectionError, setConnectionError] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const router = useRouter()
  const { user } = useAuth()

  // Get token from localStorage (AuthContext stores it there)
  const getToken = useCallback(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token')
    }
    return null
  }, [])

  // Redirect to login if not authenticated
  useEffect(() => {
    // Wait for AuthContext to initialize
    if (user === null) return
    if (user.isAnonymous || !user.user_id) {
      router.push('/login')
    }
  }, [user, router])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input after loading completes
  useEffect(() => {
    if (!loading) {
      inputRef.current?.focus()
    }
  }, [loading])

  const sendMessage = async () => {
    const text = input.trim()
    const token = getToken()
    if (!text || loading) return

    if (!token) {
      router.push('/login')
      return
    }

    const userMsg: Message = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    setConnectionError(false)

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
        }),
      })

      if (res.status === 401) {
        localStorage.removeItem('token')
        router.push('/login')
        return
      }

      const data = await res.json()

      // Store session_id for conversation continuity
      if (data.session_id) {
        setSessionId(data.session_id)
      }

      const assistantMsg: Message = {
        role: 'assistant',
        content: data.reply || data.error || 'Intet svar',
        timestamp: new Date().toISOString(),
        processing_ms: data.processing_time_ms,
        message_id: data.message_id,
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch {
      setConnectionError(true)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Kunne ikke forbinde til serveren. Tjek din forbindelse og proev igen.',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
    setSessionId(null)
    setConnectionError(false)
    inputRef.current?.focus()
  }

  // Show nothing until auth state is resolved
  if (!user || user.isAnonymous || !user.user_id) return null

  return (
    <div className="flex flex-col h-[100dvh] bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="flex-shrink-0 px-4 py-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between safe-area-top">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push('/')} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 p-1 -ml-1 touch-manipulation">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">KV1NT Chat</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {loading ? 'Taenker...' : connectionError ? 'Forbindelsesfejl' : 'Online'}
            </p>
          </div>
        </div>
        <button
          onClick={clearChat}
          className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 px-3 py-2 touch-manipulation"
        >
          Ny chat
        </button>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 overscroll-contain">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <div className="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Hej{user.display_name ? `, ${user.display_name}` : ''}!</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm">
              Jeg kan hjaelpe med research, dokumenter, kalender, juridisk og meget mere. Skriv din besked nedenfor.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-md'
                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-md shadow-sm'
            }`}>
              <p className="text-sm whitespace-pre-wrap leading-relaxed break-words">{msg.content}</p>
              {msg.processing_ms != null && msg.processing_ms > 0 && (
                <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                  {(msg.processing_ms / 1000).toFixed(1)}s
                </p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 px-4 py-3 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 safe-area-bottom">
        <div className="flex items-end gap-2 max-w-2xl mx-auto">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 px-4 py-3 text-base text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Skriv en besked..."
            disabled={loading}
            autoComplete="off"
            style={{ maxHeight: '120px' }}
            onInput={e => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="flex-shrink-0 w-11 h-11 rounded-full bg-blue-600 text-white flex items-center justify-center disabled:opacity-40 hover:bg-blue-700 active:bg-blue-800 transition-colors touch-manipulation"
          >
            {loading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            )}
          </button>
        </div>
        <p className="text-center text-xs text-gray-400 mt-2">KV1NT AI — Gemini 2.5 Flash</p>
      </div>
    </div>
  )
}
