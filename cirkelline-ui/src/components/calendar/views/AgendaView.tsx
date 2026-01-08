/**
 * AgendaView - Enhanced chronological list of events
 * Groups events by date with smart date headers (Today, Tomorrow, etc.)
 * Default view for Calendar
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { CalendarEvent } from '@/types/calendar';
import { Calendar, Clock, MapPin, Users } from 'lucide-react';

interface AgendaViewProps {
  events: CalendarEvent[];
  onEventClick: (event: CalendarEvent) => void;
  selectedEvent?: CalendarEvent | null;
}

export default function AgendaView({
  events,
  onEventClick,
  selectedEvent,
}: AgendaViewProps) {
  /**
   * Helper to get local date key (YYYY-MM-DD) without UTC conversion
   */
  const getLocalDateKey = (date: Date): string => {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };

  /**
   * Group events by date - use LOCAL time to avoid UTC conversion issues
   */
  const groupEventsByDate = (events: CalendarEvent[]) => {
    const grouped: Record<string, CalendarEvent[]> = {};

    events.forEach((event) => {
      const eventDate = new Date(event.start);
      const dateKey = getLocalDateKey(eventDate); // YYYY-MM-DD in local time

      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(event);
    });

    // Sort dates
    const sortedDates = Object.keys(grouped).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime()
    );

    return sortedDates.map((date) => ({
      date,
      events: grouped[date].sort(
        (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime()
      ),
    }));
  };

  /**
   * Format date header with smart labels (Today, Tomorrow, etc.)
   * Use LOCAL time comparison to avoid UTC conversion issues
   */
  const formatDateHeader = (dateString: string): string => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const isToday = getLocalDateKey(date) === getLocalDateKey(today);
    const isTomorrow = getLocalDateKey(date) === getLocalDateKey(tomorrow);

    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
    const monthDay = date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });

    if (isToday) {
      return `Today • ${dayName} ${monthDay}`;
    } else if (isTomorrow) {
      return `Tomorrow • ${dayName} ${monthDay}`;
    } else {
      return `${dayName} ${monthDay}`;
    }
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

  const groupedEvents = groupEventsByDate(events);

  // Empty state
  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Calendar className="w-12 h-12 text-light-text/30 dark:text-dark-text/30 mb-4" />
        <h3 className="text-sm font-medium text-light-text dark:text-dark-text mb-1">
          No events scheduled
        </h3>
        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
          Your calendar is clear for the upcoming period
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2 md:space-y-3">
      {groupedEvents.map(({ date, events: dateEvents }, groupIndex) => (
        <motion.div
          key={date}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: groupIndex * 0.05 }}
        >
          {/* Date Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <h3 className="text-xs font-semibold text-light-text dark:text-dark-text">
              {formatDateHeader(date)}
            </h3>
            <div className="flex-1 h-px bg-border-primary" />
          </div>

          {/* Events for this date */}
          <div className="space-y-0.5 md:space-y-1">
            {dateEvents.map((event, eventIndex) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: groupIndex * 0.05 + eventIndex * 0.03 }}
                onClick={() => onEventClick(event)}
                className={`group cursor-pointer rounded border-l-2 transition-all ${
                  selectedEvent?.id === event.id
                    ? 'bg-accent/10 dark:bg-accent/20 border-light-event-bg dark:border-dark-event-bg ring-1 ring-border-primary'
                    : 'bg-app-container hover:bg-accent/5 dark:hover:bg-accent/10 border-light-event-bg dark:border-dark-event-bg'
                }`}
                whileHover={{ scale: 1.005, x: 2 }}
                whileTap={{ scale: 0.995 }}
              >
                <div className="px-3 py-2">
                  {/* Event Title */}
                  <h4 className="text-xs font-medium text-light-text dark:text-dark-text mb-1 group-hover:text-accent transition-colors">
                    {event.summary}
                  </h4>

                  {/* Event Details */}
                  <div className="flex flex-wrap items-center gap-3 text-[10px] text-light-text-secondary dark:text-dark-text-secondary">
                    {/* Time */}
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>
                        {formatTime(event.start)} - {formatTime(event.end)}
                      </span>
                    </div>

                    {/* Location */}
                    {event.location && (
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        <span className="truncate max-w-[150px]">
                          {event.location}
                        </span>
                      </div>
                    )}

                    {/* Attendees */}
                    {event.attendees && event.attendees.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        <span>{event.attendees.length}</span>
                      </div>
                    )}
                  </div>

                  {/* Description Preview */}
                  {event.description && (
                    <p className="mt-1.5 text-[10px] text-light-text-secondary dark:text-dark-text-secondary line-clamp-1">
                      {event.description}
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
