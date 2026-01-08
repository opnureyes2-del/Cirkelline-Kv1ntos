/**
 * MonthView - Grid calendar view (7×5/6 grid)
 * Shows month with event pills in each day cell
 * Most complex view - handles event positioning and overflow
 */

'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { CalendarEvent } from '@/types/calendar';

interface MonthViewProps {
  events: CalendarEvent[];
  selectedDate: Date;
  onDateClick: (date: Date) => void;
  onEventClick: (event: CalendarEvent) => void;
}

export default function MonthView({
  events,
  selectedDate,
  onDateClick,
  onEventClick,
}: MonthViewProps) {
  /**
   * Get calendar grid for the selected month
   * Returns array of week arrays, each containing 7 day objects
   */
  const calendarGrid = useMemo(() => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();

    // First day of month
    const firstDay = new Date(year, month, 1);
    // Adjust for Monday start (0 = Monday, 6 = Sunday)
    const firstDayOfWeek = (firstDay.getDay() + 6) % 7;

    // Last day of month
    const lastDay = new Date(year, month + 1, 0);
    const lastDate = lastDay.getDate();

    // Build grid
    const weeks: Array<Array<{ date: Date; isCurrentMonth: boolean }>> = [];
    let week: Array<{ date: Date; isCurrentMonth: boolean }> = [];

    // Fill leading days from previous month
    for (let i = 0; i < firstDayOfWeek; i++) {
      const prevMonthDate = new Date(year, month, -(firstDayOfWeek - i - 1));
      week.push({ date: prevMonthDate, isCurrentMonth: false });
    }

    // Fill current month days
    for (let day = 1; day <= lastDate; day++) {
      const date = new Date(year, month, day);
      week.push({ date, isCurrentMonth: true });

      if (week.length === 7) {
        weeks.push(week);
        week = [];
      }
    }

    // Fill trailing days from next month
    if (week.length > 0) {
      const remainingDays = 7 - week.length;
      for (let i = 1; i <= remainingDays; i++) {
        const nextMonthDate = new Date(year, month + 1, i);
        week.push({ date: nextMonthDate, isCurrentMonth: false });
      }
      weeks.push(week);
    }

    return weeks;
  }, [selectedDate]);

  /**
   * Get events for a specific date
   * IMPORTANT: Compare dates in LOCAL time, not UTC!
   */
  const getEventsForDate = (date: Date): CalendarEvent[] => {
    // Use local date components to avoid UTC conversion issues
    const dateKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        // Use local date components for the event too
        const eventDateKey = `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, '0')}-${String(eventDate.getDate()).padStart(2, '0')}`;
        return eventDateKey === dateKey;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  };

  /**
   * Check if date is today
   */
  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  /**
   * Check if date is selected
   */
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

  /**
   * Format time for event pill
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const MAX_EVENTS_SHOWN = 2;

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      {/* Day Headers - Week starts on Monday */}
      <div className="grid grid-cols-[20px_repeat(7,1fr)] md:grid-cols-[24px_repeat(7,1fr)] border-b border-border-primary bg-app-container flex-shrink-0">
        {/* Week number header */}
        <div className="px-0.5 py-0.5 text-center border-r border-border-primary">
          <span className="text-[8px] md:text-[9px] font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase">
            W
          </span>
        </div>
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
          <div
            key={day}
            className="px-1 py-0.5 text-center border-r border-border-primary last:border-r-0 min-w-0"
          >
            <span className="text-[9px] md:text-[10px] font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wide">
              {/* Full names on desktop, single letter on mobile */}
              <span className="hidden sm:inline">{day}</span>
              <span className="sm:hidden">{['M', 'T', 'W', 'T', 'F', 'S', 'S'][index]}</span>
            </span>
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {calendarGrid.map((week, weekIndex) => (
          <div key={weekIndex} className="grid grid-cols-[20px_repeat(7,1fr)] md:grid-cols-[24px_repeat(7,1fr)] border-b border-border-primary last:border-b-0 flex-1 min-h-0">
            {/* Week Number */}
            <div className="flex items-center justify-center border-r border-border-primary bg-app-container">
              <span className="text-[8px] md:text-[9px] font-medium text-accent opacity-50">
                {getWeekNumber(week[0].date)}
              </span>
            </div>
            {week.map(({ date, isCurrentMonth }, dayIndex) => {
              const dayEvents = getEventsForDate(date);
              const hasMoreEvents = dayEvents.length > MAX_EVENTS_SHOWN;
              const visibleEvents = dayEvents.slice(0, MAX_EVENTS_SHOWN);
              const hiddenCount = dayEvents.length - MAX_EVENTS_SHOWN;

              return (
                <motion.div
                  key={`${weekIndex}-${dayIndex}`}
                  onClick={() => onDateClick(date)}
                  className={`relative p-1 sm:p-1.5 cursor-pointer transition-all border-r border-border-primary last:border-r-0 min-w-0 overflow-hidden ${
                    isToday(date)
                      ? ''
                      : isSelected(date)
                        ? 'bg-light-event-bg dark:bg-dark-event-bg'
                        : 'bg-app-container hover:bg-app-container'
                  } ${
                    isSelected(date) && !isToday(date) ? 'ring-2 ring-light-event-bg dark:ring-dark-event-bg ring-inset' : ''
                  }`}
                  style={isToday(date) ? { backgroundColor: 'rgb(var(--accent-rgb))' } : undefined}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: (weekIndex * 7 + dayIndex) * 0.01 }}
                >
                  {/* Date Number & Event Count */}
                  <div className="flex items-center justify-between mb-0.5 md:mb-1">
                    <span className={`text-[9px] md:text-xs font-semibold ${
                        isToday(date)
                          ? 'flex items-center justify-center w-4 h-4 md:w-6 md:h-6 bg-accent text-white rounded-full'
                          : isCurrentMonth
                          ? 'text-light-text dark:text-dark-text'
                          : 'text-light-text-secondary/40 dark:text-dark-text-secondary/40'
                      }`}>
                      {date.getDate()}
                    </span>
                    {dayEvents.length > 0 && (
                      <span className="text-[8px] md:text-[10px] font-medium text-accent bg-accent/10 dark:bg-accent/20 px-1 md:px-1.5 py-0.5 rounded-full">
                        {dayEvents.length}
                      </span>
                    )}
                  </div>

                  {/* Event Pills */}
                  <div className="space-y-0.5">
                    {visibleEvents.map((event) => (
                      <motion.div
                        key={event.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          onEventClick(event);
                        }}
                        className="flex items-center gap-1 px-1 py-0.5 rounded-sm cursor-pointer transition-colors bg-border-primary hover:bg-border-primary/80"
                        whileTap={{ scale: 0.98 }}
                      >
                        <span className="text-[9px] md:text-[9px] font-medium text-light-text dark:text-dark-text truncate">
                          {event.summary}
                        </span>
                      </motion.div>
                    ))}

                    {/* "+N more" indicator */}
                    {hasMoreEvents && (
                      <div className="text-[9px] font-medium text-light-text-secondary dark:text-dark-text-secondary">
                        +{hiddenCount} more
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
