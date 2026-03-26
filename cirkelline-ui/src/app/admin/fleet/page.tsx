'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Ship,
  Heart,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Activity,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Star,
  BookOpen,
  Gavel,
  Zap,
  Eye,
  Shield,
  Minus
} from 'lucide-react'

// ─── Types ───────────────────────────────────────────────────────────────────

interface AdmiralData {
  name: string
  score: number
  skills_count: number
  status: string
  skills?: SkillData[]
}

interface SkillData {
  name: string
  score: number
  interval: string
  last_run?: string
  status?: string
}

interface FleetData {
  health_score: number
  admiral_count: number
  total_skills: number
  admiral_avg: number
  skills_avg: number
  over_80_pct: number
  under_70_count: number
  under_70_skills: string[]
  admirals: AdmiralData[]
  movements?: MovementData[]
  excellence?: string[]
  timestamp?: string
}

interface MovementData {
  admiral: string
  skill: string
  from: number
  to: number
  change: number
}

interface LearningData {
  recent_sessions?: LearningSession[]
  council_decisions?: CouncilDecision[]
  pipeline_stats?: PipelineStats
}

interface LearningSession {
  id: string
  admiral: string
  topic: string
  timestamp: string
  outcome?: string
}

interface CouncilDecision {
  id: string
  message: string
  verdict: string
  timestamp: string
  provider?: string
}

interface PipelineStats {
  events_ingested: number
  patterns_detected: number
  layers: number
  version: string
}

interface GuideSection {
  title: string
  content: string
  section_id: string
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const scoreColor = (score: number) =>
  score >= 95 ? 'text-emerald-500' :
  score >= 80 ? 'text-blue-500' :
  score >= 70 ? 'text-yellow-500' :
  'text-red-500'

const scoreBg = (score: number) =>
  score >= 95 ? 'bg-emerald-500/10' :
  score >= 80 ? 'bg-blue-500/10' :
  score >= 70 ? 'bg-yellow-500/10' :
  'bg-red-500/10'

const scoreBorder = (score: number) =>
  score >= 95 ? 'border-emerald-500/30' :
  score >= 80 ? 'border-blue-500/30' :
  score >= 70 ? 'border-yellow-500/30' :
  'border-red-500/30'

const scoreGlow = (score: number) =>
  score >= 95 ? 'shadow-emerald-500/20' :
  score >= 80 ? 'shadow-blue-500/20' :
  score >= 70 ? 'shadow-yellow-500/20' :
  'shadow-red-500/20'

const statusDot = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'active':
    case 'running':
      return 'bg-emerald-500'
    case 'idle':
    case 'sleeping':
      return 'bg-blue-400'
    case 'disabled':
      return 'bg-gray-400'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-gray-400'
  }
}

const formatTimestamp = (ts: string) => {
  try {
    const date = new Date(ts)
    return date.toLocaleString('da-DK', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return ts
  }
}

// ─── Skeleton Components ─────────────────────────────────────────────────────

function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary animate-pulse ${className}`}>
      <div className="h-4 bg-light-bg dark:bg-dark-bg rounded w-1/3 mb-3" />
      <div className="h-8 bg-light-bg dark:bg-dark-bg rounded w-1/2 mb-2" />
      <div className="h-3 bg-light-bg dark:bg-dark-bg rounded w-2/3" />
    </div>
  )
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="bg-light-surface dark:bg-dark-surface rounded-xl p-4 border border-border-primary animate-pulse">
          <div className="h-3 bg-light-bg dark:bg-dark-bg rounded w-2/3 mb-3" />
          <div className="h-10 bg-light-bg dark:bg-dark-bg rounded w-1/2 mx-auto mb-2" />
          <div className="h-2 bg-light-bg dark:bg-dark-bg rounded w-1/3 mx-auto" />
        </div>
      ))}
    </div>
  )
}

// ─── Stagger animation variants ──────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function FleetDashboardPage() {
  const [fleetData, setFleetData] = useState<FleetData | null>(null)
  const [learningData, setLearningData] = useState<LearningData | null>(null)
  const [guides, setGuides] = useState<GuideSection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedAdmiral, setExpandedAdmiral] = useState<string | null>(null)
  const [expandedGuide, setExpandedGuide] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [refreshing, setRefreshing] = useState(false)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  const fetchFleetData = useCallback(async (showRefreshing = false) => {
    const token = localStorage.getItem('token')
    if (!token) return

    if (showRefreshing) setRefreshing(true)

    try {
      const response = await fetch(`${apiUrl}/api/admiral/fleet`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (!response.ok) throw new Error(`Fleet data: ${response.status}`)

      const data = await response.json()
      setFleetData(data.data || data)
      setError(null)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Kunne ikke hente fleet data')
    } finally {
      if (showRefreshing) setRefreshing(false)
    }
  }, [apiUrl])

  const fetchLearningData = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${apiUrl}/api/admiral/learnings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setLearningData(data.data || data)
      }
    } catch {
      // Learning data is supplementary — fail silently
    }
  }, [apiUrl])

  const fetchGuides = useCallback(async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const response = await fetch(`${apiUrl}/api/admiral/guides`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setGuides(data.data || data.sections || data || [])
      }
    } catch {
      // Guides are supplementary — fail silently
    }
  }, [apiUrl])

  // Initial load
  useEffect(() => {
    const loadAll = async () => {
      setLoading(true)
      await Promise.all([
        fetchFleetData(),
        fetchLearningData(),
        fetchGuides()
      ])
      setLoading(false)
    }
    loadAll()
  }, [fetchFleetData, fetchLearningData, fetchGuides])

  // Auto-refresh fleet data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchFleetData()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchFleetData])

  const handleManualRefresh = () => {
    fetchFleetData(true)
    fetchLearningData()
  }

  // Sort admirals by score (lowest first to highlight attention areas)
  const sortedAdmirals = fleetData?.admirals
    ? [...fleetData.admirals].sort((a, b) => a.score - b.score)
    : []

  // ─── Error State ─────────────────────────────────────────────────────────

  if (error && !fleetData) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col items-center justify-center py-24">
            <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
            <h2 className="text-xl font-heading font-semibold text-light-text dark:text-dark-text mb-2">
              Kunne ikke indlæse Fleet data
            </h2>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-6">
              {error}
            </p>
            <button
              onClick={() => { setError(null); setLoading(true); fetchFleetData().then(() => setLoading(false)) }}
              className="px-6 py-3 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors font-medium"
            >
              Prøv igen
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─── Loading State ───────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header skeleton */}
          <div className="flex items-center gap-4 mb-4">
            <div className="w-10 h-10 bg-light-bg dark:bg-dark-bg rounded-lg animate-pulse" />
            <div>
              <div className="h-8 bg-light-bg dark:bg-dark-bg rounded w-48 animate-pulse mb-2" />
              <div className="h-4 bg-light-bg dark:bg-dark-bg rounded w-64 animate-pulse" />
            </div>
          </div>

          {/* Hero skeleton */}
          <SkeletonCard className="text-center py-12" />

          {/* Metrics skeleton */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>

          {/* Grid skeleton */}
          <SkeletonGrid />
        </div>
      </div>
    )
  }

  if (!fleetData) return null

  // ─── Main Render ─────────────────────────────────────────────────────────

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* ═══════════════════════════════════════════════════════════════════
            SECTION 1: HEADER — Health Score Hero
            ═══════════════════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <Ship className="w-8 h-8 text-accent" />
            <div>
              <h1 className="text-2xl sm:text-3xl font-heading font-bold text-light-text dark:text-dark-text">
                Admiral Fleet
              </h1>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Realtidsoverblik over alle admiraler og skills
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Last refresh */}
            <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary hidden sm:block">
              Opdateret {lastRefresh.toLocaleTimeString('da-DK', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>

            {/* Refresh button */}
            <button
              onClick={handleManualRefresh}
              disabled={refreshing}
              className="p-2 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg disabled:opacity-50 transition-colors"
              title="Opdater nu"
            >
              <RefreshCw
                size={18}
                className={`text-light-text dark:text-dark-text ${refreshing ? 'animate-spin' : ''}`}
              />
            </button>

            {/* Live indicator */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10">
              <motion.div
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
              </motion.div>
              <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Live</span>
            </div>
          </div>
        </motion.div>

        {/* Health Score Hero Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`relative overflow-hidden bg-light-surface dark:bg-dark-surface rounded-2xl p-8 sm:p-12 border border-border-primary text-center shadow-lg ${scoreGlow(fleetData.health_score)}`}
        >
          {/* Background glow effect */}
          <div className={`absolute inset-0 ${scoreBg(fleetData.health_score)} opacity-30`} />

          <div className="relative z-10">
            <div className="flex items-center justify-center gap-2 mb-3">
              <Heart className={`w-6 h-6 ${scoreColor(fleetData.health_score)}`} />
              <span className="text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">
                Fleet Sundhed
              </span>
            </div>

            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
            >
              <span className={`text-7xl sm:text-8xl font-heading font-bold ${scoreColor(fleetData.health_score)}`}>
                {fleetData.health_score.toFixed(1)}
              </span>
            </motion.div>

            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-2 mb-6">
              Fleet Health Score
            </p>

            {/* Status badges */}
            <div className="flex items-center justify-center gap-3 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-light-bg dark:bg-dark-bg text-sm font-medium text-light-text dark:text-dark-text border border-border-primary">
                <Ship size={14} className="text-accent" />
                {fleetData.admiral_count} Admiraler
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-light-bg dark:bg-dark-bg text-sm font-medium text-light-text dark:text-dark-text border border-border-primary">
                <Zap size={14} className="text-accent" />
                {fleetData.total_skills} Skills
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-sm font-medium text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                <CheckCircle size={14} />
                Kører
              </span>
            </div>
          </div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════════════════
            SECTION 2: FLEET METRICS ROW — 4 stat cards
            ═══════════════════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {/* Admiral Average */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Admiral Gns.</p>
              <Ship size={20} className="text-accent" />
            </div>
            <div className="flex items-baseline gap-2">
              <p className={`text-3xl font-semibold font-heading ${scoreColor(fleetData.admiral_avg)}`}>
                {fleetData.admiral_avg.toFixed(1)}
              </p>
              <TrendingUp size={16} className="text-emerald-500" />
            </div>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
              Gennemsnitlig admiral score
            </p>
          </div>

          {/* Skills Average */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Skills Gns.</p>
              <Zap size={20} className="text-accent" />
            </div>
            <div className="flex items-baseline gap-2">
              <p className={`text-3xl font-semibold font-heading ${scoreColor(fleetData.skills_avg)}`}>
                {fleetData.skills_avg.toFixed(1)}
              </p>
              <TrendingUp size={16} className="text-emerald-500" />
            </div>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
              Gennemsnitlig skill score
            </p>
          </div>

          {/* Over 80% */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Over 80%</p>
              <CheckCircle size={20} className="text-emerald-500" />
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-semibold font-heading text-emerald-500">
                {fleetData.over_80_pct.toFixed(0)}%
              </p>
              <Minus size={16} className="text-light-text-secondary dark:text-dark-text-secondary" />
            </div>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
              Skills over 80 procent
            </p>
          </div>

          {/* Under 70 */}
          <div className={`bg-light-surface dark:bg-dark-surface rounded-xl p-6 border ${
            fleetData.under_70_count > 0 ? 'border-red-500/50' : 'border-border-primary'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Under 70</p>
              <AlertTriangle size={20} className={fleetData.under_70_count > 0 ? 'text-red-500' : 'text-light-text-secondary dark:text-dark-text-secondary'} />
            </div>
            <div className="flex items-baseline gap-2">
              <p className={`text-3xl font-semibold font-heading ${fleetData.under_70_count > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                {fleetData.under_70_count}
              </p>
              {fleetData.under_70_count > 0 && (
                <TrendingDown size={16} className="text-red-500" />
              )}
            </div>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
              {fleetData.under_70_count > 0
                ? 'Kræver opmærksomhed!'
                : 'Alle skills over 70'}
            </p>
          </div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════════════════
            SECTION 3: ADMIRAL GRID — Visual grid of all admirals
            ═══════════════════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading flex items-center gap-2">
              <Eye size={20} className="text-accent" />
              Alle Admiraler
            </h2>
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
              Sorteret efter score (laveste først)
            </p>
          </div>

          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3"
          >
            {sortedAdmirals.map((admiral) => (
              <motion.div
                key={admiral.name}
                variants={itemVariants}
                whileHover={{ scale: 1.03, y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setExpandedAdmiral(expandedAdmiral === admiral.name ? null : admiral.name)}
                className={`cursor-pointer bg-light-surface dark:bg-dark-surface rounded-xl p-4 border transition-all ${
                  expandedAdmiral === admiral.name
                    ? `${scoreBorder(admiral.score)} shadow-md ${scoreGlow(admiral.score)}`
                    : 'border-border-primary hover:border-border-primary/80'
                }`}
              >
                {/* Admiral name + status dot */}
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${statusDot(admiral.status)}`} />
                  <p className="text-xs font-medium text-light-text dark:text-dark-text truncate">
                    {admiral.name}
                  </p>
                </div>

                {/* Score */}
                <div className={`text-center py-2 rounded-lg ${scoreBg(admiral.score)} mb-2`}>
                  <p className={`text-2xl font-bold font-heading ${scoreColor(admiral.score)}`}>
                    {admiral.score.toFixed(1)}
                  </p>
                </div>

                {/* Skills count */}
                <p className="text-xs text-center text-light-text-secondary dark:text-dark-text-secondary">
                  {admiral.skills_count} skills
                </p>

                {/* Expanded skill details */}
                <AnimatePresence>
                  {expandedAdmiral === admiral.name && admiral.skills && admiral.skills.length > 0 && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="mt-3 pt-3 border-t border-border-primary overflow-hidden"
                    >
                      <div className="space-y-1.5">
                        {admiral.skills
                          .sort((a: SkillData, b: SkillData) => a.score - b.score)
                          .map((skill: SkillData) => (
                          <div key={skill.name} className="flex items-center justify-between text-xs">
                            <span className="text-light-text-secondary dark:text-dark-text-secondary truncate mr-2">
                              {skill.name}
                            </span>
                            <span className={`font-medium flex-shrink-0 ${scoreColor(skill.score)}`}>
                              {skill.score.toFixed(0)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════════════════
            SECTION 4: ATTENTION — Skills needing attention
            ═══════════════════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-4"
        >
          {/* Under 70 Skills */}
          <div className={`bg-light-surface dark:bg-dark-surface rounded-xl p-6 border ${
            fleetData.under_70_skills && fleetData.under_70_skills.length > 0
              ? 'border-red-500/30'
              : 'border-border-primary'
          }`}>
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-3 flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-500" />
              Opmærksomhed
            </h3>
            {fleetData.under_70_skills && fleetData.under_70_skills.length > 0 ? (
              <ul className="space-y-2">
                {fleetData.under_70_skills.map((skill, idx) => (
                  <li key={idx} className="text-xs text-red-600 dark:text-red-400 flex items-center gap-2 bg-red-500/5 rounded-lg px-3 py-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                    {skill}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-6">
                <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  Ingen skills under 70. Alt ser godt ud!
                </p>
              </div>
            )}
          </div>

          {/* Movements */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-3 flex items-center gap-2">
              <Activity size={16} className="text-accent" />
              Bevægelser
            </h3>
            {fleetData.movements && fleetData.movements.length > 0 ? (
              <ul className="space-y-2">
                {fleetData.movements.slice(0, 8).map((movement, idx) => (
                  <li key={idx} className="text-xs flex items-center justify-between bg-light-bg dark:bg-dark-bg rounded-lg px-3 py-2">
                    <span className="text-light-text dark:text-dark-text truncate mr-2">
                      {movement.admiral} / {movement.skill}
                    </span>
                    <span className={`flex items-center gap-1 flex-shrink-0 font-medium ${
                      movement.change >= 0 ? 'text-emerald-500' : 'text-red-500'
                    }`}>
                      {movement.change >= 0 ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      {movement.change >= 0 ? '+' : ''}{movement.change.toFixed(1)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary text-center py-6">
                Ingen nylige bevægelser
              </p>
            )}
          </div>

          {/* Excellence */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-3 flex items-center gap-2">
              <Star size={16} className="text-yellow-500" />
              Excellence
            </h3>
            {fleetData.excellence && fleetData.excellence.length > 0 ? (
              <ul className="space-y-2">
                {fleetData.excellence.slice(0, 8).map((item, idx) => (
                  <li key={idx} className="text-xs text-light-text dark:text-dark-text flex items-center gap-2 bg-yellow-500/5 rounded-lg px-3 py-2">
                    <Star size={10} className="text-yellow-500 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-6">
                <Star className="w-8 h-8 text-yellow-500/30 mx-auto mb-2" />
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  Excellence data ikke tilgængelig
                </p>
              </div>
            )}
          </div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════════════════
            SECTION 5: RECENT ACTIVITY — Learning & Council
            ═══════════════════════════════════════════════════════════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-4"
        >
          {/* Recent Learning Sessions */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-4 flex items-center gap-2">
              <BookOpen size={16} className="text-blue-500" />
              Seneste Læring
            </h3>
            {learningData?.recent_sessions && learningData.recent_sessions.length > 0 ? (
              <ul className="space-y-3">
                {learningData.recent_sessions.slice(0, 5).map((session, idx) => (
                  <li key={session.id || idx} className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-light-text dark:text-dark-text">
                        {session.admiral}
                      </span>
                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                        {formatTimestamp(session.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      {session.topic}
                    </p>
                    {session.outcome && (
                      <span className="inline-block mt-1.5 text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-500">
                        {session.outcome}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary text-center py-6">
                Ingen nylige læringssessioner
              </p>
            )}
          </div>

          {/* Recent Council Decisions */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-4 flex items-center gap-2">
              <Gavel size={16} className="text-purple-500" />
              Council Beslutninger
            </h3>
            {learningData?.council_decisions && learningData.council_decisions.length > 0 ? (
              <ul className="space-y-3">
                {learningData.council_decisions.slice(0, 5).map((decision, idx) => (
                  <li key={decision.id || idx} className="bg-light-bg dark:bg-dark-bg rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                        decision.verdict === 'GODKENDT'
                          ? 'bg-emerald-500/10 text-emerald-500'
                          : decision.verdict === 'VENT'
                          ? 'bg-yellow-500/10 text-yellow-500'
                          : 'bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text'
                      }`}>
                        {decision.verdict}
                      </span>
                      <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                        {formatTimestamp(decision.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1 line-clamp-2">
                      {decision.message}
                    </p>
                    {decision.provider && (
                      <span className="inline-block mt-1.5 text-xs text-light-text-secondary dark:text-dark-text-secondary opacity-60">
                        via {decision.provider}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary text-center py-6">
                Ingen nylige council-beslutninger
              </p>
            )}
          </div>

          {/* Pipeline Stats */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
            <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-4 flex items-center gap-2">
              <Zap size={16} className="text-orange-500" />
              Pipeline
            </h3>
            {learningData?.pipeline_stats ? (
              <div className="space-y-4">
                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-4">
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Events Indlæst</p>
                  <p className="text-2xl font-semibold font-heading text-light-text dark:text-dark-text">
                    {learningData.pipeline_stats.events_ingested.toLocaleString()}
                  </p>
                </div>
                <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-4">
                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Mønstre Fundet</p>
                  <p className="text-2xl font-semibold font-heading text-light-text dark:text-dark-text">
                    {learningData.pipeline_stats.patterns_detected.toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center justify-between bg-light-bg dark:bg-dark-bg rounded-lg p-4">
                  <div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Version</p>
                    <p className="text-sm font-medium text-light-text dark:text-dark-text">
                      {learningData.pipeline_stats.version}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Lag</p>
                    <p className="text-sm font-medium text-light-text dark:text-dark-text">
                      {learningData.pipeline_stats.layers}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary text-center py-6">
                Pipeline data ikke tilgængelig
              </p>
            )}
          </div>
        </motion.div>

        {/* ═══════════════════════════════════════════════════════════════════
            SECTION 6: SYSTEM GUIDE — Collapsible semantic summaries
            ═══════════════════════════════════════════════════════════════════ */}
        {guides && guides.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
          >
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading mb-4 flex items-center gap-2">
              <Shield size={20} className="text-accent" />
              System Guide
            </h2>

            <div className="space-y-2">
              {guides.map((guide) => (
                <div
                  key={guide.section_id || guide.title}
                  className="bg-light-surface dark:bg-dark-surface rounded-xl border border-border-primary overflow-hidden"
                >
                  <button
                    onClick={() => setExpandedGuide(
                      expandedGuide === (guide.section_id || guide.title)
                        ? null
                        : (guide.section_id || guide.title)
                    )}
                    className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-light-bg dark:hover:bg-dark-bg transition-colors"
                  >
                    <div className="flex-1 mr-4">
                      <p className="text-sm font-medium text-light-text dark:text-dark-text">
                        {guide.title}
                      </p>
                      {expandedGuide !== (guide.section_id || guide.title) && (
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1 line-clamp-1">
                          {guide.content.substring(0, 120)}{guide.content.length > 120 ? '...' : ''}
                        </p>
                      )}
                    </div>
                    <ChevronDown
                      size={18}
                      className={`text-light-text-secondary dark:text-dark-text-secondary flex-shrink-0 transition-transform ${
                        expandedGuide === (guide.section_id || guide.title) ? 'rotate-180' : ''
                      }`}
                    />
                  </button>

                  <AnimatePresence>
                    {expandedGuide === (guide.section_id || guide.title) && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-4 border-t border-border-primary pt-4">
                          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary whitespace-pre-wrap leading-relaxed">
                            {guide.content}
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* ─── Footer ────────────────────────────────────────────────────── */}
        <div className="text-center py-4">
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
            Admiral Fleet Dashboard — Opdateres automatisk hvert 30. sekund
            {fleetData.timestamp && ` — Data fra ${formatTimestamp(fleetData.timestamp)}`}
          </p>
        </div>

      </div>
    </div>
  )
}
