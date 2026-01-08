'use client'

import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'

export type StatVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: LucideIcon
  variant?: StatVariant
  trend?: {
    value: number
    direction: 'up' | 'down' | 'neutral'
    label?: string
  }
  loading?: boolean
  className?: string
  onClick?: () => void
}

const variantStyles: Record<StatVariant, { bg: string; text: string; icon: string }> = {
  default: {
    bg: 'bg-light-surface dark:bg-dark-surface',
    text: 'text-light-text dark:text-dark-text',
    icon: 'text-accent'
  },
  success: {
    bg: 'bg-emerald-50 dark:bg-emerald-950/30',
    text: 'text-emerald-700 dark:text-emerald-400',
    icon: 'text-emerald-500'
  },
  warning: {
    bg: 'bg-amber-50 dark:bg-amber-950/30',
    text: 'text-amber-700 dark:text-amber-400',
    icon: 'text-amber-500'
  },
  danger: {
    bg: 'bg-red-50 dark:bg-red-950/30',
    text: 'text-red-700 dark:text-red-400',
    icon: 'text-red-500'
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-950/30',
    text: 'text-blue-700 dark:text-blue-400',
    icon: 'text-blue-500'
  }
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
  trend,
  loading = false,
  className,
  onClick
}: StatCardProps) {
  const styles = variantStyles[variant]

  const TrendIcon = trend?.direction === 'up'
    ? TrendingUp
    : trend?.direction === 'down'
      ? TrendingDown
      : Minus

  const trendColor = trend?.direction === 'up'
    ? 'text-emerald-500'
    : trend?.direction === 'down'
      ? 'text-red-500'
      : 'text-slate-400'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={onClick ? { scale: 1.02 } : undefined}
      className={cn(
        'rounded-xl border border-border-primary p-6 transition-all',
        styles.bg,
        onClick && 'cursor-pointer hover:shadow-lg',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary mb-1">
            {title}
          </p>

          {loading ? (
            <div className="h-8 w-24 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
          ) : (
            <p className={cn('text-2xl font-bold', styles.text)}>
              {value}
            </p>
          )}

          {subtitle && !loading && (
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
              {subtitle}
            </p>
          )}

          {trend && !loading && (
            <div className={cn('flex items-center gap-1 mt-2', trendColor)}>
              <TrendIcon size={14} />
              <span className="text-xs font-medium">
                {trend.value > 0 ? '+' : ''}{trend.value}%
              </span>
              {trend.label && (
                <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  {trend.label}
                </span>
              )}
            </div>
          )}
        </div>

        {Icon && (
          <div className={cn(
            'p-3 rounded-lg bg-white/50 dark:bg-black/20',
            styles.icon
          )}>
            <Icon size={24} />
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default StatCard
