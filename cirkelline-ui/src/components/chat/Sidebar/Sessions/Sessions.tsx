'use client'

import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import { useQueryState } from 'nuqs'

import { useStore } from '@/store'
import useSessionLoader from '@/hooks/useSessionLoader'
import { useSidebar } from '@/hooks/useSidebar'

import SessionItem from './SessionItem'
import SessionBlankState from './SessionBlankState'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

// Hook to detect mobile view
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  return isMobile
}

interface SkeletonListProps {
  skeletonCount: number
}
const SkeletonList: FC<SkeletonListProps> = ({ skeletonCount }) => {
  const list = useMemo(
    () => Array.from({ length: skeletonCount }, (_, i) => i),
    [skeletonCount]
  )

  return list.map((k, idx) => (
    <Skeleton
      key={k}
      className={cn(
        'mb-1 h-14 rounded-lg bg-light-surface px-3 py-2 dark:bg-dark-surface',
        idx > 0 && 'bg-light-bg dark:bg-dark-bg'
      )}
    />
  ))
}

const Sessions = () => {
  const { isCollapsed } = useSidebar()
  const isMobile = useIsMobile()

  // On mobile, sidebar is never "collapsed" - it slides in full-width
  // Only use collapsed view on desktop (md+)
  const effectiveIsCollapsed = isMobile ? false : isCollapsed

  const [agentId] = useQueryState('agent', {
    parse: (v) => v || undefined,
    history: 'push'
  })
  const [teamId] = useQueryState('team')
  const [sessionId] = useQueryState('session')
  const [dbId] = useQueryState('db_id')

  const {
    selectedEndpoint,
    mode,
    isEndpointActive,
    isEndpointLoading,
    hydrated,
    sessionsData,
    setSessionsData,
    isSessionsLoading
  } = useStore()

  console.log({ sessionsData })

  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null
  )

  const { getSessions, getSession } = useSessionLoader()

  useEffect(() => {
    if (hydrated && sessionId && selectedEndpoint && (agentId || teamId)) {
      const entityType = agentId ? 'agent' : 'team'
      getSession({ entityType, agentId, teamId, dbId }, sessionId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, sessionId, selectedEndpoint, agentId, teamId, dbId])

  useEffect(() => {
    console.log('🔍 Sessions useEffect triggered:', {
      selectedEndpoint,
      isEndpointLoading,
      agentId,
      teamId,
      dbId,
      mode
    })

    if (!selectedEndpoint || isEndpointLoading) {
      console.log('❌ Early return: endpoint not ready')
      return
    }

    if (!(agentId || teamId || dbId)) {
      console.log('❌ Early return: missing agentId/teamId/dbId')
      setSessionsData([])
      return
    }

    console.log('✅ Calling getSessions with:', { mode, agentId, teamId, dbId })
    // ✅ REMOVED: Don't clear sessions here - the merge logic in useSessionLoader preserves optimistic sessions
    getSessions({
      entityType: mode,
      agentId,
      teamId,
      dbId
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selectedEndpoint,
    agentId,
    teamId,
    mode,
    isEndpointLoading,
    getSessions,
    dbId
  ])

  useEffect(() => {
    if (sessionId) setSelectedSessionId(sessionId)
  }, [sessionId])

  const handleSessionClick = useCallback(
    (id: string) => () => setSelectedSessionId(id),
    []
  )

  if (isSessionsLoading || isEndpointLoading) {
    return (
      <div className="w-full px-2 py-2">
        <SkeletonList skeletonCount={6} />
      </div>
    )
  }

  return (
    <div className="w-full font-body">

      {!isEndpointActive ||
      (!isSessionsLoading &&
        (!sessionsData || sessionsData?.length === 0)) ? (
        <SessionBlankState />
      ) : (
        <div className={`flex flex-col gap-y-1 ${effectiveIsCollapsed ? '' : 'pr-1'}`}>
          {sessionsData?.slice(0, 6).map((entry, idx) => (
            <SessionItem
              key={`${entry?.session_id}-${idx}`}
              currentSessionId={selectedSessionId}
              isSelected={selectedSessionId === entry?.session_id}
              onSessionClick={handleSessionClick(entry?.session_id)}
              session_name={entry?.session_name ?? '-'}
              session_id={entry?.session_id}
              created_at={entry?.created_at}
              isCollapsed={effectiveIsCollapsed}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default Sessions
