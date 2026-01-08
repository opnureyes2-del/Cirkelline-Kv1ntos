'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { motion } from 'framer-motion'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!mounted || !isOpen) return null

  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6 bg-black/50 backdrop-blur-sm overflow-y-auto">
      <motion.div
        className="w-full max-w-4xl bg-light-surface dark:bg-dark-surface rounded-2xl shadow-2xl overflow-hidden my-auto"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-primary">
          <h2 className="text-2xl font-heading font-bold text-light-text dark:text-dark-text">
            Settings
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary rounded-lg transition-colors"
          >
            <X size={20} className="text-light-text-secondary dark:text-dark-text-secondary" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-12rem)]">
          <div className="flex flex-col items-center justify-center py-20">
            <p className="text-light-text-secondary dark:text-dark-text-secondary mb-2">
              Settings page coming soon
            </p>
            <p className="text-sm text-light-text-secondary/70 dark:text-dark-text-secondary/70">
              Configure your preferences and account settings here
            </p>
          </div>
        </div>
      </motion.div>
    </div>,
    document.body
  )
}
