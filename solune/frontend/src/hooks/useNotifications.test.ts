import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useNotifications } from './useNotifications';

// Mock useAuth to provide a user with a selected project
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { selected_project_id: 'test-project' },
    isAuthenticated: true,
  }),
}));

// Mock the activityApi to return empty results by default
vi.mock('@/services/api', () => ({
  activityApi: {
    feed: vi.fn().mockResolvedValue({ items: [], has_more: false, next_cursor: null, total_count: 0 }),
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useNotifications', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('returns initial empty notifications', () => {
    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    expect(result.current.notifications).toEqual([]);
    expect(result.current.unreadCount).toBe(0);
  });

  it('returns unreadCount of 0 when no notifications exist', () => {
    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    expect(result.current.unreadCount).toBe(0);
  });

  it('markAllRead updates without error on empty notifications', () => {
    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });

    act(() => {
      result.current.markAllRead();
    });

    expect(result.current.unreadCount).toBe(0);
  });

  it('persists read state to localStorage', () => {
    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });

    act(() => {
      result.current.markAllRead();
    });

    const stored = localStorage.getItem('solune-read-notifications');
    expect(stored).toBeDefined();
    expect(JSON.parse(stored!)).toEqual([]);
  });

  it('initializes from localStorage', () => {
    localStorage.setItem('solune-read-notifications', JSON.stringify(['notif-1', 'notif-2']));

    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    // The hook reads from localStorage for its readIds set
    expect(result.current.notifications).toEqual([]);
  });

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('solune-read-notifications', 'not-valid-json{');

    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    // Should not throw, falls back to empty set
    expect(result.current.unreadCount).toBe(0);
  });

  it('exposes markAllRead as a function', () => {
    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    expect(typeof result.current.markAllRead).toBe('function');
  });
});
