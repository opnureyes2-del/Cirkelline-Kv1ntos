'use client'

import { motion, HTMLMotionProps } from 'framer-motion'
import { fadeIn, fadeInFast } from '@/lib/animations'
import { useReducedMotion } from '@/lib/animations/hooks'

interface FadeInProps extends HTMLMotionProps<"div"> {
  /** Use fast animation (150ms instead of 250ms) */
  fast?: boolean
  /** Delay before animation starts (in seconds) */
  delay?: number
  /** Custom duration (in seconds) */
  duration?: number
}

/**
 * FadeIn Component
 * Simple fade-in animation wrapper
 * 
 * @example
 * <FadeIn>
 *   <YourContent />
 * </FadeIn>
 * 
 * @example
 * <FadeIn fast delay={0.2}>
 *   <YourContent />
 * </FadeIn>
 */
export function FadeIn({ 
  children, 
  fast = false, 
  delay = 0,
  duration,
  ...props 
}: FadeInProps) {
  const shouldReduce = useReducedMotion()
  
  const variant = fast ? fadeInFast : fadeIn
  
  // Override transition if custom duration or delay is provided
  const customTransition = (duration !== undefined || delay > 0) ? {
    duration: duration !== undefined ? duration : (fast ? 0.15 : 0.25),
    delay,
  } : undefined

  return (
    <motion.div
      initial={shouldReduce ? false : "initial"}
      animate={shouldReduce ? undefined : "animate"}
      exit={shouldReduce ? undefined : "exit"}
      variants={shouldReduce ? undefined : variant}
      transition={customTransition}
      {...props}
    >
      {children}
    </motion.div>
  )
}