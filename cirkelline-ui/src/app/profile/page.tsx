'use client'

import { useState, useEffect } from 'react'
import { Save, MessageSquare, FolderOpen, Sparkles, Calendar, ArrowUpCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'
import { motion } from 'framer-motion'
import ProfileHero from '@/components/profile/ProfileHero'
import StatCard from '@/components/profile/StatCard'
import ActivityFeed from '@/components/profile/ActivityFeed'
import { TierBadge } from '@/components/TierBadge'
import { useSubscription } from '@/hooks/useSubscription'

interface UserStatistics {
  messages_sent: number
  conversations_started: number
  messages_received: number
  documents_uploaded: number
  memories_captured: number
  last_active: number
  favorite_theme: string
  favorite_accent: string
}

interface RecentActivity {
  type: string
  description: string
  timestamp: number
}

interface StatisticsData {
  success: boolean
  user_id: string
  email: string
  created_at: string
  member_since_days: number
  statistics: UserStatistics
  recent_activity: RecentActivity[]
}

export default function ProfileAccountPage() {
  const { user } = useAuth()
  const { subscription, canUpgrade, isLoading: subscriptionLoading } = useSubscription()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [bio, setBio] = useState('')
  const [location, setLocation] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [instructions, setInstructions] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [statistics, setStatistics] = useState<StatisticsData | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [connectedServices, setConnectedServices] = useState({
    google: false,
    microsoft: false,
    github: false,
    discord: false
  })

  // Track initial values
  const [initialName, setInitialName] = useState('')
  const [initialBio, setInitialBio] = useState('')
  const [initialLocation, setInitialLocation] = useState('')
  const [initialJobTitle, setInitialJobTitle] = useState('')
  const [initialInstructions, setInitialInstructions] = useState('')

  // Fetch user statistics
  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
        const response = await fetch(`${apiUrl}/api/user/statistics`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const data = await response.json()
          setStatistics(data)

          // Load profile fields from preferences
          if (data.profile) {
            const profileData = data.profile
            if (profileData.bio) {
              setBio(profileData.bio)
              setInitialBio(profileData.bio)
            }
            if (profileData.location) {
              setLocation(profileData.location)
              setInitialLocation(profileData.location)
            }
            if (profileData.job_title) {
              setJobTitle(profileData.job_title)
              setInitialJobTitle(profileData.job_title)
            }
            if (profileData.instructions) {
              setInstructions(profileData.instructions)
              setInitialInstructions(profileData.instructions)
            }
          }

          // Load connected services status
          if (data.connected_services) {
            setConnectedServices(data.connected_services)
          }
        }
      } catch (error) {
        console.error('Failed to fetch statistics:', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      fetchStatistics()
    }
  }, [user])

  // Initialize with user data
  useEffect(() => {
    if (user) {
      const displayName = user.display_name || user.email?.split('@')[0] || 'User'
      setName(displayName)
      setInitialName(displayName)
      setEmail(user.email || '')
    }
  }, [user])

  // Detect changes
  useEffect(() => {
    const nameChanged = name !== initialName
    const bioChanged = bio !== initialBio
    const locationChanged = location !== initialLocation
    const jobTitleChanged = jobTitle !== initialJobTitle
    const instructionsChanged = instructions !== initialInstructions
    setHasChanges(nameChanged || bioChanged || locationChanged || jobTitleChanged || instructionsChanged)
  }, [name, bio, location, jobTitle, instructions, initialName, initialBio, initialLocation, initialJobTitle, initialInstructions])

  const handleSave = async () => {
    setSaving(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        toast.error('Not authenticated')
        return
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.cirkelline.com'
      const response = await fetch(`${apiUrl}/api/user/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          display_name: name,
          bio: bio,
          location: location,
          job_title: jobTitle,
          instructions: instructions
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update profile')
      }

      const data = await response.json()

      // Store new token
      localStorage.setItem('token', data.token)

      // Update initial values
      setInitialName(name)
      setInitialBio(bio)
      setInitialLocation(location)
      setInitialJobTitle(jobTitle)
      setInitialInstructions(instructions)
      setHasChanges(false)

      toast.success('Profile updated successfully!')

      // Reload page to update UI everywhere
      setTimeout(() => {
        window.location.reload()
      }, 500)

    } catch (err) {
      console.error('Profile update error:', err)
      toast.error('Failed to update profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  // Format member since date
  const formatMemberSince = (dateString: string, days: number) => {
    try {
      const date = new Date(dateString)
      const month = date.toLocaleDateString('en-US', { month: 'short' })
      const year = date.getFullYear()
      return `${month} ${year} (${days} days)`
    } catch {
      return 'Recently'
    }
  }

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Skeleton loading */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-8 border border-border-primary animate-pulse">
            <div className="flex gap-6">
              <div className="w-28 h-28 rounded-full bg-light-bg dark:bg-dark-bg" />
              <div className="flex-1 space-y-4">
                <div className="h-8 bg-light-bg dark:bg-dark-bg rounded w-48" />
                <div className="h-4 bg-light-bg dark:bg-dark-bg rounded w-32" />
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 pb-12">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Hero Section */}
        <ProfileHero
          name={name}
          email={email}
          memberSince={
            statistics
              ? formatMemberSince(statistics.created_at, statistics.member_since_days)
              : 'Recently'
          }
          isAdmin={user?.email === 'opnureyes2@gmail.com' || user?.email === 'opnureyes2@gmail.com'}
        />

        {/* Statistics Grid */}
        {statistics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <StatCard
                icon={MessageSquare}
                value={statistics.statistics.conversations_started}
                label="Conversations"
                delay={0}
              />

              <StatCard
                icon={Sparkles}
                value={statistics.statistics.messages_sent}
                label="Messages"
                delay={0.1}
              />

              <StatCard
                icon={FolderOpen}
                value={statistics.statistics.documents_uploaded}
                label="Documents"
                delay={0.2}
              />

              <StatCard
                icon={Calendar}
                value={`Day ${statistics.member_since_days}`}
                label="Member Status"
                delay={0.3}
              />
            </div>
          </motion.div>
        )}

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Details - 2 columns */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2"
          >
            <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary">
              <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-6 font-heading">
                Profile Details
              </h2>

              <div className="space-y-6">
                {/* Display Name */}
                <div>
                  <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-sans transition-colors"
                    placeholder="Your name"
                  />
                  <p className="mt-1 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    This is how you&apos;ll appear to others in the system
                  </p>
                </div>

                {/* Email (Read-only) */}
                <div>
                  <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    disabled
                    className="w-full px-4 py-3 rounded-lg bg-light-bg/50 dark:bg-dark-bg/50 text-light-text/60 dark:text-dark-text/60 border border-border-primary cursor-not-allowed font-sans"
                    placeholder="your@email.com"
                  />
                  <p className="mt-1 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    Email address cannot be changed
                  </p>
                </div>

                {/* Bio */}
                <div>
                  <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                    Bio
                  </label>
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value.slice(0, 200))}
                    rows={3}
                    className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent resize-none font-sans transition-colors"
                    placeholder="Tell us about yourself..."
                    maxLength={200}
                  />
                  <div className="flex justify-between items-center mt-1">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      A brief description about you
                    </p>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      {bio.length}/200
                    </p>
                  </div>
                </div>

                {/* Two-column grid for smaller fields */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Location */}
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-sans transition-colors"
                      placeholder="City, Country"
                    />
                    <p className="mt-1 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      Where are you based?
                    </p>
                  </div>

                  {/* Job Title */}
                  <div>
                    <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                      Job Title
                    </label>
                    <input
                      type="text"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent font-sans transition-colors"
                      placeholder="Software Engineer"
                    />
                    <p className="mt-1 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      Your role or profession
                    </p>
                  </div>
                </div>

                {/* Instructions for Cirkelline */}
                <div>
                  <label className="block text-sm font-medium text-light-text dark:text-dark-text mb-2">
                    Instructions for Cirkelline
                  </label>
                  <textarea
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value.slice(0, 500))}
                    rows={4}
                    className="w-full px-4 py-3 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text border border-border-primary focus:outline-none focus:border-accent resize-none font-sans transition-colors"
                    placeholder="Add any special instructions or preferences for how Cirkelline should interact with you..."
                    maxLength={500}
                  />
                  <div className="flex justify-between items-center mt-1">
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      Custom instructions to personalize your Cirkelline experience
                    </p>
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      {instructions.length}/500
                    </p>
                  </div>
                </div>
              </div>

              {/* Save Button - Only show when changes exist */}
              {hasChanges && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-end mt-8 pt-6 border-t border-border-primary"
                >
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-lg text-white font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105"
                    style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
                  >
                    {saving ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Saving...</span>
                      </>
                    ) : (
                      <>
                        <Save size={18} />
                        <span>Save Changes</span>
                      </>
                    )}
                  </button>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Connected Services & Recent Activity - 1 column */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-1 space-y-6"
          >
            {/* Your Plan */}
            {!subscriptionLoading && subscription && (
              <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 border border-border-primary">
                <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 font-heading">
                  Your Plan
                </h2>

                <div className="space-y-4">
                  {/* Current Tier */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      Current Tier
                    </span>
                    <TierBadge tier={subscription.tier.slug} />
                  </div>

                  {/* Subscription Status */}
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      Status
                    </span>
                    <span className={`text-sm font-medium ${
                      subscription.status === 'active'
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-yellow-600 dark:text-yellow-400'
                    }`}>
                      {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                    </span>
                  </div>

                  {/* Billing Cycle (if paid tier) */}
                  {subscription.tier.slug !== 'member' && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                          Billing
                        </span>
                        <span className="text-sm font-medium text-light-text dark:text-dark-text">
                          {subscription.billing_cycle.charAt(0).toUpperCase() + subscription.billing_cycle.slice(1)}
                        </span>
                      </div>

                      {subscription.current_period_end && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                            Next Billing
                          </span>
                          <span className="text-sm font-medium text-light-text dark:text-dark-text">
                            {new Date(subscription.current_period_end).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </>
                  )}

                  {/* Upgrade Button */}
                  {canUpgrade && (
                    <button
                      onClick={() => toast.info('Upgrade feature coming soon! Contact admin for tier upgrades.')}
                      className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-white font-medium transition-all hover:scale-105"
                      style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
                    >
                      <ArrowUpCircle size={18} />
                      <span>Upgrade Plan</span>
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Connected Services */}
            <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 border border-border-primary">
              <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-4 font-heading">
                Connected Services
              </h2>

              <div className="flex items-center justify-center gap-4">
                {/* Google */}
                <button
                  className={`
                    p-2 rounded-lg transition-all duration-300
                    hover:scale-110
                    ${connectedServices.google ? 'opacity-100' : 'opacity-30 grayscale'}
                  `}
                  title="Google"
                >
                  <svg viewBox="0 0 24 24" className="w-5 h-5">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                </button>

                {/* Microsoft */}
                <button
                  className={`
                    p-2 rounded-lg transition-all duration-300
                    hover:scale-110
                    ${connectedServices.microsoft ? 'opacity-100' : 'opacity-30 grayscale'}
                  `}
                  title="Microsoft"
                >
                  <svg viewBox="0 0 23 23" className="w-5 h-5">
                    <path fill="#f25022" d="M0 0h11v11H0z"/>
                    <path fill="#00a4ef" d="M12 0h11v11H12z"/>
                    <path fill="#7fba00" d="M0 12h11v11H0z"/>
                    <path fill="#ffb900" d="M12 12h11v11H12z"/>
                  </svg>
                </button>

                {/* GitHub */}
                <button
                  className={`
                    p-2 rounded-lg transition-all duration-300
                    hover:scale-110
                    ${connectedServices.github ? 'opacity-100' : 'opacity-30 grayscale'}
                  `}
                  title="GitHub"
                >
                  <svg viewBox="0 0 24 24" className="w-5 h-5" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                </button>

                {/* Discord */}
                <button
                  className={`
                    p-2 rounded-lg transition-all duration-300
                    hover:scale-110
                    ${connectedServices.discord ? 'opacity-100' : 'opacity-30 grayscale'}
                  `}
                  title="Discord"
                >
                  <svg viewBox="0 0 71 55" className="w-5 h-5">
                    <path fill="#5865F2" d="M60.1045 4.8978C55.5792 2.8214 50.7265 1.2916 45.6527 0.41542C45.5603 0.39851 45.468 0.440769 45.4204 0.525289C44.7963 1.6353 44.105 3.0834 43.6209 4.2216C38.1637 3.4046 32.7345 3.4046 27.3892 4.2216C26.905 3.0581 26.1886 1.6353 25.5617 0.525289C25.5141 0.443589 25.4218 0.40133 25.3294 0.41542C20.2584 1.2888 15.4057 2.8186 10.8776 4.8978C10.8384 4.9147 10.8048 4.9429 10.7825 4.9795C1.57795 18.7309 -0.943561 32.1443 0.293408 45.3914C0.299005 45.4562 0.335386 45.5182 0.385761 45.5576C6.45866 50.0174 12.3413 52.7249 18.1147 54.5195C18.2071 54.5477 18.305 54.5139 18.3638 54.4378C19.7295 52.5728 20.9469 50.6063 21.9907 48.5383C22.0523 48.4172 21.9935 48.2735 21.8676 48.2256C19.9366 47.4931 18.0979 46.6 16.3292 45.5858C16.1893 45.5041 16.1781 45.304 16.3068 45.2082C16.679 44.9293 17.0513 44.6391 17.4067 44.3461C17.471 44.2926 17.5606 44.2813 17.6362 44.3151C29.2558 49.6202 41.8354 49.6202 53.3179 44.3151C53.3935 44.2785 53.4831 44.2898 53.5502 44.3433C53.9057 44.6363 54.2779 44.9293 54.6529 45.2082C54.7816 45.304 54.7732 45.5041 54.6333 45.5858C52.8646 46.6197 51.0259 47.4931 49.0921 48.2228C48.9662 48.2707 48.9102 48.4172 48.9718 48.5383C50.038 50.6034 51.2554 52.5699 52.5959 54.435C52.6519 54.5139 52.7526 54.5477 52.845 54.5195C58.6464 52.7249 64.529 50.0174 70.6019 45.5576C70.6551 45.5182 70.6887 45.459 70.6943 45.3942C72.1747 30.0791 68.2147 16.7757 60.1968 4.9823C60.1772 4.9429 60.1437 4.9147 60.1045 4.8978ZM23.7259 37.3253C20.2276 37.3253 17.3451 34.1136 17.3451 30.1693C17.3451 26.225 20.1717 23.0133 23.7259 23.0133C27.308 23.0133 30.1626 26.2532 30.1066 30.1693C30.1066 34.1136 27.28 37.3253 23.7259 37.3253ZM47.3178 37.3253C43.8196 37.3253 40.9371 34.1136 40.9371 30.1693C40.9371 26.225 43.7636 23.0133 47.3178 23.0133C50.9 23.0133 53.7545 26.2532 53.6986 30.1693C53.6986 34.1136 50.9 37.3253 47.3178 37.3253Z"/>
                  </svg>
                </button>
              </div>
            </div>

            <ActivityFeed
              activities={statistics?.recent_activity || []}
            />
          </motion.div>
        </div>
      </div>
    </div>
  )
}
