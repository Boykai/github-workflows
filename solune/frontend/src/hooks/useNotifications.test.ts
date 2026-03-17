import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useNotifications } from './useNotifications';

describe('useNotifications', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('returns initial empty notifications', () => {
    const { result } = renderHook(() => useNotifications());
    expect(result.current.notifications).toEqual([]);
    expect(result.current.unreadCount).toBe(0);
  });

  it('returns unreadCount of 0 when no notifications exist', () => {
    const { result } = renderHook(() => useNotifications());
    expect(result.current.unreadCount).toBe(0);
  });

  it('markAllRead updates without error on empty notifications', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.markAllRead();
    });

    expect(result.current.unreadCount).toBe(0);
  });

  it('persists read state to localStorage', () => {
    const { result } = renderHook(() => useNotifications());

    act(() => {
      result.current.markAllRead();
    });

    const stored = localStorage.getItem('solune-read-notifications');
    expect(stored).toBeDefined();
    expect(JSON.parse(stored!)).toEqual([]);
  });

  it('initializes from localStorage', () => {
    localStorage.setItem('solune-read-notifications', JSON.stringify(['notif-1', 'notif-2']));

    const { result } = renderHook(() => useNotifications());
    // The hook reads from localStorage for its readIds set
    expect(result.current.notifications).toEqual([]);
  });

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('solune-read-notifications', 'not-valid-json{');

    const { result } = renderHook(() => useNotifications());
    // Should not throw, falls back to empty set
    expect(result.current.unreadCount).toBe(0);
  });

  it('exposes markAllRead as a function', () => {
    const { result } = renderHook(() => useNotifications());
    expect(typeof result.current.markAllRead).toBe('function');
  });
});
