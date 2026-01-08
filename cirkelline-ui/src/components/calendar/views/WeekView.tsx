/**
 * WeekView - 7-day view with events listed under each day
 */

'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { CalendarEvent } from '@/types/calendar';

interface WeekViewProps {
  events: CalendarEvent[];
  selectedDate: Date;
  onDateClick: (date: Date) => void;
  onEventClick: (event: CalendarEvent) => void;
}

export default function WeekView({
  events,
  selectedDate,
  onDateClick,
  onEventClick,
}: WeekViewProps) {
  const weekDays = useMemo(() => {
    const startOfWeek = new Date(selectedDate);
    // Adjust for Monday start (Monday = 0, Sunday = 6)
    const dayOfWeek = (startOfWeek.getDay() + 6) % 7;
    startOfWeek.setDate(startOfWeek.getDate() - dayOfWeek);

    const days: Date[] = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      days.push(day);
    }
    return days;
  }, [selectedDate]);

  // Compare dates in LOCAL time, not UTC, to avoid off-by-one errors
  const getEventsForDate = (date: Date): CalendarEvent[] => {
    const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        const eventDateKey = `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, '0')}-${String(eventDate.getDate()).padStart(2, '0')}`;
        return eventDateKey === dateKey;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  };

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const isSelected = (date: Date): boolean => {
    return (
      date.getDate() === selectedDate.getDate() &&
      date.getMonth() === selectedDate.getMonth() &&
      date.getFullYear() === selectedDate.getFullYear()
    );
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

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Week Number Header */}
      <div className="flex items-center justify-center py-1 border-b border-border-primary bg-app-container">
        <span className="text-[10px] font-bold text-accent">Week {getWeekNumber(weekDays[0])}</span>
      </div>
      {/* Week Grid */}
      <div className="grid grid-cols-7 flex-1 min-h-0">
        {weekDays.map((day, index) => {
          const dayEvents = getEventsForDate(day);

          return (
            <div
              key={index}
              className="flex flex-col bg-app-container"
            >
              {/* Day Header */}
              <div
                onClick={() => onDateClick(day)}
                className={`p-2 text-center cursor-pointer border-b border-border-primary transition-all ${
                  isToday(day)
                    ? ''
                    : isSelected(day)
                      ? 'bg-light-event-bg dark:bg-dark-event-bg ring-2 ring-light-event-bg dark:ring-dark-event-bg ring-inset'
                      : 'hover:bg-accent/5'
                }`}
                style={isToday(day) ? { backgroundColor: 'rgb(var(--accent-rgb))' } : undefined}
              >
                <div className={`text-[9px] font-semibold uppercase ${isToday(day) ? 'text-white' : 'text-light-text-secondary dark:text-dark-text-secondary'}`}>
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index]}
                </div>
                <div className={`text-sm font-bold ${isToday(day) ? 'text-white' : 'text-light-text dark:text-dark-text'}`}>
                  {day.getDate()}
                </div>
              </div>

              {/* Events List */}
              <div className="flex-1 p-1 overflow-auto">
                {dayEvents.length === 0 ? (
                  <div className="text-[9px] text-light-text-secondary/50 dark:text-dark-text-secondary/50 text-center py-4">
                    No events
                  </div>
                ) : (
                  <div className="space-y-1">
                    {dayEvents.map((event) => (
                      <motion.div
                        key={event.id}
                        onClick={() => onEventClick(event)}
                        className="p-1.5 rounded bg-light-event-bg dark:bg-dark-event-bg cursor-pointer hover:bg-light-event-bg/80 dark:hover:bg-dark-event-bg/80 transition-colors"
                        whileHover={{ x: 2 }}
                      >
                        <div className="flex items-center gap-1">
                          <div className="w-1 h-1 rounded-full bg-accent flex-shrink-0" />
                          <span className="text-[10px] text-light-text dark:text-dark-text font-medium truncate">
                            {event.summary}
                          </span>
                        </div>
                        <div className="text-[9px] text-accent font-medium pl-2">
                          {formatTime(event.start)}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
