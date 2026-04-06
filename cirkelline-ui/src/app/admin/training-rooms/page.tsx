'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  BookOpen,
  RefreshCw,
  Search,
  ChevronRight,
  GraduationCap,
  Clock,
  Filter
} from 'lucide-react'

interface TrainingRoom {
  id: string
  name: string
  phase: string
  mastery_level: number
  sessions_completed: number
  total_sessions: number
  is_active: boolean
  last_activity: string
  collaboration_score: number
  team_name?: string
}

const PHASE_COLORS: Record<string, string> = {
  foundations: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  guided: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  graduated: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  archived: 'bg-gray-100 text-gray-600 dark:bg-gray-800/30 dark:text-gray-400',
  intermediate: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
  validation: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  mastery: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
}

export default function TrainingRoomsPage() {
  const router = useRouter()
  const [rooms, setRooms] = useState<TrainingRoom[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [phaseFilter, setPhaseFilter] = useState<string>('all')

  const fetchRooms = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetch('/api/training-rooms')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const roomList = data.rooms || data || []
      setRooms(Array.isArray(roomList) ? roomList : [])
    } catch {
      setError('Kunne ikke hente training rooms fra Cosmic')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchRooms() }, [fetchRooms])

  const phases = ['all', ...new Set(rooms.map(r => r.phase).filter(Boolean))]

  const filtered = rooms
    .filter(r => phaseFilter === 'all' || r.phase === phaseFilter)
    .filter(r => !search || r.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => (b.mastery_level || 0) - (a.mastery_level || 0))

  const masteryPct = (m: number) => Math.round((m || 0) * 100)

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <BookOpen className="w-7 h-7 text-accent" />
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-light-text dark:text-dark-text font-heading">
                Training Rooms
              </h1>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                {rooms.length} rooms fra Cosmic Library
              </p>
            </div>
          </div>
          <button
            onClick={() => { setLoading(true); fetchRooms() }}
            className="flex items-center gap-2 px-3 py-2 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline text-sm">Refresh</span>
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
            <input
              type="text"
              placeholder="Search rooms..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-light-surface dark:bg-dark-surface border border-border-primary rounded-lg text-sm text-light-text dark:text-dark-text placeholder:text-light-text-secondary"
            />
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <Filter className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary flex-shrink-0" />
            {phases.map(phase => (
              <button
                key={phase}
                onClick={() => setPhaseFilter(phase)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                  phaseFilter === phase
                    ? 'bg-accent text-white'
                    : 'bg-light-surface dark:bg-dark-surface border border-border-primary text-light-text dark:text-dark-text hover:border-accent'
                }`}
              >
                {phase === 'all' ? `All (${rooms.length})` : `${phase} (${rooms.filter(r => r.phase === phase).length})`}
              </button>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && rooms.length === 0 && (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Room Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(room => (
            <button
              key={room.id}
              onClick={() => router.push(`/admin/training-rooms/${room.id}`)}
              className="text-left bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4 hover:border-accent active:scale-[0.98] transition-all"
            >
              {/* Room Name + Phase */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="text-sm font-semibold text-light-text dark:text-dark-text line-clamp-2 flex-1">
                  {room.name}
                </h3>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${PHASE_COLORS[room.phase] || PHASE_COLORS.foundations}`}>
                  {room.phase}
                </span>
              </div>

              {/* Mastery Bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary flex items-center gap-1">
                    <GraduationCap className="w-3 h-3" /> Mastery
                  </span>
                  <span className="text-xs font-medium text-light-text dark:text-dark-text">
                    {masteryPct(room.mastery_level)}%
                  </span>
                </div>
                <div className="h-2 bg-light-bg dark:bg-dark-bg rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      masteryPct(room.mastery_level) >= 80 ? 'bg-green-500' :
                      masteryPct(room.mastery_level) >= 50 ? 'bg-amber-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${Math.max(masteryPct(room.mastery_level), 2)}%` }}
                  />
                </div>
              </div>

              {/* Stats Row */}
              <div className="flex items-center justify-between text-xs text-light-text-secondary dark:text-dark-text-secondary">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {room.sessions_completed}/{room.total_sessions} sessions
                </span>
                <span className={`flex items-center gap-1 ${room.is_active ? 'text-green-600 dark:text-green-400' : ''}`}>
                  {room.is_active ? 'Active' : 'Inactive'}
                </span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </button>
          ))}
        </div>

        {/* Empty State */}
        {!loading && filtered.length === 0 && (
          <div className="text-center py-12 text-light-text-secondary dark:text-dark-text-secondary">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Ingen training rooms fundet</p>
          </div>
        )}
      </div>
    </div>
  )
}
