/**
 * RightPanel - 3-state detail panel for Calendar
 * States:
 * 1. upcoming: Next 7-14 days of events (default)
 * 2. dayEvents: All events for a selected day
 * 3. eventDetail: Full details of a selected event
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CalendarEvent, RightPanelState } from '@/types/calendar';
import { ArrowLeft, Calendar, Clock, MapPin, Users, Trash2, Edit } from 'lucide-react';

interface RightPanelProps {
  state: RightPanelState;
  events: CalendarEvent[];
  selectedDate: Date | null;
  selectedEvent: CalendarEvent | null;
  onBack: () => void;
  onEventClick: (event: CalendarEvent) => void;
  onEditEvent?: (event: CalendarEvent) => void;
  onDeleteEvent?: (event: CalendarEvent) => void;
}

export default function RightPanel({
  state,
  events,
  selectedDate,
  selectedEvent,
  onBack,
  onEventClick,
  onEditEvent,
  onDeleteEvent,
}: RightPanelProps) {
  /**
   * Format date header
   */
  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  /**
   * Format time from ISO string
   */
  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  /**
   * Get upcoming events (next 7-14 days)
   */
  const getUpcomingEvents = (): CalendarEvent[] => {
    const now = new Date();
    const twoWeeksFromNow = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);

    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        return eventDate >= now && eventDate <= twoWeeksFromNow;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
      .slice(0, 10); // Limit to 10 events
  };

  /**
   * Get events for a specific day - use LOCAL time to avoid UTC conversion issues
   */
  const getDayEvents = (): CalendarEvent[] => {
    if (!selectedDate) return [];

    const dateKey = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`;

    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        const eventDateKey = `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, '0')}-${String(eventDate.getDate()).padStart(2, '0')}`;
        return eventDateKey === dateKey;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  };

  /**
   * Render compact event card (for lists)
   */
  const renderEventCard = (event: CalendarEvent) => (
    <motion.div
      key={event.id}
      onClick={() => onEventClick(event)}
      className="group cursor-pointer bg-app-container hover:bg-app-container/80 rounded-lg p-3 border border-light-border dark:border-dark-border transition-all"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <h4 className="text-sm font-medium text-light-text dark:text-dark-text mb-1 group-hover:text-accent transition-colors line-clamp-1">
        {event.summary}
      </h4>
      <div className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary">
        <Clock className="w-3 h-3" />
        <span>{formatTime(event.start)}</span>
        {event.location && (
          <>
            <span>•</span>
            <MapPin className="w-3 h-3" />
            <span className="truncate">{event.location}</span>
          </>
        )}
      </div>
    </motion.div>
  );

  // State 1: Upcoming Events
  if (state === 'upcoming') {
    const upcomingEvents = getUpcomingEvents();

    return (
      <div className="p-6">
        <h2 className="text-sm font-medium text-light-text dark:text-dark-text mb-4">
          Upcoming Events
        </h2>

        {upcomingEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Calendar className="w-10 h-10 text-light-text/30 dark:text-dark-text/30 mb-3" />
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
              No upcoming events
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {upcomingEvents.map((event) => renderEventCard(event))}
          </div>
        )}
      </div>
    );
  }

  // State 2: Day Events
  if (state === 'dayEvents' && selectedDate) {
    const dayEvents = getDayEvents();

    return (
      <div className="p-6">
        {/* Back Button */}
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-xs text-accent hover:underline mb-4"
        >
          <ArrowLeft className="w-3 h-3" />
          Back to upcoming
        </button>

        {/* Date Header */}
        <h2 className="text-sm font-medium text-light-text dark:text-dark-text mb-4">
          {formatDate(selectedDate)}
        </h2>

        {/* Events List */}
        {dayEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Calendar className="w-10 h-10 text-light-text/30 dark:text-dark-text/30 mb-3" />
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
              No events on this day
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {dayEvents.map((event) => renderEventCard(event))}
          </div>
        )}
      </div>
    );
  }

  // State 3: Event Detail
  if (state === 'eventDetail' && selectedEvent) {
    return (
      <div className="p-6">
        {/* Back Button */}
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-xs text-accent hover:underline mb-4"
        >
          <ArrowLeft className="w-3 h-3" />
          Back
        </button>

        {/* Event Title */}
        <h2 className="text-lg font-medium text-light-text dark:text-dark-text mb-6">
          {selectedEvent.summary}
        </h2>

        {/* Event Details */}
        <div className="space-y-4">
          {/* Time */}
          <div className="flex items-start gap-3">
            <Clock className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary mt-0.5" />
            <div className="text-sm">
              <p className="text-light-text dark:text-dark-text">
                {formatTime(selectedEvent.start)} - {formatTime(selectedEvent.end)}
              </p>
              <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                {new Date(selectedEvent.start).toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
            </div>
          </div>

          {/* Location */}
          {selectedEvent.location && (
            <div className="flex items-start gap-3">
              <MapPin className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary mt-0.5" />
              <p className="text-sm text-light-text dark:text-dark-text">
                {selectedEvent.location}
              </p>
            </div>
          )}

          {/* Attendees */}
          {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
            <div className="flex items-start gap-3">
              <Users className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary mt-0.5" />
              <div className="text-sm flex-1">
                <p className="text-light-text dark:text-dark-text mb-2">
                  {selectedEvent.attendees.length} attendees
                </p>
                <div className="space-y-1">
                  {selectedEvent.attendees.map((attendee, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 text-xs text-light-text-secondary dark:text-dark-text-secondary"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-light-text-secondary dark:bg-dark-text-secondary" />
                      <span>{attendee.displayName || attendee.email}</span>
                      {attendee.responseStatus && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-app-container">
                          {attendee.responseStatus}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Description */}
          {selectedEvent.description && (
            <div className="pt-4 border-t border-light-border dark:border-dark-border">
              <p className="text-xs font-medium text-light-text dark:text-dark-text mb-2">
                Description
              </p>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary whitespace-pre-wrap">
                {selectedEvent.description}
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mt-6 pt-6 border-t border-light-border dark:border-dark-border">
          {onEditEvent && (
            <button
              onClick={() => onEditEvent(selectedEvent)}
              className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-accent hover:bg-accent/10 rounded-lg transition-colors"
            >
              <Edit className="w-3.5 h-3.5" />
              Edit
            </button>
          )}
          {onDeleteEvent && (
            <button
              onClick={() => onDeleteEvent(selectedEvent)}
              className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
          )}
        </div>
      </div>
    );
  }

  // Fallback
  return null;
}
