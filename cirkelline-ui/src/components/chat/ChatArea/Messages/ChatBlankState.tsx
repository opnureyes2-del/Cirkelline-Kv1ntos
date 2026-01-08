'use client'

import { motion, AnimatePresence } from 'framer-motion'
import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { Heart } from 'lucide-react'

interface TypingTextProps {
  text: string
  className?: string
  speed?: number
  delay?: number
  onComplete?: () => void
}

const TypingText: React.FC<TypingTextProps> = ({ text, className = '', speed = 50, delay = 0, onComplete }) => {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    const startTimeout = setTimeout(() => {
      setIsTyping(true)
    }, delay)

    return () => clearTimeout(startTimeout)
  }, [delay])

  useEffect(() => {
    if (!isTyping) return

    if (currentIndex < text.length) {
      // Variable speed to mimic human typing
      const char = text[currentIndex]
      let typingSpeed = speed

      // Slower after punctuation
      if (currentIndex > 0 && /[.,!?]/.test(text[currentIndex - 1])) {
        typingSpeed = speed * 4
      }
      // Faster for consecutive letters
      else if (currentIndex > 0 && /[a-zA-Z]/.test(char) && /[a-zA-Z]/.test(text[currentIndex - 1])) {
        typingSpeed = speed * 0.8
      }
      // Random variance to feel more natural
      typingSpeed += (Math.random() - 0.5) * speed * 0.4

      const timeout = setTimeout(() => {
        setDisplayedText(prev => prev + text[currentIndex])
        setCurrentIndex(prev => prev + 1)
      }, typingSpeed)

      return () => clearTimeout(timeout)
    } else if (currentIndex === text.length && onComplete) {
      onComplete()
    }
  }, [currentIndex, text, speed, isTyping, onComplete])

  const showCursor = isTyping && currentIndex < text.length

  return (
    <span className={className}>
      {displayedText}
      {showCursor && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.5, repeat: Infinity, repeatType: 'reverse' }}
          className="inline-block ml-1"
        >
          |
        </motion.span>
      )}
    </span>
  )
}

const ChatBlankState = () => {
  const { user } = useAuth()
  const isGuest = !user || user.isAnonymous
  const userName = user?.display_name || user?.email?.split('@')[0] || 'User'
  const [showSubtext, setShowSubtext] = useState(false)
  const [showSupportButton, setShowSupportButton] = useState(false)
  const [isSupportOpen, setIsSupportOpen] = useState(false)
  const supportRef = useRef<HTMLDivElement>(null)

  // Close support panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (supportRef.current && !supportRef.current.contains(event.target as Node)) {
        setIsSupportOpen(false)
      }
    }
    if (isSupportOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isSupportOpen])

  return (
    <section
      className="relative flex flex-col items-center justify-center text-center py-12 overflow-hidden"
      aria-label="Welcome message"
    >
      {/* Support Us Button - Top Right - Shows after welcome animation */}
      <AnimatePresence>
        {showSupportButton && (
          <motion.div
            ref={supportRef}
            className="fixed top-24 -right-4 md:-right-6"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
          >
            <motion.button
              onClick={() => setIsSupportOpen(!isSupportOpen)}
              className="flex items-center gap-2 pl-3 pr-8 md:pr-12 py-2 rounded-l-xl transition-all text-white"
              style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Heart size={18} />
              <span className="font-heading text-sm font-semibold">Support Us</span>
            </motion.button>

            {/* Support Panel */}
            <AnimatePresence>
              {isSupportOpen && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                  className="absolute top-12 right-0 w-80 bg-light-elevated dark:bg-dark-elevated border border-border-primary rounded-lg shadow-lg p-5 z-50"
                >
                  <h3 className="font-heading text-base font-bold text-light-text dark:text-dark-text mb-2">
                    Help us develop and maintain cirkelline in this initial stage
                  </h3>
                  <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary leading-relaxed mb-4">
                    Built with passion by two developers in our spare time. Your support fuels our growth and unlocks exclusive early supporter benefits.
                  </p>
                  <motion.button
                    onClick={() => {}}
                    className="w-full px-4 py-2 rounded-lg font-semibold transition-all hover:shadow-md bg-[#D0D0D0] dark:bg-[#2A2A2A] text-light-text dark:text-dark-text"
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgb(var(--accent-rgb))'
                      e.currentTarget.style.color = 'white'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = ''
                      e.currentTarget.style.color = ''
                    }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Donate Now
                  </motion.button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
      <div className="max-w-2xl space-y-4">
        {isGuest ? (
          <>
            <motion.h2
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="font-heading text-4xl text-light-text dark:text-dark-text"
            >
              <TypingText
                text="Hi! I am Cirkelline"
                speed={60}
                delay={2000}
                onComplete={() => setShowSubtext(true)}
              />
            </motion.h2>
            {showSubtext && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="text-xl text-light-text/80 dark:text-dark-text/80 font-sans"
              >
                <TypingText
                  text="Your new personal assistant! How can I help you?"
                  speed={50}
                  delay={300}
                  onComplete={() => setShowSupportButton(true)}
                />
              </motion.p>
            )}
          </>
        ) : (
          <motion.h2
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="font-heading text-4xl text-light-text dark:text-dark-text"
          >
            <TypingText
              text={`Welcome back, ${userName}`}
              speed={60}
              delay={2000}
              onComplete={() => setShowSupportButton(true)}
            />
          </motion.h2>
        )}
      </div>
    </section>
  )
}

export default ChatBlankState
