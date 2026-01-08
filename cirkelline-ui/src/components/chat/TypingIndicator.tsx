'use client'

import { motion } from 'framer-motion'
import Avatar from '@/components/Avatar'

interface TypingIndicatorProps {
  message?: string
}

export default function TypingIndicator({ message = "Thinking" }: TypingIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className="flex items-start gap-3 px-4 py-3"
    >
      <Avatar type="ai" thinking />

      <div className="flex-1">
        <div className="inline-flex items-center gap-2 px-4 py-3 rounded-2xl bg-light-bg dark:bg-dark-elevated border border-border-primary">
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-sm text-light-text-secondary dark:text-dark-text-secondary"
          >
            {message}
          </motion.span>
        </div>
      </div>
    </motion.div>
  )
}