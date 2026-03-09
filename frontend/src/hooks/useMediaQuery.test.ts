/**
 * Unit tests for useMediaQuery and useIsMobile hooks.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMediaQuery, useIsMobile } from './useMediaQuery';
import { BREAKPOINTS } from '@/constants';

describe('useMediaQuery', () => {
  let listeners: Map<string, (e: MediaQueryListEvent) => void>;
  let matchesMap: Map<string, boolean>;

  beforeEach(() => {
    listeners = new Map();
    matchesMap = new Map();

    vi.stubGlobal(
      'matchMedia',
      vi.fn((query: string) => {
        const mql = {
          matches: matchesMap.get(query) ?? false,
          media: query,
          addEventListener: vi.fn((_event: string, handler: (e: MediaQueryListEvent) => void) => {
            listeners.set(query, handler);
          }),
          removeEventListener: vi.fn(
            (_event: string, _handler: (e: MediaQueryListEvent) => void) => {
              listeners.delete(query);
            }
          ),
        };
        return mql;
      })
    );
  });

  it('returns false by default when query does not match', () => {
    const { result } = renderHook(() => useMediaQuery('(max-width: 767px)'));
    expect(result.current).toBe(false);
  });

  it('returns true when query matches', () => {
    matchesMap.set('(max-width: 767px)', true);
    const { result } = renderHook(() => useMediaQuery('(max-width: 767px)'));
    expect(result.current).toBe(true);
  });

  it('updates when media query changes', () => {
    const query = '(max-width: 767px)';
    const { result } = renderHook(() => useMediaQuery(query));
    expect(result.current).toBe(false);

    // Simulate media query change
    const handler = listeners.get(query);
    expect(handler).toBeDefined();
    act(() => {
      handler!({ matches: true } as MediaQueryListEvent);
    });
    expect(result.current).toBe(true);
  });

  it('cleans up listener on unmount', () => {
    const query = '(max-width: 767px)';
    const { unmount } = renderHook(() => useMediaQuery(query));
    expect(listeners.has(query)).toBe(true);
    unmount();
    expect(listeners.has(query)).toBe(false);
  });
});

describe('useIsMobile', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn((query: string) => ({
        matches: query === `(max-width: ${BREAKPOINTS.md - 1}px)`,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }))
    );
  });

  it('uses the md breakpoint from BREAKPOINTS constant', () => {
    const { result } = renderHook(() => useIsMobile());
    // When matchMedia reports the query matches, we are on mobile
    expect(result.current).toBe(true);
    expect(window.matchMedia).toHaveBeenCalledWith(`(max-width: ${BREAKPOINTS.md - 1}px)`);
  });
});
