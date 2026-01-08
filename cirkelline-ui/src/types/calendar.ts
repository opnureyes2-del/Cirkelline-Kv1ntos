/**
 * Calendar data types
 * Supports both standalone calendar and Google Calendar integration
 */

/**
 * Calendar view types
 */
export type CalendarViewType = 'agenda' | 'month' | 'week' | 'day';

/**
 * Right panel states
 */
export type RightPanelState = 'upcoming' | 'dayEvents' | 'eventDetail';

/**
 * Calendar source types
 */
export type CalendarSource = 'local' | 'google';

/**
 * Calendar (container for events)
 */
export interface Calendar {
  id: string;
  name: string;
  color: string;
  is_default: boolean;
  is_visible: boolean;
  source: CalendarSource;
  external_id?: string;
  sync_enabled: boolean;
  last_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Calendar event attendee
 */
export interface CalendarAttendee {
  email: string;
  displayName?: string;
  responseStatus?: 'needsAction' | 'accepted' | 'declined' | 'tentative';
}

/**
 * Calendar event data
 */
export interface CalendarEvent {
  id: string;
  calendar_id?: string;
  calendar_name?: string;
  calendar_color?: string;
  summary: string;
  title?: string; // Alias for summary
  description?: string;
  location?: string;
  start: string; // ISO 8601 datetime string
  end: string;   // ISO 8601 datetime string
  start_time?: string; // Alias for start
  end_time?: string;   // Alias for end
  all_day?: boolean;
  recurrence_rule?: string;
  color?: string;
  external_id?: string;
  external_link?: string;
  source?: CalendarSource;
  sync_status?: string;
  attendees?: CalendarAttendee[];
  created?: string;
  updated?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Response from GET /api/google/calendar/events
 */
export interface CalendarEventListResponse {
  events: CalendarEvent[];
}

/**
 * Request body for POST /api/google/calendar/events
 */
export interface CreateEventRequest {
  summary: string;
  description?: string;
  location?: string;
  start: string; // ISO 8601 datetime string
  end: string;   // ISO 8601 datetime string
  attendees?: string[]; // Array of email addresses
}

/**
 * Request body for PUT /api/google/calendar/events/{id}
 */
export interface UpdateEventRequest {
  summary?: string;
  description?: string;
  location?: string;
  start?: string;
  end?: string;
  attendees?: string[];
}

/**
 * Generic API error response
 */
export interface CalendarApiError {
  detail: string;
}

// ═══════════════════════════════════════════════════════════════
// STANDALONE CALENDAR TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Request body for creating a calendar
 */
export interface CreateCalendarRequest {
  name: string;
  color?: string;
  is_default?: boolean;
}

/**
 * Request body for updating a calendar
 */
export interface UpdateCalendarRequest {
  name?: string;
  color?: string;
  is_default?: boolean;
  is_visible?: boolean;
}

/**
 * Request body for creating a standalone event
 */
export interface CreateStandaloneEventRequest {
  calendar_id?: string; // Optional - hook will auto-create default calendar if not provided
  title: string;
  description?: string;
  location?: string;
  start_time: string; // ISO 8601 datetime
  end_time: string;   // ISO 8601 datetime
  all_day?: boolean;
  color?: string;
}

/**
 * Request body for updating a standalone event
 */
export interface UpdateStandaloneEventRequest {
  calendar_id?: string;
  title?: string;
  description?: string;
  location?: string;
  start_time?: string;
  end_time?: string;
  all_day?: boolean;
  color?: string;
}

/**
 * Response from GET /api/calendar/calendars
 */
export interface CalendarListResponse {
  calendars: Calendar[];
  total: number;
}

/**
 * Response from GET /api/calendar/events
 */
export interface StandaloneEventListResponse {
  events: CalendarEvent[];
  total_count: number;
}
