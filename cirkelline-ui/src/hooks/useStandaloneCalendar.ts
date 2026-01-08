/**
 * Custom hook for Standalone Calendar data and operations
 * Works without external connections - data stored in PostgreSQL
 */

import { useState, useCallback, useEffect } from 'react';
import {
  Calendar,
  CalendarEvent,
  CalendarListResponse,
  StandaloneEventListResponse,
  CreateCalendarRequest,
  UpdateCalendarRequest,
  CreateStandaloneEventRequest,
  UpdateStandaloneEventRequest,
  CalendarApiError,
  CalendarViewType,
  RightPanelState
} from '@/types/calendar';

interface SyncStatus {
  google_connected: boolean;
}

interface SyncResult {
  success: boolean;
  google_connected: boolean;
  message: string;
  synced: number;
  created: number;
  updated: number;
}

interface UseStandaloneCalendarReturn {
  // Calendar state
  calendars: Calendar[];
  selectedCalendarIds: string[];

  // Event state
  events: CalendarEvent[];
  currentEvent: CalendarEvent | null;
  loading: boolean;
  error: string | null;

  // Google sync state
  googleConnected: boolean;
  isSyncing: boolean;
  lastSyncResult: SyncResult | null;

  // View state
  activeView: CalendarViewType;
  selectedDate: Date;
  selectedEvent: CalendarEvent | null;
  rightPanelState: RightPanelState;

  // Calendar actions
  fetchCalendars: () => Promise<void>;
  createCalendar: (data: CreateCalendarRequest) => Promise<Calendar | null>;
  updateCalendar: (id: string, data: UpdateCalendarRequest) => Promise<boolean>;
  deleteCalendar: (id: string) => Promise<boolean>;
  toggleCalendarVisibility: (id: string) => void;

  // Event actions
  fetchEvents: (timeMin?: string, timeMax?: string, limit?: number) => Promise<void>;
  fetchEventDetail: (eventId: string) => Promise<void>;
  createEvent: (data: CreateStandaloneEventRequest) => Promise<boolean>;
  updateEvent: (eventId: string, data: UpdateStandaloneEventRequest) => Promise<boolean>;
  deleteEvent: (eventId: string) => Promise<boolean>;
  clearError: () => void;
  clearCurrentEvent: () => void;

  // Google sync actions
  checkSyncStatus: () => Promise<void>;
  syncFromGoogle: () => Promise<SyncResult | null>;

  // View actions
  setActiveView: (view: CalendarViewType) => void;
  setSelectedDate: (date: Date) => void;
  setSelectedEvent: (event: CalendarEvent | null) => void;
  setRightPanelState: (state: RightPanelState) => void;
  goToToday: () => void;

  // Utility
  getDefaultCalendar: () => Calendar | undefined;
  hasCalendars: boolean;
}

export function useStandaloneCalendar(): UseStandaloneCalendarReturn {
  // Calendar state
  const [calendars, setCalendars] = useState<Calendar[]>([]);
  const [selectedCalendarIds, setSelectedCalendarIds] = useState<string[]>([]);

  // Event state
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [currentEvent, setCurrentEvent] = useState<CalendarEvent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // View state
  const [activeView, setActiveView] = useState<CalendarViewType>('month');
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [rightPanelState, setRightPanelState] = useState<RightPanelState>('upcoming');

  // Google sync state
  const [googleConnected, setGoogleConnected] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';

  /**
   * Get JWT token from localStorage
   */
  const getToken = useCallback((): string | null => {
    return localStorage.getItem('token');
  }, []);

  /**
   * Generic fetch wrapper with auth
   */
  const authenticatedFetch = useCallback(async (
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> => {
    const token = getToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${apiUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData: CalendarApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response;
  }, [apiUrl, getToken]);

  // ═══════════════════════════════════════════════════════════════
  // CALENDAR OPERATIONS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Fetch all calendars for the user
   */
  const fetchCalendars = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/calendar/calendars');
      const data: CalendarListResponse = await response.json();

      setCalendars(data.calendars);

      // Select visible calendars by default
      const visibleIds = data.calendars
        .filter(c => c.is_visible)
        .map(c => c.id);
      setSelectedCalendarIds(visibleIds);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch calendars';
      setError(errorMessage);
      console.error('Error fetching calendars:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Create a new calendar
   */
  const createCalendar = useCallback(async (data: CreateCalendarRequest): Promise<Calendar | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/calendar/calendars', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const newCalendar: Calendar = await response.json();

      // Add to local state
      setCalendars(prev => [...prev, newCalendar]);
      setSelectedCalendarIds(prev => [...prev, newCalendar.id]);

      return newCalendar;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create calendar';
      setError(errorMessage);
      console.error('Error creating calendar:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Update an existing calendar
   */
  const updateCalendar = useCallback(async (
    id: string,
    data: UpdateCalendarRequest
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/calendar/calendars/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      const updatedCalendar: Calendar = await response.json();

      // Update in local state
      setCalendars(prev => prev.map(cal =>
        cal.id === id ? updatedCalendar : cal
      ));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update calendar';
      setError(errorMessage);
      console.error('Error updating calendar:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Delete a calendar
   */
  const deleteCalendar = useCallback(async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/calendar/calendars/${id}`, {
        method: 'DELETE',
      });

      // Remove from local state
      setCalendars(prev => prev.filter(cal => cal.id !== id));
      setSelectedCalendarIds(prev => prev.filter(calId => calId !== id));

      // Remove events from this calendar
      setEvents(prev => prev.filter(event => event.calendar_id !== id));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete calendar';
      setError(errorMessage);
      console.error('Error deleting calendar:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Toggle calendar visibility (local only)
   */
  const toggleCalendarVisibility = useCallback((id: string) => {
    setSelectedCalendarIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(calId => calId !== id);
      } else {
        return [...prev, id];
      }
    });
  }, []);

  // ═══════════════════════════════════════════════════════════════
  // EVENT OPERATIONS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Fetch events for visible calendars
   */
  const fetchEvents = useCallback(async (
    timeMin?: string,
    timeMax?: string,
    limit: number = 100
  ) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (timeMin) params.append('time_min', timeMin);
      if (timeMax) params.append('time_max', timeMax);

      const response = await authenticatedFetch(`/api/calendar/events?${params}`);
      const data: StandaloneEventListResponse = await response.json();

      // Normalize event data (ensure summary field exists)
      const normalizedEvents = data.events.map(event => ({
        ...event,
        summary: event.summary || event.title || 'Untitled Event',
        start: event.start || event.start_time || '',
        end: event.end || event.end_time || '',
      }));

      setEvents(normalizedEvents);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch events';
      setError(errorMessage);
      console.error('Error fetching events:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Fetch full event details
   */
  const fetchEventDetail = useCallback(async (eventId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/calendar/events/${eventId}`);
      const data: CalendarEvent = await response.json();

      // Normalize
      const normalizedEvent = {
        ...data,
        summary: data.summary || data.title || 'Untitled Event',
        start: data.start || data.start_time || '',
        end: data.end || data.end_time || '',
      };

      setCurrentEvent(normalizedEvent);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch event detail';
      setError(errorMessage);
      console.error('Error fetching event detail:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Create a new event - auto-creates default calendar if none exists
   */
  const createEvent = useCallback(async (data: CreateStandaloneEventRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      // If no calendar_id provided and no calendars exist, create a default one first
      const eventData = { ...data };

      if (!eventData.calendar_id) {
        // Check if we have any calendars
        if (calendars.length === 0) {
          // Create default calendar first
          const response = await authenticatedFetch('/api/calendar/calendars', {
            method: 'POST',
            body: JSON.stringify({ name: 'My Calendar', color: '#8E0B83' }),
          });
          const newCalendar: Calendar = await response.json();
          setCalendars([newCalendar]);
          setSelectedCalendarIds([newCalendar.id]);
          eventData.calendar_id = newCalendar.id;
        } else {
          // Use default or first calendar
          const defaultCal = calendars.find(c => c.is_default) || calendars[0];
          eventData.calendar_id = defaultCal.id;
        }
      }

      const response = await authenticatedFetch('/api/calendar/events', {
        method: 'POST',
        body: JSON.stringify(eventData),
      });

      const newEvent: CalendarEvent = await response.json();

      // Normalize and add to local state
      const normalizedEvent = {
        ...newEvent,
        summary: newEvent.summary || newEvent.title || data.title,
        start: newEvent.start || newEvent.start_time || data.start_time,
        end: newEvent.end || newEvent.end_time || data.end_time,
      };

      setEvents(prev => [...prev, normalizedEvent].sort((a, b) =>
        new Date(a.start).getTime() - new Date(b.start).getTime()
      ));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create event';
      setError(errorMessage);
      console.error('Error creating event:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, calendars]);

  /**
   * Update an existing event
   */
  const updateEvent = useCallback(async (
    eventId: string,
    data: UpdateStandaloneEventRequest
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/calendar/events/${eventId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      const updatedEvent: CalendarEvent = await response.json();

      // Normalize
      const normalizedEvent = {
        ...updatedEvent,
        summary: updatedEvent.summary || updatedEvent.title || 'Untitled Event',
        start: updatedEvent.start || updatedEvent.start_time || '',
        end: updatedEvent.end || updatedEvent.end_time || '',
      };

      // Update in local state
      setEvents(prev => prev.map(event =>
        event.id === eventId ? normalizedEvent : event
      ).sort((a, b) =>
        new Date(a.start).getTime() - new Date(b.start).getTime()
      ));

      // Update current event if it was the one being edited
      if (currentEvent?.id === eventId) {
        setCurrentEvent(normalizedEvent);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update event';
      setError(errorMessage);
      console.error('Error updating event:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentEvent]);

  /**
   * Delete an event
   */
  const deleteEvent = useCallback(async (eventId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/calendar/events/${eventId}`, {
        method: 'DELETE',
      });

      // Remove from local state
      setEvents(prev => prev.filter(event => event.id !== eventId));

      // Clear current event if it was deleted
      if (currentEvent?.id === eventId) {
        setCurrentEvent(null);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete event';
      setError(errorMessage);
      console.error('Error deleting event:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentEvent]);

  // ═══════════════════════════════════════════════════════════════
  // GOOGLE SYNC OPERATIONS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if Google Calendar is connected
   */
  const checkSyncStatus = useCallback(async () => {
    try {
      const response = await authenticatedFetch('/api/calendar/sync/status');
      const data: SyncStatus = await response.json();
      setGoogleConnected(data.google_connected);
    } catch (err) {
      console.error('Error checking sync status:', err);
      setGoogleConnected(false);
    }
  }, [authenticatedFetch]);

  /**
   * Sync events from Google Calendar
   * - Pulls events from Google
   * - Merges with local database
   * - Refreshes local events list
   */
  const syncFromGoogle = useCallback(async (): Promise<SyncResult | null> => {
    setIsSyncing(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/calendar/sync/google', {
        method: 'POST',
      });
      const result: SyncResult = await response.json();

      setLastSyncResult(result);
      setGoogleConnected(result.google_connected);

      // If sync was successful, refresh events
      if (result.success) {
        await fetchEvents();
      }

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sync with Google';
      setError(errorMessage);
      console.error('Error syncing from Google:', err);
      return null;
    } finally {
      setIsSyncing(false);
    }
  }, [authenticatedFetch, fetchEvents]);

  // Check sync status on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      checkSyncStatus();
    }
  }, [checkSyncStatus]);

  // ═══════════════════════════════════════════════════════════════
  // UTILITY FUNCTIONS
  // ═══════════════════════════════════════════════════════════════

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentEvent = useCallback(() => {
    setCurrentEvent(null);
  }, []);

  const goToToday = useCallback(() => {
    setSelectedDate(new Date());
    setRightPanelState('upcoming');
  }, []);

  const getDefaultCalendar = useCallback((): Calendar | undefined => {
    return calendars.find(c => c.is_default) || calendars[0];
  }, [calendars]);

  // Filter events by selected calendars
  const filteredEvents = events.filter(event =>
    !event.calendar_id || selectedCalendarIds.includes(event.calendar_id)
  );

  return {
    // Calendar state
    calendars,
    selectedCalendarIds,

    // Event state (filtered by selected calendars)
    events: filteredEvents,
    currentEvent,
    loading,
    error,

    // Google sync state
    googleConnected,
    isSyncing,
    lastSyncResult,

    // View state
    activeView,
    selectedDate,
    selectedEvent,
    rightPanelState,

    // Calendar actions
    fetchCalendars,
    createCalendar,
    updateCalendar,
    deleteCalendar,
    toggleCalendarVisibility,

    // Event actions
    fetchEvents,
    fetchEventDetail,
    createEvent,
    updateEvent,
    deleteEvent,
    clearError,
    clearCurrentEvent,

    // Google sync actions
    checkSyncStatus,
    syncFromGoogle,

    // View actions
    setActiveView,
    setSelectedDate,
    setSelectedEvent,
    setRightPanelState,
    goToToday,

    // Utility
    getDefaultCalendar,
    hasCalendars: calendars.length > 0,
  };
}

export default useStandaloneCalendar;
