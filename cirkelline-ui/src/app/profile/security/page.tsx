'use client'

import { Shield, Lock, Smartphone, LogOut, AlertTriangle } from 'lucide-react'

export default function ProfileSecurityPage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
              Security
            </h1>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
            Manage your account security and privacy settings
          </p>
        </div>

        {/* Password Section (Placeholder) */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <Lock className="w-6 h-6 text-light-text-secondary dark:text-dark-text-secondary" />
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading">
              Password
            </h2>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-4">
            Change your account password to keep your account secure
          </p>
          <button
            disabled
            className="px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text font-sans cursor-not-allowed"
          >
            Change Password (Coming Soon)
          </button>
        </div>

        {/* Two-Factor Authentication (Placeholder) */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <Smartphone className="w-6 h-6 text-light-text-secondary dark:text-dark-text-secondary" />
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading">
              Two-Factor Authentication
            </h2>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-4">
            Add an extra layer of security to your account with 2FA
          </p>
          <button
            disabled
            className="px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text font-sans cursor-not-allowed"
          >
            Enable 2FA (Coming Soon)
          </button>
        </div>

        {/* Active Sessions (Placeholder) */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary mb-6 opacity-50">
          <div className="flex items-center gap-3 mb-6">
            <LogOut className="w-6 h-6 text-light-text-secondary dark:text-dark-text-secondary" />
            <h2 className="text-xl font-semibold text-light-text dark:text-dark-text font-heading">
              Active Sessions
            </h2>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-4">
            Manage and review devices that are currently logged into your account
          </p>
          <div className="bg-light-bg dark:bg-dark-bg rounded-lg p-4 border border-border-primary">
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary text-center">
              Session management coming soon
            </p>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border-2 border-error/20">
          <div className="flex items-center gap-3 mb-6">
            <AlertTriangle className="w-6 h-6 text-error" />
            <h2 className="text-xl font-semibold text-error font-heading">
              Danger Zone
            </h2>
          </div>
          <div className="space-y-4">
            {/* Export Data (Placeholder) */}
            <div className="pb-4 border-b border-border-primary">
              <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-2">
                Export Your Data
              </h3>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-3">
                Download a copy of all your data (conversations, documents, settings)
              </p>
              <button
                disabled
                className="px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text font-sans text-sm cursor-not-allowed opacity-50"
              >
                Export Data (Coming Soon)
              </button>
            </div>

            {/* Delete Account (Placeholder) */}
            <div>
              <h3 className="text-sm font-semibold text-error mb-2">
                Delete Account
              </h3>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-3">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <button
                disabled
                className="px-4 py-2 rounded-lg bg-error/10 text-error font-sans text-sm cursor-not-allowed opacity-50"
              >
                Delete Account (Coming Soon)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
