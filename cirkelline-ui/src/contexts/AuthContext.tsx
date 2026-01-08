"use client"

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useStore } from '@/store';

interface User {
  user_id: string;
  email?: string;
  display_name?: string;
  isAnonymous: boolean;
  is_admin?: boolean;
  // Tier information
  tier_slug?: string;
  tier_level?: number;
  subscription_status?: string;
}

interface AuthContextType {
  user: User | null;
  login: (token: string) => void;
  register: (token: string) => void;
  logout: () => void;
  getUserId: () => string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// v1.3.4: Removed anonymous user ID generation - accounts are now required
// The setNotAuthenticated function marks user as needing login (no anon-xxx IDs)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Initialize user on mount
  useEffect(() => {
    initializeUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const initializeUser = () => {
    // Check for JWT in localStorage
    const token = localStorage.getItem('token');

    if (token) {
      try {
        // Decode JWT (simple base64 decode of payload)
        const payload = JSON.parse(atob(token.split('.')[1]));

        // Check if token is expired
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          // Token expired, clear it - user needs to login
          localStorage.removeItem('token');
          setNotAuthenticated();
        } else {
          // Valid JWT, set authenticated user
          setUser({
            user_id: payload.user_id,
            email: payload.email,
            display_name: payload.display_name,
            isAnonymous: false,
            is_admin: payload.is_admin,
            // Extract tier information from JWT
            tier_slug: payload.tier_slug || 'member',
            tier_level: payload.tier_level || 1,
            subscription_status: payload.subscription_status || 'active',
          });

          // Load user preferences from backend on page load
          loadUserPreferences(token, payload.user_id);
        }
      } catch (error) {
        console.error('Error decoding token:', error);
        setNotAuthenticated();
      }
    } else {
      // No JWT - user needs to login
      // v1.3.4: No longer generate anon-xxx IDs - accounts are required
      setNotAuthenticated();
    }
  };

  // v1.3.4: Set user as not authenticated (needs to login)
  // This replaces createAnonymousUser - no anon IDs are generated
  const setNotAuthenticated = () => {
    setUser({
      user_id: '',  // Empty - no user ID for unauthenticated users
      isAnonymous: true,  // Triggers login gate in page.tsx
    });
  };

  // Helper function to load user preferences from backend
  const loadUserPreferences = async (token: string, userId: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';
      const response = await fetch(`${apiUrl}/api/user/preferences`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const preferences = data.preferences || {};

        console.log('📥 Loading user preferences from backend:', preferences);

        // Apply preferences to localStorage
        if (preferences.theme) {
          localStorage.setItem('theme', preferences.theme);
        }

        if (preferences.accentColor) {
          localStorage.setItem('accentColor', preferences.accentColor);

          // Apply accent color to CSS variable
          const colorMap: { [key: string]: string } = {
            contrast: '', // Will be calculated below
            purple: '142, 11, 131',
            orange: '236, 75, 19',
            green: '19, 236, 129',
            blue: '19, 128, 236',
            pink: '236, 19, 128',
          };

          let rgbValue: string;
          if (preferences.accentColor === 'contrast') {
            const isDark = document.documentElement.classList.contains('dark');
            rgbValue = isDark ? '224, 224, 224' : '33, 33, 36'; // #E0E0E0 (dark) : #212124 (light)
          } else {
            rgbValue = colorMap[preferences.accentColor] || '142, 11, 131';
          }

          document.documentElement.style.setProperty('--accent-rgb', rgbValue);
          console.log('🎨 Applied accent color from backend:', preferences.accentColor, 'RGB:', rgbValue);
        }

        // Sidebar collapsed state
        if (preferences.sidebarCollapsed !== undefined) {
          const sidebarState = {
            state: { isCollapsed: preferences.sidebarCollapsed, isMobileOpen: false },
            version: 0
          };
          localStorage.setItem('sidebar-state', JSON.stringify(sidebarState));
        }

        // Sidebar sections (expanded/collapsed state) - stored under "sidebar" in DB
        if (preferences.sidebar) {
          // Apply each section state to localStorage
          Object.entries(preferences.sidebar).forEach(([key, value]) => {
            localStorage.setItem(key, JSON.stringify(value));
          });
        }

        // Banner dismissed state
        if (preferences.bannerDismissed !== undefined) {
          const bannerKey = `noticeBannerDismissed-${userId}`;
          localStorage.setItem(bannerKey, preferences.bannerDismissed.toString());
        }

        // TopBar icons expanded state
        if (preferences.topbarIconsExpanded !== undefined) {
          localStorage.setItem('topbar-icons-expanded', JSON.stringify(preferences.topbarIconsExpanded));
        }

        console.log('✅ User preferences loaded and applied to localStorage');

        // Dispatch custom events to notify components
        window.dispatchEvent(new Event('storage'));
        window.dispatchEvent(new CustomEvent('accentColorChange')); // Notify buttons to update text/icon colors
        window.dispatchEvent(new CustomEvent('sidebarPreferencesLoaded'));
        window.dispatchEvent(new CustomEvent('bannerPreferencesLoaded'));
        window.dispatchEvent(new CustomEvent('topbarPreferencesLoaded'));

      } else {
        console.warn('Failed to load user preferences:', response.status);
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  };

  // ✅ v1.2.33: Save user's browser timezone to backend on login
  const saveUserTimezone = async (token: string) => {
    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';

      await fetch(`${apiUrl}/api/user/preferences`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ timezone })
      });

      console.log('🌍 Saved user timezone to backend:', timezone);
    } catch (error) {
      console.error('Error saving timezone:', error);
    }
  };

  const login = (token: string) => {
    // 1. Clear all chat state from previous user/guest session
    useStore.getState().setMessages([]);
    useStore.getState().setSessionsData([]);
    useStore.getState().setStreamingErrorMessage('');

    // 2. Save JWT to localStorage with key 'token' (standard key for backend)
    localStorage.setItem('token', token);

    // 3. Decode and set user from JWT
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({
        user_id: payload.user_id,
        email: payload.email,
        display_name: payload.display_name,
        isAnonymous: false,
        is_admin: payload.is_admin,
        // Extract tier information from JWT
        tier_slug: payload.tier_slug || 'member',
        tier_level: payload.tier_level || 1,
        subscription_status: payload.subscription_status || 'active',
      });
      console.log('✅ JWT token stored in localStorage as "token"');
      console.log('✅ User logged in:', payload.email, payload.is_admin ? '(Admin)' : '(Regular)');
      console.log('✅ Chat state cleared for new user');

      // 4. Load user preferences from backend
      loadUserPreferences(token, payload.user_id);

      // 5. Save user's browser timezone to backend (v1.2.33)
      saveUserTimezone(token);
    } catch (error) {
      console.error('Error decoding token during login:', error);
    }
  };

  const register = (token: string) => {
    // Register is the same as login - both save token and decode user
    login(token);
  };

  const logout = () => {
    // 1. Clear JWT
    localStorage.removeItem('token');

    // 2. Clear all chat state from Zustand store
    useStore.getState().setMessages([]);
    useStore.getState().setSessionsData([]);
    useStore.getState().setStreamingErrorMessage('');

    // 3. Set user as not authenticated (triggers login gate)
    // v1.3.4: No longer generate anon IDs - accounts are required
    setNotAuthenticated();

    // 4. Force full page reload to clear URL params and start fresh
    window.location.href = '/';
  };

  const getUserId = (): string => {
    return user?.user_id || '';
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, getUserId }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
