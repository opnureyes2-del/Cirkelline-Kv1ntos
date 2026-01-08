'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, Book, Info, Mail } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useLearnMore } from '@/contexts/LearnMoreContext'

interface LearnMoreModalProps {
  isOpen: boolean
  onClose: () => void
}

type Tab = 'howto' | 'about' | 'contact'

export default function LearnMoreModal({ isOpen, onClose }: LearnMoreModalProps) {
  const [mounted, setMounted] = useState(false)
  const { activeTab: contextTab } = useLearnMore()
  const [activeTab, setActiveTab] = useState<Tab>(contextTab === 'about' ? 'about' : contextTab === 'contact' ? 'contact' : 'howto')

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (isOpen && contextTab) {
      setActiveTab(contextTab === 'about' ? 'about' : contextTab === 'contact' ? 'contact' : 'howto')
    }
  }, [isOpen, contextTab])

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
            Learn More
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
            onClick={() => setActiveTab('howto')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'howto'
                ? 'text-accent border-b-2 border-accent'
                : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            <Book size={16} />
            How to Use
          </button>
          <button
            onClick={() => setActiveTab('about')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'about'
                ? 'text-accent border-b-2 border-accent'
                : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            <Info size={16} />
            About
          </button>
          <button
            onClick={() => setActiveTab('contact')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
              activeTab === 'contact'
                ? 'text-accent border-b-2 border-accent'
                : 'text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text'
            }`}
          >
            <Mail size={16} />
            Contact
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-12rem)]">
          <AnimatePresence mode="wait">
            {activeTab === 'howto' && (
              <motion.div
                key="howto"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-xl font-heading font-bold text-light-text dark:text-dark-text mb-4">
                    Getting Started with Cirkelline
                  </h3>
                  <div className="space-y-4 text-light-text dark:text-dark-text">
                    <div>
                      <h4 className="font-semibold mb-2">1. Start a Conversation</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        Simply type your message in the chat input at the bottom of the screen.
                        Cirkelline is here to assist you with a wide range of tasks, from answering
                        questions to helping with creative projects.
                      </p>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">2. Manage Your Sessions</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        Your conversations are automatically saved as sessions in the sidebar.
                        You can return to any previous conversation by clicking on it. Use the dot
                        menu to rename, archive, or delete sessions.
                      </p>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">3. Build Your Memory Profile</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        Cirkelline learns from your conversations to provide more personalized assistance.
                        Your memories are stored securely and can be viewed in the Memories section
                        of the sidebar.
                      </p>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">4. Customize Your Experience</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        Switch between light and dark themes, update your profile, and explore
                        marketplace features to enhance your Cirkelline experience.
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'about' && (
              <motion.div
                key="about"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-xl font-heading font-bold text-light-text dark:text-dark-text mb-4">
                    About Cirkelline
                  </h3>
                  <div className="space-y-4 text-light-text dark:text-dark-text">
                    <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      Cirkelline is your intelligent personal assistant, designed to help you be more
                      productive, creative, and informed. Powered by advanced AI technology, Cirkelline
                      adapts to your needs and grows with you over time.
                    </p>

                    <div>
                      <h4 className="font-semibold mb-2">Our Mission</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        To provide everyone with a personalized AI assistant that understands their
                        unique needs, preferences, and goals. We believe AI should be accessible,
                        helpful, and respectful of your privacy.
                      </p>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">Key Features</h4>
                      <ul className="text-sm text-light-text-secondary dark:text-dark-text-secondary space-y-2 list-disc list-inside">
                        <li>Advanced conversational AI with natural language understanding</li>
                        <li>Persistent memory that learns from your interactions</li>
                        <li>Session management for organizing your conversations</li>
                        <li>Multi-model support for diverse AI capabilities</li>
                        <li>Secure and private by design</li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">Privacy & Security</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        Your data is encrypted and stored securely. We never share your conversations
                        or personal information with third parties. You have full control over your
                        data and can delete it at any time.
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'contact' && (
              <motion.div
                key="contact"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="space-y-6"
              >
                <div>
                  <h3 className="text-xl font-heading font-bold text-light-text dark:text-dark-text mb-4">
                    Get in Touch
                  </h3>
                  <div className="space-y-4">
                    <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                      We&apos;d love to hear from you! Whether you have questions, feedback, or need
                      support, our team is here to help.
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg border border-border-primary bg-light-elevated dark:bg-dark-elevated">
                        <h4 className="font-semibold text-light-text dark:text-dark-text mb-2">
                          Email Support
                        </h4>
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-2">
                          For general inquiries and support
                        </p>
                        <a
                          href="mailto:support@cirkelline.com"
                          className="text-sm text-accent hover:underline"
                        >
                          support@cirkelline.com
                        </a>
                      </div>

                      <div className="p-4 rounded-lg border border-border-primary bg-light-elevated dark:bg-dark-elevated">
                        <h4 className="font-semibold text-light-text dark:text-dark-text mb-2">
                          Business Inquiries
                        </h4>
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-2">
                          For partnerships and enterprise solutions
                        </p>
                        <a
                          href="mailto:business@cirkelline.com"
                          className="text-sm text-accent hover:underline"
                        >
                          business@cirkelline.com
                        </a>
                      </div>

                      <div className="p-4 rounded-lg border border-border-primary bg-light-elevated dark:bg-dark-elevated">
                        <h4 className="font-semibold text-light-text dark:text-dark-text mb-2">
                          Technical Support
                        </h4>
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-2">
                          For technical issues and bugs
                        </p>
                        <a
                          href="mailto:tech@cirkelline.com"
                          className="text-sm text-accent hover:underline"
                        >
                          tech@cirkelline.com
                        </a>
                      </div>

                      <div className="p-4 rounded-lg border border-border-primary bg-light-elevated dark:bg-dark-elevated">
                        <h4 className="font-semibold text-light-text dark:text-dark-text mb-2">
                          Social Media
                        </h4>
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-2">
                          Follow us for updates and news
                        </p>
                        <div className="flex gap-2">
                          <a href="#" className="text-sm text-accent hover:underline">Twitter</a>
                          <span className="text-light-text-secondary dark:text-dark-text-secondary">•</span>
                          <a href="#" className="text-sm text-accent hover:underline">LinkedIn</a>
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 p-4 rounded-lg bg-accent/10 border border-accent/20">
                      <h4 className="font-semibold text-accent mb-2">Response Time</h4>
                      <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        We typically respond to all inquiries within 24 hours during business days.
                        Premium and Pro users receive priority support with faster response times.
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>,
    document.body
  )
}
