import { describe, it, expect, beforeEach, vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Import store after mocking localStorage
import { useStore } from '@/store'

describe('Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useStore())
    act(() => {
      result.current.setMessages([])
      result.current.setIsStreaming(false)
      result.current.setActivityStatus(null)
      result.current.setEndpoints([])
      result.current.setAgents([])
      result.current.setTeams([])
      result.current.setSessionsData(() => null)
      result.current.setCurrentRunId(null)
      result.current.setIsCancelling(false)
    })
    vi.clearAllMocks()
  })

  describe('messages', () => {
    it('should set messages directly', () => {
      const { result } = renderHook(() => useStore())

      const messages = [
        { role: 'user' as const, content: 'Hello' },
        { role: 'assistant' as const, content: 'Hi there!' },
      ]

      act(() => {
        result.current.setMessages(messages as any)
      })

      expect(result.current.messages).toEqual(messages)
    })

    it('should update messages with function', () => {
      const { result } = renderHook(() => useStore())

      const initialMessage = { role: 'user' as const, content: 'Hello' }
      const newMessage = { role: 'assistant' as const, content: 'Hi!' }

      act(() => {
        result.current.setMessages([initialMessage] as any)
      })

      act(() => {
        result.current.setMessages((prev) => [...prev, newMessage] as any)
      })

      expect(result.current.messages).toHaveLength(2)
    })
  })

  describe('streaming state', () => {
    it('should toggle streaming state', () => {
      const { result } = renderHook(() => useStore())

      expect(result.current.isStreaming).toBe(false)

      act(() => {
        result.current.setIsStreaming(true)
      })

      expect(result.current.isStreaming).toBe(true)

      act(() => {
        result.current.setIsStreaming(false)
      })

      expect(result.current.isStreaming).toBe(false)
    })
  })

  describe('activity status', () => {
    it('should set activity status', () => {
      const { result } = renderHook(() => useStore())

      expect(result.current.activityStatus).toBeNull()

      act(() => {
        result.current.setActivityStatus('typing')
      })

      expect(result.current.activityStatus).toBe('typing')

      act(() => {
        result.current.setActivityStatus(null)
      })

      expect(result.current.activityStatus).toBeNull()
    })
  })

  describe('endpoint state', () => {
    it('should set endpoints', () => {
      const { result } = renderHook(() => useStore())

      const endpoints = [
        { endpoint: '/api/chat', id__endpoint: 'chat-1' },
        { endpoint: '/api/search', id__endpoint: 'search-1' },
      ]

      act(() => {
        result.current.setEndpoints(endpoints)
      })

      expect(result.current.endpoints).toEqual(endpoints)
    })

    it('should set selected endpoint', () => {
      const { result } = renderHook(() => useStore())

      act(() => {
        result.current.setSelectedEndpoint('http://localhost:7777')
      })

      expect(result.current.selectedEndpoint).toBe('http://localhost:7777')
    })

    it('should set endpoint loading state', () => {
      const { result } = renderHook(() => useStore())

      act(() => {
        result.current.setIsEndpointLoading(true)
      })

      expect(result.current.isEndpointLoading).toBe(true)

      act(() => {
        result.current.setIsEndpointLoading(false)
      })

      expect(result.current.isEndpointLoading).toBe(false)
    })
  })

  describe('mode', () => {
    it('should default to team mode', () => {
      const { result } = renderHook(() => useStore())
      expect(result.current.mode).toBe('team')
    })

    it('should switch between modes', () => {
      const { result } = renderHook(() => useStore())

      act(() => {
        result.current.setMode('agent')
      })

      expect(result.current.mode).toBe('agent')

      act(() => {
        result.current.setMode('team')
      })

      expect(result.current.mode).toBe('team')
    })
  })

  describe('cancel run state', () => {
    it('should manage run id', () => {
      const { result } = renderHook(() => useStore())

      expect(result.current.currentRunId).toBeNull()

      act(() => {
        result.current.setCurrentRunId('run-123')
      })

      expect(result.current.currentRunId).toBe('run-123')
    })

    it('should manage cancelling state', () => {
      const { result } = renderHook(() => useStore())

      expect(result.current.isCancelling).toBe(false)

      act(() => {
        result.current.setIsCancelling(true)
      })

      expect(result.current.isCancelling).toBe(true)
    })
  })

  describe('sessions', () => {
    it('should set sessions data', () => {
      const { result } = renderHook(() => useStore())

      const sessions = [
        { session_id: '1', name: 'Session 1' },
        { session_id: '2', name: 'Session 2' },
      ]

      act(() => {
        result.current.setSessionsData(sessions as any)
      })

      expect(result.current.sessionsData).toEqual(sessions)
    })

    it('should update sessions with function', () => {
      const { result } = renderHook(() => useStore())

      const initialSessions = [{ session_id: '1', name: 'Session 1' }]

      act(() => {
        result.current.setSessionsData(initialSessions as any)
      })

      act(() => {
        result.current.setSessionsData((prev) => [
          ...(prev || []),
          { session_id: '2', name: 'Session 2' },
        ] as any)
      })

      expect(result.current.sessionsData).toHaveLength(2)
    })
  })
})
