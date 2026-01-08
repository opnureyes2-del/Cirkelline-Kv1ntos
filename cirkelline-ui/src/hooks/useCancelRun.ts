import { useCallback } from 'react'
import { useStore } from '@/store'
import { APIRoutes } from '@/api/routes'
import { getAuthHeaders } from '@/lib/auth-headers'
import { useAuth } from '@/contexts/AuthContext'
import { constructEndpointUrl } from '@/lib/constructEndpointUrl'

/**
 * Hook for cancelling an ongoing AI run.
 * Uses dual-layer cancellation:
 * 1. Frontend AbortController - immediately aborts fetch
 * 2. Backend cancel endpoint - ensures AGNO cleanup
 */
export const useCancelRun = () => {
  const { getUserId } = useAuth()
  const selectedEndpoint = useStore((state) => state.selectedEndpoint)
  const currentRunId = useStore((state) => state.currentRunId)
  const abortController = useStore((state) => state.abortController)
  const setIsStreaming = useStore((state) => state.setIsStreaming)
  const setActivityStatus = useStore((state) => state.setActivityStatus)
  const setCurrentRunId = useStore((state) => state.setCurrentRunId)
  const setAbortController = useStore((state) => state.setAbortController)
  const isCancelling = useStore((state) => state.isCancelling)
  const setIsCancelling = useStore((state) => state.setIsCancelling)
  const setMessages = useStore((state) => state.setMessages)

  const cancelRun = useCallback(async () => {
    // Prevent double-click / multiple cancel calls
    if (isCancelling) return
    setIsCancelling(true)

    try {
      // 1. Abort fetch immediately for instant UI response
      if (abortController) {
        abortController.abort()
        setAbortController(null)
      }

      // 2. Update UI state
      setIsStreaming(false)
      setActivityStatus(null)

      // 3. Append cancelled text to the last agent message
      setMessages((prev) => {
        const newMsgs = [...prev]
        const lastMessage = newMsgs[newMsgs.length - 1]
        if (lastMessage?.role === 'agent') {
          // If there's content, append. Otherwise just show cancelled text
          lastMessage.content = lastMessage.content?.trim()
            ? `${lastMessage.content}\n\n*[Response cancelled by user]*`
            : '*[Response cancelled by user]*'
        }
        return newMsgs
      })

      // 4. Call backend cancel endpoint for proper AGNO cleanup
      if (currentRunId) {
        const url = APIRoutes.CancelTeamRun(
          constructEndpointUrl(selectedEndpoint),
          'cirkelline',
          currentRunId
        )
        const formData = new FormData()
        formData.append('user_id', getUserId())

        // Fire and forget - don't block on backend response
        // The abort already worked, this is just for backend cleanup
        fetch(url, {
          method: 'POST',
          headers: getAuthHeaders(),
          body: formData
        }).catch((error) => {
          // Ignore errors - the abort already worked
          console.log('Cancel endpoint call failed (non-blocking):', error)
        })

        setCurrentRunId(null)
      }
    } finally {
      setIsCancelling(false)
    }
  }, [
    isCancelling,
    setIsCancelling,
    abortController,
    setAbortController,
    setIsStreaming,
    setActivityStatus,
    setMessages,
    currentRunId,
    selectedEndpoint,
    getUserId,
    setCurrentRunId
  ])

  return { cancelRun, isCancelling }
}
