/**
 * DayView - Single day detailed view
 * Shows all events for selected date in chronological order
 * Simpler than Week view - just single column
 */

'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { CalendarEvent } from '@/types/calendar';
import { Clock, MapPin, Users } from 'lucide-react';

interface DayViewProps {
  events: CalendarEvent[];
  selectedDate: Date;
  onEventClick: (event: CalendarEvent) => void;
}

export default function DayView({
  events,
  selectedDate,
  onEventClick,
}: DayViewProps) {
  /**
   * Get events for the selected date - use LOCAL time to avoid UTC conversion issues
   */
  const dayEvents = useMemo(() => {
    const dateKey = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`;

    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        const eventDateKey = `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, '0')}-${String(eventDate.getDate()).padStart(2, '0')}`;
        return eventDateKey === dateKey;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  }, [events, selectedDate]);

  /**
   * Format time
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
   * Get ISO week number (Monday-based, ISO 8601)
   */
  const getWeekNumber = (date: Date): number => {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    const dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  };

  /**
   * Format date header
   */
  const formatDateHeader = (): string => {
    const isToday =
      selectedDate.toDateString() === new Date().toDateString();

    const dateStr = selectedDate.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });

    const weekNum = `Week ${getWeekNumber(selectedDate)}`;
    return isToday ? `Today • ${dateStr} • ${weekNum}` : `${dateStr} • ${weekNum}`;
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Date Header */}
      <div className="border-b border-border-primary px-6 py-4">
        <h2 className="text-lg font-medium text-light-text dark:text-dark-text">
          {formatDateHeader()}
        </h2>
        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
          {dayEvents.length} {dayEvents.length === 1 ? 'event' : 'events'} scheduled
        </p>
      </div>

      {/* Events List */}
      <div className="flex-1 overflow-y-auto p-4">
        {dayEvents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-12 h-12 bg-app-container rounded-full flex items-center justify-center mb-3">
              <Clock className="w-6 h-6 text-light-text/30 dark:text-dark-text/30" />
            </div>
            <h3 className="text-xs font-medium text-light-text dark:text-dark-text mb-1">
              No events today
            </h3>
            <p className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary">
              Your day is clear
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-w-3xl mx-auto">
            {dayEvents.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => onEventClick(event)}
                className="group cursor-pointer bg-app-container hover:bg-accent/5 dark:hover:bg-accent/10 border border-border-primary rounded p-3 border-l-2 border-l-border-primary transition-all"
                whileHover={{ scale: 1.005, x: 2 }}
                whileTap={{ scale: 0.995 }}
              >
                {/* Time */}
                <div className="flex items-center gap-1.5 mb-2">
                  <Clock className="w-3.5 h-3.5 text-accent" />
                  <span className="text-xs font-medium text-accent">
                    {formatTime(event.start)} - {formatTime(event.end)}
                  </span>
                </div>

                {/* Event Title */}
                <h3 className="text-sm font-medium text-light-text dark:text-dark-text mb-2 group-hover:text-accent transition-colors">
                  {event.summary}
                </h3>

                {/* Event Details */}
                <div className="space-y-1.5">
                  {/* Location */}
                  {event.location && (
                    <div className="flex items-center gap-1.5 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      <MapPin className="w-3.5 h-3.5" />
                      <span>{event.location}</span>
                    </div>
                  )}

                  {/* Attendees */}
                  {event.attendees && event.attendees.length > 0 && (
                    <div className="flex items-center gap-1.5 text-xs text-light-text-secondary dark:text-dark-text-secondary">
                      <Users className="w-3.5 h-3.5" />
                      <span>{event.attendees.length} attendees</span>
                    </div>
                  )}

                  {/* Description Preview */}
                  {event.description && (
                    <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary line-clamp-2 mt-2">
                      {event.description}
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
