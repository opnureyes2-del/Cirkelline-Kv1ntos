const AGENT_OS_URL = process.env.NEXT_PUBLIC_AGENT_OS_URL || 'http://localhost:7777'

export interface SendMessageParams {
  agentId?: string
  teamId?: string
  message: string
  files?: File[]
  stream?: boolean
  sessionId?: string
  userId?: string
}

export interface StreamChunk {
  type: 'content' | 'error' | 'done'
  content?: string
  error?: string
}

export async function sendMessage({
  agentId,
  teamId,
  message,
  files = [],
  stream = true,
  sessionId,
  userId,
}: SendMessageParams): Promise<Response> {
  // Determine endpoint
  let endpoint: string
  if (agentId) {
    endpoint = `${AGENT_OS_URL}/agents/${agentId}/runs`
  } else if (teamId) {
    endpoint = `${AGENT_OS_URL}/teams/${teamId}/runs`
  } else {
    throw new Error('Either agentId or teamId must be provided')
  }

  // Create FormData
  const formData = new FormData()
  formData.append('message', message)
  formData.append('stream', stream.toString())

  if (sessionId) {
    formData.append('session_id', sessionId)
  }

  if (userId) {
    formData.append('user_id', userId)
  }

  // Append files
  files.forEach((file) => {
    formData.append('files', file)
  })

  // Send request
  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`AgentOS API error: ${response.status} ${response.statusText}`)
  }

  return response
}

export async function* streamResponse(response: Response): AsyncGenerator<StreamChunk> {
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('Response body is not readable')
  }

  try {
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        yield { type: 'done' }
        break
      }

      // Decode chunk
      buffer += decoder.decode(value, { stream: true })

      // Process complete SSE messages
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()

          if (data === '[DONE]') {
            yield { type: 'done' }
            return
          }

          try {
            const parsed = JSON.parse(data)

            if (parsed.error) {
              yield { type: 'error', error: parsed.error }
            } else if (parsed.content) {
              yield { type: 'content', content: parsed.content }
            }
          } catch {
            // Ignore parse errors for non-JSON data lines
            console.warn('Failed to parse SSE data:', data)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
