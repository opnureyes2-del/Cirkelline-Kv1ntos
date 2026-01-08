'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ArrowUpDown, ChevronLeft, ChevronRight, Brain, Clock, Trash2, Tag, X } from 'lucide-react'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'

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

export default function MemoriesPage() {
  // Use environment variable for API endpoint
  const endpoint = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // State
  const [memories, setMemories] = useState<Memory[]>([])
  const [filteredMemories, setFilteredMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(18) // 18 memories per page (3x6 grid)

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'updated_at' | 'memory'>('updated_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [showAllTopics, setShowAllTopics] = useState(false)

  // Extract unique topics with counts (for topic cloud)
  const topicCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    memories.forEach(m => m.topics?.forEach(t => {
      counts[t] = (counts[t] || 0) + 1
    }))
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
  }, [memories])

  // Modal
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Load memories
  const loadMemories = useCallback(async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')

      if (!token) {
        toast.error('Please log in to view memories')
        setLoading(false)
        return
      }

      const response = await fetch(`${endpoint}/api/user/memories`, {
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
    } catch (error) {
      console.error('Failed to load memories:', error)
      toast.error('Failed to load memories')
      setMemories([])
    } finally {
      setLoading(false)
    }
  }, [endpoint])

  // Load on mount
  useEffect(() => {
    loadMemories()
  }, [loadMemories])

  // Filter and sort memories
  useEffect(() => {
    let filtered = [...memories]

    // Apply topic filter
    if (selectedTopics.length > 0) {
      filtered = filtered.filter(memory =>
        selectedTopics.some(topic => memory.topics?.includes(topic))
      )
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(memory =>
        memory.memory.toLowerCase().includes(query) ||
        memory.topics?.some(topic => topic.toLowerCase().includes(query))
      )
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'updated_at') {
        const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0
        const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB
      } else {
        // Sort by memory content
        const comparison = a.memory.localeCompare(b.memory)
        return sortOrder === 'desc' ? -comparison : comparison
      }
    })

    setFilteredMemories(filtered)
    setCurrentPage(1) // Reset to first page when filters change
  }, [memories, searchQuery, sortBy, sortOrder, selectedTopics])

  // Pagination
  const totalPages = Math.ceil(filteredMemories.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedMemories = filteredMemories.slice(startIndex, endIndex)

  // Modal handlers
  const handleOpenMemory = (memory: Memory) => {
    setSelectedMemory(memory)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setSelectedMemory(null)
  }

  // Delete memory handler
  const handleDeleteMemory = async (memoryId: string) => {
    if (!confirm('Are you sure you want to delete this memory? This action cannot be undone.')) {
      return
    }

    setIsDeleting(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Please log in to delete memories')
        return
      }

      const response = await fetch(`${endpoint}/api/user/memories/${memoryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to delete memory')
      }

      toast.success('Memory deleted successfully')

      // Remove from local state
      setMemories(prev => prev.filter(m => m.memory_id !== memoryId))

      // Close modal
      handleCloseModal()
    } catch (error) {
      console.error('Failed to delete memory:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to delete memory')
    } finally {
      setIsDeleting(false)
    }
  }

  // Truncate text
  const truncateText = (text: string, maxLength: number = 150) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  // Toggle topic filter
  const toggleTopic = (topic: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    setSelectedTopics(prev =>
      prev.includes(topic)
        ? prev.filter(t => t !== topic)
        : [...prev, topic]
    )
  }

  // Clear all topic filters
  const clearTopicFilters = () => {
    setSelectedTopics([])
  }

  return (
    <div className="min-h-screen bg-light-bg dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading mb-2">
            Memories
          </h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary">
            {loading ? 'Loading...' : `${filteredMemories.length} memor${filteredMemories.length !== 1 ? 'ies' : 'y'}${selectedTopics.length > 0 ? ` (filtered)` : ''}`}
          </p>
        </motion.div>

        {/* Topic Cloud */}
        {!loading && topicCounts.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.05 }}
            className="mb-6"
          >
            <div className="flex items-center gap-2 mb-3">
              <Tag size={16} className="text-light-text-secondary dark:text-dark-text-secondary" />
              <span className="text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">
                Filter by Topic
              </span>
              {selectedTopics.length > 0 && (
                <button
                  onClick={clearTopicFilters}
                  className="ml-2 text-xs px-2 py-0.5 rounded-full
                           bg-accent/10 text-accent hover:bg-accent/20
                           transition-colors flex items-center gap-1"
                >
                  <X size={12} />
                  Clear ({selectedTopics.length})
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {(showAllTopics ? topicCounts : topicCounts.slice(0, 20)).map(([topic, count]) => {
                const isSelected = selectedTopics.includes(topic)
                return (
                  <button
                    key={topic}
                    onClick={() => toggleTopic(topic)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all
                              ${isSelected
                                ? 'bg-accent text-white border border-accent'
                                : 'bg-light-surface dark:bg-dark-surface border border-border-primary hover:border-accent/50'
                              }`}
                  >
                    {topic} <span className={isSelected ? 'text-white/70' : 'text-light-text-secondary dark:text-dark-text-secondary'}>({count})</span>
                  </button>
                )
              })}
              {topicCounts.length > 20 && (
                <button
                  onClick={() => setShowAllTopics(!showAllTopics)}
                  className="px-3 py-1.5 text-xs font-medium text-accent hover:text-accent/80
                           hover:bg-accent/10 rounded-full transition-colors"
                >
                  {showAllTopics ? 'Show less' : `+${topicCounts.length - 20} more`}
                </button>
              )}
            </div>
          </motion.div>
        )}

        {/* Active Filters Display */}
        {selectedTopics.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-3 rounded-lg bg-accent/5 border border-accent/20"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                  Showing memories with:
                </span>
                {selectedTopics.map(topic => (
                  <span
                    key={topic}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs
                             bg-accent text-white"
                  >
                    {topic}
                    <button
                      onClick={() => toggleTopic(topic)}
                      className="hover:bg-white/20 rounded-full p-0.5 transition-colors"
                    >
                      <X size={10} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Controls Bar */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="mb-6 flex flex-col sm:flex-row gap-4"
        >
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary" size={18} />
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       placeholder:text-light-text-secondary dark:placeholder:text-dark-text-secondary
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all"
            />
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [newSortBy, newSortOrder] = e.target.value.split('-') as [typeof sortBy, typeof sortOrder]
                setSortBy(newSortBy)
                setSortOrder(newSortOrder)
              }}
              className="appearance-none pl-10 pr-10 py-2.5 rounded-lg
                       bg-light-surface dark:bg-dark-surface
                       border border-border-primary
                       text-light-text dark:text-dark-text
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent
                       transition-all cursor-pointer"
            >
              <option value="updated_at-desc">Recently Updated</option>
              <option value="updated_at-asc">Least Recent</option>
              <option value="memory-asc">Content A-Z</option>
              <option value="memory-desc">Content Z-A</option>
            </select>
            <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 text-light-text-secondary dark:text-dark-text-secondary pointer-events-none" size={18} />
          </div>
        </motion.div>

        {/* Memories List */}
        {loading ? (
          // Loading Skeletons
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-32 rounded-lg bg-light-surface/50 dark:bg-dark-surface/50
                         border border-border-primary animate-pulse"
              />
            ))}
          </div>
        ) : paginatedMemories.length === 0 ? (
          // Empty State
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="text-center py-16"
          >
            <Brain className="mx-auto mb-4 text-light-text-secondary dark:text-dark-text-secondary" size={64} />
            <h3 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2">
              No memories found
            </h3>
            <p className="text-light-text-secondary dark:text-dark-text-secondary mb-6">
              {searchQuery ? 'Try adjusting your search' : 'Have conversations to build memories'}
            </p>
          </motion.div>
        ) : (
          // Memories List
          <div className="space-y-3 mb-8">
            {paginatedMemories.map((memory, index) => {
              const updatedAt = memory.updated_at
                ? formatDistanceToNow(new Date(memory.updated_at), { addSuffix: true })
                : 'Unknown'

              return (
                <motion.div
                  key={memory.memory_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.2 }}
                  onClick={() => handleOpenMemory(memory)}
                  className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary
                           overflow-hidden hover:border-accent/50 transition-all cursor-pointer
                           hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary"
                >
                  <div className="p-4">
                    {/* Memory Content */}
                    <div className="mb-3">
                      <p className="text-sm text-light-text dark:text-dark-text leading-relaxed">
                        {truncateText(memory.memory)}
                      </p>
                    </div>

                    {/* Topics */}
                    {memory.topics && memory.topics.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {memory.topics.map((topic, idx) => {
                          const isFiltered = selectedTopics.includes(topic)
                          return (
                            <button
                              key={idx}
                              onClick={(e) => toggleTopic(topic, e)}
                              className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all
                                       ${isFiltered
                                         ? 'bg-accent text-white border border-accent'
                                         : 'bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20'
                                       }`}
                            >
                              {topic}
                            </button>
                          )
                        })}
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-3 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      <span className="flex items-center gap-1">
                        <Clock size={12} />
                        {updatedAt}
                      </span>
                      {memory.agent_id && (
                        <span className="text-xs">
                          Agent: {memory.agent_id}
                        </span>
                      )}
                      {memory.team_id && (
                        <span className="text-xs">
                          Team: {memory.team_id}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Pagination */}
        {!loading && paginatedMemories.length > 0 && totalPages > 1 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="flex items-center justify-center gap-2"
          >
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-2 rounded-lg border border-border-primary
                       bg-light-surface dark:bg-dark-surface
                       text-light-text dark:text-dark-text
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-accent/10 hover:border-accent/30
                       transition-all"
            >
              <ChevronLeft size={20} />
            </button>

            <span className="px-4 py-2 text-sm text-light-text dark:text-dark-text">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-2 rounded-lg border border-border-primary
                       bg-light-surface dark:bg-dark-surface
                       text-light-text dark:text-dark-text
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:bg-accent/10 hover:border-accent/30
                       transition-all"
            >
              <ChevronRight size={20} />
            </button>
          </motion.div>
        )}
      </div>

      {/* Memory Detail Modal */}
      <AnimatePresence>
        {isModalOpen && selectedMemory && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={handleCloseModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary
                       max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl"
            >
              {/* Modal Header */}
              <div className="sticky top-0 bg-light-surface dark:bg-dark-surface border-b border-border-primary p-6 z-10">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h2 className="text-xl font-bold text-light-text dark:text-dark-text mb-2">
                      Memory Details
                    </h2>
                    <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      {selectedMemory.updated_at
                        ? `Updated ${formatDistanceToNow(new Date(selectedMemory.updated_at), { addSuffix: true })}`
                        : 'No update date'}
                    </p>
                  </div>
                  <button
                    onClick={handleCloseModal}
                    className="ml-4 p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg
                             text-light-text-secondary dark:text-dark-text-secondary
                             hover:text-light-text dark:hover:text-dark-text transition-all"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Memory Content */}
                <div>
                  <h3 className="text-sm font-semibold text-light-text-secondary dark:text-dark-text-secondary mb-2">
                    Memory
                  </h3>
                  <p className="text-light-text dark:text-dark-text leading-relaxed whitespace-pre-wrap">
                    {selectedMemory.memory}
                  </p>
                </div>

                {/* Original Input */}
                {selectedMemory.input && (
                  <div>
                    <h3 className="text-sm font-semibold text-light-text-secondary dark:text-dark-text-secondary mb-2">
                      Original Input
                    </h3>
                    <p className="text-light-text dark:text-dark-text leading-relaxed whitespace-pre-wrap">
                      {selectedMemory.input}
                    </p>
                  </div>
                )}

                {/* Topics */}
                {selectedMemory.topics && selectedMemory.topics.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-light-text-secondary dark:text-dark-text-secondary mb-2">
                      Topics (click to filter)
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedMemory.topics.map((topic, idx) => {
                        const isFiltered = selectedTopics.includes(topic)
                        return (
                          <button
                            key={idx}
                            onClick={() => {
                              toggleTopic(topic)
                              handleCloseModal()
                            }}
                            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all
                                     ${isFiltered
                                       ? 'bg-accent text-white border border-accent'
                                       : 'bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20'
                                     }`}
                          >
                            {topic}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                <div className="pt-4 border-t border-border-primary">
                  <h3 className="text-sm font-semibold text-light-text-secondary dark:text-dark-text-secondary mb-3">
                    Metadata
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-light-text-secondary dark:text-dark-text-secondary">Memory ID:</span>
                      <span className="text-light-text dark:text-dark-text font-mono text-xs">
                        {selectedMemory.memory_id}
                      </span>
                    </div>
                    {selectedMemory.agent_id && (
                      <div className="flex justify-between">
                        <span className="text-light-text-secondary dark:text-dark-text-secondary">Agent ID:</span>
                        <span className="text-light-text dark:text-dark-text">{selectedMemory.agent_id}</span>
                      </div>
                    )}
                    {selectedMemory.team_id && (
                      <div className="flex justify-between">
                        <span className="text-light-text-secondary dark:text-dark-text-secondary">Team ID:</span>
                        <span className="text-light-text dark:text-dark-text">{selectedMemory.team_id}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="sticky bottom-0 bg-light-surface dark:bg-dark-surface border-t border-border-primary p-6">
                <div className="flex gap-3">
                  <button
                    onClick={() => handleDeleteMemory(selectedMemory.memory_id)}
                    disabled={isDeleting}
                    className="flex-1 px-4 py-2.5 rounded-lg
                             bg-red-500/10 hover:bg-red-500/20
                             text-red-500 font-medium
                             border border-red-500/20 hover:border-red-500/40
                             disabled:opacity-50 disabled:cursor-not-allowed
                             transition-colors flex items-center justify-center gap-2"
                  >
                    <Trash2 size={16} />
                    {isDeleting ? 'Deleting...' : 'Delete Memory'}
                  </button>
                  <button
                    onClick={handleCloseModal}
                    className="flex-1 px-4 py-2.5 rounded-lg
                             bg-accent hover:bg-accent/90
                             text-white font-medium
                             transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
