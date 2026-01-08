'use client'

import { useState, useEffect, forwardRef, useImperativeHandle } from 'react'
import { createPortal } from 'react-dom'
import { Loader2, RefreshCw } from 'lucide-react'
import MemoryModal from './MemoryModal'
import { motion } from 'framer-motion'

interface Memory {
  memory_id: string
  memory: string
  input: string | null
  topics: string[]
  updated_at: string | null
  agent_id: string | null
  team_id: string | null
}

interface MemoriesResponse {
  success: boolean
  count: number
  memories: Memory[]
}

export interface MemoriesRef {
  refresh: () => void
  isLoading: boolean
}

const Memories = forwardRef<MemoriesRef>((props, ref) => {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    fetchMemories()
  }, [])

  // Expose refresh function to parent via ref
  useImperativeHandle(ref, () => ({
    refresh: fetchMemories,
    isLoading: loading
  }))

  const fetchMemories = async () => {
    try {
      setLoading(true)
      setError(null)

      const token = localStorage.getItem('token')

      // Check if user is logged in
      if (!token) {
        setLoading(false)
        setError('auth')
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

      const response = await fetch(`${apiUrl}/api/user/memories`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch memories: ${response.statusText}`)
      }

      const data: MemoriesResponse = await response.json()
      setMemories(data.memories)
    } catch (err) {
      console.error('Error fetching memories:', err)
      setError(err instanceof Error ? err.message : 'Failed to load memories')
    } finally {
      setLoading(false)
    }
  }

  const truncateMemory = (text: string, maxLength: number = 60) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-5 h-5 text-accent animate-spin" />
      </div>
    )
  }

  if (error) {
    // Special handling for authentication error
    if (error === 'auth') {
      return (
        <div className="px-4 py-8 text-center">
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Please login or signup to enable persistent memories
          </p>
        </div>
      )
    }

    return (
      <div className="px-4 py-4 space-y-3">
        <p className="text-xs text-red-600 dark:text-red-400 text-center">{error}</p>
        <button
          onClick={fetchMemories}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg bg-accent hover:bg-accent/90 text-white transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Try Again
        </button>
      </div>
    )
  }

  if (memories.length === 0) {
    return (
      <div className="px-4 py-8 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
          No memories yet
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500">
          Start chatting to build your memory profile
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-1 px-2">
        {/* Memory list */}
        {memories.map((memory) => (
          <motion.button
            key={memory.memory_id}
            onClick={() => setSelectedMemory(memory)}
            className="w-full px-3 py-2.5 text-left rounded-lg transition-colors group flex items-center gap-3 border border-border-primary bg-light-bg hover:border-border-primary dark:bg-dark-bg"
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.15 }}
          >
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate text-[#6b6b6b] dark:text-[#a0a0a0]">
                {truncateMemory(memory.memory, 80)}
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Memory Detail Modal - Rendered via Portal */}
      {mounted && selectedMemory && createPortal(
        <MemoryModal
          memory={selectedMemory}
          onClose={() => setSelectedMemory(null)}
        />,
        document.body
      )}
    </>
  )
})

Memories.displayName = 'Memories'

export default Memories
