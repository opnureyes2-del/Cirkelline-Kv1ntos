'use client'

import { motion, HTMLMotionProps } from 'framer-motion'
import { useReducedMotion } from '@/lib/animations/hooks'

interface SlideUpProps extends HTMLMotionProps<"div"> {
  /** Delay before animation starts (in seconds) */
  delay?: number
  /** Distance to slide from (in pixels) */
  distance?: number
}

/**
 * SlideUp Component
 * Slide up animation with fade
 * 
 * @example
 * <SlideUp>
 *   <YourContent />
 * </SlideUp>
 * 
 * @example
 * <SlideUp delay={0.1} distance={30}>
 *   <YourContent />
 * </SlideUp>
 */
export function SlideUp({ 
  children, 
  delay = 0,
  distance = 20,
  ...props 
}: SlideUpProps) {
  const shouldReduce = useReducedMotion()

  const customVariant = {
    initial: {
      opacity: 0,
      y: distance
    },
    animate: {
      opacity: 1,
      y: 0
    },
    exit: {
      opacity: 0,
      y: 10
    },
  }

  const customTransition = {
    type: "spring" as const,
    stiffness: 300,
    damping: 30,
    delay,
  }

  return (
    <motion.div
      initial={shouldReduce ? false : "initial"}
      animate={shouldReduce ? undefined : "animate"}
      exit={shouldReduce ? undefined : "exit"}
      variants={shouldReduce ? undefined : customVariant}
      transition={customTransition}
      {...props}
    >
      {children}
    </motion.div>
  )
}