import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSidebarState } from './useSidebarState';

describe('useSidebarState', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('defaults to not collapsed', () => {
    const { result } = renderHook(() => useSidebarState());
    expect(result.current.isCollapsed).toBe(false);
  });

  it('initializes from localStorage when true', () => {
    localStorage.setItem('sidebar-collapsed', 'true');

    const { result } = renderHook(() => useSidebarState());
    expect(result.current.isCollapsed).toBe(true);
  });

  it('initializes from localStorage when false', () => {
    localStorage.setItem('sidebar-collapsed', 'false');

    const { result } = renderHook(() => useSidebarState());
    expect(result.current.isCollapsed).toBe(false);
  });

  it('toggle changes state from false to true', () => {
    const { result } = renderHook(() => useSidebarState());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isCollapsed).toBe(true);
  });

  it('toggle changes state from true to false', () => {
    localStorage.setItem('sidebar-collapsed', 'true');

    const { result } = renderHook(() => useSidebarState());

    act(() => {
      result.current.toggle();
    });

    expect(result.current.isCollapsed).toBe(false);
  });

  it('persists toggle to localStorage', () => {
    const { result } = renderHook(() => useSidebarState());

    act(() => {
      result.current.toggle();
    });

    expect(localStorage.getItem('sidebar-collapsed')).toBe('true');
  });

  it('handles multiple toggles', () => {
    const { result } = renderHook(() => useSidebarState());

    act(() => {
      result.current.toggle();
    });
    expect(result.current.isCollapsed).toBe(true);

    act(() => {
      result.current.toggle();
    });
    expect(result.current.isCollapsed).toBe(false);
    expect(localStorage.getItem('sidebar-collapsed')).toBe('false');
  });

  it('handles localStorage errors gracefully', () => {
    const originalGetItem = Storage.prototype.getItem;
    Storage.prototype.getItem = () => {
      throw new Error('SecurityError');
    };

    const { result } = renderHook(() => useSidebarState());
    expect(result.current.isCollapsed).toBe(false);

    Storage.prototype.getItem = originalGetItem;
  });
});
