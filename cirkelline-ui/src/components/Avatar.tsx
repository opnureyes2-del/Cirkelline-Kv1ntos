'use client'

import { motion } from 'framer-motion'

interface AvatarProps {
  type: 'user' | 'ai'
  size?: 'sm' | 'md' | 'lg'
  animate?: boolean
  thinking?: boolean
}

export default function Avatar({ type, size = 'md', animate = false, thinking = false }: AvatarProps) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12'
  }

  if (type === 'ai') {
    return (
      <motion.div
        className="rounded-full"
        style={{
          backgroundColor: 'rgb(var(--accent-rgb))',
          width: '14px',
          height: '14px'
        }}
        initial={animate ? { scale: 0 } : undefined}
        animate={animate ?
          { scale: 1 } :
          thinking ? {
            opacity: [0.4, 1, 0.4]
          } : undefined
        }
        transition={animate ?
          { type: "spring", stiffness: 260, damping: 20 } :
          thinking ? {
            duration: 1.8,
            repeat: Infinity,
            ease: [0.4, 0, 0.6, 1]
          } : undefined
        }
      />
    )
  }

  return (
    <motion.div
      initial={animate ? { scale: 0 } : undefined}
      animate={animate ? { scale: 1 } : undefined}
      transition={{ type: "spring", stiffness: 260, damping: 20 }}
      className={`${sizeClasses[size]} rounded-full bg-accent flex items-center justify-center text-white font-bold`}
    >
      <span className="text-sm">U</span>
    </motion.div>
  )
}