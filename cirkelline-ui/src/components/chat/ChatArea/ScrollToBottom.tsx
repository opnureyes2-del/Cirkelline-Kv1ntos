'use client'

import type React from 'react'
import { useEffect, useRef } from 'react'

import { motion, AnimatePresence } from 'framer-motion'
import { useStickToBottomContext } from 'use-stick-to-bottom'

import { Button } from '@/components/ui/button'
import Icon from '@/components/ui/icon'
import { useStore } from '@/store'

const ScrollToBottom: React.FC = () => {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext()
  const { isStreaming } = useStore()
  const hasSeenResponseRef = useRef(true) // Start as true (no unseen response)

  // When streaming starts, mark response as unseen
  useEffect(() => {
    if (isStreaming) {
      hasSeenResponseRef.current = false
    }
  }, [isStreaming])

  // When user scrolls to bottom after streaming ends, mark as seen
  useEffect(() => {
    if (isAtBottom && !isStreaming && !hasSeenResponseRef.current) {
      hasSeenResponseRef.current = true
    }
  }, [isAtBottom, isStreaming])

  // Response is ready when streaming is done, user scrolled up, AND they haven't seen it yet
  const isResponseReady = !isStreaming && !isAtBottom && !hasSeenResponseRef.current

  // Gentle bounce animation - slow with pauses
  const gentleBounce = {
    y: [0, -8, 0],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      repeatDelay: 0.5,
      ease: "easeInOut" as const
    }
  }

  return (
    <AnimatePresence>
      {!isAtBottom && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.3, ease: 'easeInOut' }}
          className="absolute left-1/2 -translate-x-1/2"
          style={{ bottom: '1rem' }}
        >
          <motion.div
            animate={isResponseReady ? gentleBounce : { y: 0 }}
            whileHover={!isResponseReady ? { y: 3 } : {}}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            <Button
            onClick={() => scrollToBottom()}
            type="button"
            size="icon"
            variant={isResponseReady ? undefined : "secondary"}
            className={`
              shadow-md transition-all duration-300 focus:outline-none focus:ring-0
              ${isResponseReady
                ? '!bg-accent-start !text-white hover:opacity-90 border-none'
                : 'border border-border-primary bg-light-surface text-light-text hover:bg-light-bg dark:border-border-primary dark:bg-dark-surface dark:text-dark-text dark:hover:bg-dark-bg'
              }
            `}
          >
            <Icon
              type="arrow-down"
              size="xs"
              className={isResponseReady ? '!text-white' : ''}
            />
            </Button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default ScrollToBottom
