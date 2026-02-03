/**
 * Hook for managing calendar events state.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eventsApi } from '@/services/api';
import type { CalendarEvent, CalendarEventCreateRequest, CalendarEventUpdateRequest } from '@/types';

export function useEvents(startDate?: string, endDate?: string) {
  const queryClient = useQueryClient();

  // Fetch events
  const { data, isLoading, error } = useQuery({
    queryKey: startDate && endDate ? ['events', startDate, endDate] : ['events'],
    queryFn: () => {
      if (startDate && endDate) {
        return eventsApi.getByDateRange(startDate, endDate);
      }
      return eventsApi.list();
    },
  });

  const events = data?.events || [];

  // Create event mutation
  const createEventMutation = useMutation({
    mutationFn: (eventData: CalendarEventCreateRequest) => eventsApi.create(eventData),
    onSuccess: () => {
      // Invalidate and refetch events
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });

  // Update event mutation
  const updateEventMutation = useMutation({
    mutationFn: ({ eventId, data }: { eventId: string; data: CalendarEventUpdateRequest }) =>
      eventsApi.update(eventId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });

  // Delete event mutation
  const deleteEventMutation = useMutation({
    mutationFn: (eventId: string) => eventsApi.delete(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });

  return {
    events,
    isLoading,
    error,
    createEvent: createEventMutation.mutateAsync,
    updateEvent: (eventId: string, data: CalendarEventUpdateRequest) =>
      updateEventMutation.mutateAsync({ eventId, data }),
    deleteEvent: deleteEventMutation.mutateAsync,
    isCreating: createEventMutation.isPending,
    isUpdating: updateEventMutation.isPending,
    isDeleting: deleteEventMutation.isPending,
  };
}

/**
 * Get events for a specific date.
 */
export function getEventsForDate(events: CalendarEvent[], date: string): CalendarEvent[] {
  return events.filter((event) => event.date === date);
}

/**
 * Check if a date has any events.
 */
export function hasEvents(events: CalendarEvent[], date: string): boolean {
  return events.some((event) => event.date === date);
}
