'use client'

import { FC, useCallback, useEffect, useMemo, useState } from 'react'
import { useSidebar } from '@/hooks/useSidebar'
import JournalItem, { JournalEntry } from './JournalItem'
import JournalDetailModal from './JournalDetailModal'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { BookOpen } from 'lucide-react'

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

  return (
    <>
      {list.map((k, idx) => (
        <Skeleton
          key={k}
          className={cn(
            'mb-1 h-12 rounded-lg bg-light-surface px-3 py-2 dark:bg-dark-surface',
            idx > 0 && 'bg-light-bg dark:bg-dark-bg'
          )}
        />
      ))}
    </>
  )
}

const JournalBlankState = () => (
  <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
    <BookOpen className="w-8 h-8 text-light-text-secondary dark:text-dark-text-secondary opacity-30 mb-2" />
    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
      No journals yet
    </p>
    <p className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary mt-1 opacity-70">
      Journals are created daily from your conversations
    </p>
  </div>
)

const Journals = () => {
  const { isCollapsed } = useSidebar()
  const isMobile = useIsMobile()
  const effectiveIsCollapsed = isMobile ? false : isCollapsed

  const [journals, setJournals] = useState<JournalEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [, setTotal] = useState(0)
  const [selectedJournal, setSelectedJournal] = useState<JournalEntry | null>(null)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  const fetchJournals = useCallback(async () => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        setIsLoading(false)
        return
      }

      const res = await fetch(`${apiUrl}/api/journals?limit=7`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (res.ok) {
        const data = await res.json()
        setJournals(data.journals || [])
        setTotal(data.total || 0)
      }
    } catch (error) {
      console.error('Failed to fetch journals:', error)
    } finally {
      setIsLoading(false)
    }
  }, [apiUrl])

  useEffect(() => {
    fetchJournals()
  }, [fetchJournals])

  const handleJournalClick = (journal: JournalEntry) => {
    setSelectedJournal(journal)
  }

  if (isLoading) {
    return (
      <div className="w-full px-2 py-2">
        <SkeletonList skeletonCount={3} />
      </div>
    )
  }

  return (
    <div className="w-full font-body">
      {journals.length === 0 ? (
        <JournalBlankState />
      ) : (
        <div className={`flex flex-col gap-y-1 ${effectiveIsCollapsed ? '' : 'pr-1'}`}>
          {journals.map((journal) => (
            <JournalItem
              key={journal.id}
              journal={journal}
              isCollapsed={effectiveIsCollapsed}
              onClick={() => handleJournalClick(journal)}
            />
          ))}
        </div>
      )}

      {/* Journal Detail Modal */}
      <JournalDetailModal
        journal={selectedJournal}
        journals={journals}
        onClose={() => setSelectedJournal(null)}
        onNavigate={(journal) => setSelectedJournal(journal)}
      />
    </div>
  )
}

export default Journals
