'use client'

import { Users, Shield, Activity as ActivityIcon, CheckCircle, XCircle, AlertTriangle, Globe, UserCheck, Clock } from 'lucide-react'
import { useState, useEffect } from 'react'
import type { ActivityLogStats } from '@/types/os'

export default function AdminOverviewPage() {
  const [loading, setLoading] = useState(true)

  // Activity stats
  const [activityStats, setActivityStats] = useState<ActivityLogStats>({
    total_logs: 0,
    successful_actions: 0,
    failed_actions: 0,
    admin_actions: 0,
    avg_duration_ms: 0,
    unique_users: 0,
    logs_last_24h: 0,
    failed_logins_last_hour: 0,
    action_breakdown: []
  })

  // User stats
  const [userStats, setUserStats] = useState({
    total_users: 0,
    online_users: 0,
    admin_users: 0,
    new_users_week: 0
  })

  // Fetch all stats
  useEffect(() => {
    const fetchAllStats = async () => {
      try {
        const token = localStorage.getItem('token')
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

        // Fetch activity stats
        const activityResponse = await fetch(`${apiUrl}/api/admin/activity?page=1&limit=1`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (activityResponse.ok) {
          const activityData = await activityResponse.json()
          setActivityStats(activityData.stats || {})
        }

        // Fetch user stats
        const userResponse = await fetch(`${apiUrl}/api/admin/users?page=1&limit=1`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (userResponse.ok) {
          const userData = await userResponse.json()
          setUserStats(userData.stats || {})
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchAllStats()
  }, [])

  // Calculate success rate
  const successRate = activityStats.total_logs > 0
    ? Math.round((activityStats.successful_actions / activityStats.total_logs) * 100)
    : 0

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
              Admin Overview
            </h1>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-body">
            System statistics and management dashboard
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && (
          <>
            {/* User Statistics */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                User Metrics
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Total Users</p>
                      <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">{userStats.total_users}</p>
                    </div>
                    <Users className="w-8 h-8 text-light-text-secondary dark:text-dark-text-secondary" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Online Now</p>
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400 font-heading mt-1">{userStats.online_users}</p>
                    </div>
                    <Globe className="w-8 h-8 text-green-600 dark:text-green-400" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">New (7 days)</p>
                      <p className="text-2xl font-bold text-accent font-heading mt-1">{userStats.new_users_week}</p>
                    </div>
                    <UserCheck className="w-8 h-8 text-accent" />
                  </div>
                </div>
              </div>
            </div>

            {/* Activity Statistics */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading mb-4 flex items-center gap-2">
                <ActivityIcon className="w-5 h-5" />
                Activity Metrics
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Success Rate</p>
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400 font-heading mt-1">{successRate}%</p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Avg Response</p>
                      <p className="text-2xl font-bold text-light-text dark:text-dark-text font-heading mt-1">{Math.round(activityStats.avg_duration_ms)}ms</p>
                    </div>
                    <Clock className="w-8 h-8 text-light-text-secondary dark:text-dark-text-secondary" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Failed Logins (1h)</p>
                      <p className="text-2xl font-bold text-red-600 dark:text-red-400 font-heading mt-1">{activityStats.failed_logins_last_hour}</p>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  </div>
                </div>

                <div className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-body">Failed Actions</p>
                      <p className="text-2xl font-bold text-red-600 dark:text-red-400 font-heading mt-1">{activityStats.failed_actions.toLocaleString()}</p>
                    </div>
                    <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
