import MarkdownRenderer from '@/components/ui/typography/MarkdownRenderer'
import { useStore } from '@/store'
import type { ChatMessage } from '@/types/os'
import Videos from './Multimedia/Videos'
import Images from './Multimedia/Images'
import Audios from './Multimedia/Audios'
import { memo, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Copy, ThumbsUp, ThumbsDown, Check, Send } from 'lucide-react'
import FeedbackModal from '@/components/chat/FeedbackModal'
import { useAuth } from '@/contexts/AuthContext'
import { useQueryState } from 'nuqs'
import { toast } from 'sonner'
import { useStreamingText } from '@/hooks/useStreamingText'
import { getAuthHeaders } from '@/lib/auth-headers'
import { constructEndpointUrl } from '@/lib/constructEndpointUrl'

interface MessageProps {
  message: ChatMessage
}

interface AgentMessageProps extends MessageProps {
  showAvatar?: boolean
  hideActions?: boolean
  isStreaming?: boolean
}

const AgentMessage = ({ message, hideActions = false, isStreaming = false }: AgentMessageProps) => {
  const { streamingErrorMessage, selectedEndpoint, setMessages, setIsStreaming, setActivityStatus } = useStore()
  const { user } = useAuth()
  const [sessionId] = useQueryState('session')
  const [isHovered, setIsHovered] = useState(false)
  const [isCopied, setIsCopied] = useState(false)
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false)
  const [feedbackType, setFeedbackType] = useState<'positive' | 'negative' | null>(null)

  // HITL (Human-in-the-Loop) state
  const [hitlInputs, setHitlInputs] = useState<Record<string, string>>({})
  const [hitlSubmitting, setHitlSubmitting] = useState(false)

  // Handle HITL form submission
  const handleHitlSubmit = useCallback(async () => {
    if (!message.hitlRunId || !message.hitlSessionId) return

    setHitlSubmitting(true)
    setActivityStatus('Processing your input...')

    try {
      const endpointUrl = constructEndpointUrl(selectedEndpoint)
      const continueUrl = `${endpointUrl}/teams/cirkelline/runs/${message.hitlRunId}/continue`

      const formData = new FormData()
      formData.append('session_id', message.hitlSessionId)
      formData.append('user_input', JSON.stringify(hitlInputs))
      formData.append('stream', 'true')

      const response = await fetch(continueUrl, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      })

      if (!response.ok) {
        throw new Error('Failed to continue run')
      }

      // Update the message to clear HITL state
      setMessages((prevMessages: ChatMessage[]) => {
        return prevMessages.map((msg: ChatMessage) => {
          if (msg.hitlRunId === message.hitlRunId) {
            return {
              ...msg,
              hitlPaused: false,
              content: msg.content + '\n\n*Processing your input...*'
            }
          }
          return msg
        })
      })

      // Process the streaming response
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        setIsStreaming(true)
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Parse SSE events
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))

                // Handle content events
                if (data.event === 'TeamRunContent' || data.event === 'RunContent') {
                  const content = data.content
                  if (typeof content === 'string') {
                    setMessages((prevMessages: ChatMessage[]) => {
                      const newMessages = [...prevMessages]
                      const lastMessage = newMessages[newMessages.length - 1]
                      if (lastMessage && lastMessage.role === 'agent') {
                        lastMessage.content = content
                      }
                      return newMessages
                    })
                  }
                }

                // Handle another pause
                if (data.event === 'paused') {
                  console.log('⏸️ HITL: Another pause detected', data)
                  // The streaming handler will handle this
                }
              } catch {
                // Ignore parse errors
              }
            }
          }
        }
      }

      toast.success('Input submitted successfully')
    } catch (error) {
      console.error('HITL submit error:', error)
      toast.error('Failed to submit input. Please try again.')
    } finally {
      setHitlSubmitting(false)
      setIsStreaming(false)
      setActivityStatus(null)
    }
  }, [message.hitlRunId, message.hitlSessionId, hitlInputs, selectedEndpoint, setMessages, setIsStreaming, setActivityStatus])

  // Apply typewriter animation only for streaming messages
  const animatedContent = useStreamingText(message.content || '', 2)
  const displayedContent = isStreaming ? animatedContent : message.content

  // Apply typewriter animation for audio transcript if streaming
  const animatedTranscript = useStreamingText(message.response_audio?.transcript || '', 2)
  const displayedTranscript = isStreaming ? animatedTranscript : message.response_audio?.transcript

  const handleCopy = async () => {
    const textToCopy = message.content || message.response_audio?.transcript || ''
    try {
      await navigator.clipboard.writeText(textToCopy)
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleFeedback = (type: 'up' | 'down') => {
    // Check if user is authenticated
    if (!user || user.isAnonymous) {
      toast.error('Please log in to submit feedback')
      return
    }

    // Set feedback state for visual feedback
    setFeedback(type)

    // Open feedback modal
    setFeedbackType(type === 'up' ? 'positive' : 'negative')
    setFeedbackModalOpen(true)
  }

  let messageContent
  if (message.streamingError) {
    messageContent = (
      <p className="text-destructive">
        Oops! Something went wrong while streaming.{' '}
        {streamingErrorMessage ? (
          <>{streamingErrorMessage}</>
        ) : (
          'Please try refreshing the page or try again later.'
        )}
      </p>
    )
  } else if (message.content) {
    messageContent = (
      <div className="flex w-full flex-col gap-4">
        <MarkdownRenderer>{displayedContent}</MarkdownRenderer>
        {message.videos && message.videos.length > 0 && (
          <Videos videos={message.videos} />
        )}
        {message.images && message.images.length > 0 && (
          <Images images={message.images} />
        )}
        {message.audio && message.audio.length > 0 && (
          <Audios audio={message.audio} />
        )}
      </div>
    )
  } else if (message.response_audio) {
    if (!message.response_audio.transcript) {
      messageContent = null // No content when thinking
    } else {
      messageContent = (
        <div className="flex w-full flex-col gap-4">
          <MarkdownRenderer>
            {displayedTranscript}
          </MarkdownRenderer>
          {message.response_audio.content && message.response_audio && (
            <Audios audio={[message.response_audio]} />
          )}
        </div>
      )
    }
  } else {
    messageContent = null // No content when thinking
  }

  return (
    <motion.div
      className="flex flex-row items-start gap-3 font-body group"
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Content area - only render when there's actual content */}
      {messageContent && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className={`flex-1 relative ${!hideActions ? 'pb-10' : ''}`}
        >
          <div
            className={`
              flex flex-col gap-2 rounded-lg p-3 -ml-3 transition-colors duration-200
              border
              ${!hideActions && isHovered ? 'border-border-primary' : 'border-transparent'}
            `}
          >
            {/* Message content */}
            <div className="relative">
              {messageContent}
            </div>

            {/* HITL Input Form */}
            {message.hitlPaused && message.hitlRequirements && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 rounded-lg bg-light-bg dark:bg-dark-bg border border-border-primary"
              >
                <div className="space-y-4">
                  {message.hitlRequirements
                    .filter(req => req.needs_user_input)
                    .flatMap(req => req.user_input_schema || [])
                    .map((field, index) => (
                      <div key={index} className="space-y-2">
                        <label className="block text-sm font-medium text-light-text dark:text-dark-text">
                          {field.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </label>
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                          {field.description}
                        </p>
                        {field.field_type === 'bool' ? (
                          <select
                            className="w-full px-3 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                            value={hitlInputs[field.name] || ''}
                            onChange={(e) => setHitlInputs(prev => ({ ...prev, [field.name]: e.target.value }))}
                          >
                            <option value="">Select...</option>
                            <option value="true">Yes</option>
                            <option value="false">No</option>
                          </select>
                        ) : (
                          <input
                            type={field.field_type === 'int' || field.field_type === 'float' ? 'number' : 'text'}
                            className="w-full px-3 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                            placeholder={field.description}
                            value={hitlInputs[field.name] || ''}
                            onChange={(e) => setHitlInputs(prev => ({ ...prev, [field.name]: e.target.value }))}
                          />
                        )}
                      </div>
                    ))}

                  <button
                    onClick={handleHitlSubmit}
                    disabled={hitlSubmitting}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {hitlSubmitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send size={16} />
                        Submit
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </div>

          {/* Action buttons - only show on hover */}
          {!hideActions && isHovered && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.15 }}
            className="flex items-center gap-2 absolute bottom-0 right-0"
          >
              {/* Copy button */}
              <button
                onClick={handleCopy}
                className="p-2 rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                title="Copy message"
              >
                {isCopied ? (
                  <Check size={14} className="text-green-600 dark:text-green-400" />
                ) : (
                  <Copy size={14} className="text-light-text-secondary dark:text-dark-text-secondary" />
                )}
              </button>

              {/* Thumbs up */}
              <button
                onClick={() => handleFeedback('up')}
                className={`p-2 rounded-lg transition-colors ${
                  feedback === 'up'
                    ? 'bg-green-100 dark:bg-green-900/30'
                    : 'hover:bg-light-bg dark:hover:bg-dark-bg'
                }`}
                title="Good response"
              >
                <ThumbsUp
                  size={14}
                  className={
                    feedback === 'up'
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-light-text-secondary dark:text-dark-text-secondary'
                  }
                  fill={feedback === 'up' ? 'currentColor' : 'none'}
                />
              </button>

              {/* Thumbs down */}
              <button
                onClick={() => handleFeedback('down')}
                className={`p-2 rounded-lg transition-colors ${
                  feedback === 'down'
                    ? 'bg-red-100 dark:bg-red-900/30'
                    : 'hover:bg-light-bg dark:hover:bg-dark-bg'
                }`}
                title="Bad response"
              >
                <ThumbsDown
                  size={14}
                  className={
                    feedback === 'down'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-light-text-secondary dark:text-dark-text-secondary'
                  }
                  fill={feedback === 'down' ? 'currentColor' : 'none'}
                />
              </button>
            </motion.div>
          )}

        {/* Feedback Modal */}
        {feedbackModalOpen && feedbackType && (
          <FeedbackModal
            message={message}
            feedbackType={feedbackType}
            sessionId={sessionId}
            onClose={() => {
              setFeedbackModalOpen(false)
              setFeedbackType(null)
            }}
          />
        )}
        </motion.div>
      )}
    </motion.div>
  )
}

const UserMessage = memo(({ message }: MessageProps) => {
  const formatRelativeTime = (timestamp: number) => {
    const now = Math.floor(Date.now() / 1000)
    const diff = now - timestamp
    
    if (diff < 10) return 'Just now'
    if (diff < 60) return `${diff}s ago`
    if (diff < 3600) return `${Math.floor(diff / 60)}min ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
    return `${Math.floor(diff / 604800)}w ago`
  }

  return (
    <motion.div
      className="flex flex-col items-end pt-4 text-start max-md:break-words gap-1"
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      <motion.div
        initial={{ opacity: 0, x: 10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="max-w-[70%]"
      >
        <div className="px-4 py-3 rounded-lg text-sm font-body bg-[#E4E4E2] dark:bg-[#2A2A2A] text-gray-900 dark:text-white">
          {message.content}
        </div>
      </motion.div>
      <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
        {formatRelativeTime(message.created_at)}
      </div>
    </motion.div>
  )
})

AgentMessage.displayName = 'AgentMessage'
UserMessage.displayName = 'UserMessage'
export { AgentMessage, UserMessage }
