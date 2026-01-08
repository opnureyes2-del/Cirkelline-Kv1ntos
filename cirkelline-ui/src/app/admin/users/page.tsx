'use client'

import { useEffect, useState, useCallback } from 'react'
import type { User, UserDetails } from '@/types/os'
import { Users as UsersIcon, Search, Filter, ChevronLeft, ChevronRight, UserCheck, UserX, Shield, Mail, Calendar, Hash, Activity } from 'lucide-react'
import { toast } from 'sonner'
import { motion, AnimatePresence } from 'framer-motion'

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [userDetails, setUserDetails] = useState<Record<string, UserDetails>>({})
  const limit = 20

  // Fetch users
  const fetchUsers = useCallback(async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const searchParam = searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''
      const statusParam = statusFilter !== 'all' ? `&status_filter=${statusFilter}` : ''

      const response = await fetch(
        `${apiUrl}/api/admin/users?page=${page}&limit=${limit}${searchParam}${statusParam}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setUsers(data.data || [])
        setTotal(data.total || 0)
      } else {
        toast.error('Failed to load users')
      }
    } catch (error) {
      console.error('Users fetch error:', error)
      toast.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, searchQuery])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  // Fetch user details when expanding
  const fetchUserDetails = async (userId: string) => {
    if (userDetails[userId]) return // Already cached

    try {
      const token = localStorage.getItem('token')
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
      const response = await fetch(`${apiUrl}/api/admin/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const result = await response.json()
        setUserDetails(prev => ({
          ...prev,
          [userId]: result.data
        }))
      } else {
        toast.error('Failed to load user details')
      }
    } catch (error) {
      console.error('User details fetch error:', error)
      toast.error('Failed to load user details')
    }
  }

  // Handle expand
  const handleExpand = (userId: string) => {
    if (expandedId === userId) {
      setExpandedId(null)
    } else {
      setExpandedId(userId)
      fetchUserDetails(userId)
    }
  }

  // Handle search
  const handleSearch = () => {
    setPage(1)
    fetchUsers()
  }

  // Format timestamp
  const formatDate = (timestamp: number | null) => {
    if (!timestamp) return 'Never'
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // Format relative time
  const formatRelativeTime = (timestamp: number | null) => {
    if (!timestamp) return 'Never'
    const now = Date.now()
    const diff = now - (timestamp * 1000)
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-light-text dark:text-dark-text font-heading">
            User Management
          </h1>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans mt-1">
            Manage registered users and monitor activity
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-6">
          {/* Search */}
          <div className="flex items-center gap-2 flex-1 w-full sm:w-auto">
            <Search size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
            <input
              type="text"
              placeholder="Search by email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 px-3 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 rounded-lg text-white text-sm font-sans transition-colors"
              style={{ backgroundColor: 'rgb(var(--accent-rgb))' }}
            >
              Search
            </button>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter size={18} className="text-light-text-secondary dark:text-dark-text-secondary" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setPage(1)
              }}
              className="px-3 py-2 rounded-lg border border-border-primary bg-light-surface dark:bg-dark-surface text-light-text dark:text-dark-text text-sm font-sans focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="all">All Users</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="admin">Admins Only</option>
            </select>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Empty State */}
        {!loading && users.length === 0 && (
          <div className="text-center py-12">
            <UsersIcon className="w-16 h-16 mx-auto text-light-text-secondary dark:text-dark-text-secondary mb-4" />
            <p className="text-lg text-light-text dark:text-dark-text font-heading mb-2">
              No users found
            </p>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
              {searchQuery ? 'Try a different search query' : 'Registered users will appear here'}
            </p>
          </div>
        )}

        {/* Users Table */}
        {!loading && users.length > 0 && (
          <div className="space-y-3">
            {users.map((user) => (
              <motion.div
                key={user.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-light-surface dark:bg-dark-surface rounded-lg border border-border-primary overflow-hidden"
              >
                {/* Row Header */}
                <div
                  onClick={() => handleExpand(user.id)}
                  className="p-4 cursor-pointer hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors"
                >
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                    {/* Status Indicator */}
                    <div className="md:col-span-1 flex items-center">
                      <div className={`p-2 rounded-lg ${user.is_online ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-900/30'}`}>
                        {user.is_online ? (
                          <UserCheck className="w-5 h-5 text-green-600 dark:text-green-400" />
                        ) : (
                          <UserX className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                        )}
                      </div>
                    </div>

                    {/* User Info */}
                    <div className="md:col-span-6">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-semibold text-light-text dark:text-dark-text font-sans">
                          {user.email}
                        </p>
                        {user.is_admin && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                            Admin
                          </span>
                        )}
                        {user.is_online && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                            Online
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                        {user.display_name || 'No display name'}
                        {user.admin_name && ` • ${user.admin_name} (${user.admin_role})`}
                      </p>
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans mt-1">
                        Joined {formatDate(user.created_at)}
                        {user.last_login && ` • Last login ${formatRelativeTime(user.last_login)}`}
                      </p>
                    </div>

                    {/* Quick Stats */}
                    <div className="md:col-span-3">
                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                        User ID: {user.id.substring(0, 8)}...
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="md:col-span-2 flex items-center justify-end gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleExpand(user.id)
                        }}
                        className="text-xs px-3 py-1.5 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg text-light-text dark:text-dark-text transition-colors font-sans"
                      >
                        {expandedId === user.id ? 'Collapse' : 'Details'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                <AnimatePresence>
                  {expandedId === user.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="border-t border-border-secondary overflow-hidden"
                    >
                      <div className="p-4 space-y-4">
                        {/* Loading user details */}
                        {!userDetails[user.id] && (
                          <div className="flex justify-center py-4">
                            <div className="w-6 h-6 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                          </div>
                        )}

                        {/* User details loaded */}
                        {userDetails[user.id] && (
                          <>
                            {/* Basic Info */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                                  <Mail size={14} /> Contact Information
                                </h4>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2">
                                  <div>
                                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Email</p>
                                    <p className="text-sm text-light-text dark:text-dark-text font-sans">{userDetails[user.id].email}</p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Display Name</p>
                                    <p className="text-sm text-light-text dark:text-dark-text font-sans">{userDetails[user.id].display_name || 'Not set'}</p>
                                  </div>
                                </div>
                              </div>

                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                                  <Hash size={14} /> Account Details
                                </h4>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2">
                                  <div>
                                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">User ID</p>
                                    <p className="text-sm text-light-text dark:text-dark-text font-sans font-mono break-all">{userDetails[user.id].id}</p>
                                  </div>
                                  <div>
                                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Status</p>
                                    <div className="flex items-center gap-2 mt-1">
                                      {userDetails[user.id].is_admin && (
                                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                                          Admin
                                        </span>
                                      )}
                                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${userDetails[user.id].is_online ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-900/30 text-gray-600 dark:text-gray-400'}`}>
                                        {userDetails[user.id].is_online ? 'Online' : 'Offline'}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Activity Stats */}
                            <div>
                              <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                                <Activity size={14} /> Activity Statistics
                              </h4>
                              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Sessions</p>
                                  <p className="text-xl font-bold text-light-text dark:text-dark-text font-heading mt-1">{userDetails[user.id].statistics.session_count}</p>
                                </div>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Memories</p>
                                  <p className="text-xl font-bold text-light-text dark:text-dark-text font-heading mt-1">{userDetails[user.id].statistics.memory_count}</p>
                                </div>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                                  <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Feedback</p>
                                  <p className="text-xl font-bold text-light-text dark:text-dark-text font-heading mt-1">{userDetails[user.id].statistics.feedback_count}</p>
                                </div>
                              </div>
                            </div>

                            {/* Timestamps */}
                            <div>
                              <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                                <Calendar size={14} /> Timeline
                              </h4>
                              <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">
                                  <div>
                                    <span className="font-semibold">Created:</span> {formatDate(userDetails[user.id].created_at)}
                                  </div>
                                  <div>
                                    <span className="font-semibold">Updated:</span> {formatDate(userDetails[user.id].updated_at)}
                                  </div>
                                  <div>
                                    <span className="font-semibold">Last Login:</span> {formatDate(userDetails[user.id].last_login)}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Account Age */}
                            {userDetails[user.id].account_age_days !== undefined && (
                              <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Account Age</p>
                                <p className="text-lg font-bold text-light-text dark:text-dark-text font-heading mt-1">
                                  {userDetails[user.id].account_age_days} days
                                </p>
                              </div>
                            )}

                            {/* User Preferences */}
                            {userDetails[user.id].preferences && Object.keys(userDetails[user.id].preferences || {}).length > 0 && (
                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">User Preferences</h4>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg">
                                  <pre className="text-xs text-light-text dark:text-dark-text font-mono overflow-x-auto">
                                    {JSON.stringify(userDetails[user.id].preferences, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            )}

                            {/* Admin Profile (if applicable) */}
                            {userDetails[user.id].admin_profile && (
                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans flex items-center gap-2">
                                  <Shield size={14} /> Admin Profile
                                </h4>
                                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg space-y-2">
                                  <div>
                                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Name & Role</p>
                                    <p className="text-sm text-light-text dark:text-dark-text font-sans">
                                      {userDetails[user.id].admin_profile?.name} • {userDetails[user.id].admin_profile?.role}
                                    </p>
                                  </div>
                                  {userDetails[user.id].admin_profile?.personal_context && (
                                    <div>
                                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Personal Context</p>
                                      <p className="text-sm text-light-text dark:text-dark-text font-sans">{userDetails[user.id].admin_profile?.personal_context}</p>
                                    </div>
                                  )}
                                  {userDetails[user.id].admin_profile?.custom_instructions && (
                                    <div>
                                      <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-sans">Custom Instructions</p>
                                      <p className="text-sm text-light-text dark:text-dark-text font-sans">{userDetails[user.id].admin_profile?.custom_instructions}</p>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Recent Sessions */}
                            {/* @ts-expect-error - userDetails[user.id] is guaranteed to exist within this block (line 354 check) */}
                            {(userDetails[user.id] as UserDetails).recent_sessions?.length > 0 && (
                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">Recent Sessions ({(userDetails[user.id] as UserDetails).recent_sessions?.length})</h4>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2 max-h-48 overflow-y-auto">
                                  {(userDetails[user.id] as UserDetails).recent_sessions?.map((session, idx: number) => (
                                    <div key={idx} className="text-xs border-b border-border-secondary last:border-0 pb-2 last:pb-0">
                                      <p className="font-mono text-light-text dark:text-dark-text">{session.session_id.substring(0, 16)}...</p>
                                      <p className="text-light-text-secondary dark:text-dark-text-secondary">Created: {new Date(session.created_at * 1000).toLocaleString()}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Recent Memories */}
                            {/* @ts-expect-error - userDetails[user.id] is guaranteed to exist within this block (line 354 check) */}
                            {(userDetails[user.id] as UserDetails).recent_memories?.length > 0 && (
                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">Recent Memories ({(userDetails[user.id] as UserDetails).recent_memories?.length})</h4>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2 max-h-48 overflow-y-auto">
                                  {(userDetails[user.id] as UserDetails).recent_memories?.map((memory, idx: number) => (
                                    <div key={idx} className="text-xs border-b border-border-secondary last:border-0 pb-2 last:pb-0">
                                      <p className="text-light-text dark:text-dark-text">{memory.memory}</p>
                                      <p className="text-light-text-secondary dark:text-dark-text-secondary mt-1">
                                        {new Date(memory.updated_at * 1000).toLocaleString()}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Recent Feedback */}
                            {/* @ts-expect-error - userDetails[user.id] is guaranteed to exist within this block (line 354 check) */}
                            {(userDetails[user.id] as UserDetails).recent_feedback?.length > 0 && (
                              <div>
                                <h4 className="text-xs font-semibold text-light-text dark:text-dark-text mb-2 font-sans">Recent Feedback ({(userDetails[user.id] as UserDetails).recent_feedback?.length})</h4>
                                <div className="bg-light-bg-secondary dark:bg-dark-bg-secondary p-3 rounded-lg space-y-2 max-h-48 overflow-y-auto">
                                  {(userDetails[user.id] as UserDetails).recent_feedback?.map((feedback, idx: number) => (
                                    <div key={idx} className="text-xs border-b border-border-secondary last:border-0 pb-2 last:pb-0">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${feedback.feedback_type === 'positive' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'}`}>
                                          {feedback.feedback_type}
                                        </span>
                                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-900/30 text-gray-600 dark:text-gray-400">
                                          {feedback.status}
                                        </span>
                                      </div>
                                      <p className="text-light-text dark:text-dark-text">{feedback.message_content}</p>
                                      {feedback.user_comments && (
                                        <p className="text-light-text-secondary dark:text-dark-text-secondary italic mt-1">&quot;{feedback.user_comments}&quot;</p>
                                      )}
                                      <p className="text-light-text-secondary dark:text-dark-text-secondary mt-1">
                                        {formatDate(feedback.created_at)}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {!loading && users.length > 0 && totalPages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
              Page {page} of {totalPages} • Showing {users.length} of {total} users
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed text-light-text dark:text-dark-text transition-colors"
              >
                <ChevronLeft size={18} />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg border border-border-primary hover:bg-light-bg dark:hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed text-light-text dark:text-dark-text transition-colors"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
