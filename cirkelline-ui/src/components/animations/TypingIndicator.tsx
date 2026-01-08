'use client'

import { motion } from 'framer-motion'
import { typingDot } from '@/lib/animations'
import { useReducedMotion } from '@/lib/animations/hooks'

interface TypingIndicatorProps {
  /** Size of the dots: 'sm' | 'md' | 'lg' */
  size?: 'sm' | 'md' | 'lg'
  /** Custom color for the dots */
  color?: string
  /** Additional className for the container */
  className?: string
}

/**
 * TypingIndicator Component
 * Animated three-dot typing indicator
 * 
 * @example
 * <TypingIndicator />
 * 
 * @example
 * <TypingIndicator size="lg" color="rgba(var(--accent-rgb), 1)" />
 */
export function TypingIndicator({ 
  size = 'md',
  color,
  className = ''
}: TypingIndicatorProps) {
  const shouldReduce = useReducedMotion()

  const sizeMap = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
  }

  const gapMap = {
    sm: 'gap-1',
    md: 'gap-1.5',
    lg: 'gap-2',
  }

  const dotSize = sizeMap[size]
  const dotGap = gapMap[size]
  const dotColor = color || 'rgba(var(--accent-rgb), 0.8)'

  return (
    <div className={`flex items-center ${dotGap} ${className}`}>
      <motion.div
        className={`${dotSize} rounded-full`}
        style={{ backgroundColor: dotColor }}
        variants={shouldReduce ? undefined : typingDot(0)}
        animate={shouldReduce ? undefined : "animate"}
      />
      <motion.div
        className={`${dotSize} rounded-full`}
        style={{ backgroundColor: dotColor }}
        variants={shouldReduce ? undefined : typingDot(1)}
        animate={shouldReduce ? undefined : "animate"}
      />
      <motion.div
        className={`${dotSize} rounded-full`}
        style={{ backgroundColor: dotColor }}
        variants={shouldReduce ? undefined : typingDot(2)}
        animate={shouldReduce ? undefined : "animate"}
      />
    </div>
  )
}