/**
 * CalendarView - Main Calendar Container
 * Simple, responsive layout that fills its container
 * Desktop: Calendar + Upcoming side by side
 * Mobile: Calendar stacked above Upcoming
 */

'use client';

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MonthView from './views/MonthView';
import WeekView from './views/WeekView';
import DayView from './views/DayView';
import { CalendarViewType, CalendarEvent, Calendar as CalendarType, CreateCalendarRequest, CreateStandaloneEventRequest, UpdateStandaloneEventRequest } from '@/types/calendar';
import { Calendar, Clock, Plus, X, MapPin, ChevronDown, ChevronUp } from 'lucide-react';

interface CalendarViewProps {
  activeView: CalendarViewType;
  events: CalendarEvent[];
  loading: boolean;
  error: string | null;
  selectedDate: Date;
  selectedEvent: CalendarEvent | null;
  clearError: () => void;
  setSelectedDate: (date: Date) => void;
  setSelectedEvent: (event: CalendarEvent | null) => void;
  // Layout mode - when 'side-by-side', use stacked internal layout
  layoutMode?: 'stacked' | 'side-by-side';
  // Mobile panel switcher (controlled from TopBar)
  mobilePanel?: 'calendar' | 'events';
  // Standalone calendar props
  calendars?: CalendarType[];
  selectedCalendarIds?: string[];
  onToggleCalendar?: (id: string) => void;
  onCreateCalendar?: (data: CreateCalendarRequest) => Promise<CalendarType | null>;
  onDeleteCalendar?: (id: string) => Promise<boolean>;
  onUpdateCalendar?: (id: string, data: { name?: string; color?: string }) => Promise<boolean>;
  onCreateEvent?: (data: CreateStandaloneEventRequest) => Promise<boolean>;
  onUpdateEvent?: (eventId: string, data: UpdateStandaloneEventRequest) => Promise<boolean>;
  onDeleteEvent?: (eventId: string) => Promise<boolean>;
  getDefaultCalendar?: () => CalendarType | undefined;
}

export default function CalendarView({
  activeView,
  events,
  loading,
  error,
  selectedDate,
  selectedEvent,
  clearError,
  setSelectedDate,
  setSelectedEvent,
  layoutMode = 'stacked',
  mobilePanel = 'calendar',
  calendars = [],
  onCreateEvent,
  onUpdateEvent,
  onDeleteEvent,
  getDefaultCalendar,
}: CalendarViewProps) {
  // Event modal state (used for both create and edit)
  const [showEventModal, setShowEventModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null); // null = create mode, event = edit mode
  const [isUpcomingExpanded, setIsUpcomingExpanded] = useState(false);
  const [eventDate, setEventDate] = useState<Date | null>(null);
  const [eventTitle, setEventTitle] = useState('');
  const [eventDescription, setEventDescription] = useState('');
  const [eventLocation, setEventLocation] = useState('');
  const [eventStartTime, setEventStartTime] = useState('09:00');
  const [eventEndTime, setEventEndTime] = useState('10:00');
  const [eventAllDay, setEventAllDay] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Get upcoming events (next 7 days)
  const upcomingEvents = useMemo(() => {
    const now = new Date();
    const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        return eventDate >= now && eventDate <= weekFromNow;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
      .slice(0, 10);
  }, [events]);

  // Get events for selected date - use LOCAL time to avoid UTC conversion issues
  const selectedDateEvents = useMemo(() => {
    const dateKey = `${selectedDate.getFullYear()}-${String(selectedDate.getMonth() + 1).padStart(2, '0')}-${String(selectedDate.getDate()).padStart(2, '0')}`;
    return events
      .filter((event) => {
        const eventDate = new Date(event.start);
        const eventDateKey = `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, '0')}-${String(eventDate.getDate()).padStart(2, '0')}`;
        return eventDateKey === dateKey;
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  }, [events, selectedDate]);

  // Format time
  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  // Format date for display
  const formatEventDate = (isoString: string): string => {
    const date = new Date(isoString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';

    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  // Handle date click - just select the date, don't open modal
  const handleDateClick = (date: Date) => {
    setSelectedDate(date);
  };

  // Handle create event button click
  const handleCreateEventClick = () => {
    if (onCreateEvent) {
      setEditingEvent(null); // Create mode
      setEventDate(selectedDate);
      setEventTitle('');
      setEventDescription('');
      setEventLocation('');
      setEventStartTime('09:00');
      setEventEndTime('10:00');
      setEventAllDay(false);
      setShowEventModal(true);
    }
  };

  // Handle edit event click
  const handleEditEventClick = (event: CalendarEvent) => {
    setEditingEvent(event);
    setEventDate(new Date(event.start));
    setEventTitle(event.summary || event.title || '');
    setEventDescription(event.description || '');
    setEventLocation(event.location || '');

    // Parse time from event
    const startDate = new Date(event.start);
    const endDate = new Date(event.end);
    setEventStartTime(`${startDate.getHours().toString().padStart(2, '0')}:${startDate.getMinutes().toString().padStart(2, '0')}`);
    setEventEndTime(`${endDate.getHours().toString().padStart(2, '0')}:${endDate.getMinutes().toString().padStart(2, '0')}`);
    setEventAllDay(event.all_day || false);
    setShowEventModal(true);
  };

  // Handle save event (create or update)
  const handleSaveEvent = async () => {
    if (!eventDate || !eventTitle.trim()) return;

    setIsSaving(true);

    const startDateTime = new Date(eventDate);
    const endDateTime = new Date(eventDate);

    if (!eventAllDay) {
      const [startHour, startMin] = eventStartTime.split(':').map(Number);
      const [endHour, endMin] = eventEndTime.split(':').map(Number);
      startDateTime.setHours(startHour, startMin, 0, 0);
      endDateTime.setHours(endHour, endMin, 0, 0);
    } else {
      startDateTime.setHours(0, 0, 0, 0);
      endDateTime.setHours(23, 59, 59, 999);
    }

    let success = false;

    if (editingEvent && onUpdateEvent) {
      // Update existing event
      success = await onUpdateEvent(editingEvent.id, {
        title: eventTitle.trim(),
        description: eventDescription.trim() || undefined,
        location: eventLocation.trim() || undefined,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        all_day: eventAllDay,
      });
    } else if (onCreateEvent) {
      // Create new event
      const defaultCalendar = getDefaultCalendar?.() || calendars[0];
      success = await onCreateEvent({
        calendar_id: defaultCalendar?.id,
        title: eventTitle.trim(),
        description: eventDescription.trim() || undefined,
        location: eventLocation.trim() || undefined,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        all_day: eventAllDay,
      });
    }

    if (success) {
      setShowEventModal(false);
      setEditingEvent(null);
      setSelectedEvent(null);
    }

    setIsSaving(false);
  };

  // Handle delete event
  const handleDeleteEvent = async () => {
    if (!editingEvent || !onDeleteEvent) return;

    setIsDeleting(true);
    const success = await onDeleteEvent(editingEvent.id);

    if (success) {
      setShowEventModal(false);
      setShowDeleteConfirm(false);
      setEditingEvent(null);
      setSelectedEvent(null);
    }

    setIsDeleting(false);
  };

  const closeModal = () => {
    setShowEventModal(false);
    setEditingEvent(null);
    setShowDeleteConfirm(false);
  };

  const isToday = selectedDate.toDateString() === new Date().toDateString();

  return (
    <div className="flex flex-col h-full overflow-hidden" style={{ backgroundColor: 'var(--app-container-bg)' }}>
      {/* Error Banner */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 sm:px-6 py-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800"
          >
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <p className="text-xs text-red-800 dark:text-red-200">{error}</p>
              <button onClick={clearError} className="text-red-600 dark:text-red-400 hover:text-red-800">
                <X size={14} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content - Responsive layout */}
      {/* Mobile: shows one panel at a time based on tab */}
      {/* Desktop: side by side */}
      <div className={`flex flex-1 min-h-0 overflow-hidden w-full ${layoutMode === 'side-by-side' ? 'flex-col' : 'flex-col lg:flex-row'}`}>
        {/* Calendar Grid - visible on desktop always, on mobile only when calendar panel active */}
        {/* In side-by-side mode: 40% height for calendar, 60% for events */}
        <div
          className={`${mobilePanel === 'calendar' ? 'flex' : 'hidden'} lg:flex min-h-0 overflow-hidden p-0 flex-col ${layoutMode === 'side-by-side' ? 'flex-shrink-0' : 'flex-1'}`}
          style={layoutMode === 'side-by-side' ? { height: '40%' } : undefined}
        >
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent"></div>
            </div>
          ) : (
            <>
              {activeView === 'month' && (
                <MonthView
                  events={events}
                  selectedDate={selectedDate}
                  onDateClick={handleDateClick}
                  onEventClick={handleEditEventClick}
                />
              )}
              {activeView === 'week' && (
                <WeekView
                  events={events}
                  selectedDate={selectedDate}
                  onDateClick={handleDateClick}
                  onEventClick={handleEditEventClick}
                />
              )}
              {activeView === 'day' && (
                <DayView
                  events={events}
                  selectedDate={selectedDate}
                  onEventClick={handleEditEventClick}
                />
              )}
            </>
          )}
        </div>

        {/* Right Panel: Selected Day or Upcoming Events */}
        {/* Mobile: shown when events panel active */}
        {/* Desktop: always visible on the right */}
        {/* In side-by-side mode: 60% height for events panel */}
        <div
          className={`
            ${mobilePanel === 'events' ? 'flex' : 'hidden'} lg:flex
            ${layoutMode === 'side-by-side' ? 'w-full border-t' : 'w-full lg:w-72 xl:w-80 lg:border-l'}
            border-border-primary bg-app-container flex-col flex-shrink-0
            ${layoutMode === 'side-by-side' ? '' : 'flex-1 lg:flex-initial'}
          `}
          style={layoutMode === 'side-by-side' ? { height: '60%' } : undefined}
        >
          <div className="flex-1 overflow-auto app-scroll px-3 py-1.5">
            {/* Header with Create Event button */}
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-light-text dark:text-dark-text">
                {isToday ? 'Today' : selectedDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
              </h3>
              {/* Create Event Button - styled like header elements */}
              {onCreateEvent && (
                <button
                  onClick={handleCreateEventClick}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-light-text dark:text-dark-text rounded-lg bg-[#E4E4E2] dark:bg-[#2A2A2A] hover:bg-[#D4D4D2] dark:hover:bg-[#3A3A3A] transition-colors"
                >
                  <Plus size={14} className="text-accent" />
                  <span>Create</span>
                </button>
              )}
            </div>

            {/* Selected Date Events */}
            {selectedDateEvents.length > 0 ? (
              <div className="space-y-1.5 mb-3">
                {selectedDateEvents.map((event) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={() => handleEditEventClick(event)}
                    className={`p-2 rounded-md transition-all cursor-pointer ${
                      selectedEvent?.id === event.id
                        ? 'bg-accent/10 ring-1 ring-accent'
                        : 'bg-app-container hover:bg-accent/5'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-1">
                      <Clock size={12} className="text-accent" />
                      <span className="text-[11px] font-medium text-accent">
                        {formatTime(event.start)}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-light-text dark:text-dark-text line-clamp-1">
                      {event.summary}
                    </p>
                    {event.location && (
                      <p className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary mt-1 flex items-center gap-1">
                        <MapPin size={10} /> {event.location}
                      </p>
                    )}
                    {event.description && (
                      <p className="text-[10px] text-light-text-secondary dark:text-dark-text-secondary mt-1 line-clamp-2">
                        {event.description}
                      </p>
                    )}
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 mb-3">
                <Calendar size={20} className="mx-auto text-light-text/20 dark:text-dark-text/20 mb-1.5" />
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                  No events
                </p>
              </div>
            )}

          </div>

          {/* Upcoming Events - GLUED TO BOTTOM */}
          {upcomingEvents.length > 0 && (
            <div className="border-t border-border-primary px-3 py-2 bg-app-container">
              {/* Header with chevron */}
              <button
                onClick={() => setIsUpcomingExpanded(!isUpcomingExpanded)}
                className="w-full flex items-center justify-between mb-2"
              >
                <h4 className="text-xs font-semibold text-light-text-secondary dark:text-dark-text-secondary">
                  UPCOMING
                </h4>
                {isUpcomingExpanded ? (
                  <ChevronDown className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                ) : (
                  <ChevronUp className="w-4 h-4 text-light-text-secondary dark:text-dark-text-secondary" />
                )}
              </button>

              {/* First event always visible */}
              <div
                onClick={() => {
                  setSelectedDate(new Date(upcomingEvents[0].start));
                  setSelectedEvent(upcomingEvents[0]);
                }}
                className="p-2 rounded hover:bg-app-container cursor-pointer transition-colors"
              >
                <p className="text-[10px] text-accent font-medium">
                  {formatEventDate(upcomingEvents[0].start)} · {formatTime(upcomingEvents[0].start)}
                </p>
                <p className="text-xs text-light-text dark:text-dark-text line-clamp-1">
                  {upcomingEvents[0].summary}
                </p>
              </div>

              {/* Expandable section for more events */}
              <AnimatePresence>
                {isUpcomingExpanded && upcomingEvents.length > 1 && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="space-y-1.5 mt-1.5">
                      {upcomingEvents.slice(1).map((event) => (
                        <div
                          key={event.id}
                          onClick={() => {
                            setSelectedDate(new Date(event.start));
                            setSelectedEvent(event);
                          }}
                          className="p-2 rounded hover:bg-app-container cursor-pointer transition-colors"
                        >
                          <p className="text-[10px] text-accent font-medium">
                            {formatEventDate(event.start)} · {formatTime(event.start)}
                          </p>
                          <p className="text-xs text-light-text dark:text-dark-text line-clamp-1">
                            {event.summary}
                          </p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* Event Create/Edit Modal */}
      <AnimatePresence>
        {showEventModal && eventDate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4"
            onClick={closeModal}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-app-container rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
            >
              {/* Modal Header */}
              <div className="px-4 py-3 border-b border-border-primary flex items-center justify-between">
                <h3 className="text-sm font-semibold text-light-text dark:text-dark-text">
                  {editingEvent ? 'Edit Event' : 'New Event'} - {eventDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </h3>
                <button
                  onClick={closeModal}
                  className="p-1 hover:bg-app-container rounded transition-colors"
                >
                  <X size={16} className="text-light-text-secondary" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-4 space-y-4">
                {/* Title */}
                <div>
                  <input
                    type="text"
                    value={eventTitle}
                    onChange={(e) => setEventTitle(e.target.value)}
                    placeholder="Event title"
                    className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                    autoFocus
                  />
                </div>

                {/* All Day Toggle */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={eventAllDay}
                    onChange={(e) => setEventAllDay(e.target.checked)}
                    className="w-4 h-4 rounded border-border-primary text-accent focus:ring-accent"
                  />
                  <span className="text-sm text-light-text dark:text-dark-text">All day</span>
                </label>

                {/* Time Selection */}
                {!eventAllDay && (
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="block text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">Start</label>
                      <input
                        type="time"
                        value={eventStartTime}
                        onChange={(e) => setEventStartTime(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-xs text-light-text-secondary dark:text-dark-text-secondary mb-1">End</label>
                      <input
                        type="time"
                        value={eventEndTime}
                        onChange={(e) => setEventEndTime(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                      />
                    </div>
                  </div>
                )}

                {/* Location */}
                <div>
                  <input
                    type="text"
                    value={eventLocation}
                    onChange={(e) => setEventLocation(e.target.value)}
                    placeholder="Location (optional)"
                    className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text"
                  />
                </div>

                {/* Description */}
                <div>
                  <textarea
                    value={eventDescription}
                    onChange={(e) => setEventDescription(e.target.value)}
                    placeholder="Description (optional)"
                    rows={3}
                    className="w-full px-3 py-2 text-sm bg-app-container border border-border-primary rounded-lg focus:outline-none focus:border-accent text-light-text dark:text-dark-text resize-none"
                  />
                </div>
              </div>

              {/* Modal Footer */}
              <div className="px-4 py-3 border-t border-border-primary flex justify-between">
                {/* Delete button (only in edit mode) */}
                <div>
                  {editingEvent && onDeleteEvent && (
                    <button
                      onClick={() => setShowDeleteConfirm(true)}
                      className="px-3 py-2 text-sm text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                      Delete
                    </button>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={closeModal}
                    className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEvent}
                    disabled={!eventTitle.trim() || isSaving}
                    className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSaving ? 'Saving...' : (editingEvent ? 'Save Changes' : 'Create Event')}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteConfirm && editingEvent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-[70] p-4"
            onClick={() => setShowDeleteConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-app-container rounded-xl shadow-2xl w-full max-w-sm overflow-hidden"
            >
              <div className="p-4">
                <h3 className="text-sm font-semibold text-light-text dark:text-dark-text mb-2">
                  Delete Event
                </h3>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-4">
                  Are you sure you want to delete &quot;{editingEvent.summary || editingEvent.title}&quot;? This action cannot be undone.
                </p>
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setShowDeleteConfirm(false)}
                    className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text dark:hover:text-dark-text transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteEvent}
                    disabled={isDeleting}
                    className="px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50"
                  >
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
