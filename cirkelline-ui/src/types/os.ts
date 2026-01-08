export interface ToolCall {
  role: 'user' | 'tool' | 'system' | 'assistant'
  content: string | null
  tool_call_id: string
  tool_name: string
  tool_args: Record<string, string>
  tool_call_error: boolean
  metrics: {
    time: number
  }
  created_at: number
}

export interface ReasoningSteps {
  title: string
  action?: string
  result: string
  reasoning: string
  confidence?: number
  next_action?: string
}
export interface ReasoningStepProps {
  index: number
  stepTitle: string
}
export interface ReasoningProps {
  reasoning: ReasoningSteps[]
}

// Behind the Scenes Event Tracking
export interface BehindTheScenesEvent {
  id: string
  timestamp: number
  eventType: RunEvent
  source: string              // Agent/team name (e.g., "Cirkelline", "Web Researcher")
  sourceType: 'main' | 'team' | 'agent'
  description: string         // Human-readable description
  details?: {
    toolName?: string
    toolArgs?: Record<string, unknown>
    toolResult?: string
    executionTime?: number
    reasoningContent?: string
    action?: string
    confidence?: number
    // Retry event fields
    retryAttempt?: number
    maxRetries?: number
    retryDelay?: number
    // Error event fields
    errorType?: string
    retryAttempts?: number
    // Metrics event fields
    metrics?: TokenMetrics
    tokenUsage?: {
      input: number
      output: number
      total: number
    }
    costs?: {
      input: number
      output: number
      total: number
    }
    model?: string
  }
  status: 'started' | 'in_progress' | 'completed' | 'error'
  depth: number              // For hierarchical indent (0=Cirkelline, 1=sub-team/agent)
  parentEventId?: string
}

export type ToolCallProps = {
  tools: ToolCall
}
interface ModelMessage {
  content: string | null
  context?: MessageContext[]
  created_at: number
  metrics?: {
    time: number
    prompt_tokens: number
    input_tokens: number
    completion_tokens: number
    output_tokens: number
  }
  name: string | null
  role: string
  tool_args?: unknown
  tool_call_id: string | null
  tool_calls: Array<{
    function: {
      arguments: string
      name: string
    }
    id: string
    type: string
  }> | null
}

export interface Model {
  name: string
  model: string
  provider: string
}

export interface Agent {
  agent_id: string
  name: string
  description: string
  model: Model
  storage?: boolean
}

export interface Team {
  team_id: string
  name: string
  description: string
  model: Model
  storage?: boolean
}

interface MessageContext {
  query: string
  docs?: Array<Record<string, object>>
  time?: number
}

export enum RunEvent {
  RunStarted = 'RunStarted',
  RunContent = 'RunContent',
  RunCompleted = 'RunCompleted',
  RunError = 'RunError',
  RunOutput = 'RunOutput',
  UpdatingMemory = 'UpdatingMemory',
  ToolCallStarted = 'ToolCallStarted',
  ToolCallCompleted = 'ToolCallCompleted',
  MemoryUpdateStarted = 'MemoryUpdateStarted',
  MemoryUpdateCompleted = 'MemoryUpdateCompleted',
  ReasoningStarted = 'ReasoningStarted',
  ReasoningStep = 'ReasoningStep',
  ReasoningCompleted = 'ReasoningCompleted',
  RunCancelled = 'RunCancelled',
  RunPaused = 'RunPaused',
  RunContinued = 'RunContinued',
  // Team Events
  TeamRunStarted = 'TeamRunStarted',
  TeamRunContent = 'TeamRunContent',
  TeamRunCompleted = 'TeamRunCompleted',
  TeamRunError = 'TeamRunError',
  TeamRunCancelled = 'TeamRunCancelled',
  TeamToolCallStarted = 'TeamToolCallStarted',
  TeamToolCallCompleted = 'TeamToolCallCompleted',
  TeamReasoningStarted = 'TeamReasoningStarted',
  TeamReasoningStep = 'TeamReasoningStep',
  TeamReasoningCompleted = 'TeamReasoningCompleted',
  TeamMemoryUpdateStarted = 'TeamMemoryUpdateStarted',
  TeamMemoryUpdateCompleted = 'TeamMemoryUpdateCompleted',
  // Custom Backend Events
  Retry = 'retry',
  Error = 'error',
  MetricsUpdate = 'MetricsUpdate',
  Paused = 'paused'
}

export interface TokenMetrics {
  input_tokens: number
  output_tokens: number
  total_tokens: number
  input_cost: number
  output_cost: number
  total_cost: number
  model: string
}

export interface ResponseAudio {
  id?: string
  content?: string
  transcript?: string
  channels?: number
  sample_rate?: number
}

export interface NewRunResponse {
  status: 'RUNNING' | 'PAUSED' | 'CANCELLED'
}

export interface RunResponseContent {
  content?: string | object
  content_type: string
  context?: MessageContext[]
  event: RunEvent
  event_data?: object
  messages?: ModelMessage[]
  metrics?: TokenMetrics
  model?: string
  run_id?: string
  agent_id?: string
  session_id?: string
  tool?: ToolCall
  tools?: Array<ToolCall>
  created_at: number
  extra_data?: AgentExtraData
  images?: ImageData[]
  videos?: VideoData[]
  audio?: AudioData[]
  response_audio?: ResponseAudio
}

export interface RunResponse {
  content?: string | object
  content_type: string
  context?: MessageContext[]
  event: RunEvent
  event_data?: object
  messages?: ModelMessage[]
  metrics?: TokenMetrics
  model?: string
  run_id?: string
  agent_id?: string
  agent_name?: string
  team_name?: string
  session_id?: string
  tool?: ToolCall
  tools?: Array<ToolCall>
  created_at: number
  extra_data?: AgentExtraData
  images?: ImageData[]
  videos?: VideoData[]
  audio?: AudioData[]
  response_audio?: ResponseAudio
}

export interface AgentExtraData {
  reasoning_steps?: ReasoningSteps[]
  reasoning_messages?: ReasoningMessage[]
  references?: ReferenceData[]
}

export interface AgentExtraData {
  reasoning_messages?: ReasoningMessage[]
  references?: ReferenceData[]
}

export interface ReasoningMessage {
  role: 'user' | 'tool' | 'system' | 'assistant'
  content: string | null
  tool_call_id?: string
  tool_name?: string
  tool_args?: Record<string, string>
  tool_call_error?: boolean
  metrics?: {
    time: number
  }
  created_at?: number
}
export interface ChatMessage {
  role: 'user' | 'agent' | 'assistant' | 'system' | 'tool' | 'delegation'
  content: string
  streamingError?: boolean
  created_at: number
  tool_calls?: ToolCall[]
  extra_data?: {
    reasoning_steps?: ReasoningSteps[]
    reasoning_messages?: ReasoningMessage[]
    references?: ReferenceData[]
  }
  images?: ImageData[]
  videos?: VideoData[]
  audio?: AudioData[]
  response_audio?: ResponseAudio
  // AGNO Attribution Fields (for multi-agent transparency)
  teamId?: string
  teamName?: string
  agentId?: string
  agentName?: string
  runId?: string
  parentRunId?: string
  isDelegation?: boolean  // True if this is a delegation message
  delegatedTo?: string    // Who was this delegated to?
  delegationTask?: string // What task was delegated?
  // Behind the Scenes Timeline
  behindTheScenes?: BehindTheScenesEvent[]  // Complete event timeline for this message
  // Human-in-the-Loop (HITL) Fields
  hitlPaused?: boolean    // True if agent is waiting for user input
  hitlRunId?: string      // Run ID to continue
  hitlSessionId?: string  // Session ID for continue
  hitlRequirements?: Array<{
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

export interface AgentDetails {
  id: string
  name?: string
  db_id?: string
  // Model
  model?: Model
}

export interface TeamDetails {
  id: string
  name?: string
  db_id?: string

  // Model
  model?: Model
}

export interface ImageData {
  revised_prompt: string
  url: string
}

export interface VideoData {
  id: number
  eta: number
  url: string
}

export interface AudioData {
  base64_audio?: string
  mime_type?: string
  url?: string
  id?: string
  content?: string
  channels?: number
  sample_rate?: number
}

export interface ReferenceData {
  query: string
  references: Reference[]
  time?: number
}

export interface Reference {
  content: string
  meta_data: {
    chunk: number
    chunk_size: number
  }
  name: string
}

export interface FeedbackSubmission {
  id: string
  user_id: string
  user_email?: string  // From JOIN with users table
  session_id: string | null
  message_content: string
  feedback_type: 'positive' | 'negative'
  user_comments: string | null
  status: 'unread' | 'seen' | 'done'
  created_at: number
  updated_at: number
}

export interface User {
  id: string
  email: string
  display_name: string | null
  is_admin: boolean
  admin_name?: string
  admin_role?: string
  is_online: boolean
  created_at: number
  updated_at: number
  last_login: number | null
  preferences?: Record<string, unknown>
}

export interface UserDetails extends User {
  account_age_days?: number
  admin_profile?: {
    name: string
    role: string
    personal_context: string
    preferences: string
    custom_instructions: string
  }
  statistics: {
    session_count: number
    memory_count: number
    feedback_count: number
  }
  recent_sessions?: Array<{
    session_id: string
    created_at: number
    updated_at: number
  }>
  recent_memories?: Array<{
    memory: string
    updated_at: number
  }>
  recent_feedback?: Array<{
    id: string
    feedback_type: string
    message_content: string
    user_comments: string | null
    status: string
    created_at: number
  }>
}

export interface AdminStats {
  users: {
    total: number
    online: number
    admins: number
    new_week: number
    new_month: number
  }
  sessions: {
    total: number
    today: number
    week: number
  }
  memories: {
    total: number
  }
  feedback: {
    total: number
    unread: number
    positive: number
    negative: number
  }
  recent_users: Array<{
    id: string
    email: string
    display_name: string | null
    created_at: number
  }>
}

export interface ActivityLog {
  id: string
  timestamp: number
  user_id: string | null
  user_email: string | null
  user_display_name: string | null
  action_type: string
  endpoint: string
  http_method: string
  status_code: number
  success: boolean
  error_message: string | null
  error_type: string | null
  target_user_id: string | null
  target_resource_id: string | null
  resource_type: string | null
  details: Record<string, unknown> | null
  duration_ms: number | null
  ip_address: string | null
  user_agent: string | null
  is_admin: boolean
}

export interface ActivityLogStats {
  total_logs: number
  successful_actions: number
  failed_actions: number
  admin_actions: number
  avg_duration_ms: number
  unique_users: number
  logs_last_24h: number
  failed_logins_last_hour: number
  action_breakdown: Array<{
    action: string
    count: number
  }>
}

export interface SessionEntry {
  session_id: string
  session_name: string
  created_at: number
  updated_at?: number
}

export interface Pagination {
  page: number
  limit: number
  total_pages: number
  total_count: number
}

export interface Sessions extends SessionEntry {
  data: SessionEntry[]
  meta: Pagination
}

export interface ChatEntry {
  message: {
    role: 'user' | 'system' | 'tool' | 'assistant'
    content: string
    created_at: number
  }
  response: {
    content: string
    tools?: ToolCall[]
    extra_data?: {
      reasoning_steps?: ReasoningSteps[]
      reasoning_messages?: ReasoningMessage[]
      references?: ReferenceData[]
    }
    images?: ImageData[]
    videos?: VideoData[]
    audio?: AudioData[]
    response_audio?: {
      transcript?: string
    }
    created_at: number
  }
}
