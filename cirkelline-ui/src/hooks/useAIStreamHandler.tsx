import { useCallback } from 'react'
import { flushSync } from 'react-dom'

import { APIRoutes } from '@/api/routes'

import useChatActions from '@/hooks/useChatActions'
import { useStore } from '../store'
import { RunEvent, RunResponseContent, type RunResponse, type ChatMessage, type BehindTheScenesEvent } from '@/types/os'
import { constructEndpointUrl } from '@/lib/constructEndpointUrl'
import useAIResponseStream from './useAIResponseStream'
import { ToolCall } from '@/types/os'
import { useQueryState } from 'nuqs'
import { getJsonMarkdown } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import { getAuthHeaders } from '@/lib/auth-headers'

const useAIChatStreamHandler = () => {
  const setMessages = useStore((state) => state.setMessages)
  const messages = useStore((state) => state.messages)
  const { addMessage, focusChatInput } = useChatActions()
  const [agentId] = useQueryState('agent')
  const [teamId] = useQueryState('team')
  const [sessionId, setSessionId] = useQueryState('session')
  const selectedEndpoint = useStore((state) => state.selectedEndpoint)
  const mode = useStore((state) => state.mode)
  const setStreamingErrorMessage = useStore(
    (state) => state.setStreamingErrorMessage
  )
  const setIsStreaming = useStore((state) => state.setIsStreaming)
  const setActivityStatus = useStore((state) => state.setActivityStatus)
  const setSessionsData = useStore((state) => state.setSessionsData)
  // Cancel run state management
  const setCurrentRunId = useStore((state) => state.setCurrentRunId)
  const setAbortController = useStore((state) => state.setAbortController)
  const { streamResponse } = useAIResponseStream()
  const { getUserId } = useAuth()

  /**
   * Maps tool events to user-friendly activity status messages
   * @param toolName - The name of the tool being used
   * @param toolArgs - The arguments passed to the tool
   * @param agentName - The name of the agent using the tool (for member-specific messages)
   * @returns User-friendly status message or null
   */
  const getActivityStatus = useCallback((
    toolName: string,
    toolArgs: Record<string, unknown> | undefined,
    agentName?: string
  ): string | null => {
    // Handle member agent tools (web research, analysis, etc.)
    if (toolName === 'duckduckgo_search' || toolName === 'exa_search' || toolName === 'tavily_search') {
      const query = toolArgs?.query || toolArgs?.topic || toolArgs?.q
      if (query && typeof query === 'string') {
        const shortQuery = query.length > 50 ? query.substring(0, 50) + '...' : query
        return `Searching for "${shortQuery}"`
      }
      return 'Searching the web...'
    }

    // Handle agent-specific activities based on agent name
    if (agentName) {
      const lowerAgentName = agentName.toLowerCase()
      if (lowerAgentName.includes('research analyst')) {
        return 'Analyzing the research findings...'
      } else if (lowerAgentName.includes('web researcher') && !toolName) {
        return 'Preparing to search...'
      } else if (lowerAgentName.includes('legal') && lowerAgentName.includes('analyst')) {
        return 'Analyzing the legal research...'
      }
    }

    switch (toolName) {
      case 'think':
        return 'Thinking about your request...'
      case 'analyze':
        return 'Analyzing the information...'
      case 'get_previous_session_messages':
        return 'Retrieving previous conversation...'
      case 'delegate_task_to_member':
        // Map delegation to specific specialists
        const memberId = toolArgs?.member_id as string | undefined
        if (memberId === 'research-team' || memberId?.includes('research')) {
          return 'Consulting my research specialists...'
        } else if (memberId === 'law-team' || memberId?.includes('law') || memberId?.includes('legal')) {
          return 'Checking with my legal experts...'
        } else if (memberId?.includes('audio')) {
          return 'Processing audio with my audio specialist...'
        } else if (memberId?.includes('video')) {
          return 'Analyzing video with my video specialist...'
        } else if (memberId?.includes('image')) {
          return 'Processing image with my image specialist...'
        } else if (memberId?.includes('document')) {
          return 'Reading document with my document specialist...'
        } else {
          return 'Working with my specialists...'
        }
      default:
        // Show activity status for EVERY tool - full transparency
        if (toolName) {
          // Convert snake_case to human readable
          const words = toolName.split('_')
          const readable = words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
          return `${readable}...`
        }
        return null
    }
  }, [])

  const updateMessagesWithErrorState = useCallback(() => {
    setMessages((prevMessages) => {
      const newMessages = [...prevMessages]
      const lastMessage = newMessages[newMessages.length - 1]
      if (lastMessage && lastMessage.role === 'agent') {
        lastMessage.streamingError = true
      }
      return newMessages
    })
  }, [setMessages])

  /**
   * Processes a new tool call and adds it to the message
   * @param toolCall - The tool call to add
   * @param prevToolCalls - The previous tool calls array
   * @returns Updated tool calls array
   */
  const processToolCall = useCallback(
    (toolCall: ToolCall, prevToolCalls: ToolCall[] = []) => {
      const toolCallId =
        toolCall.tool_call_id || `${toolCall.tool_name}-${toolCall.created_at}`

      const existingToolCallIndex = prevToolCalls.findIndex(
        (tc) =>
          (tc.tool_call_id && tc.tool_call_id === toolCall.tool_call_id) ||
          (!tc.tool_call_id &&
            toolCall.tool_name &&
            toolCall.created_at &&
            `${tc.tool_name}-${tc.created_at}` === toolCallId)
      )
      if (existingToolCallIndex >= 0) {
        const updatedToolCalls = [...prevToolCalls]
        updatedToolCalls[existingToolCallIndex] = {
          ...updatedToolCalls[existingToolCallIndex],
          ...toolCall
        }
        return updatedToolCalls
      } else {
        return [...prevToolCalls, toolCall]
      }
    },
    []
  )

  /**
   * Processes tool calls from a chunk, handling both single tool object and tools array formats
   * @param chunk - The chunk containing tool call data
   * @param existingToolCalls - The existing tool calls array
   * @returns Updated tool calls array
   */
  const processChunkToolCalls = useCallback(
    (
      chunk: RunResponseContent | RunResponse,
      existingToolCalls: ToolCall[] = []
    ) => {
      let updatedToolCalls = [...existingToolCalls]
      // Handle new single tool object format
      if (chunk.tool) {
        updatedToolCalls = processToolCall(chunk.tool, updatedToolCalls)
      }
      // Handle legacy tools array format
      if (chunk.tools && chunk.tools.length > 0) {
        for (const toolCall of chunk.tools) {
          updatedToolCalls = processToolCall(toolCall, updatedToolCalls)
        }
      }

      return updatedToolCalls
    },
    [processToolCall]
  )

  /**
   * ============================================
   * BEHIND THE SCENES: Event Capture System
   * ============================================
   * Maps streaming events to user-friendly timeline entries
   */

  /**
   * Creates a BehindTheScenesEvent from a RunResponse chunk
   * @param chunk - The streaming event chunk
   * @returns BehindTheScenesEvent or null if event should not be captured
   */
  const createBehindTheScenesEvent = useCallback((chunk: RunResponse): BehindTheScenesEvent | null => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const agnoChunk = chunk as any // Access AGNO official fields
    const teamName = agnoChunk.team_name || 'System'
    const agentName = agnoChunk.agent_name || null
    const source = agentName || teamName

    // Determine source type and depth
    let sourceType: 'main' | 'team' | 'agent' = 'main'
    let depth = 0

    if (teamName === 'Cirkelline') {
      sourceType = 'main'
      depth = 0
    } else if (agentName) {
      sourceType = 'agent'
      depth = 1
    } else if (teamName) {
      sourceType = 'team'
      depth = 1
    }

    // Generate event ID
    const eventId = `${chunk.event}-${chunk.created_at}-${Math.random().toString(36).substr(2, 9)}`

    // Map event to description
    let description = ''
    let status: 'started' | 'in_progress' | 'completed' | 'error' = 'in_progress'
    const details: BehindTheScenesEvent['details'] = {}

    switch (chunk.event) {
      case RunEvent.TeamRunStarted:
        description = `${source} started working`
        status = 'started'
        break

      case RunEvent.RunStarted:
        description = `${source} started`
        status = 'started'
        break

      case RunEvent.ToolCallStarted:
      case RunEvent.TeamToolCallStarted:
        const toolName = chunk.tool?.tool_name
        const toolArgs = chunk.tool?.tool_args

        if (toolName === 'think') {
          description = `${source}: Planning response`
          details.toolName = toolName
          // Extract reasoning content from backend (sent as reasoning_content field)
          details.reasoningContent = (chunk as { reasoning_content?: string }).reasoning_content || toolArgs?.thought || toolArgs?.reasoning as string
        } else if (toolName === 'analyze') {
          description = `${source}: Analyzing information`
          details.toolName = toolName
          // Extract reasoning content from backend
          details.reasoningContent = (chunk as { reasoning_content?: string }).reasoning_content || toolArgs?.analysis as string
        } else if (toolName === 'delegate_task_to_member') {
          const memberName = toolArgs?.member_name || toolArgs?.agent || toolArgs?.member_id || toolArgs?.agent_name || 'team member'
          const taskDesc = toolArgs?.task_description || toolArgs?.task || ''
          description = `${source}: Delegating to ${memberName}`
          details.toolName = toolName
          details.toolArgs = { member_name: memberName, task: taskDesc }
        } else if (toolName === 'duckduckgo_search' || toolName === 'exa_search' || toolName === 'tavily_search') {
          const query = toolArgs?.query || toolArgs?.topic || toolArgs?.q || ''
          const shortQuery = typeof query === 'string' && query.length > 50
            ? query.substring(0, 50) + '...'
            : query
          description = `${source}: Searching for "${shortQuery}"`
          details.toolName = toolName
          details.toolArgs = { query: shortQuery }
        } else if (toolName) {
          description = `${source}: Using ${toolName} tool`
          details.toolName = toolName
          details.toolArgs = toolArgs as Record<string, unknown>
        } else {
          return null // Skip if no tool name
        }
        status = 'started'
        break

      case RunEvent.ToolCallCompleted:
      case RunEvent.TeamToolCallCompleted:
        const completedToolName = chunk.tool?.tool_name
        if (completedToolName === 'think' || completedToolName === 'analyze') {
          description = `${source}: ${completedToolName === 'think' ? 'Planning' : 'Analysis'} complete`
        } else if (completedToolName === 'delegate_task_to_member') {
          description = `${source}: Delegation complete`
        } else if (completedToolName) {
          description = `${source}: ${completedToolName} complete`
        } else {
          return null
        }
        status = 'completed'
        details.toolName = completedToolName
        details.executionTime = chunk.tool?.metrics?.time
        break

      case RunEvent.ReasoningStep:
      case RunEvent.TeamReasoningStep:
        // AGNO emits ReasoningStep events with the step in chunk.content
        const reasoningStep = chunk.content as { title?: string; reasoning?: string; action?: string; confidence?: number }
        if (reasoningStep && reasoningStep.title) {
          description = `${source}: ${reasoningStep.title}`
          // Use pre-formatted markdown from chunk.reasoning_content, fallback to reasoning field
          details.reasoningContent = (chunk as { reasoning_content?: string }).reasoning_content || reasoningStep.reasoning
          details.action = reasoningStep.action
          details.confidence = reasoningStep.confidence
        } else {
          return null
        }
        status = 'in_progress'
        break

      case RunEvent.ReasoningCompleted:
      case RunEvent.TeamReasoningCompleted:
        description = `${source}: Reasoning complete`
        status = 'completed'
        break

      case RunEvent.MemoryUpdateStarted:
      case RunEvent.TeamMemoryUpdateStarted:
        description = `${source}: Saving insights to memory`
        status = 'started'
        break

      case RunEvent.MemoryUpdateCompleted:
      case RunEvent.TeamMemoryUpdateCompleted:
        description = `${source}: Memory updated`
        status = 'completed'
        break

      case RunEvent.RunContent:
      case RunEvent.TeamRunContent:
        // Skip content events - they happen for every streaming chunk (too noisy)
        return null

      case RunEvent.RunCompleted:
        description = `${source}: Completed`
        status = 'completed'
        break

      case RunEvent.TeamRunCompleted:
        description = `${source}: Completed`
        status = 'completed'
        break

      case RunEvent.RunError:
      case RunEvent.TeamRunError:
        description = `${source}: Error occurred`
        status = 'error'
        details.toolResult = chunk.content as string
        break

      case RunEvent.Retry: // Backend retry notification
        const retryData = chunk as unknown as { attempt?: number; max_retries?: number; delay?: number; message?: string }
        description = retryData.message || `Retrying request (attempt ${retryData.attempt || 1}/${retryData.max_retries || 3})`
        status = 'in_progress'
        details.retryAttempt = retryData.attempt
        details.maxRetries = retryData.max_retries
        details.retryDelay = retryData.delay
        break

      case RunEvent.Error: // Backend error notification
        const errorData = chunk as unknown as { error?: string; type?: string; retries?: number }
        description = errorData.error || 'An error occurred'
        status = 'error'
        details.errorType = errorData.type
        details.retryAttempts = errorData.retries
        break

      case RunEvent.MetricsUpdate: // Token usage and cost metrics
        const metricsData = chunk.metrics
        if (metricsData) {
          const formattedCost = metricsData.total_cost < 0.01
            ? `$${metricsData.total_cost.toFixed(6)}`
            : `$${metricsData.total_cost.toFixed(4)}`
          description = `${source}: ${metricsData.total_tokens.toLocaleString()} tokens used (${formattedCost})`
          status = 'completed'
          details.metrics = metricsData
          details.tokenUsage = {
            input: metricsData.input_tokens,
            output: metricsData.output_tokens,
            total: metricsData.total_tokens
          }
          details.costs = {
            input: metricsData.input_cost,
            output: metricsData.output_cost,
            total: metricsData.total_cost
          }
          details.model = metricsData.model
        } else {
          return null
        }
        break

      default:
        // Skip events we don't want to show
        return null
    }

    return {
      id: eventId,
      timestamp: chunk.created_at,
      eventType: chunk.event,
      source,
      sourceType,
      description,
      details,
      status,
      depth,
      parentEventId: agnoChunk.parent_run_id
    }
  }, [])

  /**
   * Captures an event for the Behind the Scenes timeline
   * Appends to the most recent agent message's behindTheScenes array
   */
  const captureForBehindTheScenes = useCallback((chunk: RunResponse) => {
    const event = createBehindTheScenesEvent(chunk)
    if (!event) return

    console.log('🎬 BEHIND THE SCENES EVENT CAPTURED:', {
      event: chunk.event,
      source: event.source,
      description: event.description,
      depth: event.depth,
      hasReasoningContent: !!event.details?.reasoningContent,
      hasToolArgs: !!event.details?.toolArgs,
      details: event.details
    })

    setMessages((prev) => {
      const newMessages = [...prev]

      // Find the most recent agent message to attach this event to
      // This should be the last message that was added when we started streaming
      for (let i = newMessages.length - 1; i >= 0; i--) {
        if (newMessages[i].role === 'agent') {
          const msg = newMessages[i]
          msg.behindTheScenes = [
            ...(msg.behindTheScenes || []),
            event
          ]
          break
        }
      }

      return newMessages
    })
  }, [createBehindTheScenesEvent, setMessages])

  const handleStreamResponse = useCallback(
    async (input: string | FormData) => {
      setIsStreaming(true)

      // Create AbortController for cancel functionality
      const controller = new AbortController()
      setAbortController(controller)

      const formData = input instanceof FormData ? input : new FormData()
      if (typeof input === 'string') {
        formData.append('message', input)
      }

      setMessages((prevMessages) => {
        if (prevMessages.length >= 2) {
          const lastMessage = prevMessages[prevMessages.length - 1]
          const secondLastMessage = prevMessages[prevMessages.length - 2]
          if (
            lastMessage.role === 'agent' &&
            lastMessage.streamingError &&
            secondLastMessage.role === 'user'
          ) {
            return prevMessages.slice(0, -2)
          }
        }
        return prevMessages
      })

      addMessage({
        role: 'user',
        content: formData.get('message') as string,
        created_at: Math.floor(Date.now() / 1000)
      })

      addMessage({
        role: 'agent',
        content: '',
        tool_calls: [],
        streamingError: false,
        created_at: Math.floor(Date.now() / 1000) + 1
      })

      let lastContent = ''
      let newSessionId = sessionId
      try {
        const endpointUrl = constructEndpointUrl(selectedEndpoint)

        let RunUrl: string | null = null

        if (mode === 'team' && teamId) {
          RunUrl = APIRoutes.TeamRun(endpointUrl, teamId)
        } else if (mode === 'agent' && agentId) {
          RunUrl = APIRoutes.AgentRun(endpointUrl).replace(
            '{agent_id}',
            agentId
          )
        }

        if (!RunUrl) {
          updateMessagesWithErrorState()
          setStreamingErrorMessage('Please select an agent or team first.')
          setIsStreaming(false)
          return
        }

        formData.append('stream', 'true')

        // Fix: If this is a brand new chat (messages array is empty), always force empty session_id
        // This prevents race conditions where clearChat() was called but sessionId URL param hasn't updated yet
        const effectiveSessionId = messages.length === 0 ? '' : (sessionId ?? '')
        formData.append('session_id', effectiveSessionId)

        console.log('🆕 SESSION CHECK:', {
          messagesLength: messages.length,
          urlSessionId: sessionId,
          effectiveSessionId: effectiveSessionId,
          isNewChat: messages.length === 0
        })

        const sendingUserId = getUserId()
        console.log('💬 SENDING MESSAGE with user_id:', sendingUserId)
        formData.append('user_id', sendingUserId)

        // Send user's timezone to backend
        const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
        formData.append('timezone', userTimezone)
        console.log('🌍 SENDING TIMEZONE:', userTimezone)

        await streamResponse({
          apiUrl: RunUrl,
          headers: getAuthHeaders(),
          requestBody: formData,
          signal: controller.signal,  // Pass AbortController signal for cancellation
          onChunk: (chunk: RunResponse) => {
            // Capture events for Behind the Scenes
            captureForBehindTheScenes(chunk)

            // 🔄 Handle retry events - show user we're retrying
            if (chunk.event === 'retry') {
              const retryData = chunk as unknown as { attempt?: number; max_retries?: number; delay?: number; message?: string }
              const statusMessage = retryData.message || `Retrying... (Attempt ${retryData.attempt || 1}/${retryData.max_retries || 3})`
              setActivityStatus(statusMessage)
              return // Don't process further
            }

            // ❌ Handle error events - show error message to user
            if (chunk.event === 'error') {
              const errorData = chunk as unknown as { error?: string; type?: string; retries?: number }
              const errorMessage = errorData.error || 'An error occurred'
              setActivityStatus('')  // Clear activity status
              setStreamingErrorMessage(errorMessage)
              return // Don't process further
            }

            // ⏸️ Handle HITL paused events - agent needs user input
            if (chunk.event === RunEvent.Paused) {
              console.log('⏸️ HITL: Run paused - needs user input', chunk)
              const pausedData = chunk as unknown as {
                run_id: string
                session_id: string
                requirements: Array<{
                  needs_user_input: boolean
                  needs_confirmation: boolean
                  user_input_schema?: Array<{
                    name: string
                    field_type: string
                    description: string
                    value: string | null
                  }>
                  tool_name?: string
                  tool_args?: Record<string, unknown>
                }>
              }

              // Store the paused state for the UI to render the input form
              setMessages((prevMessages) => {
                const newMessages = [...prevMessages]
                const lastMessage = newMessages[newMessages.length - 1]
                if (lastMessage && lastMessage.role === 'agent') {
                  // Add HITL data to the last agent message
                  lastMessage.hitlPaused = true
                  lastMessage.hitlRunId = pausedData.run_id
                  lastMessage.hitlSessionId = pausedData.session_id
                  lastMessage.hitlRequirements = pausedData.requirements

                  // Show a prompt in the message content
                  const fields = pausedData.requirements
                    .filter(r => r.needs_user_input)
                    .flatMap(r => r.user_input_schema || [])

                  if (fields.length > 0) {
                    const fieldList = fields.map(f => `- **${f.name}**: ${f.description}`).join('\n')
                    lastMessage.content = `I need some more information to complete this task:\n\n${fieldList}\n\nPlease fill in the details below.`
                  }
                }
                return newMessages
              })

              setActivityStatus('Waiting for your input...')
              return // Don't process further - wait for user input
            }

            // Track run_id for cancel functionality (capture from first event that has it)
            if (chunk.run_id && !useStore.getState().currentRunId) {
              setCurrentRunId(chunk.run_id as string)
            }

            // Handle session ID and optimistic session add for ANY event with a session_id
            // This catches cases where TeamRunStarted arrives after other events
            if (chunk.session_id && (!sessionId || sessionId !== chunk.session_id)) {
              // New session detected - save it and update URL
              newSessionId = chunk.session_id as string

              // Update URL with the actual session ID from backend
              // Only if we don't already have this session ID in the URL
              if (sessionId !== chunk.session_id) {
                setSessionId(chunk.session_id as string)
              }

              console.log('✨ OPTIMISTIC SESSION ADD:')
              console.log('  Current sessionId:', sessionId)
              console.log('  New chunk.session_id:', chunk.session_id)

              const sessionData = {
                session_id: chunk.session_id as string,
                session_name: formData.get('message') as string,
                created_at: chunk.created_at
              }
              console.log('  Session data to add:', sessionData)

              setSessionsData((prevSessionsData) => {
                console.log('  Previous sessions before add:', prevSessionsData?.length || 0)
                const sessionExists = prevSessionsData?.some(
                  (session) => session.session_id === chunk.session_id
                )
                console.log('  Session already exists?:', sessionExists)
                if (sessionExists) {
                  return prevSessionsData
                }
                const newData = [sessionData, ...(prevSessionsData ?? [])]
                console.log('  New sessions count:', newData.length)
                return newData
              })
            }

            if (
              chunk.event === RunEvent.ToolCallStarted ||
              chunk.event === RunEvent.TeamToolCallStarted ||
              chunk.event === RunEvent.ToolCallCompleted ||
              chunk.event === RunEvent.TeamToolCallCompleted
            ) {
              // ✅ SHOW ALL: Including delegation tools for full transparency
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const agnoChunk = chunk as any
              const toolName = chunk.tool?.tool_name
              const toolArgs = chunk.tool?.tool_args
              const delegationTools = ['delegate_task_to_member']
              const coordinationTools = ['think', 'analyze']
              const internalTools = ['get_previous_session_messages']

              if (toolName && delegationTools.includes(toolName) && (chunk.event === RunEvent.ToolCallStarted || chunk.event === RunEvent.TeamToolCallStarted)) {
                // ✅ SHOW DELEGATION: Create a special delegation message
                const taskDescription = toolArgs?.task_description || toolArgs?.task || 'Unknown task'
                // Try multiple field names to find the actual agent/team
                let memberName = toolArgs?.member_name || toolArgs?.agent || toolArgs?.member_id || toolArgs?.agent_name || 'team member'

                // 🔧 WORKAROUND: Backend sends wrong member_id when Cirkelline delegates to teams
                // Map agent IDs to their parent teams when delegation is from Cirkelline
                const delegatingFrom = agnoChunk.team_name || agnoChunk.agent_name
                if (delegatingFrom === 'Cirkelline') {
                  const agentToTeamMap: Record<string, string> = {
                    'web-researcher': 'Research Team',
                    'research-analyst': 'Research Team',
                    'legal-researcher': 'Law Team',
                    'legal-analyst': 'Law Team'
                  }

                  if (memberName in agentToTeamMap) {
                    memberName = agentToTeamMap[memberName]
                  }
                }

                console.log('🔄 DELEGATION DETECTED:', {
                  from: delegatingFrom,
                  to: memberName,
                  task: taskDescription,
                  tool_args: toolArgs
                })

                setMessages((prevMessages) => {
                  const delegationMessage: ChatMessage = {
                    role: 'delegation',
                    content: `**Delegating to ${memberName}:**\n\n${taskDescription}`,
                    created_at: Math.floor(Date.now() / 1000),
                    isDelegation: true,
                    delegatedTo: memberName,
                    delegationTask: taskDescription,
                    teamName: agnoChunk.team_name,
                    teamId: agnoChunk.team_id,
                    agentName: agnoChunk.agent_name,
                    agentId: agnoChunk.agent_id,
                    runId: agnoChunk.run_id,
                    parentRunId: agnoChunk.parent_run_id
                  }
                  return [...prevMessages, delegationMessage]
                })

                // Still set activity status for UX (pass agent name for context)
                const status = getActivityStatus(toolName, toolArgs, agnoChunk.agent_name)
                if (status) {
                  console.log('🔥 SETTING ACTIVITY STATUS (delegation):', status)
                  setActivityStatus(status)
                }
              } else if (toolName && coordinationTools.includes(toolName)) {
                // Coordination tools: just set activity status, don't show
                if (chunk.event === RunEvent.ToolCallStarted || chunk.event === RunEvent.TeamToolCallStarted) {
                  const status = getActivityStatus(toolName, toolArgs, agnoChunk.agent_name)
                  if (status) {
                    console.log('🔥 SETTING ACTIVITY STATUS (coordination):', status)
                    setActivityStatus(status)
                  }
                }
              } else if (toolName && internalTools.includes(toolName)) {
                // Internal tools: just set activity status, don't show badge
                if (chunk.event === RunEvent.ToolCallStarted || chunk.event === RunEvent.TeamToolCallStarted) {
                  const status = getActivityStatus(toolName, toolArgs, agnoChunk.agent_name)
                  if (status) {
                    console.log('🔥 SETTING ACTIVITY STATUS (internal tool):', status)
                    setActivityStatus(status)
                  }
                }
              } else if (toolName) {
                // 🔧 IMPORTANT: Only process tools that should be shown as badges
                // Exclude delegation, coordination, and internal tools (already shown elsewhere or as activity status)
                const hiddenTools = [...delegationTools, ...coordinationTools, ...internalTools]

                if (!hiddenTools.includes(toolName)) {
                  // Set activity status for ALL tools - full transparency
                  if ((chunk.event === RunEvent.ToolCallStarted || chunk.event === RunEvent.TeamToolCallStarted)) {
                    const status = getActivityStatus(toolName, toolArgs, agnoChunk.agent_name)
                    if (status) {
                      console.log('🔥 SETTING ACTIVITY STATUS (tool):', status)
                      setActivityStatus(status)
                    }
                  }

                  // Show all other tools as badges (web search, code execution, etc.)
                  // 🔧 FIX: Match tool calls to correct agent by agent_name and run_id
                  setMessages((prevMessages) => {
                    const newMessages = [...prevMessages]
                    const agentName = agnoChunk.agent_name
                    const runId = agnoChunk.run_id
                    const teamName = agnoChunk.team_name

                    // Find the correct agent message by matching agent_name and run_id
                    // Search backwards to find most recent message from this agent with same run_id
                    let foundMessage = false
                    for (let i = newMessages.length - 1; i >= 0; i--) {
                      const message = newMessages[i]
                      if (message.role === 'agent' &&
                          message.agentName === agentName &&
                          message.runId === runId) {
                        message.tool_calls = processChunkToolCalls(
                          chunk,
                          message.tool_calls
                        )
                        foundMessage = true
                        break // Found the right message, stop searching
                      }
                    }

                    // If no message found, create placeholder message that RunContent will append to
                    if (!foundMessage) {
                      console.log('🔧 Creating placeholder message for tool calls:', { agentName, runId })
                      const placeholderMessage: ChatMessage = {
                        role: 'agent',
                        content: '', // Will be filled by RunContent
                        created_at: Math.floor(Date.now() / 1000),
                        agentName: agentName,
                        teamName: teamName,
                        agentId: agnoChunk.agent_id,
                        teamId: agnoChunk.team_id,
                        runId: runId,
                        parentRunId: agnoChunk.parent_run_id,
                        tool_calls: processChunkToolCalls(chunk, [])
                      }
                      newMessages.push(placeholderMessage)
                    }

                    return newMessages
                  })
                }
              }
            } else if (chunk.event === RunEvent.RunContent) {
              // ✅ SHOW ALL: Member agent content (Web Researcher, Research Analyst)
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const agnoChunk = chunk as any // Access AGNO official fields
              console.log('✅ PROCESSING MEMBER AGENT CONTENT:', {
                agent_name: agnoChunk.agent_name,
                agentId: agnoChunk.agent_id,
                contentPreview: typeof chunk.content === 'string' ? chunk.content.substring(0, 50) : chunk.content
              })

              // Manage activity status based on agent
              const agentName = agnoChunk.agent_name
              const teamName = agnoChunk.team_name

              // Update activity status to show what's happening
              // NOTE: We don't show "Writing response..." when Cirkelline responds
              // because the user can already see content streaming
              console.log('🔥 RUNCONTENT EVENT:', { agentName, teamName })
              if (agentName) {
                // Update status for member agents
                const lowerAgentName = agentName.toLowerCase().trim()
                if (lowerAgentName.includes('web') || lowerAgentName.includes('research')) {
                  if (lowerAgentName.includes('analyst')) {
                    console.log('🔥 SETTING ACTIVITY STATUS (analyst):', 'Analyzing the research findings...')
                    setActivityStatus('Analyzing the research findings...')
                  } else if (lowerAgentName.includes('web')) {
                    console.log('🔥 SETTING ACTIVITY STATUS (web researcher):', 'Searching the web...')
                    setActivityStatus('Searching the web...')
                  }
                }
              }
              // For member agents, status updated when they start generating content

              // 🎬 TYPEWRITER EFFECT: Use flushSync to force immediate render for each chunk
              // This prevents React 18's automatic batching from showing all content at once
              flushSync(() => {
              setMessages((prevMessages) => {
                const newMessages = [...prevMessages]
                const lastMessage = newMessages[newMessages.length - 1]

                // Check if we can append to last message (same agent, same run)
                const canAppend = lastMessage &&
                  lastMessage.role === 'agent' &&
                  lastMessage.agentName === agnoChunk.agent_name &&
                  lastMessage.runId === agnoChunk.run_id

                if (canAppend && typeof chunk.content === 'string') {
                  const uniqueContent = chunk.content.replace(lastContent, '')
                  lastMessage.content += uniqueContent
                  lastContent = chunk.content

                  lastMessage.tool_calls = processChunkToolCalls(
                    chunk,
                    lastMessage.tool_calls
                  )
                } else if (canAppend && typeof chunk?.content !== 'string' && chunk.content !== null) {
                  const jsonBlock = getJsonMarkdown(chunk?.content)
                  lastMessage.content += jsonBlock
                  lastContent = jsonBlock
                } else if (typeof chunk.content === 'string' || chunk.content !== null) {
                  // Create new message with AGNO attribution
                  const content = typeof chunk.content === 'string' ? chunk.content : getJsonMarkdown(chunk.content)
                  const newMessage: ChatMessage = {
                    role: 'agent',
                    content: content,
                    created_at: Math.floor(Date.now() / 1000),
                    agentName: agnoChunk.agent_name,
                    agentId: agnoChunk.agent_id,
                    runId: agnoChunk.run_id,
                    parentRunId: agnoChunk.parent_run_id
                  }
                  lastContent = typeof chunk.content === 'string' ? chunk.content : content
                  newMessages.push(newMessage)
                }
                return newMessages
              })
              }) // Close flushSync
            } else if (chunk.event === RunEvent.TeamRunContent) {
              // ✅ SHOW ALL: Team content from ALL teams (Cirkelline, Research Team, Law Team)
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const agnoChunk = chunk as any // Access AGNO official fields
              const teamName = agnoChunk.team_name
              console.log('✅ PROCESSING TEAM CONTENT:', {
                team_name: teamName,
                teamId: agnoChunk.team_id,
                runId: agnoChunk.run_id,
                parentRunId: agnoChunk.parent_run_id,
                contentPreview: typeof chunk.content === 'string' ? chunk.content.substring(0, 50) : chunk.content
              })

              // DO NOT set "Writing response..." status - user can see content streaming
              // Status bar only shows background activities (delegation, searching, analyzing)

              // 🎬 TYPEWRITER EFFECT: Use flushSync to force immediate render for each chunk
              // This prevents React 18's automatic batching from showing all content at once
              flushSync(() => {
              setMessages((prevMessages) => {
                const newMessages = [...prevMessages]
                const lastMessage = newMessages[newMessages.length - 1]

                // Check if we can append to last message (same team, same run)
                const canAppend = lastMessage &&
                  lastMessage.role === 'agent' &&
                  lastMessage.teamName === teamName &&
                  lastMessage.runId === agnoChunk.run_id

                if (canAppend && typeof chunk.content === 'string') {
                  const uniqueContent = chunk.content.replace(lastContent, '')
                  lastMessage.content += uniqueContent
                  lastContent = chunk.content

                  // Handle tool calls streaming
                  lastMessage.tool_calls = processChunkToolCalls(
                    chunk,
                    lastMessage.tool_calls
                  )
                  if (chunk.extra_data?.reasoning_steps) {
                    lastMessage.extra_data = {
                      ...lastMessage.extra_data,
                      reasoning_steps: chunk.extra_data.reasoning_steps
                    }
                  }

                  if (chunk.extra_data?.references) {
                    lastMessage.extra_data = {
                      ...lastMessage.extra_data,
                      references: chunk.extra_data.references
                    }
                  }

                  if (chunk.images) {
                    lastMessage.images = chunk.images
                  }
                  if (chunk.videos) {
                    lastMessage.videos = chunk.videos
                  }
                  if (chunk.audio) {
                    lastMessage.audio = chunk.audio
                  }
                } else if (canAppend && typeof chunk?.content !== 'string' && chunk.content !== null) {
                  const jsonBlock = getJsonMarkdown(chunk?.content)
                  lastMessage.content += jsonBlock
                  lastContent = jsonBlock
                } else if (canAppend && chunk.response_audio?.transcript && typeof chunk.response_audio?.transcript === 'string') {
                  const transcript = chunk.response_audio.transcript
                  lastMessage.response_audio = {
                    ...lastMessage.response_audio,
                    transcript: lastMessage.response_audio?.transcript + transcript
                  }
                } else if (typeof chunk.content === 'string' || chunk.content !== null) {
                  // Create NEW message with AGNO attribution (different team or new run)
                  const content = typeof chunk.content === 'string' ? chunk.content : getJsonMarkdown(chunk.content)
                  const newMessage: ChatMessage = {
                    role: 'agent',
                    content: content,
                    created_at: Math.floor(Date.now() / 1000),
                    teamName: teamName,
                    teamId: agnoChunk.team_id,
                    runId: agnoChunk.run_id,
                    parentRunId: agnoChunk.parent_run_id,
                    tool_calls: processChunkToolCalls(chunk, []),
                    extra_data: chunk.extra_data,
                    images: chunk.images,
                    videos: chunk.videos,
                    audio: chunk.audio,
                    response_audio: chunk.response_audio
                  }
                  lastContent = typeof chunk.content === 'string' ? chunk.content : content
                  newMessages.push(newMessage)
                }
                return newMessages
              })
              }) // Close flushSync
            } else if (
              chunk.event === RunEvent.ReasoningStep ||
              chunk.event === RunEvent.TeamReasoningStep
            ) {
              setMessages((prevMessages) => {
                const newMessages = [...prevMessages]
                const lastMessage = newMessages[newMessages.length - 1]
                if (lastMessage && lastMessage.role === 'agent') {
                  const existingSteps =
                    lastMessage.extra_data?.reasoning_steps ?? []
                  const incomingSteps = chunk.extra_data?.reasoning_steps ?? []
                  lastMessage.extra_data = {
                    ...lastMessage.extra_data,
                    reasoning_steps: [...existingSteps, ...incomingSteps]
                  }
                }
                return newMessages
              })
            } else if (
              chunk.event === RunEvent.ReasoningCompleted ||
              chunk.event === RunEvent.TeamReasoningCompleted
            ) {
              setMessages((prevMessages) => {
                const newMessages = [...prevMessages]
                const lastMessage = newMessages[newMessages.length - 1]
                if (lastMessage && lastMessage.role === 'agent') {
                  if (chunk.extra_data?.reasoning_steps) {
                    lastMessage.extra_data = {
                      ...lastMessage.extra_data,
                      reasoning_steps: chunk.extra_data.reasoning_steps
                    }
                  }
                }
                return newMessages
              })
            } else if (
              chunk.event === RunEvent.RunError ||
              chunk.event === RunEvent.TeamRunError ||
              chunk.event === RunEvent.TeamRunCancelled
            ) {
              updateMessagesWithErrorState()
              const errorContent =
                (chunk.content as string) ||
                (chunk.event === RunEvent.TeamRunCancelled
                  ? 'Run cancelled'
                  : 'Error during run')
              setStreamingErrorMessage(errorContent)
              if (newSessionId) {
                setSessionsData(
                  (prevSessionsData) =>
                    prevSessionsData?.filter(
                      (session) => session.session_id !== newSessionId
                    ) ?? null
                )
              }
            } else if (
              chunk.event === RunEvent.UpdatingMemory ||
              chunk.event === RunEvent.TeamMemoryUpdateStarted ||
              chunk.event === RunEvent.TeamMemoryUpdateCompleted
            ) {
              // No-op for now; could surface a lightweight UI indicator in the future
            } else if (chunk.event === RunEvent.RunCompleted) {
              // 🔴 FILTER: Ignore RunCompleted from member agents
              // Only TeamRunCompleted contains the final answer
              console.log('🚫 FILTERED: RunCompleted from member agent (not displayed)', {
                agent_name: chunk.agent_name
              })
              // Do nothing - skip member agent completion
            } else if (chunk.event === RunEvent.TeamRunCompleted) {
              // 🔴 FILTER: Only show TeamRunCompleted from CIRKELLINE team (top-level)
              // Ignore TeamRunCompleted from sub-teams
              const teamName = (chunk as { team_name?: string }).team_name
              if (teamName && teamName !== 'Cirkelline') {
                console.log('🚫 FILTERED: TeamRunCompleted from sub-team (not displayed)', {
                  team_name: teamName
                })
                return // Skip sub-team completion
              }

              // ✅ ONLY show TeamRunCompleted from Cirkelline (final answer)
              console.log('✅ CIRKELLINE RUN COMPLETED - Finalizing message')
              setMessages((prevMessages) => {
                const newMessages = prevMessages.map((message, index) => {
                  if (
                    index === prevMessages.length - 1 &&
                    message.role === 'agent'
                  ) {
                    let updatedContent: string
                    if (typeof chunk.content === 'string') {
                      updatedContent = chunk.content
                    } else {
                      try {
                        updatedContent = JSON.stringify(chunk.content)
                      } catch {
                        updatedContent = 'Error parsing response'
                      }
                    }
                    return {
                      ...message,
                      content: updatedContent,
                      tool_calls: processChunkToolCalls(
                        chunk,
                        message.tool_calls
                      ),
                      images: chunk.images ?? message.images,
                      videos: chunk.videos ?? message.videos,
                      response_audio: chunk.response_audio,
                      // DON'T update created_at to keep React key stable
                      extra_data: {
                        reasoning_steps:
                          chunk.extra_data?.reasoning_steps ??
                          message.extra_data?.reasoning_steps,
                        references:
                          chunk.extra_data?.references ??
                          message.extra_data?.references
                      }
                    }
                  }
                  return message
                })
                return newMessages
              })
            }
          },
          onError: (error) => {
            updateMessagesWithErrorState()
            setStreamingErrorMessage(error.message)
            if (newSessionId) {
              setSessionsData(
                (prevSessionsData) =>
                  prevSessionsData?.filter(
                    (session) => session.session_id !== newSessionId
                  ) ?? null
              )
            }
          },
          onComplete: () => {}
        })
      } catch (error) {
        updateMessagesWithErrorState()
        setStreamingErrorMessage(
          error instanceof Error ? error.message : String(error)
        )
        if (newSessionId) {
          setSessionsData(
            (prevSessionsData) =>
              prevSessionsData?.filter(
                (session) => session.session_id !== newSessionId
              ) ?? null
          )
        }
      } finally {
        focusChatInput()
        setIsStreaming(false)
        setActivityStatus(null) // Clear activity status when stream ends
        // Clean up cancel state
        setAbortController(null)
        setCurrentRunId(null)
      }
    },
    [
      setMessages,
      addMessage,
      updateMessagesWithErrorState,
      selectedEndpoint,
      streamResponse,
      agentId,
      teamId,
      mode,
      setStreamingErrorMessage,
      setIsStreaming,
      setActivityStatus,
      focusChatInput,
      setSessionsData,
      sessionId,
      setSessionId,
      processChunkToolCalls,
      getActivityStatus,
      getUserId,
      captureForBehindTheScenes,
      messages.length,
      setAbortController,
      setCurrentRunId
    ]
  )

  return { handleStreamResponse }
}

export default useAIChatStreamHandler
