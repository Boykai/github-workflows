/**
 * Unit tests for useBoardRefresh hook.
 *
 * Covers: manual refresh deduplication, auto-refresh timer start/reset,
 * Page Visibility API pause/resume, rate limit state tracking, and
 * lastRefreshedAt initialization from TanStack Query cache.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBoardRefresh } from './useBoardRefresh';
import type { ReactNode } from 'react';

// Mock constants so intervals are short and predictable in tests
vi.mock('@/constants', () => ({
  AUTO_REFRESH_INTERVAL_MS: 1000, // 1 second for fast tests
  RATE_LIMIT_LOW_THRESHOLD: 10,
}));

// Mock ApiError for parseRefreshError tests
vi.mock('@/services/api', () => ({
  ApiError: class ApiError extends Error {
    status: number;
    error: Record<string, unknown>;
    constructor(status: number, error: Record<string, unknown>) {
      super(String(error.error || 'API Error'));
      this.name = 'ApiError';
      this.status = status;
      this.error = error;
    }
  },
}));

function createWrapper(queryClient?: QueryClient) {
  const qc =
    queryClient ??
    new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe('useBoardRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  // ---------- initial state ----------

  it('should return correct initial state when projectId is null', () => {
    const { result } = renderHook(
      () => useBoardRefresh({ projectId: null }),
      { wrapper: createWrapper() },
    );

    expect(result.current.isRefreshing).toBe(false);
    expect(result.current.lastRefreshedAt).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.rateLimitInfo).toBeNull();
    expect(result.current.isRateLimitLow).toBe(false);
  });

  // ---------- manual refresh ----------

  it('should trigger invalidateQueries on manual refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    await act(async () => {
      result.current.refresh();
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['board', 'data', 'PVT_123'] }),
    );
  });

  it('should update lastRefreshedAt after a successful refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    expect(result.current.lastRefreshedAt).toBeNull();

    await act(async () => {
      result.current.refresh();
    });

    expect(result.current.lastRefreshedAt).toBeInstanceOf(Date);
  });

  it('should deduplicate concurrent refresh calls', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    let resolveInvalidate: () => void;
    const invalidatePromise = new Promise<void>((resolve) => {
      resolveInvalidate = resolve;
    });
    const invalidateSpy = vi
      .spyOn(queryClient, 'invalidateQueries')
      .mockReturnValue(invalidatePromise);

    const { result } = renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    // Fire multiple rapid refreshes — only the first should execute
    act(() => {
      result.current.refresh();
      result.current.refresh();
      result.current.refresh();
    });

    // Only one invalidateQueries call should be in-flight
    expect(invalidateSpy).toHaveBeenCalledTimes(1);

    // Resolve the pending invalidation
    await act(async () => {
      resolveInvalidate!();
    });
  });

  // ---------- auto-refresh timer ----------

  it('should start auto-refresh timer when projectId is set', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    // No auto-refresh yet
    expect(invalidateSpy).not.toHaveBeenCalled();

    // Advance past one AUTO_REFRESH_INTERVAL_MS (1s in test)
    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    // Timer should have fired a refresh
    expect(invalidateSpy).toHaveBeenCalled();
  });

  it('should not start timer when projectId is null', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(
      () => useBoardRefresh({ projectId: null }),
      { wrapper: createWrapper(queryClient) },
    );

    vi.advanceTimersByTime(5000);
    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  it('should reset timer on manual refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    // Advance 800ms (close to the 1s interval but not past it)
    await act(async () => {
      vi.advanceTimersByTime(800);
    });

    // Manual refresh — this resets the timer
    await act(async () => {
      result.current.refresh();
    });

    invalidateSpy.mockClear();

    // Advance another 800ms — old timer would have fired by now but we reset
    await act(async () => {
      vi.advanceTimersByTime(800);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();

    // Advance to full interval from the reset point
    await act(async () => {
      vi.advanceTimersByTime(300);
    });

    expect(invalidateSpy).toHaveBeenCalled();
  });

  it('should clear timer when projectId becomes null', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { rerender } = renderHook(
      ({ projectId }) => useBoardRefresh({ projectId }),
      {
        wrapper: createWrapper(queryClient),
        initialProps: { projectId: 'PVT_123' as string | null },
      },
    );

    // Remove projectId
    rerender({ projectId: null });
    invalidateSpy.mockClear();

    // Timer should be cleared — no refresh even after a long wait
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  // ---------- resetTimer (external callers like WS events) ----------

  it('should expose resetTimer for external callers', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    // Advance 800ms, then reset timer externally
    await act(async () => {
      vi.advanceTimersByTime(800);
    });

    act(() => {
      result.current.resetTimer();
    });

    invalidateSpy.mockClear();

    // Old timer would have fired at 1000ms, but resetTimer restarted it
    await act(async () => {
      vi.advanceTimersByTime(800);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  // ---------- Page Visibility API ----------

  it('should pause timer when tab is hidden', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    // Simulate tab becoming hidden
    Object.defineProperty(document, 'hidden', { value: true, writable: true });
    document.dispatchEvent(new Event('visibilitychange'));

    invalidateSpy.mockClear();

    // Timer should be paused — no refresh even after the interval
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();

    // Restore
    Object.defineProperty(document, 'hidden', { value: false, writable: true });
  });

  it('should resume timer and refresh stale data when tab becomes visible', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    // Simulate tab hidden
    Object.defineProperty(document, 'hidden', { value: true, writable: true });
    document.dispatchEvent(new Event('visibilitychange'));

    invalidateSpy.mockClear();

    // Wait longer than the auto-refresh interval while hidden
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    // Simulate tab visible — data is stale, should trigger immediate refresh
    Object.defineProperty(document, 'hidden', { value: false, writable: true });
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
    });

    expect(invalidateSpy).toHaveBeenCalled();
  });

  // ---------- rate limit info ----------

  it('should update rateLimitInfo from boardData', () => {
    const rateLimitData = { limit: 5000, remaining: 4990, reset_at: 1700000000, used: 10 };

    const { result, rerender } = renderHook(
      ({ boardData }) => useBoardRefresh({ projectId: 'PVT_123', boardData }),
      {
        wrapper: createWrapper(),
        initialProps: { boardData: undefined as { rate_limit?: typeof rateLimitData } | undefined },
      },
    );

    expect(result.current.rateLimitInfo).toBeNull();

    // Provide board data with rate_limit
    rerender({ boardData: { rate_limit: rateLimitData } as unknown as undefined });

    expect(result.current.rateLimitInfo).toEqual(rateLimitData);
  });

  it('should mark isRateLimitLow when remaining < threshold', () => {
    const lowRateLimit = { limit: 5000, remaining: 5, reset_at: 1700000000, used: 4995 };

    const { result } = renderHook(
      () =>
        useBoardRefresh({
          projectId: 'PVT_123',
          boardData: { rate_limit: lowRateLimit } as never,
        }),
      { wrapper: createWrapper() },
    );

    expect(result.current.isRateLimitLow).toBe(true);
  });

  it('should not mark isRateLimitLow when remaining >= threshold', () => {
    const healthyRateLimit = { limit: 5000, remaining: 4000, reset_at: 1700000000, used: 1000 };

    const { result } = renderHook(
      () =>
        useBoardRefresh({
          projectId: 'PVT_123',
          boardData: { rate_limit: healthyRateLimit } as never,
        }),
      { wrapper: createWrapper() },
    );

    expect(result.current.isRateLimitLow).toBe(false);
  });

  // ---------- lastRefreshedAt seeding from query cache ----------

  it('should seed lastRefreshedAt from TanStack Query cache on first boardData', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    // Pre-populate query state to simulate a prior successful fetch
    const seedTime = Date.now() - 30_000;
    queryClient.setQueryData(['board', 'data', 'PVT_123'], { project: {}, columns: [] });
    // Manually set the dataUpdatedAt to a known value
    const state = queryClient.getQueryState(['board', 'data', 'PVT_123']);
    if (state) {
      (state as { dataUpdatedAt: number }).dataUpdatedAt = seedTime;
    }

    const { result } = renderHook(
      () =>
        useBoardRefresh({
          projectId: 'PVT_123',
          boardData: { project: {}, columns: [] } as never,
        }),
      { wrapper: createWrapper(queryClient) },
    );

    // lastRefreshedAt should have been initialized from the query cache
    expect(result.current.lastRefreshedAt).toBeInstanceOf(Date);
    expect(result.current.lastRefreshedAt!.getTime()).toBe(seedTime);
  });

  // ---------- cleanup on unmount ----------

  it('should clean up timers on unmount', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { unmount } = renderHook(
      () => useBoardRefresh({ projectId: 'PVT_123' }),
      { wrapper: createWrapper(queryClient) },
    );

    unmount();
    invalidateSpy.mockClear();

    // After unmount, timer should be cleared — no refresh calls
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
