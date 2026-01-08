import type { ChatMessage, BehindTheScenesEvent } from '@/types/os'

import { AgentMessage, UserMessage } from './MessageItem'
import Tooltip from '@/components/ui/tooltip/CustomTooltip'
import { memo, useMemo } from 'react'
import {
  ToolCallProps,
  ReasoningStepProps,
  ReasoningProps,
  ReferenceData,
  Reference
} from '@/types/os'
import React, { type FC } from 'react'

import Icon from '@/components/ui/icon'
import ChatBlankState from './ChatBlankState'
import BehindTheScenes from './BehindTheScenes'
import { useStore } from '@/store'
import { motion } from 'framer-motion'

interface MessageListProps {
  messages: ChatMessage[]
}

interface MessageWrapperProps {
  message: ChatMessage
  isLastMessage: boolean
  isLastAgentMessage: boolean
  isStreaming?: boolean
}

interface ReferenceProps {
  references: ReferenceData[]
}

interface ReferenceItemProps {
  reference: Reference
}

const ReferenceItem: FC<ReferenceItemProps> = ({ reference }) => (
  <div className="relative flex h-[63px] w-[190px] cursor-default flex-col justify-between overflow-hidden rounded-md bg-light-surface p-3 transition-colors hover:bg-light-bg dark:bg-dark-surface dark:hover:bg-dark-bg">
    <p className="text-sm font-medium text-accent">{reference.name}</p>
    <p className="truncate text-xs text-light-text-secondary dark:text-dark-text-secondary">{reference.content}</p>
  </div>
)

const References: FC<ReferenceProps> = ({ references }) => (
  <div className="flex flex-col gap-4">
    {references.map((referenceData, index) => (
      <div
        key={`${referenceData.query}-${index}`}
        className="flex flex-col gap-3"
      >
        <div className="flex flex-wrap gap-3">
          {referenceData.references.map((reference, refIndex) => (
            <ReferenceItem
              key={`${reference.name}-${reference.meta_data.chunk}-${refIndex}`}
              reference={reference}
            />
          ))}
        </div>
      </div>
    ))}
  </div>
)

const AgentMessageWrapper = ({ message, isLastAgentMessage, isStreaming = false }: MessageWrapperProps) => {
  // Determine visual style based on attribution
  const getSourceLabel = () => {
    if (message.agentName) return message.agentName
    if (message.teamName) return message.teamName
    return null
  }

  const getSourceColor = () => {
    if (message.agentName === 'Web Researcher') return 'text-green-500 dark:text-green-400'
    if (message.agentName === 'Research Analyst') return 'text-yellow-500 dark:text-yellow-400'
    if (message.teamName === 'Research Team') return 'text-purple-500 dark:text-purple-400'
    if (message.teamName === 'Law Team') return 'text-red-500 dark:text-red-400'
    if (message.teamName === 'Cirkelline') return 'text-blue-500 dark:text-blue-400'
    return 'text-accent'
  }

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

  const sourceLabel = getSourceLabel()
  const sourceColor = getSourceColor()

  return (
    <div className="flex flex-col gap-y-4">
      {/* Source Attribution Badge + Timestamp */}
      <div className="flex items-center gap-2 flex-wrap">
        {sourceLabel && sourceLabel !== 'Cirkelline' && (
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${sourceColor} bg-light-surface dark:bg-dark-surface border border-current/20`}>
            {sourceLabel}
          </div>
        )}
        <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
          {formatRelativeTime(message.created_at)}
        </div>
      </div>
      {message.extra_data?.reasoning_steps &&
        message.extra_data.reasoning_steps.length > 0 && (
          <div className="flex items-start gap-4">
            <Tooltip
              delayDuration={0}
              content={<p className="text-accent">Reasoning</p>}
              side="top"
            >
              <Icon type="reasoning" size="sm" />
            </Tooltip>
            <div className="flex flex-col gap-3">
              <p className="text-xs uppercase text-light-text dark:text-dark-text">Reasoning</p>
              <Reasonings reasoning={message.extra_data.reasoning_steps} />
            </div>
          </div>
        )}
      {message.extra_data?.references &&
        message.extra_data.references.length > 0 && (
          <div className="flex items-start gap-4">
            <Tooltip
              delayDuration={0}
              content={<p className="text-accent">References</p>}
              side="top"
            >
              <Icon type="references" size="sm" />
            </Tooltip>
            <div className="flex flex-col gap-3">
              <References references={message.extra_data.references} />
            </div>
          </div>
        )}
      {/* Tool badges hidden - causes activity indicator to disappear */}
      {/* {message.tool_calls && message.tool_calls.length > 0 && (
        <div className="flex items-start gap-3">
          <Tooltip
            delayDuration={0}
            content={<p className="text-accent">Tool Calls</p>}
            side="top"
          >
            <Icon
              type="hammer"
              className="rounded-lg bg-light-surface p-1 dark:bg-dark-surface"
              size="sm"
              color="secondary"
            />
          </Tooltip>

          <div className="flex flex-wrap gap-2">
            {message.tool_calls.map((toolCall, index) => (
              <ToolComponent
                key={
                  toolCall.tool_call_id ||
                  `${toolCall.tool_name}-${toolCall.created_at}-${index}`
                }
                tools={toolCall}
              />
            ))}
          </div>
        </div>
      )} */}
      <AgentMessage
        message={message}
        showAvatar={isLastAgentMessage}
        isStreaming={isStreaming}
      />
    </div>
  )
}
const Reasoning: FC<ReasoningStepProps> = ({ index, stepTitle }) => (
  <div className="flex items-center gap-2 text-light-text-secondary dark:text-dark-text-secondary">
    <div className="flex h-[20px] items-center rounded-md bg-light-surface p-2 dark:bg-dark-surface">
      <p className="text-xs">STEP {index + 1}</p>
    </div>
    <p className="text-xs">{stepTitle}</p>
  </div>
)
const Reasonings: FC<ReasoningProps> = ({ reasoning }) => (
  <div className="flex flex-col items-start justify-center gap-2">
    {reasoning.map((title, index) => (
      <Reasoning
        key={`${title.title}-${title.action}-${index}`}
        stepTitle={title.title}
        index={index}
      />
    ))}
  </div>
)

const ToolComponent = memo(({ tools }: ToolCallProps) => (
  <div className="cursor-default rounded-full bg-accent px-2 py-1.5 text-xs">
    <p className="font-dmmono uppercase text-white">{tools.tool_name}</p>
  </div>
))
ToolComponent.displayName = 'ToolComponent'
interface ConversationTurn {
  userMessage: ChatMessage
  intermediateWork: ChatMessage[]
  finalAnswer: ChatMessage | null
}

/**
 * InlineActivityIndicator - Shows what Cirkelline is doing in real-time
 * Appears INLINE in message area, where Cirkelline's response will appear
 * Matches BehindTheScenes styling for visual consistency
 */
const InlineActivityIndicator: FC<{ status: string }> = ({ status }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.2 }}
      className="flex items-center gap-2 mb-4"
    >
      {/* Pulsing dot indicator */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 1, 0.5]
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="w-2 h-2 rounded-full bg-accent flex-shrink-0"
      />

      {/* Status text - matches Behind the Scenes styling */}
      <span className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
        {status}
      </span>
    </motion.div>
  )
}

const Messages = ({ messages }: MessageListProps) => {
  const { isStreaming, activityStatus } = useStore()

  // Group messages into conversation turns
  const conversationTurns = useMemo(() => {
    const turns: ConversationTurn[] = []
    let currentTurn: Partial<ConversationTurn> = {
      intermediateWork: []
    }

    for (const message of messages) {
      if (message.role === 'user') {
        // Start new turn
        if (currentTurn.userMessage) {
          turns.push(currentTurn as ConversationTurn)
        }
        currentTurn = {
          userMessage: message,
          intermediateWork: [],
          finalAnswer: null
        }
      }
      else if (message.role === 'delegation' ||
               (message.role === 'agent' && message.teamName !== 'Cirkelline')) {
        // Add to intermediate work
        currentTurn.intermediateWork?.push(message)
      }
      else if (message.role === 'agent' && message.teamName === 'Cirkelline') {
        // Only treat as final answer if it has actual content, not just tool_calls
        // This allows activity indicator to show while tools are executing
        if (message.content || message.response_audio?.transcript) {
          // Final answer - complete this turn
          currentTurn.finalAnswer = message
          turns.push(currentTurn as ConversationTurn)
          currentTurn = {
            intermediateWork: []
          }
        } else {
          // Message with only tool_calls, no content yet - keep waiting for final answer
          // Activity indicator will continue showing
          currentTurn.intermediateWork?.push(message)
        }
      }
    }

    // Add incomplete turn if exists (streaming in progress)
    // ✅ BUG FIX: Also push turns that have intermediate work even without userMessage
    // This allows research work to display when it streams after Cirkelline's delegation
    if (currentTurn.userMessage || (currentTurn.intermediateWork && currentTurn.intermediateWork.length > 0)) {
      turns.push(currentTurn as ConversationTurn)
    }

    return turns
  }, [messages])

  // NO AUTO-SCROLLING - User controls their own scroll position
  // They can scroll up to read Behind the Scenes and stay there

  if (messages.length === 0) {
    return <ChatBlankState />
  }

  // Find the index of the last agent message across all turns
  let lastAgentMessageIndex = -1
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === 'agent') {
      lastAgentMessageIndex = i
      break
    }
  }

  return (
    <>
      {conversationTurns.map((turn, turnIndex) => {
        // Skip invalid turns without a user message
        if (!turn.userMessage) {
          return null
        }
        
        const isLastTurn = turnIndex === conversationTurns.length - 1
        const turnKey = `turn-${turn.userMessage.created_at}-${turnIndex}`

        // Collect all events from messages
        const allEvents: BehindTheScenesEvent[] = []
        if (turn.finalAnswer?.behindTheScenes) {
          allEvents.push(...turn.finalAnswer.behindTheScenes)
        }
        turn.intermediateWork.forEach(msg => {
          if (msg.behindTheScenes && msg.role === 'agent') {
            allEvents.push(...msg.behindTheScenes)
          }
        })

        return (
          <div key={turnKey} className="space-y-4">
            {/* User Message */}
            <div>
              <UserMessage message={turn.userMessage} />
            </div>

            {/* Behind the Scenes - Always render to maintain state */}
            <BehindTheScenes
              messages={turn.intermediateWork}
              events={allEvents}
              turnIndex={turnIndex}
            />

            {/* Final Answer - Only show when available */}
            {turn.finalAnswer && (
              <AgentMessageWrapper
                message={turn.finalAnswer}
                isLastMessage={isLastTurn}
                isLastAgentMessage={messages.indexOf(turn.finalAnswer) === lastAgentMessageIndex}
                isStreaming={isLastTurn && isStreaming}
              />
            )}

            {/* Activity Indicator - Shows at BOTTOM when NO final answer yet (disappears when Cirkelline starts writing) */}
            {isLastTurn && !turn.finalAnswer && isStreaming && activityStatus && (
              <div>
                <InlineActivityIndicator status={activityStatus} />
              </div>
            )}
          </div>
        )
      })}
    </>
  )
}

export default Messages
