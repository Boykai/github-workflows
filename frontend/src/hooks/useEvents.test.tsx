/**
 * Unit tests for useEvents hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEvents, getEventsForDate, hasEvents } from './useEvents';
import * as api from '@/services/api';
import type { ReactNode } from 'react';

// Mock the API module
vi.mock('@/services/api', () => ({
  eventsApi: {
    list: vi.fn(),
    getByDate: vi.fn(),
    getByDateRange: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockEventsApi = api.eventsApi as unknown as {
  list: ReturnType<typeof vi.fn>;
  getByDate: ReturnType<typeof vi.fn>;
  getByDateRange: ReturnType<typeof vi.fn>;
  create: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

// Create wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('useEvents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return empty events initially when loading', () => {
    mockEventsApi.list.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    expect(result.current.events).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it('should fetch all events when no date range is provided', async () => {
    const mockEvents = {
      events: [
        {
          id: 'EVENT_1',
          title: 'Event 1',
          date: '2026-02-10',
          created_at: '2026-02-01T00:00:00Z',
          updated_at: '2026-02-01T00:00:00Z',
        },
        {
          id: 'EVENT_2',
          title: 'Event 2',
          date: '2026-02-15',
          created_at: '2026-02-01T00:00:00Z',
          updated_at: '2026-02-01T00:00:00Z',
        },
      ],
    };

    mockEventsApi.list.mockResolvedValue(mockEvents);

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.events).toHaveLength(2);
    expect(result.current.events[0].id).toBe('EVENT_1');
    expect(mockEventsApi.list).toHaveBeenCalled();
  });

  it('should fetch events by date range when provided', async () => {
    const mockEvents = {
      events: [
        {
          id: 'EVENT_1',
          title: 'Event 1',
          date: '2026-02-10',
          created_at: '2026-02-01T00:00:00Z',
          updated_at: '2026-02-01T00:00:00Z',
        },
      ],
    };

    mockEventsApi.getByDateRange.mockResolvedValue(mockEvents);

    const { result } = renderHook(() => useEvents('2026-02-01', '2026-02-28'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1);
    });

    expect(result.current.events[0].id).toBe('EVENT_1');
    expect(mockEventsApi.getByDateRange).toHaveBeenCalledWith('2026-02-01', '2026-02-28');
  });

  it('should create a new event', async () => {
    const mockEvents = { events: [] };
    const newEvent = {
      id: 'EVENT_NEW',
      title: 'New Event',
      date: '2026-02-15',
      created_at: '2026-02-03T00:00:00Z',
      updated_at: '2026-02-03T00:00:00Z',
    };

    mockEventsApi.list.mockResolvedValue(mockEvents);
    mockEventsApi.create.mockResolvedValue(newEvent);

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.createEvent({
        title: 'New Event',
        date: '2026-02-15',
      });
    });

    expect(mockEventsApi.create).toHaveBeenCalledWith({
      title: 'New Event',
      date: '2026-02-15',
    });
  });

  it('should update an existing event', async () => {
    const mockEvents = { events: [] };
    const updatedEvent = {
      id: 'EVENT_1',
      title: 'Updated Event',
      date: '2026-02-15',
      created_at: '2026-02-01T00:00:00Z',
      updated_at: '2026-02-03T00:00:00Z',
    };

    mockEventsApi.list.mockResolvedValue(mockEvents);
    mockEventsApi.update.mockResolvedValue(updatedEvent);

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.updateEvent('EVENT_1', { title: 'Updated Event' });
    });

    expect(mockEventsApi.update).toHaveBeenCalledWith('EVENT_1', { title: 'Updated Event' });
  });

  it('should delete an event', async () => {
    const mockEvents = { events: [] };

    mockEventsApi.list.mockResolvedValue(mockEvents);
    mockEventsApi.delete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useEvents(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.deleteEvent('EVENT_1');
    });

    expect(mockEventsApi.delete).toHaveBeenCalledWith('EVENT_1');
  });
});

describe('getEventsForDate', () => {
  it('should return events for a specific date', () => {
    const events = [
      {
        id: 'EVENT_1',
        title: 'Event 1',
        date: '2026-02-10',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-02-01T00:00:00Z',
      },
      {
        id: 'EVENT_2',
        title: 'Event 2',
        date: '2026-02-15',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-02-01T00:00:00Z',
      },
      {
        id: 'EVENT_3',
        title: 'Event 3',
        date: '2026-02-10',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-02-01T00:00:00Z',
      },
    ];

    const result = getEventsForDate(events, '2026-02-10');

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('EVENT_1');
    expect(result[1].id).toBe('EVENT_3');
  });

  it('should return empty array when no events match the date', () => {
    const events = [
      {
        id: 'EVENT_1',
        title: 'Event 1',
        date: '2026-02-10',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-02-01T00:00:00Z',
      },
    ];

    const result = getEventsForDate(events, '2026-02-15');

    expect(result).toHaveLength(0);
  });
});

describe('hasEvents', () => {
  it('should return true when date has events', () => {
    const events = [
      {
        id: 'EVENT_1',
        title: 'Event 1',
        date: '2026-02-10',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-02-01T00:00:00Z',
      },
    ];

    const result = hasEvents(events, '2026-02-10');

    expect(result).toBe(true);
  });

  it('should return false when date has no events', () => {
    const events = [
      {
        id: 'EVENT_1',
        title: 'Event 1',
        date: '2026-02-10',
        created_at: '2026-02-01T00:00:00Z',
        updated_at: '2026-02-01T00:00:00Z',
      },
    ];

    const result = hasEvents(events, '2026-02-15');

    expect(result).toBe(false);
  });
});
