'use client'

import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  icon: LucideIcon
  value: string | number
  label: string
  gradient?: string
  delay?: number
}

export default function StatCard({ icon: Icon, value, label, gradient, delay = 0 }: StatCardProps) {
  // Default gradient if none provided
  const defaultGradient = 'from-accent/10 to-accent/5'
  const cardGradient = gradient || defaultGradient

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      className={`
        relative overflow-hidden
        bg-gradient-to-br ${cardGradient}
        rounded-xl p-4
        border border-border-primary
        hover:border-accent/30
        transition-all duration-300
        cursor-default
      `}
    >
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-16 h-16 bg-accent/5 rounded-full blur-2xl" />

      {/* Content - more compact */}
      <div className="relative flex items-center justify-between">
        <div className="flex-1">
          <div className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mb-1">
            {value}
          </div>
          <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">
            {label}
          </div>
        </div>

        {/* Icon on right side */}
        <div className="p-2 rounded-lg bg-accent/10 text-accent ml-3">
          <Icon size={20} />
        </div>
      </div>
    </motion.div>
  )
}
