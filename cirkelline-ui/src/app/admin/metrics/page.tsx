'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, DollarSign, Activity, Users, Filter } from 'lucide-react'

interface TokenMetrics {
  summary: {
    message_count: number
    total_tokens: number
    input_tokens: number
    output_tokens: number
    total_cost: number
    input_cost: number
    output_cost: number
  }
  by_agent: Array<{
    agent_id: string
    agent_name: string
    agent_type: string
    message_count: number
    total_tokens: number
    input_tokens: number
    output_tokens: number
    total_cost: number
    avg_tokens_per_message: number
  }>
  by_user: Array<{
    user_id: string
    email: string
    display_name: string
    message_count: number
    total_tokens: number
    total_cost: number
  }>
  timeline: Array<{
    period: string
    message_count: number
    total_tokens: number
    total_cost: number
  }>
  projections: {
    daily_average: number
    weekly_projection: number
    monthly_projection: number
    yearly_projection: number
  }
  filters_applied: {
    agent_id: string | null
    user_id: string | null
    start_date: string | null
    end_date: string | null
    group_by: string | null
  }
}

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<TokenMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<string>('all')

  useEffect(() => {
    fetchMetrics()
  }, [selectedAgent])

  const fetchMetrics = async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    setLoading(true)
    setError(null)

    try {
      const url = selectedAgent === 'all'
        ? `${process.env.NEXT_PUBLIC_API_URL}/api/admin/token-usage`
        : `${process.env.NEXT_PUBLIC_API_URL}/api/admin/token-usage?agent_id=${selectedAgent}`

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch metrics')
      }

      const data = await response.json()
      setMetrics(data.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`
    return num.toLocaleString()
  }

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(6)}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto"></div>
          <p className="mt-4 text-light-text-secondary dark:text-dark-text-secondary">Loading metrics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500">{error}</p>
          <button
            onClick={fetchMetrics}
            className="mt-4 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!metrics) return null

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-heading font-semibold text-light-text dark:text-dark-text">
            Token Usage Metrics
          </h1>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
            Comprehensive analytics for AI token usage and costs
          </p>
        </div>

        {/* Agent Filter */}
        <div className="flex items-center gap-2">
          <Filter size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="px-4 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text focus:outline-none focus:ring-2 focus:ring-accent"
          >
            <option value="all">All Agents</option>
            {metrics.by_agent.map((agent) => (
              <option key={agent.agent_id} value={agent.agent_id}>
                {agent.agent_name}
              </option>
            ))}
          </select>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {/* Total Messages */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Total Messages</p>
            <Activity size={20} className="text-accent" />
          </div>
          <p className="text-3xl font-semibold text-light-text dark:text-dark-text">
            {formatNumber(metrics.summary.message_count)}
          </p>
        </div>

        {/* Total Tokens */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Total Tokens</p>
            <BarChart3 size={20} className="text-accent" />
          </div>
          <p className="text-3xl font-semibold text-light-text dark:text-dark-text">
            {formatNumber(metrics.summary.total_tokens)}
          </p>
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
            Input: {formatNumber(metrics.summary.input_tokens)} | Output: {formatNumber(metrics.summary.output_tokens)}
          </p>
        </div>

        {/* Total Cost */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Total Cost</p>
            <DollarSign size={20} className="text-accent" />
          </div>
          <p className="text-3xl font-semibold text-light-text dark:text-dark-text">
            {formatCost(metrics.summary.total_cost)}
          </p>
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
            Gemini 2.5 Flash Tier 1
          </p>
        </div>

        {/* Monthly Projection */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Monthly Projection</p>
            <TrendingUp size={20} className="text-accent" />
          </div>
          <p className="text-3xl font-semibold text-light-text dark:text-dark-text">
            {formatCost(metrics.projections.monthly_projection)}
          </p>
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
            Yearly: {formatCost(metrics.projections.yearly_projection)}
          </p>
        </div>
      </motion.div>

      {/* Agent Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
      >
        <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 flex items-center gap-2">
          <BarChart3 size={20} className="text-accent" />
          Agent Breakdown
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-primary">
                <th className="text-left py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Agent</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Messages</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Tokens</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Avg/Message</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Cost</th>
              </tr>
            </thead>
            <tbody>
              {metrics.by_agent.map((agent) => (
                <tr key={agent.agent_id} className="border-b border-border-primary/50 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors">
                  <td className="py-3 px-4">
                    <div>
                      <p className="text-sm font-medium text-light-text dark:text-dark-text">{agent.agent_name}</p>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary capitalize">{agent.agent_type}</p>
                    </div>
                  </td>
                  <td className="text-right py-3 px-4 text-sm text-light-text dark:text-dark-text">
                    {formatNumber(agent.message_count)}
                  </td>
                  <td className="text-right py-3 px-4 text-sm text-light-text dark:text-dark-text">
                    {formatNumber(agent.total_tokens)}
                  </td>
                  <td className="text-right py-3 px-4 text-sm text-light-text dark:text-dark-text">
                    {formatNumber(Math.round(agent.avg_tokens_per_message))}
                  </td>
                  <td className="text-right py-3 px-4 text-sm text-accent font-medium">
                    {formatCost(agent.total_cost)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* User Breakdown */}
      {metrics.by_user.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
        >
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 flex items-center gap-2">
            <Users size={20} className="text-accent" />
            Top Users by Token Usage
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border-primary">
                  <th className="text-left py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">User</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Messages</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Tokens</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Cost</th>
                </tr>
              </thead>
              <tbody>
                {metrics.by_user.slice(0, 10).map((user) => (
                  <tr key={user.user_id} className="border-b border-border-primary/50 hover:bg-light-bg dark:hover:bg-dark-bg transition-colors">
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm font-medium text-light-text dark:text-dark-text">{user.display_name || 'Unknown'}</p>
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">{user.email}</p>
                      </div>
                    </td>
                    <td className="text-right py-3 px-4 text-sm text-light-text dark:text-dark-text">
                      {formatNumber(user.message_count)}
                    </td>
                    <td className="text-right py-3 px-4 text-sm text-light-text dark:text-dark-text">
                      {formatNumber(user.total_tokens)}
                    </td>
                    <td className="text-right py-3 px-4 text-sm text-accent font-medium">
                      {formatCost(user.total_cost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Projections */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-light-surface dark:bg-dark-surface rounded-xl p-6 border border-border-primary"
      >
        <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-accent" />
          Cost Projections
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-lg bg-light-bg dark:bg-dark-bg">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-1">Daily Average</p>
            <p className="text-2xl font-semibold text-light-text dark:text-dark-text">
              {formatCost(metrics.projections.daily_average)}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-light-bg dark:bg-dark-bg">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-1">Weekly Projection</p>
            <p className="text-2xl font-semibold text-light-text dark:text-dark-text">
              {formatCost(metrics.projections.weekly_projection)}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-light-bg dark:bg-dark-bg">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-1">Monthly Projection</p>
            <p className="text-2xl font-semibold text-accent">
              {formatCost(metrics.projections.monthly_projection)}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-light-bg dark:bg-dark-bg">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-1">Yearly Projection</p>
            <p className="text-2xl font-semibold text-light-text dark:text-dark-text">
              {formatCost(metrics.projections.yearly_projection)}
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
