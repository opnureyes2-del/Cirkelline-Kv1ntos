'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarState {
  isCollapsed: boolean
  isMobileOpen: boolean
  hasHydrated: boolean
  setHasHydrated: (hydrated: boolean) => void
  toggle: () => void
  collapse: () => void
  expand: () => void
  setMobileOpen: (open: boolean) => void
}

// Helper to save sidebar state to backend
const saveSidebarCollapsedToBackend = async (isCollapsed: boolean) => {
  const token = localStorage.getItem('token')
  if (!token) {
    console.log('⚠️ Sidebar collapsed save skipped: No token found')
    return // Not logged in
  }

  console.log('💾 Saving sidebar collapsed state to backend:', isCollapsed)

  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'
    const response = await fetch(`${apiUrl}/api/user/preferences`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ sidebarCollapsed: isCollapsed })
    })

    if (response.ok) {
      const data = await response.json()
      console.log('✅ Sidebar collapsed state saved successfully:', data)
    } else {
      console.error('❌ Failed to save sidebar collapsed state:', response.status, await response.text())
    }
  } catch (error) {
    console.error('Failed to save sidebar collapsed state:', error)
  }
}

export const useSidebar = create<SidebarState>()(
  persist(
    (set) => ({
      isCollapsed: false,
      isMobileOpen: false,
      hasHydrated: false,
      setHasHydrated: (hydrated: boolean) => set({ hasHydrated: hydrated }),
      toggle: () => set((state) => {
        const newCollapsed = !state.isCollapsed
        saveSidebarCollapsedToBackend(newCollapsed)
        return { isCollapsed: newCollapsed }
      }),
      collapse: () => {
        saveSidebarCollapsedToBackend(true)
        return set({ isCollapsed: true })
      },
      expand: () => {
        saveSidebarCollapsedToBackend(false)
        return set({ isCollapsed: false })
      },
      setMobileOpen: (open: boolean) => set({ isMobileOpen: open }),
    }),
    {
      name: 'sidebar-state',
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)

// Listen for storage events (from backend preferences load)
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === 'sidebar-state' && e.newValue) {
      try {
        const data = JSON.parse(e.newValue)
        if (data.state?.isCollapsed !== undefined) {
          console.log('🔄 useSidebar: Detected localStorage change, updating Zustand store to:', data.state.isCollapsed)
          useSidebar.setState({ isCollapsed: data.state.isCollapsed })
        }
      } catch (error) {
        console.error('Failed to parse sidebar-state from storage event:', error)
      }
    }
  })
}
