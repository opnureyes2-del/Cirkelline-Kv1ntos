'use client'

import { Link as LinkIcon } from 'lucide-react'
import GoogleConnect from '@/components/GoogleConnect'
import NotionConnect from '@/components/NotionConnect'

export default function ProfileIntegrationsPage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <LinkIcon className="w-8 h-8 text-accent" />
            <h1 className="text-3xl font-bold text-light-text dark:text-dark-text font-heading">
              Integrations
            </h1>
          </div>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-sans">
            Connect your accounts and services to enhance your Cirkelline experience
          </p>
        </div>

        {/* Google Services Card */}
        <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary">
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2 font-heading">
            Google Services
          </h2>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-6">
            Connect your Google account to access Gmail and Calendar directly in Cirkelline
          </p>

          <GoogleConnect />
        </div>

        {/* Notion Workspace Card */}
        <div className="mt-6 bg-light-surface dark:bg-dark-surface rounded-2xl p-6 sm:p-8 border border-border-primary">
          <h2 className="text-xl font-semibold text-light-text dark:text-dark-text mb-2 font-heading">
            Notion Workspace
          </h2>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-6">
            Connect your Notion workspace to access databases, projects, and tasks directly in Cirkelline
          </p>

          <NotionConnect />
        </div>

        {/* Future Integrations - Placeholders */}
        <div className="mt-6 space-y-4">
          {/* Slack Integration (Placeholder) */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 border border-border-primary opacity-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading">
                  Slack
                </h3>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
                  Connect your Slack workspace (Coming soon)
                </p>
              </div>
              <button
                disabled
                className="px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text font-sans cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>
          </div>

          {/* Discord Integration (Placeholder) */}
          <div className="bg-light-surface dark:bg-dark-surface rounded-2xl p-6 border border-border-primary opacity-50">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-light-text dark:text-dark-text font-heading">
                  Discord
                </h3>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
                  Connect your Discord account (Coming soon)
                </p>
              </div>
              <button
                disabled
                className="px-4 py-2 rounded-lg bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text font-sans cursor-not-allowed"
              >
                Coming Soon
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
