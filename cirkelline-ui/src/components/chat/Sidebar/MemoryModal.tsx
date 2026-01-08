'use client'

import { X, Calendar, Tag, FileText, Brain } from 'lucide-react'

interface Memory {
  memory_id: string
  memory: string
  input: string | null
  topics: string[]
  updated_at: string | null
  agent_id: string | null
  team_id: string | null
}

interface MemoryModalProps {
  memory: Memory
  onClose: () => void
}

export default function MemoryModal({ memory, onClose }: MemoryModalProps) {
  const formatDate = (timestamp: string | null) => {
    if (!timestamp) return 'Unknown'
    try {
      const date = new Date(timestamp)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Invalid date'
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-[100] animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[101] w-[95vw] sm:w-[85vw] md:w-[75vw] lg:w-[65vw] max-w-3xl max-h-[90vh] sm:max-h-[85vh] overflow-y-auto animate-in zoom-in-95 duration-200">
        <div className="bg-light-surface dark:bg-dark-surface rounded-lg shadow-xl border border-border-primary">
          {/* Header */}
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-border-secondary">
            <div className="flex items-center gap-2 sm:gap-3">
              <Brain className="w-5 h-5 sm:w-6 sm:h-6 text-accent" />
              <h2 className="text-lg sm:text-xl font-semibold text-light-text dark:text-dark-text font-heading">
                Memory Details
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary text-light-text-secondary dark:text-dark-text-secondary transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
            {/* Memory Content */}
            <div>
              <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-2 font-body">
                What Cirkelline Learned:
              </h3>
              <p className="text-base text-light-text dark:text-dark-text leading-relaxed bg-accent/10 p-4 rounded-lg font-body">
                {memory.memory}
              </p>
            </div>

            {/* Original Input */}
            {memory.input && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                  <h3 className="text-sm font-semibold text-light-text dark:text-dark-text font-body">
                    From Conversation:
                  </h3>
                </div>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary italic bg-light-bg-secondary dark:bg-dark-bg-secondary p-4 rounded-lg font-body">
                  &quot;{memory.input}&quot;
                </p>
              </div>
            )}

            {/* Topics */}
            {memory.topics && memory.topics.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Tag className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                  <h3 className="text-sm font-semibold text-light-text dark:text-dark-text font-body">
                    Topics:
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {memory.topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-accent/10 text-accent rounded-full text-sm font-mono font-medium"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="pt-4 border-t border-border-secondary">
              <div className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
                <Calendar className="w-4 h-4" />
                <span>{formatDate(memory.updated_at)}</span>
              </div>

              {/* Technical Details */}
              {(memory.agent_id || memory.team_id) && (
                <details className="mt-3">
                  <summary className="cursor-pointer text-xs text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text font-body">
                    Technical details
                  </summary>
                  <div className="mt-2 p-3 bg-light-bg-secondary dark:bg-dark-bg-secondary rounded text-xs text-light-text-secondary dark:text-dark-text-secondary space-y-1 font-mono">
                    <div>
                      <span className="font-semibold">ID:</span> {memory.memory_id.substring(0, 8)}...
                    </div>
                    {memory.agent_id && (
                      <div>
                        <span className="font-semibold">Agent:</span> {memory.agent_id}
                      </div>
                    )}
                    {memory.team_id && (
                      <div>
                        <span className="font-semibold">Team:</span> {memory.team_id}
                      </div>
                    )}
                  </div>
                </details>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
