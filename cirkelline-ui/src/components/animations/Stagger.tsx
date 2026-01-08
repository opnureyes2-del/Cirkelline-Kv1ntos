'use client'

import { motion, HTMLMotionProps } from 'framer-motion'
import { staggerContainer, staggerContainerFast } from '@/lib/animations'
import { useReducedMotion } from '@/lib/animations/hooks'
import { ReactNode } from 'react'

interface StaggerProps extends Omit<HTMLMotionProps<"div">, 'children'> {
  /** Child elements to stagger */
  children: ReactNode
  /** Use fast stagger (30ms instead of 50ms) */
  fast?: boolean
  /** Delay before children start appearing (in seconds) */
  delayChildren?: number
  /** Custom stagger delay between children (in seconds) */
  staggerDelay?: number
}

/**
 * Stagger Container
 * Animates children with a stagger effect
 * 
 * @example
 * <Stagger>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </Stagger>
 * 
 * @example
 * <Stagger fast staggerDelay={0.03}>
 *   {items.map(item => <StaggerItem key={item.id}>{item}</StaggerItem>)}
 * </Stagger>
 */
export function Stagger({ 
  children, 
  fast = false,
  delayChildren,
  staggerDelay,
  ...props 
}: StaggerProps) {
  const shouldReduce = useReducedMotion()
  
  const variant = fast ? staggerContainerFast : staggerContainer

  // Override transition if custom values are provided
  const customTransition = (delayChildren !== undefined || staggerDelay !== undefined) ? {
    staggerChildren: staggerDelay !== undefined ? staggerDelay : (fast ? 0.03 : 0.05),
    delayChildren: delayChildren !== undefined ? delayChildren : (fast ? 0 : 0.1),
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

interface StaggerItemProps extends HTMLMotionProps<"div"> {
  /** Distance to slide from (in pixels) */
  distance?: number
}

/**
 * Stagger Item
 * Individual item within a Stagger container
 * Use this for each child when you need more control
 * 
 * @example
 * <Stagger>
 *   {items.map(item => (
 *     <StaggerItem key={item.id}>
 *       {item.content}
 *     </StaggerItem>
 *   ))}
 * </Stagger>
 */
export function StaggerItem({ 
  children,
  distance = 20,
  ...props 
}: StaggerItemProps) {
  const shouldReduce = useReducedMotion()

  const customVariant = {
    initial: {
      opacity: 0,
      x: -distance
    },
    animate: {
      opacity: 1,
      x: 0
    },
    exit: {
      opacity: 0,
      x: -10
    },
  }

  const customTransition = {
    type: "spring" as const,
    stiffness: 300,
    damping: 24,
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