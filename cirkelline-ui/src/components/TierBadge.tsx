/**
 * TierBadge Component
 * 
 * Displays user tier with appropriate styling and icon
 */

import React from 'react'
import { Users, Zap, Briefcase, Crown, Heart } from 'lucide-react'
import type { TierSlug } from '@/types/subscription'

interface TierBadgeProps {
  tier: TierSlug
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  className?: string
}

const tierConfig = {
  member: {
    label: 'Member',
    color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
    icon: Users,
  },
  pro: {
    label: 'Pro',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    icon: Zap,
  },
  business: {
    label: 'Business',
    color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    icon: Briefcase,
  },
  elite: {
    label: 'Elite',
    color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
    icon: Crown,
  },
  family: {
    label: 'Family',
    color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300',
    icon: Heart,
  },
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs gap-1',
  md: 'px-3 py-1 text-sm gap-1.5',
  lg: 'px-4 py-2 text-base gap-2',
}

const iconSizes = {
  sm: 'w-3 h-3',
  md: 'w-4 h-4',
  lg: 'w-5 h-5',
}

export function TierBadge({ 
  tier, 
  size = 'md', 
  showIcon = true,
  className = '' 
}: TierBadgeProps) {
  const config = tierConfig[tier]
  const Icon = config.icon

  return (
    <span
      className={`
        inline-flex items-center rounded-full font-medium
        ${config.color}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {showIcon && <Icon className={iconSizes[size]} />}
      <span>{config.label}</span>
    </span>
  )
}