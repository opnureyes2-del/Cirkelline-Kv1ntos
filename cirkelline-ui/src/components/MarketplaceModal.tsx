'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, Check } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface MarketplaceModalProps {
  isOpen: boolean
  onClose: () => void
}

type Tab = 'upgrade' | 'tab2' | 'tab3'

export default function MarketplaceModal({ isOpen, onClose }: MarketplaceModalProps) {
  const [mounted, setMounted] = useState(false)
  const [activeTab, setActiveTab] = useState<Tab>('upgrade')

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

  const pricingTiers = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for getting started',
      features: [
        '10 messages per day',
        'Basic AI model access',
        'Community support',
        'Standard response time'
      ],
      highlighted: false
    },
    {
      name: 'Member',
      price: '$9',
      period: 'per month',
      description: 'For individuals who need more',
      features: [
        '100 messages per day',
        'Advanced AI models',
        'Priority support',
        'Faster response time',
        'Basic memory features'
      ],
      highlighted: false
    },
    {
      name: 'Pro',
      price: '$29',
      period: 'per month',
      description: 'For power users and professionals',
      features: [
        'Unlimited messages',
        'All AI models including premium',
        'Premium support 24/7',
        'Instant response time',
        'Advanced memory features',
        'Custom integrations',
        'Team collaboration (up to 5)'
      ],
      highlighted: true
    },
    {
      name: 'Premium',
      price: '$99',
      period: 'per month',
      description: 'For teams and enterprises',
      features: [
        'Everything in Pro',
        'Unlimited team members',
        'Custom AI model training',
        'Dedicated account manager',
        'SLA guarantee',
        'Advanced analytics',
        'API access',
        'Custom branding'
      ],
      highlighted: false
    }
  ]

  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6 bg-black/50 backdrop-blur-sm overflow-y-auto">
      <motion.div
        className="w-full max-w-6xl bg-light-surface dark:bg-dark-surface rounded-2xl shadow-2xl overflow-hidden my-auto"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.2 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-primary">
          <h2 className="text-2xl font-heading font-bold text-light-text dark:text-dark-text">
            Marketplace
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary rounded-lg transition-colors"
          >
            <X size={20} className="text-light-text-secondary dark:text-dark-text-secondary" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border-secondary">
          <button
            onClick={() => setActiveTab('upgrade')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'upgrade'
                ? 'text-accent border-b-2 border-accent'
                : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            Upgrade
          </button>
          <button
            onClick={() => setActiveTab('tab2')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'tab2'
                ? 'text-accent border-b-2 border-accent'
                : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            Tab 2
          </button>
          <button
            onClick={() => setActiveTab('tab3')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'tab3'
                ? 'text-accent border-b-2 border-accent'
                : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            Tab 3
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-12rem)]">
          <AnimatePresence mode="wait">
            {activeTab === 'upgrade' && (
              <motion.div
                key="upgrade"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Pricing Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {pricingTiers.map((tier) => (
                    <div
                      key={tier.name}
                      className={`rounded-xl p-6 border-2 transition-all ${
                        tier.highlighted
                          ? 'border-accent bg-accent/5 scale-105'
                          : 'border-border-primary bg-light-elevated dark:bg-dark-elevated hover:border-accent/50'
                      }`}
                    >
                      {/* Tier Name */}
                      <h3 className="text-xl font-heading font-bold text-light-text dark:text-dark-text mb-2">
                        {tier.name}
                      </h3>

                      {/* Price */}
                      <div className="mb-4">
                        <span className="text-4xl font-bold text-light-text dark:text-dark-text">
                          {tier.price}
                        </span>
                        <span className="text-sm text-light-text-secondary dark:text-dark-text-secondary ml-1">
                          {tier.period}
                        </span>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-6">
                        {tier.description}
                      </p>

                      {/* Features */}
                      <ul className="space-y-3 mb-6">
                        {tier.features.map((feature, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <Check
                              size={16}
                              className={`mt-0.5 flex-shrink-0 ${
                                tier.highlighted ? 'text-accent' : 'text-light-text-secondary dark:text-dark-text-secondary'
                              }`}
                            />
                            <span className="text-sm text-light-text dark:text-dark-text">
                              {feature}
                            </span>
                          </li>
                        ))}
                      </ul>

                      {/* CTA Button */}
                      <button
                        className={`w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-colors ${
                          tier.highlighted
                            ? 'bg-accent hover:bg-accent/90 text-white'
                            : 'bg-light-bg-secondary dark:bg-dark-bg-secondary hover:bg-light-bg dark:hover:bg-dark-bg text-light-text dark:text-dark-text'
                        }`}
                      >
                        {tier.name === 'Free' ? 'Current Plan' : 'Upgrade'}
                      </button>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'tab2' && (
              <motion.div
                key="tab2"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="flex items-center justify-center py-20"
              >
                <p className="text-light-text-secondary dark:text-dark-text-secondary">
                  Coming soon
                </p>
              </motion.div>
            )}

            {activeTab === 'tab3' && (
              <motion.div
                key="tab3"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="flex items-center justify-center py-20"
              >
                <p className="text-light-text-secondary dark:text-dark-text-secondary">
                  Coming soon
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>,
    document.body
  )
}
