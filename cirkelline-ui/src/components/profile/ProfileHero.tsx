'use client'

import { User, Calendar, Shield } from 'lucide-react'
import { motion } from 'framer-motion'

interface ProfileHeroProps {
  name: string
  email: string
  memberSince: string
  isAdmin?: boolean
}

export default function ProfileHero({ name, email, memberSince, isAdmin = false }: ProfileHeroProps) {
  // Get initials from name
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-8 border border-border-primary">
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
        {/* Avatar */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          className="relative"
        >
          <div
            className="
              w-24 h-24 sm:w-28 sm:h-28
              rounded-full
              bg-gradient-to-br from-accent to-accent/70
              flex items-center justify-center
              text-white font-bold text-3xl
              shadow-lg
              ring-4 ring-light-surface dark:ring-dark-surface
            "
          >
            {getInitials(name)}
          </div>

          {/* Upload button overlay (placeholder) */}
          <button
            className="
              absolute bottom-0 right-0
              w-8 h-8 sm:w-10 sm:h-10
              rounded-full
              bg-accent
              text-white
              flex items-center justify-center
              shadow-lg
              hover:scale-110
              transition-transform
              cursor-not-allowed opacity-50
            "
            title="Avatar upload coming soon"
            disabled
          >
            <User size={16} />
          </button>
        </motion.div>

        {/* User Info */}
        <div className="flex-1 text-center sm:text-left">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            {/* Name */}
            <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading mb-2 flex items-center justify-center sm:justify-start gap-2">
              {name}
              {isAdmin && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-accent/10 text-accent rounded-full">
                  <Shield size={12} />
                  Admin
                </span>
              )}
            </h1>

            {/* Email */}
            <p className="text-light-text-secondary dark:text-dark-text-secondary text-sm mb-3">
              {email}
            </p>

            {/* Member Since */}
            <div className="flex items-center justify-center sm:justify-start gap-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
              <Calendar size={16} />
              <span>Member since {memberSince}</span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
