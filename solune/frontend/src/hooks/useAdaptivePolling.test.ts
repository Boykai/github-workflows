import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  useAdaptivePolling,
  type AdaptivePollingConfig,
} from './useAdaptivePolling';

// ── Helpers ──

function renderPolling(config?: AdaptivePollingConfig) {
  return renderHook(() => useAdaptivePolling(config));
}

describe('useAdaptivePolling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(document, 'addEventListener');
    vi.spyOn(document, 'removeEventListener');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ── Initial State ──

  it('returns default state on initialization', () => {
    const { result } = renderPolling();

    expect(result.current.state).toEqual({
      currentInterval: 10_000,
      tier: 'medium',
      activityScore: 0,
      isPaused: false,
    });
  });

  it('accepts custom configuration', () => {
    const { result } = renderPolling({ baseInterval: 5_000 });

    expect(result.current.state.currentInterval).toBe(5_000);
    expect(result.current.state.tier).toBe('medium');
  });

  // ── getRefetchInterval ──

  it('returns the current interval from getRefetchInterval when not paused', () => {
    const { result } = renderPolling();

    const interval = result.current.getRefetchInterval();
    expect(interval).toBe(10_000);
  });

  it('returns false from getRefetchInterval when paused', () => {
    const { result } = renderPolling();

    // Simulate tab hidden
    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'hidden',
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(result.current.getRefetchInterval()).toBe(false);
  });

  // ── Activity Tiers ──

  it('transitions to high tier when activity score exceeds threshold', () => {
    const { result } = renderPolling({ windowSize: 5, highActivityThreshold: 0.6 });

    // Report 4 out of 5 polls with changes (score = 0.8 > 0.6)
    act(() => {
      result.current.reportPollResult(true);
      result.current.reportPollResult(true);
      result.current.reportPollResult(true);
      result.current.reportPollResult(true);
      result.current.reportPollResult(false);
    });

    expect(result.current.state.tier).toBe('high');
    expect(result.current.state.activityScore).toBe(0.8);
    expect(result.current.state.currentInterval).toBe(3_000); // minInterval default
  });

  it('transitions to medium tier for moderate activity', () => {
    const { result } = renderPolling({
      windowSize: 5,
      highActivityThreshold: 0.6,
      mediumActivityThreshold: 0.2,
    });

    // Report 2 out of 5 polls with changes (score = 0.4)
    act(() => {
      result.current.reportPollResult(true);
      result.current.reportPollResult(true);
      result.current.reportPollResult(false);
      result.current.reportPollResult(false);
      result.current.reportPollResult(false);
    });

    expect(result.current.state.tier).toBe('medium');
    expect(result.current.state.activityScore).toBe(0.4);
    expect(result.current.state.currentInterval).toBe(10_000); // baseInterval default
  });

  it('transitions to low tier when activity drops below medium threshold', () => {
    const { result } = renderPolling({
      windowSize: 5,
      mediumActivityThreshold: 0.2,
    });

    // Report 0 out of 5 polls with changes (score = 0)
    act(() => {
      result.current.reportPollResult(false);
      result.current.reportPollResult(false);
      result.current.reportPollResult(false);
      result.current.reportPollResult(false);
      result.current.reportPollResult(false);
    });

    expect(result.current.state.tier).toBe('low');
    expect(result.current.state.activityScore).toBe(0);
    expect(result.current.state.currentInterval).toBe(30_000); // maxInterval default
  });

  // ── Sliding Window ──

  it('maintains a sliding window of configured size', () => {
    const { result } = renderPolling({ windowSize: 3, highActivityThreshold: 0.6 });

    // Fill window: [true, true, true] → score = 1.0
    act(() => {
      result.current.reportPollResult(true);
      result.current.reportPollResult(true);
      result.current.reportPollResult(true);
    });
    expect(result.current.state.activityScore).toBe(1.0);

    // Push more: [true, true, false] → score = 0.666...
    act(() => {
      result.current.reportPollResult(false);
    });
    expect(result.current.state.activityScore).toBeCloseTo(0.667, 2);
    expect(result.current.state.tier).toBe('high');

    // Push more: [true, false, false] → score = 0.333...
    act(() => {
      result.current.reportPollResult(false);
    });
    expect(result.current.state.activityScore).toBeCloseTo(0.333, 2);
    expect(result.current.state.tier).toBe('medium');
  });

  // ── Backoff ──

  it('transitions to backoff tier on poll failure', () => {
    const { result } = renderPolling();

    act(() => {
      result.current.reportPollFailure();
    });

    expect(result.current.state.tier).toBe('backoff');
    // backoff: baseInterval * 2^1 = 10_000 * 2 = 20_000
    expect(result.current.state.currentInterval).toBe(20_000);
  });

  it('increases backoff interval on consecutive failures', () => {
    const { result } = renderPolling();

    act(() => {
      result.current.reportPollFailure(); // 10_000 * 2^1 = 20_000
    });
    expect(result.current.state.currentInterval).toBe(20_000);

    act(() => {
      result.current.reportPollFailure(); // 10_000 * 2^2 = 40_000
    });
    expect(result.current.state.currentInterval).toBe(40_000);

    act(() => {
      result.current.reportPollFailure(); // 10_000 * 2^3 = 80_000 → capped at 60_000
    });
    expect(result.current.state.currentInterval).toBe(60_000);
  });

  it('caps backoff at maxBackoffInterval', () => {
    const { result } = renderPolling({ maxBackoffInterval: 30_000 });

    act(() => {
      result.current.reportPollFailure();
      result.current.reportPollFailure();
      result.current.reportPollFailure();
      result.current.reportPollFailure();
    });

    expect(result.current.state.currentInterval).toBeLessThanOrEqual(30_000);
  });

  it('resets backoff on reportPollSuccess', () => {
    const { result } = renderPolling();

    // Enter backoff
    act(() => {
      result.current.reportPollFailure();
      result.current.reportPollFailure();
    });
    expect(result.current.state.tier).toBe('backoff');

    // Recover
    act(() => {
      result.current.reportPollSuccess();
    });

    expect(result.current.state.tier).not.toBe('backoff');
    // Should return to a normal tier based on activity score
    expect(result.current.state.tier).toBe('low'); // no activity yet
  });

  it('reportPollSuccess is a no-op when not in backoff', () => {
    const { result } = renderPolling();

    const stateBefore = { ...result.current.state };

    act(() => {
      result.current.reportPollSuccess();
    });

    expect(result.current.state).toEqual(stateBefore);
  });

  // ── Tab Visibility ──

  it('registers visibilitychange listener on mount', () => {
    renderPolling();

    expect(document.addEventListener).toHaveBeenCalledWith(
      'visibilitychange',
      expect.any(Function),
    );
  });

  it('pauses polling when tab becomes hidden', () => {
    const { result } = renderPolling();

    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'hidden',
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(result.current.state.isPaused).toBe(true);
    expect(result.current.getRefetchInterval()).toBe(false);
  });

  it('resumes polling and triggers immediate poll when tab becomes visible', () => {
    const { result } = renderPolling();

    // Hide tab
    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'hidden',
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(result.current.state.isPaused).toBe(true);

    // Show tab
    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'visible',
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(result.current.state.isPaused).toBe(false);
    // First call after tab regain should return near-immediate interval
    expect(result.current.getRefetchInterval()).toBe(100);
    // Subsequent call returns normal interval
    expect(result.current.getRefetchInterval()).toBe(10_000);
  });

  it('cleans up visibilitychange listener on unmount', () => {
    const { unmount } = renderPolling();

    unmount();

    expect(document.removeEventListener).toHaveBeenCalledWith(
      'visibilitychange',
      expect.any(Function),
    );
  });

  // ── Trigger Immediate Poll ──

  it('triggerImmediatePoll causes next getRefetchInterval to return 100', () => {
    const { result } = renderPolling();

    act(() => {
      result.current.triggerImmediatePoll();
    });

    expect(result.current.getRefetchInterval()).toBe(100);
    // Second call returns normal interval
    expect(result.current.getRefetchInterval()).not.toBe(100);
  });

  it('triggerImmediatePoll resets paused state', () => {
    const { result } = renderPolling();

    // Pause
    act(() => {
      Object.defineProperty(document, 'visibilityState', {
        value: 'hidden',
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(result.current.state.isPaused).toBe(true);

    // Trigger immediate
    act(() => {
      result.current.triggerImmediatePoll();
    });

    expect(result.current.state.isPaused).toBe(false);
  });

  it('triggerImmediatePoll clears backoff failures', () => {
    const { result } = renderPolling();

    act(() => {
      result.current.reportPollFailure();
    });
    expect(result.current.state.tier).toBe('backoff');

    act(() => {
      result.current.triggerImmediatePoll();
    });

    // After immediate trigger, tier is computed from activity score with 0 failures
    expect(result.current.state.tier).not.toBe('backoff');
  });

  // ── Edge: empty activity window ──

  it('handles empty activity window with score of 0', () => {
    const { result } = renderPolling();

    // No reportPollResult calls → empty window → score 0
    expect(result.current.state.activityScore).toBe(0);
    expect(result.current.state.tier).toBe('medium'); // initial default
  });
});
