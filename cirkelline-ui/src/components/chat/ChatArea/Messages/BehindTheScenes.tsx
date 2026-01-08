import { useState, useEffect, useRef, type FC } from 'react'
import type { ChatMessage, BehindTheScenesEvent } from '@/types/os'
import { AgentMessage } from './MessageItem'
import { memo } from 'react'

interface BehindTheScenesProps {
  messages: ChatMessage[]
  events: BehindTheScenesEvent[]
  turnIndex: number
}

const BehindTheScenes: FC<BehindTheScenesProps> = memo(({
  messages,
  events,
  turnIndex
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isMetricsExpanded, setIsMetricsExpanded] = useState(false)
  const buttonRef = useRef<HTMLButtonElement>(null)

  // Auto-scroll to top of Behind the Scenes when expanded
  useEffect(() => {
    if (isExpanded && buttonRef.current) {
      // Small delay to ensure content is rendered
      setTimeout(() => {
        buttonRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
      }, 100)
    }
  }, [isExpanded])

  // Combine events and messages chronologically
  const allItems: Array<{ type: 'event' | 'message', data: BehindTheScenesEvent | ChatMessage, timestamp: number }> = []

  // Add events but filter out delegation events (delegation messages already show this with task)
  events.forEach(event => {
    if (!event.description.includes('Delegating to')) {
      allItems.push({ type: 'event', data: event, timestamp: event.timestamp })
    }
  })

  messages.forEach(message => {
    allItems.push({ type: 'message', data: message, timestamp: message.created_at })
  })

  allItems.sort((a, b) => a.timestamp - b.timestamp)

  // Format agent/team names properly (web-researcher → Web Researcher)
  const formatName = (name: string): string => {
    return name
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  const getSourceLabel = (message: ChatMessage) => {
    if (message.agentName) return formatName(message.agentName)
    if (message.teamName) return message.teamName
    return null
  }


  // Format timestamp for display
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  return (
    <div className="my-4">
      <button
        ref={buttonRef}
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 rounded-lg bg-light-bg dark:bg-dark-bg hover:bg-light-surface dark:hover:bg-dark-surface transition-colors flex items-center justify-between group"
        aria-expanded={isExpanded}
        aria-controls={`behind-scenes-${turnIndex}`}
      >
        <div className="flex items-center gap-3">
          <svg
            className={`w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary">
            {isExpanded ? 'Hide' : 'Show'} Behind the Scenes
          </span>
          <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
            {allItems.length} {allItems.length === 1 ? 'event' : 'events'}
          </span>
        </div>
      </button>

      {isExpanded && (
        <div
          id={`behind-scenes-${turnIndex}`}
          role="region"
          className="mt-3 pl-4 border-l-2 border-border-primary animate-in fade-in slide-in-from-top-2 duration-200 [&_*]:!font-['Alan_Sans',_sans-serif] [&_*]:!text-xs [&_*]:!text-[#a0a0a0] [&_.font-bold]:!text-white dark:[&_.font-bold]:!text-white"
          style={{ fontFamily: 'var(--font-mono)' }}
        >
          <div className="space-y-4 text-xs text-light-text dark:text-dark-text">
            {allItems.map((item, index) => {
              const key = `behind-${turnIndex}-${item.type}-${item.timestamp}-${index}`

              if (item.type === 'event') {
                const event = item.data as BehindTheScenesEvent

                // Skip events with metrics - they're shown in the collapsible metrics box
                if (event.details?.metrics && event.details?.tokenUsage && event.details?.costs) {
                  return null
                }

                // v1.2.25: Removed aggressive filtering - users want to see all events
                // Only skip truly redundant events (no filters needed - delegation already filtered at line 24)

                // Check if this is a team thinking/planning event
                const isThinkingEvent = event.description.includes('Planning response') ||
                                       event.description.includes('is thinking')

                return (
                  <div key={key} className="relative">
                    <div className="flex">
                      <div className="flex-1 space-y-1 pb-2">
                        <div className="flex items-baseline gap-2 text-xs">
                          <span className="font-bold">
                            {isThinkingEvent ? `[${event.source} is thinking]` : `[${event.source}]`}
                          </span>
                          <span className="text-light-text-secondary dark:text-dark-text-secondary">
                            {formatTime(event.timestamp)}
                          </span>
                        </div>
                        {!isThinkingEvent && (
                          <div className="pl-3 border-l-2 border-border-primary text-xs">
                            {event.description}
                          </div>
                        )}
                        {event.details?.reasoningContent ? (
                          <div className="pl-3 border-l-2 border-border-primary text-xs">
                            {event.details.reasoningContent}
                          </div>
                        ) : null}
                        {event.details?.toolArgs?.task ? (
                          <div className="pl-3 border-l-2 border-border-primary text-xs">
                            Task: {String(event.details.toolArgs.task)}
                          </div>
                        ) : null}
                        {event.details?.toolArgs?.query ? (
                          <div className="pl-3 border-l-2 border-border-primary text-xs">
                            Query: {String(event.details.toolArgs.query)}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>
                )
              }

              const message = item.data as ChatMessage

              if (message.role === 'delegation') {
                const fromTeam = message.teamName || 'System'
                const toMember = message.delegatedTo || 'team member'
                const task = message.delegationTask || ''

                return (
                  <div key={key} className="relative">
                    <div className="flex">
                      <div className="flex-1 space-y-1 pb-2">
                        <div className="flex items-baseline gap-2 text-xs">
                          <span className="font-bold">
                            [{fromTeam} delegating to {toMember}]
                          </span>
                          <span className="text-light-text-secondary dark:text-dark-text-secondary">
                            {formatTime(message.created_at)}
                          </span>
                        </div>
                        {task ? (
                          <div className="pl-3 border-l-2 border-border-primary text-xs">
                            {task}
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>
                )
              }

              if (message.role === 'agent') {
                const sourceLabel = getSourceLabel(message)
                const hasReasoningSteps = message.extra_data?.reasoning_steps && message.extra_data.reasoning_steps.length > 0
                const hasToolCalls = message.tool_calls && message.tool_calls.length > 0

                return (
                  <div key={key} className="relative">
                    <div className="flex">
                      <div className="flex-1 space-y-1 pb-2">
                        {sourceLabel ? (
                          <div className="flex items-baseline gap-2 text-xs">
                            <span className="font-bold">
                              [{sourceLabel}]
                            </span>
                            <span className="text-light-text-secondary dark:text-dark-text-secondary">
                              {formatTime(message.created_at)}
                            </span>
                          </div>
                        ) : null}

                        {hasToolCalls ? (
                          <div className="space-y-1 pl-3 border-l-2 border-border-primary text-xs">
                            {message.tool_calls!.map((toolCall, idx) => (
                              <div key={idx}>
                                {toolCall.tool_name}
                                {toolCall.tool_args && Object.keys(toolCall.tool_args).length > 0 ? (
                                  <span> {JSON.stringify(toolCall.tool_args)}</span>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        ) : null}

                        {hasReasoningSteps ? (
                          <div className="space-y-1 pl-3 border-l-2 border-border-primary text-xs">
                            {message.extra_data!.reasoning_steps!.map((step, idx) => (
                              <div key={idx}>
                                {idx + 1}. {step.title}
                                {step.reasoning ? (
                                  <div className="pl-3 border-l-2 border-border-primary">
                                    {step.reasoning}
                                  </div>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        ) : null}

                        {message.content ? (
                          <div className="pl-3 border-l-2 border-border-primary text-xs [&_*]:!m-0 [&_*]:!p-0 [&_*]:!font-normal [&_*]:!leading-normal [&_li]:!ml-3 [&_.prose]:!gap-y-0">
                            <AgentMessage message={message} showAvatar={false} hideActions={true} />
                          </div>
                        ) : null}
                      </div>
                    </div>
                  </div>
                )
              }

              return null
            })}

            {/* Collapsible Metrics Section */}
            {(() => {
              // Calculate running totals and collect individual metrics
              let totalTokens = 0
              let totalInputTokens = 0
              let totalOutputTokens = 0
              let totalCost = 0
              let totalInputCost = 0
              let totalOutputCost = 0
              const eventsWithMetrics: BehindTheScenesEvent[] = []

              events.forEach(event => {
                if (event.details?.tokenUsage) {
                  totalInputTokens += event.details.tokenUsage.input
                  totalOutputTokens += event.details.tokenUsage.output
                  totalTokens += event.details.tokenUsage.total
                  eventsWithMetrics.push(event)
                }
                if (event.details?.costs) {
                  totalInputCost += event.details.costs.input
                  totalOutputCost += event.details.costs.output
                  totalCost += event.details.costs.total
                }
              })

              // Only show if we have metrics
              if (totalTokens > 0) {
                return (
                  <div className="mt-6">
                    <button
                      onClick={() => setIsMetricsExpanded(!isMetricsExpanded)}
                      className="w-full p-3 rounded-lg bg-light-bg dark:bg-dark-bg hover:bg-light-surface dark:hover:bg-dark-surface transition-colors flex items-center justify-between group"
                      aria-expanded={isMetricsExpanded}
                    >
                      <div className="flex items-center gap-3">
                        <svg
                          className={`w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary transition-transform ${isMetricsExpanded ? 'rotate-90' : ''}`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        <span className="text-sm font-bold text-white dark:text-white">
                          {isMetricsExpanded ? 'Hide' : 'View'} Metrics
                        </span>
                      </div>
                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                        {totalTokens.toLocaleString()} tokens · ${totalCost < 0.01 ? totalCost.toFixed(6) : totalCost.toFixed(4)}
                      </span>
                    </button>

                    {isMetricsExpanded && (
                      <div className="mt-3 pl-4 border-l-2 border-border-primary animate-in fade-in slide-in-from-top-2 duration-200 space-y-4">
                        {/* Individual Event Metrics */}
                        {eventsWithMetrics.map((event, idx) => (
                          <div key={`metric-${event.id}-${idx}`} className="pb-4 border-b border-border-primary last:border-b-0 last:pb-0">
                            <div className="text-xs space-y-2">
                              <div className="font-bold text-white dark:text-white">{event.source}</div>
                              <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Total Tokens:</span>
                                  <span className="ml-2 font-medium text-light-text dark:text-dark-text">
                                    {event.details?.tokenUsage?.total.toLocaleString()}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Total Cost:</span>
                                  <span className="ml-2 font-medium text-accent">
                                    ${event.details?.costs?.total && event.details.costs.total < 0.01
                                      ? event.details.costs.total.toFixed(6)
                                      : event.details?.costs?.total.toFixed(4)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Input:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text">
                                    {event.details?.tokenUsage?.input.toLocaleString()} tokens
                                  </span>
                                </div>
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Input Cost:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text">
                                    ${event.details?.costs?.input.toFixed(6)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Output:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text">
                                    {event.details?.tokenUsage?.output.toLocaleString()} tokens
                                  </span>
                                </div>
                                <div>
                                  <span className="text-light-text-secondary dark:text-dark-text-secondary">Output Cost:</span>
                                  <span className="ml-2 text-light-text dark:text-dark-text">
                                    ${event.details?.costs?.output.toFixed(6)}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}

                        {/* Conversation Summary */}
                        <div className="pt-4 border-t-2 border-border-primary">
                          <div className="text-xs space-y-2">
                            <div className="font-bold text-white dark:text-white text-sm">Conversation Summary</div>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Total Tokens:</span>
                                <span className="ml-2 font-bold text-light-text dark:text-dark-text">
                                  {totalTokens.toLocaleString()}
                                </span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Total Cost:</span>
                                <span className="ml-2 font-bold text-accent">
                                  ${totalCost < 0.01 ? totalCost.toFixed(6) : totalCost.toFixed(4)}
                                </span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Input:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">
                                  {totalInputTokens.toLocaleString()} tokens
                                </span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Input Cost:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">
                                  ${totalInputCost.toFixed(6)}
                                </span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Output:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">
                                  {totalOutputTokens.toLocaleString()} tokens
                                </span>
                              </div>
                              <div>
                                <span className="text-light-text-secondary dark:text-dark-text-secondary">Output Cost:</span>
                                <span className="ml-2 text-light-text dark:text-dark-text">
                                  ${totalOutputCost.toFixed(6)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )
              }
              return null
            })()}
          </div>
        </div>
      )}
    </div>
  )
})

BehindTheScenes.displayName = 'BehindTheScenes'

export default BehindTheScenes
