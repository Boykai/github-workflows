/**
 * Unit tests for useCyclingPlaceholder hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCyclingPlaceholder } from './useCyclingPlaceholder';

describe('useCyclingPlaceholder', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const prompts = ['Prompt A', 'Prompt B', 'Prompt C'];

  it('returns the first prompt initially', () => {
    const { result } = renderHook(() => useCyclingPlaceholder(prompts));
    expect(result.current).toBe('Prompt A');
  });

  it('cycles to the next prompt after the interval', () => {
    const { result } = renderHook(() =>
      useCyclingPlaceholder(prompts, { intervalMs: 3000 }),
    );

    expect(result.current).toBe('Prompt A');

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(result.current).toBe('Prompt B');

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(result.current).toBe('Prompt C');
  });

  it('wraps around to the first prompt after exhausting the list', () => {
    const { result } = renderHook(() =>
      useCyclingPlaceholder(prompts, { intervalMs: 1000 }),
    );

    act(() => {
      vi.advanceTimersByTime(3000);
    });
    expect(result.current).toBe('Prompt A');
  });

  it('does not cycle when enabled is false', () => {
    const { result } = renderHook(() =>
      useCyclingPlaceholder(prompts, { enabled: false, intervalMs: 1000 }),
    );

    expect(result.current).toBe('Prompt A');

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current).toBe('Prompt A');
  });

  it('pauses and resets index when disabled mid-cycle', () => {
    const { result, rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) =>
        useCyclingPlaceholder(prompts, { enabled, intervalMs: 1000 }),
      { initialProps: { enabled: true } },
    );

    // Advance to second prompt
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe('Prompt B');

    // Disable — should reset to first prompt
    rerender({ enabled: false });
    expect(result.current).toBe('Prompt A');

    // Should NOT advance while disabled
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current).toBe('Prompt A');
  });

  it('returns the first prompt when prefers-reduced-motion is active', () => {
    // Mock matchMedia to report prefers-reduced-motion
    const mql = {
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    vi.spyOn(window, 'matchMedia').mockReturnValue(mql as unknown as MediaQueryList);

    const { result } = renderHook(() =>
      useCyclingPlaceholder(prompts, { intervalMs: 1000 }),
    );

    expect(result.current).toBe('Prompt A');

    // Should NOT cycle even after time passes
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current).toBe('Prompt A');

    vi.restoreAllMocks();
  });

  it('falls back to addListener/removeListener when addEventListener is unavailable', () => {
    const addListener = vi.fn();
    const removeListener = vi.fn();
    const mql = {
      matches: false,
      addListener,
      removeListener,
    };
    vi.spyOn(window, 'matchMedia').mockReturnValue(mql as unknown as MediaQueryList);

    const { unmount } = renderHook(() =>
      useCyclingPlaceholder(prompts, { intervalMs: 1000 }),
    );

    expect(addListener).toHaveBeenCalledTimes(1);

    unmount();

    expect(removeListener).toHaveBeenCalledTimes(1);
    vi.restoreAllMocks();
  });

  it('does not cycle when only one prompt is provided', () => {
    const { result } = renderHook(() =>
      useCyclingPlaceholder(['Only one'], { intervalMs: 1000 }),
    );

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current).toBe('Only one');
  });

  it('returns empty string for empty prompts array', () => {
    const { result } = renderHook(() => useCyclingPlaceholder([]));
    expect(result.current).toBe('');
  });

  it('uses default 5000ms interval when not specified', () => {
    const { result } = renderHook(() => useCyclingPlaceholder(prompts));

    expect(result.current).toBe('Prompt A');

    // At 4999ms, should still be first prompt
    act(() => {
      vi.advanceTimersByTime(4999);
    });
    expect(result.current).toBe('Prompt A');

    // At 5000ms, should advance
    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe('Prompt B');
  });
});
