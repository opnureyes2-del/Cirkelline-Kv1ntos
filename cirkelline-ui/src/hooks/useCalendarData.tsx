/**
 * Custom hook for Google Calendar data and operations
 * Provides event list, detail, create, update, and delete functionality
 */

import { useState, useCallback } from 'react';
import {
  CalendarEvent,
  CalendarEventListResponse,
  CreateEventRequest,
  UpdateEventRequest,
  CalendarApiError,
  CalendarViewType,
  RightPanelState
} from '@/types/calendar';

interface UseCalendarDataReturn {
  // State
  events: CalendarEvent[];
  currentEvent: CalendarEvent | null;
  loading: boolean;
  error: string | null;

  // View state
  activeView: CalendarViewType;
  selectedDate: Date;
  selectedEvent: CalendarEvent | null;
  rightPanelState: RightPanelState;

  // Actions
  fetchEvents: (timeMin?: string, timeMax?: string, maxResults?: number) => Promise<void>;
  fetchEventDetail: (eventId: string) => Promise<void>;
  createEvent: (data: CreateEventRequest) => Promise<boolean>;
  updateEvent: (eventId: string, data: UpdateEventRequest) => Promise<boolean>;
  deleteEvent: (eventId: string) => Promise<boolean>;
  clearError: () => void;
  clearCurrentEvent: () => void;

  // View actions
  setActiveView: (view: CalendarViewType) => void;
  setSelectedDate: (date: Date) => void;
  setSelectedEvent: (event: CalendarEvent | null) => void;
  setRightPanelState: (state: RightPanelState) => void;
  goToToday: () => void;
}

export function useCalendarData(): UseCalendarDataReturn {
  // Data state
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [currentEvent, setCurrentEvent] = useState<CalendarEvent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // View state
  const [activeView, setActiveView] = useState<CalendarViewType>('month'); // Default to month view
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [rightPanelState, setRightPanelState] = useState<RightPanelState>('upcoming');

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

  /**
   * Fetch list of calendar events
   * @param timeMin ISO 8601 datetime (default: now)
   * @param timeMax ISO 8601 datetime (default: 7 days from now)
   * @param maxResults Number of events to fetch (default: 20)
   */
  const fetchEvents = useCallback(async (
    timeMin?: string,
    timeMax?: string,
    maxResults: number = 20
  ) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ max_results: maxResults.toString() });
      if (timeMin) {
        params.append('time_min', timeMin);
      }
      if (timeMax) {
        params.append('time_max', timeMax);
      }

      const response = await authenticatedFetch(`/api/google/calendar/events?${params}`);
      const data: CalendarEventListResponse = await response.json();

      setEvents(data.events);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch events';
      setError(errorMessage);
      console.error('Error fetching calendar events:', err);
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
      const response = await authenticatedFetch(`/api/google/calendar/events/${eventId}`);
      const data: CalendarEvent = await response.json();
      setCurrentEvent(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch event detail';
      setError(errorMessage);
      console.error('Error fetching event detail:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Create a new calendar event
   */
  const createEvent = useCallback(async (data: CreateEventRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/google/calendar/events', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const newEvent: CalendarEvent = await response.json();

      // Add to local state
      setEvents(prev => [...prev, newEvent].sort((a, b) =>
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
  }, [authenticatedFetch]);

  /**
   * Update an existing calendar event
   */
  const updateEvent = useCallback(async (
    eventId: string,
    data: UpdateEventRequest
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/calendar/events/${eventId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      const updatedEvent: CalendarEvent = await response.json();

      // Update in local state
      setEvents(prev => prev.map(event =>
        event.id === eventId ? updatedEvent : event
      ).sort((a, b) =>
        new Date(a.start).getTime() - new Date(b.start).getTime()
      ));

      // Update current event if it was the one being edited
      if (currentEvent?.id === eventId) {
        setCurrentEvent(updatedEvent);
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
   * Delete a calendar event
   */
  const deleteEvent = useCallback(async (eventId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/google/calendar/events/${eventId}`, {
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

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Clear current event detail
   */
  const clearCurrentEvent = useCallback(() => {
    setCurrentEvent(null);
  }, []);

  /**
   * Jump to today's date
   */
  const goToToday = useCallback(() => {
    setSelectedDate(new Date());
    setRightPanelState('upcoming');
  }, []);

  return {
    // Data state
    events,
    currentEvent,
    loading,
    error,

    // View state
    activeView,
    selectedDate,
    selectedEvent,
    rightPanelState,

    // Data actions
    fetchEvents,
    fetchEventDetail,
    createEvent,
    updateEvent,
    deleteEvent,
    clearError,
    clearCurrentEvent,

    // View actions
    setActiveView,
    setSelectedDate,
    setSelectedEvent,
    setRightPanelState,
    goToToday,
  };
}
