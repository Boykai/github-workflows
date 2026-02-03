/**
 * Calendar component for viewing and managing events.
 */

import { useState } from 'react';
import { useEvents, getEventsForDate, hasEvents } from '@/hooks/useEvents';
import { EventModal } from './EventModal';
import './Calendar.css';

export function Calendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Get first and last day of the month to fetch events
  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  const startDate = firstDayOfMonth.toISOString().split('T')[0];
  const endDate = lastDayOfMonth.toISOString().split('T')[0];

  const { events, isLoading, createEvent, updateEvent, deleteEvent } = useEvents(
    startDate,
    endDate
  );

  // Get calendar grid data
  const firstDayOfWeek = firstDayOfMonth.getDay(); // 0 = Sunday
  const daysInMonth = lastDayOfMonth.getDate();

  // Previous month details
  const prevMonth = new Date(year, month, 0);
  const daysInPrevMonth = prevMonth.getDate();

  // Generate calendar days
  const calendarDays: (Date | null)[] = [];

  // Add days from previous month
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    calendarDays.push(new Date(year, month - 1, daysInPrevMonth - i));
  }

  // Add days from current month
  for (let i = 1; i <= daysInMonth; i++) {
    calendarDays.push(new Date(year, month, i));
  }

  // Add days from next month to complete the grid
  const remainingDays = 42 - calendarDays.length; // 6 rows * 7 days
  for (let i = 1; i <= remainingDays; i++) {
    calendarDays.push(new Date(year, month + 1, i));
  }

  const monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleDateClick = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    setSelectedDate(dateStr);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedDate(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent, date: Date) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleDateClick(date);
    }
  };

  const formatDate = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  const isCurrentMonth = (date: Date): boolean => {
    return date.getMonth() === month;
  };

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const selectedDateEvents = selectedDate ? getEventsForDate(events, selectedDate) : [];

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <div className="calendar-title">
          <h2>
            {monthNames[month]} {year}
          </h2>
        </div>
        <div className="calendar-nav">
          <button
            className="nav-button"
            onClick={handlePrevMonth}
            aria-label="Previous month"
          >
            ‹
          </button>
          <button className="today-button" onClick={handleToday}>
            Today
          </button>
          <button
            className="nav-button"
            onClick={handleNextMonth}
            aria-label="Next month"
          >
            ›
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="calendar-loading">
          <div className="spinner" />
          <p>Loading events...</p>
        </div>
      ) : (
        <div className="calendar-grid">
          {/* Day names header */}
          {dayNames.map((day) => (
            <div key={day} className="calendar-day-name">
              {day}
            </div>
          ))}

          {/* Calendar days */}
          {calendarDays.map((date, index) => {
            if (!date) return <div key={index} className="calendar-day empty" />;

            const dateStr = formatDate(date);
            const hasEvent = hasEvents(events, dateStr);
            const dayEvents = getEventsForDate(events, dateStr);

            return (
              <div
                key={index}
                className={`calendar-day ${!isCurrentMonth(date) ? 'other-month' : ''} ${
                  isToday(date) ? 'today' : ''
                } ${hasEvent ? 'has-events' : ''}`}
                onClick={() => handleDateClick(date)}
                onKeyDown={(e) => handleKeyDown(e, date)}
                tabIndex={0}
                role="button"
                aria-label={`${date.getDate()} ${monthNames[date.getMonth()]}, ${dayEvents.length} events`}
              >
                <span className="day-number">{date.getDate()}</span>
                {hasEvent && (
                  <div className="event-indicators">
                    {dayEvents.slice(0, 3).map((event) => (
                      <div
                        key={event.id}
                        className="event-dot"
                        title={event.title}
                      />
                    ))}
                    {dayEvents.length > 3 && (
                      <span className="more-events">+{dayEvents.length - 3}</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {isModalOpen && selectedDate && (
        <EventModal
          date={selectedDate}
          events={selectedDateEvents}
          onClose={handleCloseModal}
          onCreateEvent={createEvent}
          onUpdateEvent={updateEvent}
          onDeleteEvent={deleteEvent}
        />
      )}
    </div>
  );
}
