'use client'

import TasksBoardView from './TasksBoardView'

interface TaskList {
  id: string
  name: string
}

interface TasksPanelProps {
  isOpen: boolean
  googleSyncEnabled?: boolean
  layoutMode?: 'stacked' | 'side-by-side'
  showCompleted?: boolean
  selectedListId?: string | null
  onListChange?: (listId: string) => void
  onListsLoaded?: (lists: TaskList[]) => void
}

export default function TasksPanel({
  isOpen,
  googleSyncEnabled = false,
  layoutMode = 'stacked',
  showCompleted = true,
  selectedListId,
  onListChange,
  onListsLoaded
}: TasksPanelProps) {
  if (!isOpen) return null

  return (
    <div className="h-full min-h-0 overflow-hidden">
      <TasksBoardView
        googleSyncEnabled={googleSyncEnabled}
        layoutMode={layoutMode}
        showCompleted={showCompleted}
        selectedListId={selectedListId}
        onListChange={onListChange}
        onListsLoaded={onListsLoaded}
      />
    </div>
  )
}
