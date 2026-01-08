'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function PageLoader() {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Show loader for at least 1 second for smooth experience
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center gap-8 bg-light-bg dark:bg-dark-bg"
        >
          {/* Circle Animation */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="relative"
          >
            {/* Outer rotating ring */}
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-24 h-24 rounded-full border-4 border-transparent border-t-accent-start border-r-accent-end"
            />

            {/* Inner pulsing circle */}
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute inset-0 m-auto w-12 h-12 rounded-full bg-gradient-to-br from-accent-start to-accent-end opacity-20"
            />

            {/* Center dot */}
            <motion.div
              animate={{ scale: [1, 0.8, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute inset-0 m-auto w-4 h-4 rounded-full bg-accent"
            />
          </motion.div>

          {/* Cirkelline Text */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-4xl text-light-text dark:text-dark-text font-sans font-normal"
          >
            Cirkelline
          </motion.h1>
        </motion.div>
      )}
    </AnimatePresence>
  )
}