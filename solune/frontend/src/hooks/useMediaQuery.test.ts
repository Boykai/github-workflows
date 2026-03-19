import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useMediaQuery } from './useMediaQuery';

describe('useMediaQuery', () => {
  let listeners: Array<(e: MediaQueryListEvent) => void>;
  let matchesValue: boolean;

  beforeEach(() => {
    listeners = [];
    matchesValue = false;

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: matchesValue,
        media: query,
        addEventListener: (_event: string, handler: (e: MediaQueryListEvent) => void) => {
          listeners.push(handler);
        },
        removeEventListener: (_event: string, handler: (e: MediaQueryListEvent) => void) => {
          listeners = listeners.filter((l) => l !== handler);
        },
      })),
    });
  });

  afterEach(() => {
    listeners = [];
  });

  it('returns false when query does not match', () => {
    matchesValue = false;
    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));
    expect(result.current).toBe(false);
  });

  it('returns true when query matches', () => {
    matchesValue = true;
    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));
    expect(result.current).toBe(true);
  });

  it('updates when media query changes', () => {
    matchesValue = false;
    const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));
    expect(result.current).toBe(false);

    act(() => {
      listeners.forEach((l) => l({ matches: true } as MediaQueryListEvent));
    });
    expect(result.current).toBe(true);
  });

  it('cleans up listener on unmount', () => {
    matchesValue = false;
    const { unmount } = renderHook(() => useMediaQuery('(max-width: 768px)'));
    expect(listeners.length).toBe(1);

    unmount();
    expect(listeners.length).toBe(0);
  });
});
