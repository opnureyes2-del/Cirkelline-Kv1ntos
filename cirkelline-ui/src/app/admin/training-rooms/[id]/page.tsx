'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft,
  BookOpen,
  GraduationCap,
  Clock,
  Users,
  Settings,
  Activity,
  Tag,
  Shield
} from 'lucide-react'

interface RoomDetail {
  id: string
  name: string
  team_id: string
  team_name: string
  phase: string
  current_lesson: string | null
  sessions_completed: number
  total_sessions: number
  mastery_level: number
  avg_response_quality: number
  collaboration_score: number
  is_active: boolean
  last_activity: string
  observer_notes: string | null
  training_config: {
    type: string
    domain: string
    tags: string[]
    task_description: string
    commanding_admiral: string
    participants: string[]
    assembled_at: string
    auto_gathered: boolean
  }
}

const PHASE_COLORS: Record<string, string> = {
  foundations: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  guided: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  graduated: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  archived: 'bg-gray-100 text-gray-600 dark:bg-gray-800/30 dark:text-gray-400',
}

export default function TrainingRoomDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [room, setRoom] = useState<RoomDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!params.id) return
    setLoading(true)
    fetch(`/api/training-rooms/${params.id}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => setRoom(data))
      .catch(() => setError('Room ikke fundet'))
      .finally(() => setLoading(false))
  }, [params.id])

  const masteryPct = (m: number) => Math.round((m || 0) * 100)

  const formatDate = (d: string) => {
    if (!d) return 'Aldrig'
    return new Date(d).toLocaleString('da-DK', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  }

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh]">
      <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (error || !room) return (
    <div className="p-8 text-center">
      <p className="text-red-500 mb-4">{error || 'Room ikke fundet'}</p>
      <button onClick={() => router.push('/admin/training-rooms')} className="text-accent hover:underline">
        Tilbage til Training Rooms
      </button>
    </div>
  )

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Back + Header */}
        <button
          onClick={() => router.push('/admin/training-rooms')}
          className="flex items-center gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-accent mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Tilbage til Training Rooms
        </button>

        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-accent flex-shrink-0" />
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-light-text dark:text-dark-text font-heading">
                {room.name}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PHASE_COLORS[room.phase] || PHASE_COLORS.foundations}`}>
                  {room.phase}
                </span>
                <span className={`text-xs ${room.is_active ? 'text-green-600 dark:text-green-400' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                  {room.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Mastery */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6 mb-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold text-light-text dark:text-dark-text flex items-center gap-2">
              <GraduationCap className="w-4 h-4" /> Mastery Level
            </h2>
            <span className="text-2xl font-bold text-accent">{masteryPct(room.mastery_level)}%</span>
          </div>
          <div className="h-3 bg-light-bg dark:bg-dark-bg rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                masteryPct(room.mastery_level) >= 80 ? 'bg-green-500' :
                masteryPct(room.mastery_level) >= 50 ? 'bg-amber-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.max(masteryPct(room.mastery_level), 2)}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary flex items-center gap-1"><Clock className="w-3 h-3" /> Sessions</p>
            <p className="text-xl font-bold text-light-text dark:text-dark-text mt-1">
              {room.sessions_completed}<span className="text-sm font-normal text-light-text-secondary dark:text-dark-text-secondary">/{room.total_sessions}</span>
            </p>
          </div>
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary flex items-center gap-1"><Activity className="w-3 h-3" /> Response Quality</p>
            <p className="text-xl font-bold text-light-text dark:text-dark-text mt-1">{Math.round(room.avg_response_quality * 100)}%</p>
          </div>
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary flex items-center gap-1"><Users className="w-3 h-3" /> Collaboration</p>
            <p className="text-xl font-bold text-light-text dark:text-dark-text mt-1">{Math.round(room.collaboration_score * 100)}%</p>
          </div>
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary flex items-center gap-1"><Clock className="w-3 h-3" /> Last Activity</p>
            <p className="text-sm font-medium text-light-text dark:text-dark-text mt-1">{formatDate(room.last_activity)}</p>
          </div>
        </div>

        {/* Training Config */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6 mb-6">
          <h2 className="text-sm font-semibold text-light-text dark:text-dark-text flex items-center gap-2 mb-4">
            <Settings className="w-4 h-4" /> Training Configuration
          </h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Task</span>
              <span className="text-sm text-light-text dark:text-dark-text">{room.training_config.task_description || 'Ingen beskrivelse'}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Admiral</span>
              <span className="text-sm font-medium text-accent flex items-center gap-1">
                <Shield className="w-3 h-3" /> {room.training_config.commanding_admiral}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Domain</span>
              <span className="text-sm text-light-text dark:text-dark-text">{room.training_config.domain}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Type</span>
              <span className="text-sm text-light-text dark:text-dark-text">{room.training_config.type}</span>
            </div>
            {room.training_config.tags.length > 0 && (
              <div className="flex items-start gap-3">
                <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Tags</span>
                <div className="flex flex-wrap gap-1">
                  {room.training_config.tags.map(tag => (
                    <span key={tag} className="px-2 py-0.5 bg-accent/10 text-accent rounded-full text-xs flex items-center gap-1">
                      <Tag className="w-3 h-3" /> {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="flex items-center gap-3">
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Auto-gathered</span>
              <span className="text-sm text-light-text dark:text-dark-text">{room.training_config.auto_gathered ? 'Ja' : 'Nej'}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary w-32 flex-shrink-0">Assembled</span>
              <span className="text-sm text-light-text dark:text-dark-text">{formatDate(room.training_config.assembled_at)}</span>
            </div>
          </div>
        </div>

        {/* Observer Notes */}
        {room.observer_notes && (
          <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-6">
            <h2 className="text-sm font-semibold text-light-text dark:text-dark-text mb-2">Observer Notes</h2>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary whitespace-pre-wrap">{room.observer_notes}</p>
          </div>
        )}
      </div>
    </div>
  )
}
