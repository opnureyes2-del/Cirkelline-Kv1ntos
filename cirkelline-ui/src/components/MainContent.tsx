'use client'

import { useSidebar } from '@/hooks/useSidebar'

export default function MainContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar()

  return (
    <main
      className={`
        h-screen pt-16
        bg-light-bg dark:bg-dark-bg
        transition-all duration-300 ease-in-out
        ${isCollapsed ? 'md:ml-16' : 'md:ml-64'}
      `}
    >
      {children}
    </main>
  )
}
