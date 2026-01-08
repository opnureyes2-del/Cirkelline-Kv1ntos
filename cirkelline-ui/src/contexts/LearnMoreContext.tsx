'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

interface LearnMoreContextType {
  isOpen: boolean
  openLearnMore: (tab?: 'about' | 'contact') => void
  closeLearnMore: () => void
  activeTab: 'about' | 'contact'
}

const LearnMoreContext = createContext<LearnMoreContextType | undefined>(undefined)

export function LearnMoreProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'about' | 'contact'>('about')

  const openLearnMore = (tab: 'about' | 'contact' = 'about') => {
    setActiveTab(tab)
    setIsOpen(true)
  }

  const closeLearnMore = () => {
    setIsOpen(false)
  }

  return (
    <LearnMoreContext.Provider value={{ isOpen, openLearnMore, closeLearnMore, activeTab }}>
      {children}
    </LearnMoreContext.Provider>
  )
}

export function useLearnMore() {
  const context = useContext(LearnMoreContext)
  if (context === undefined) {
    throw new Error('useLearnMore must be used within a LearnMoreProvider')
  }
  return context
}
