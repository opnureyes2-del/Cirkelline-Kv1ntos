import { toast } from 'sonner'

import { APIRoutes } from './routes'

import { AgentDetails, Sessions, TeamDetails } from '@/types/os'

export const getAgentsAPI = async (
  endpoint: string
): Promise<AgentDetails[]> => {
  const url = APIRoutes.GetAgents(endpoint)
  try {
    const response = await fetch(url, { method: 'GET' })
    if (!response.ok) {
      toast.error(`Failed to fetch  agents: ${response.statusText}`)
      return []
    }
    const data = await response.json()
    return data
  } catch {
    toast.error('Error fetching  agents')
    return []
  }
}

export const getStatusAPI = async (base: string): Promise<number> => {
  const response = await fetch(APIRoutes.Status(base), {
    method: 'GET'
  })
  return response.status
}

export const getAllSessionsAPI = async (
  base: string,
  type: 'agent' | 'team',
  componentId: string,
  dbId: string,
  userId: string
): Promise<Sessions | { data: [] }> => {
  try {
    const url = new URL(APIRoutes.GetSessions(base))
    url.searchParams.set('type', type)
    url.searchParams.set('component_id', componentId)
    url.searchParams.set('db_id', dbId)
    url.searchParams.set('user_id', userId)

    const response = await fetch(url.toString(), {
      method: 'GET'
    })

    if (!response.ok) {
      if (response.status === 404) {
        return { data: [] }
      }
      throw new Error(`Failed to fetch sessions: ${response.statusText}`)
    }
    return response.json()
  } catch {
    return { data: [] }
  }
}

export const getSessionAPI = async (
  base: string,
  type: 'agent' | 'team',
  sessionId: string,
  dbId?: string
) => {
  // build query string
  const queryParams = new URLSearchParams({ type })
  if (dbId) queryParams.append('db_id', dbId)

  const response = await fetch(
    `${APIRoutes.GetSession(base, sessionId)}?${queryParams.toString()}`,
    {
      method: 'GET'
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to fetch session: ${response.statusText}`)
  }

  return response.json()
}

export const deleteSessionAPI = async (
  base: string,
  dbId: string,
  sessionId: string
) => {
  const queryParams = new URLSearchParams()
  if (dbId) queryParams.append('db_id', dbId)
  const response = await fetch(
    `${APIRoutes.DeleteSession(base, sessionId)}?${queryParams.toString()}`,
    {
      method: 'DELETE'
    }
  )
  return response
}

export const getTeamsAPI = async (endpoint: string): Promise<TeamDetails[]> => {
  const url = APIRoutes.GetTeams(endpoint)
  try {
    const response = await fetch(url, { method: 'GET' })
    if (!response.ok) {
      toast.error(`Failed to fetch  teams: ${response.statusText}`)
      return []
    }
    const data = await response.json()

    return data
  } catch {
    toast.error('Error fetching  teams')
    return []
  }
}

export const deleteTeamSessionAPI = async (
  base: string,
  teamId: string,
  sessionId: string
) => {
  const response = await fetch(
    APIRoutes.DeleteTeamSession(base, teamId, sessionId),
    {
      method: 'DELETE'
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to delete team session: ${response.statusText}`)
  }
  return response
}

// ================================================================================
// Sessions Management API (for /profile/sessions page)
// ================================================================================

export interface SessionListFilters {
  search?: string
  dateFrom?: number // Unix timestamp
  dateTo?: number // Unix timestamp
  sortBy?: 'created_at' | 'updated_at' | 'session_name'
  sortOrder?: 'asc' | 'desc'
}

export interface SessionListItem {
  session_id: string
  session_name: string
  created_at: string // ISO date
  updated_at: string // ISO date
  message_count?: number
}

export interface SessionListResponse {
  data: SessionListItem[]
  page: number
  limit: number
  total: number
}

/**
 * List user sessions with pagination, search, and filters
 * For use in /profile/sessions page
 * Backend automatically filters by user_id from JWT
 */
export const listUserSessionsAPI = async (
  base: string,
  page: number = 1,
  limit: number = 20,
  filters?: SessionListFilters
): Promise<SessionListResponse> => {
  try {
    // Validate base URL
    if (!base || base.trim() === '') {
      console.error('listUserSessionsAPI: Invalid base URL:', base)
      throw new Error('Base URL is required')
    }

    const url = new URL(APIRoutes.GetSessions(base))

    // Pagination
    url.searchParams.set('page', page.toString())
    url.searchParams.set('limit', limit.toString())

    // Session type - we only show team sessions (Cirkelline conversations)
    url.searchParams.set('type', 'team')

    // Filters
    if (filters?.search) {
      url.searchParams.set('session_name', filters.search)
    }

    if (filters?.sortBy) {
      url.searchParams.set('sort_by', filters.sortBy)
    }

    if (filters?.sortOrder) {
      url.searchParams.set('sort_order', filters.sortOrder)
    }

    // Date filters
    if (filters?.dateFrom) {
      url.searchParams.set('created_after', filters.dateFrom.toString())
    }

    if (filters?.dateTo) {
      url.searchParams.set('created_before', filters.dateTo.toString())
    }

    // Get JWT token from localStorage
    const token = localStorage.getItem('token')

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      credentials: 'include'
    })

    if (!response.ok) {
      if (response.status === 404) {
        return { data: [], page, limit, total: 0 }
      }
      throw new Error(`Failed to fetch sessions: ${response.statusText}`)
    }

    const result = await response.json()

    // Backend returns pagination info in 'meta' object
    const meta = result.meta || {}

    return {
      data: result.data || [],
      page: meta.page || page,
      limit: meta.limit || limit,
      total: meta.total_count || 0
    }
  } catch (error) {
    console.error('Error fetching user sessions:', error)
    toast.error('Failed to load sessions')
    return { data: [], page, limit, total: 0 }
  }
}

/**
 * Get detailed session information
 * For use in session details modal
 */
export const getSessionDetailsAPI = async (
  base: string,
  sessionId: string
) => {
  try {
    const url = new URL(APIRoutes.GetSessionDetails(base, sessionId))
    url.searchParams.set('type', 'team')

    // Get JWT token from localStorage
    const token = localStorage.getItem('token')

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch session details: ${response.statusText}`)
    }

    return response.json()
  } catch (error) {
    console.error('Error fetching session details:', error)
    toast.error('Failed to load session details')
    throw error
  }
}

/**
 * Delete multiple sessions at once
 * For use in bulk delete operation
 */
export const bulkDeleteSessionsAPI = async (
  base: string,
  sessionIds: string[]
): Promise<boolean> => {
  try {
    const response = await fetch(APIRoutes.BulkDeleteSessions(base), {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        session_ids: sessionIds,
        types: sessionIds.map(() => 'team') // All sessions are team type
      })
    })

    if (!response.ok) {
      throw new Error(`Failed to delete sessions: ${response.statusText}`)
    }

    toast.success(`Successfully deleted ${sessionIds.length} session${sessionIds.length > 1 ? 's' : ''}`)
    return true
  } catch (error) {
    console.error('Error bulk deleting sessions:', error)
    toast.error('Failed to delete sessions')
    return false
  }
}
