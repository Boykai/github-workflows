/**
 * Modal component for viewing and managing events on a specific date.
 */

import { useState } from 'react';
import type {
  CalendarEvent,
  CalendarEventCreateRequest,
  CalendarEventUpdateRequest,
} from '@/types';
import './EventModal.css';

interface EventModalProps {
  date: string;
  events: CalendarEvent[];
  onClose: () => void;
  onCreateEvent: (event: CalendarEventCreateRequest) => Promise<CalendarEvent>;
  onUpdateEvent: (eventId: string, data: CalendarEventUpdateRequest) => Promise<CalendarEvent>;
  onDeleteEvent: (eventId: string) => Promise<void>;
}

type ViewMode = 'list' | 'create' | 'edit';

export function EventModal({
  date,
  events,
  onClose,
  onCreateEvent,
  onUpdateEvent,
  onDeleteEvent,
}: EventModalProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    startTime: '',
    endTime: '',
  });

  const formatDate = (dateStr: string): string => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleCreateClick = () => {
    setFormData({ title: '', description: '', startTime: '', endTime: '' });
    setViewMode('create');
  };

  const handleEditClick = (event: CalendarEvent) => {
    setEditingEvent(event);
    setFormData({
      title: event.title,
      description: event.description || '',
      startTime: event.startTime || '',
      endTime: event.endTime || '',
    });
    setViewMode('edit');
  };

  const handleCancelForm = () => {
    setViewMode('list');
    setEditingEvent(null);
    setFormData({ title: '', description: '', startTime: '', endTime: '' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      if (viewMode === 'create') {
        await onCreateEvent({
          title: formData.title,
          description: formData.description || undefined,
          date,
          startTime: formData.startTime || undefined,
          endTime: formData.endTime || undefined,
        });
      } else if (viewMode === 'edit' && editingEvent) {
        await onUpdateEvent(editingEvent.id, {
          title: formData.title,
          description: formData.description || undefined,
          startTime: formData.startTime || undefined,
          endTime: formData.endTime || undefined,
        });
      }
      handleCancelForm();
    } catch (error) {
      console.error('Failed to save event:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (eventId: string) => {
    if (!window.confirm('Are you sure you want to delete this event?')) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onDeleteEvent(eventId);
      setViewMode('list');
    } catch (error) {
      console.error('Failed to delete event:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      if (viewMode !== 'list') {
        handleCancelForm();
      } else {
        onClose();
      }
    }
  };

  return (
    <div
      className="event-modal-overlay"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="event-modal-title"
    >
      <div className="event-modal">
        <div className="event-modal-header">
          <h3 id="event-modal-title">{formatDate(date)}</h3>
          <button
            className="modal-close-button"
            onClick={onClose}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>

        <div className="event-modal-content">
          {viewMode === 'list' ? (
            <>
              <div className="events-list">
                {events.length === 0 ? (
                  <p className="no-events">No events scheduled for this day</p>
                ) : (
                  events.map((event) => (
                    <div key={event.id} className="event-item">
                      <div className="event-item-header">
                        <h4 className="event-item-title">{event.title}</h4>
                        {(event.startTime || event.endTime) && (
                          <span className="event-time">
                            {event.startTime}
                            {event.endTime && ` - ${event.endTime}`}
                          </span>
                        )}
                      </div>
                      {event.description && (
                        <p className="event-item-description">{event.description}</p>
                      )}
                      <div className="event-item-actions">
                        <button
                          className="event-edit-button"
                          onClick={() => handleEditClick(event)}
                          disabled={isSubmitting}
                        >
                          Edit
                        </button>
                        <button
                          className="event-delete-button"
                          onClick={() => handleDelete(event.id)}
                          disabled={isSubmitting}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
              <button className="add-event-button" onClick={handleCreateClick}>
                + Add Event
              </button>
            </>
          ) : (
            <form className="event-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="event-title">Title *</label>
                <input
                  id="event-title"
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  autoFocus
                  disabled={isSubmitting}
                />
              </div>

              <div className="form-group">
                <label htmlFor="event-description">Description</label>
                <textarea
                  id="event-description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  rows={3}
                  disabled={isSubmitting}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="event-start-time">Start Time</label>
                  <input
                    id="event-start-time"
                    type="time"
                    value={formData.startTime}
                    onChange={(e) =>
                      setFormData({ ...formData, startTime: e.target.value })
                    }
                    disabled={isSubmitting}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="event-end-time">End Time</label>
                  <input
                    id="event-end-time"
                    type="time"
                    value={formData.endTime}
                    onChange={(e) =>
                      setFormData({ ...formData, endTime: e.target.value })
                    }
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={handleCancelForm}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-button"
                  disabled={isSubmitting || !formData.title.trim()}
                >
                  {isSubmitting ? 'Saving...' : viewMode === 'create' ? 'Create' : 'Update'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
