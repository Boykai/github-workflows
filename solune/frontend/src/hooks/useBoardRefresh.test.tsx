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

// Mock boardApi so manual refresh (forceRefresh=true) can be tested
const mockGetBoardData = vi.fn().mockResolvedValue({ project: {}, columns: [] });
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
  boardApi: {
    getBoardData: (...args: unknown[]) => mockGetBoardData(...args),
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
    mockGetBoardData.mockReset().mockResolvedValue({ project: {}, columns: [] });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  // ---------- initial state ----------

  it('should return correct initial state when projectId is null', () => {
    const { result } = renderHook(() => useBoardRefresh({ projectId: null }), {
      wrapper: createWrapper(),
    });

    expect(result.current.isRefreshing).toBe(false);
    expect(result.current.lastRefreshedAt).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.rateLimitInfo).toBeNull();
    expect(result.current.isRateLimitLow).toBe(false);
  });

  // ---------- manual refresh ----------

  it('should call boardApi.getBoardData with refresh=true on manual refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.refresh();
    });

    // Manual refresh should bypass server cache
    expect(mockGetBoardData).toHaveBeenCalledWith('PVT_123', true);
    // And write the result directly into the TanStack Query cache
    expect(setQueryDataSpy).toHaveBeenCalledWith(['board', 'data', 'PVT_123'], expect.anything());
  });

  it('should cancel in-progress queries before manual refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const cancelSpy = vi.spyOn(queryClient, 'cancelQueries').mockResolvedValue();

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.refresh();
    });

    // Manual refresh should cancel any in-progress automatic refresh
    expect(cancelSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['board', 'data', 'PVT_123'] })
    );
  });

  it('should update lastRefreshedAt after a successful refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    mockGetBoardData.mockResolvedValue({ project: {}, columns: [] });

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

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
    let resolveGetBoardData: (value: unknown) => void;
    const pendingPromise = new Promise((resolve) => {
      resolveGetBoardData = resolve;
    });
    mockGetBoardData.mockReturnValue(pendingPromise);

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    // Fire multiple rapid refreshes — only the first should execute
    await act(async () => {
      result.current.refresh();
      result.current.refresh();
      result.current.refresh();
    });

    // Only one getBoardData call should be in-flight
    expect(mockGetBoardData).toHaveBeenCalledTimes(1);

    // Resolve the pending call
    await act(async () => {
      resolveGetBoardData!({ project: {}, columns: [] });
    });
  });

  // ---------- auto-refresh timer ----------

  it('should start auto-refresh timer when projectId is set', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    // No auto-refresh yet
    expect(invalidateSpy).not.toHaveBeenCalled();

    // Advance past one AUTO_REFRESH_INTERVAL_MS (1s in test)
    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    // Timer should have fired a refresh via invalidateQueries (not force-refresh)
    expect(invalidateSpy).toHaveBeenCalled();
  });

  it('should use invalidateQueries for auto-refresh (not force-refresh)', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();
    mockGetBoardData.mockClear();

    renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    // Advance past one interval to trigger auto-refresh
    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    // Auto-refresh should NOT call boardApi.getBoardData directly — it uses
    // invalidateQueries to allow TanStack Query to refetch with its default queryFn.
    expect(mockGetBoardData).not.toHaveBeenCalled();
  });

  it('should not start timer when projectId is null', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    renderHook(() => useBoardRefresh({ projectId: null }), { wrapper: createWrapper(queryClient) });

    vi.advanceTimersByTime(5000);
    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  it('should reset timer on manual refresh', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();
    mockGetBoardData.mockResolvedValue({ project: {}, columns: [] });

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

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

    const { rerender } = renderHook(({ projectId }) => useBoardRefresh({ projectId }), {
      wrapper: createWrapper(queryClient),
      initialProps: { projectId: 'PVT_123' as string | null },
    });

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

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

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

    renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

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

    renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

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
      }
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
      { wrapper: createWrapper() }
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
      { wrapper: createWrapper() }
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
      { wrapper: createWrapper(queryClient) }
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

    const { unmount } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    unmount();
    invalidateSpy.mockClear();

    // After unmount, timer should be cleared — no refresh calls
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });

  // ---------- requestBoardReload debouncing (refresh contract Rule 3) ----------

  it('should expose requestBoardReload function', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    expect(result.current.requestBoardReload).toBeTypeOf('function');
  });

  it('requestBoardReload should trigger a board data invalidation', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    invalidateSpy.mockClear();

    await act(async () => {
      result.current.requestBoardReload();
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['board', 'data', 'PVT_123'] })
    );
  });

  it('requestBoardReload should debounce rapid calls within 2s window', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    invalidateSpy.mockClear();

    // First call should execute immediately
    await act(async () => {
      result.current.requestBoardReload();
    });

    const firstCallCount = invalidateSpy.mock.calls.filter(
      (c) => JSON.stringify(c[0]).includes('board')
    ).length;
    expect(firstCallCount).toBe(1);

    // Second call within debounce window should be deferred
    invalidateSpy.mockClear();
    await act(async () => {
      result.current.requestBoardReload();
    });

    // Should not have called immediately
    expect(invalidateSpy).not.toHaveBeenCalled();

    // After debounce window, it should fire
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ['board', 'data', 'PVT_123'] })
    );
  });

  it('manual refresh should cancel pending debounced reload', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();
    vi.spyOn(queryClient, 'cancelQueries').mockResolvedValue();
    vi.spyOn(queryClient, 'setQueryData');

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    // First trigger requestBoardReload
    await act(async () => {
      result.current.requestBoardReload();
    });

    // Then immediately request another (will be debounced)
    await act(async () => {
      result.current.requestBoardReload();
    });

    // Now do a manual refresh — should cancel the debounced reload
    await act(async () => {
      result.current.refresh();
    });

    // The manual refresh should have called getBoardData (force=true)
    expect(mockGetBoardData).toHaveBeenCalledWith('PVT_123', true);
  });

  it('simultaneous auto-refresh + external reload should be deduplicated (FR-010)', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    // Trigger requestBoardReload (simulates a WebSocket refresh event)
    await act(async () => {
      result.current.requestBoardReload();
    });

    // Clear so we can count the next batch of calls
    invalidateSpy.mockClear();

    // Immediately trigger another requestBoardReload (simulates auto-refresh overlap)
    await act(async () => {
      result.current.requestBoardReload();
    });

    // The second request should be deduplicated (within debounce window).
    // At most one pending debounced reload should fire after the window.
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    // Should fire at most once for the deferred debounced reload
    const boardDataInvalidations = invalidateSpy.mock.calls.filter(
      (call) => {
        const qk = call[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      }
    );
    expect(boardDataInvalidations.length).toBeLessThanOrEqual(1);
  });

  it('resetTimer should reset the auto-refresh countdown', async () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

    const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
      wrapper: createWrapper(queryClient),
    });

    // Advance halfway through auto-refresh interval
    await act(async () => {
      vi.advanceTimersByTime(500);
    });

    // Reset timer (simulated external trigger, e.g. WebSocket event)
    await act(async () => {
      result.current.resetTimer();
    });

    invalidateSpy.mockClear();

    // Advance by the original interval minus a bit — should NOT fire yet
    // because the timer was reset
    await act(async () => {
      vi.advanceTimersByTime(900);
    });

    const earlyInvalidations = invalidateSpy.mock.calls.filter(
      (call) => {
        const qk = call[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      }
    );
    expect(earlyInvalidations.length).toBe(0);

    // Advance the remaining time — now it should fire
    await act(async () => {
      vi.advanceTimersByTime(200);
    });

    const laterInvalidations = invalidateSpy.mock.calls.filter(
      (call) => {
        const qk = call[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      }
    );
    expect(laterInvalidations.length).toBe(1);
  });

  // ── T052: Refresh policy contract verification ──────────────────

  describe('refresh policy contract (T052)', () => {
    it('auto-refresh timer pauses on hidden tab and resumes on visible', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
        wrapper: createWrapper(queryClient),
      });

      // Hide tab — timer paused
      Object.defineProperty(document, 'hidden', { value: true, writable: true });
      document.dispatchEvent(new Event('visibilitychange'));
      invalidateSpy.mockClear();

      // No auto-refresh while hidden
      await act(async () => {
        vi.advanceTimersByTime(5000);
      });
      expect(invalidateSpy).not.toHaveBeenCalled();

      // Show tab — should resume and refresh stale data
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
      await act(async () => {
        document.dispatchEvent(new Event('visibilitychange'));
      });
      expect(invalidateSpy).toHaveBeenCalled();

      // Restore
      Object.defineProperty(document, 'hidden', { value: false, writable: true });
    });

    it('manual refresh bypasses cache by calling getBoardData with refresh=true', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
        wrapper: createWrapper(queryClient),
      });

      await act(async () => {
        result.current.refresh();
      });

      // Should call getBoardData with refresh=true (second argument)
      expect(mockGetBoardData).toHaveBeenCalledWith('PVT_123', true);
    });

    it('deduplication: only one refresh within BOARD_RELOAD_DEBOUNCE_MS window', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      const { result } = renderHook(() => useBoardRefresh({ projectId: 'PVT_123' }), {
        wrapper: createWrapper(queryClient),
      });

      invalidateSpy.mockClear();

      // Fire requestBoardReload twice rapidly
      await act(async () => {
        result.current.requestBoardReload();
      });

      const firstCount = invalidateSpy.mock.calls.filter((c) => {
        const qk = c[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      }).length;

      invalidateSpy.mockClear();
      await act(async () => {
        result.current.requestBoardReload();
      });

      // Second call is debounced — no immediate invalidation
      expect(invalidateSpy).not.toHaveBeenCalled();
      expect(firstCount).toBe(1);
    });
  });

  // ---------- WebSocket-aware auto-refresh suppression (T020) ----------

  describe('auto-refresh timer suppression when WebSocket is healthy', () => {
    it('should not start auto-refresh timer when isWebSocketConnected is true', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      renderHook(
        () => useBoardRefresh({ projectId: 'PVT_123', isWebSocketConnected: true }),
        { wrapper: createWrapper(queryClient) },
      );

      // Clear any initial calls
      invalidateSpy.mockClear();

      // Advance past the auto-refresh interval (1000ms in test config)
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });

      // No board data invalidation should have fired — timer is suppressed
      const boardInvalidations = invalidateSpy.mock.calls.filter((c) => {
        const qk = c[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      });
      expect(boardInvalidations).toHaveLength(0);
    });

    it('should resume auto-refresh timer when WebSocket disconnects', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      const { rerender } = renderHook(
        ({ connected }: { connected: boolean }) =>
          useBoardRefresh({ projectId: 'PVT_123', isWebSocketConnected: connected }),
        {
          wrapper: createWrapper(queryClient),
          initialProps: { connected: true },
        },
      );

      // Timer should be suppressed while connected
      invalidateSpy.mockClear();
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });
      const suppressedCalls = invalidateSpy.mock.calls.filter((c) => {
        const qk = c[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      });
      expect(suppressedCalls).toHaveLength(0);

      // Disconnect WebSocket — timer should resume
      rerender({ connected: false });
      invalidateSpy.mockClear();

      await act(async () => {
        vi.advanceTimersByTime(1500);
      });

      const resumedCalls = invalidateSpy.mock.calls.filter((c) => {
        const qk = c[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      });
      expect(resumedCalls.length).toBeGreaterThanOrEqual(1);
    });
  });

  // ── Refresh contract regression tests (T029-T030/FR-009/FR-006) ──────────

  describe('Refresh Contract Regression', () => {
    it('T029: auto-refresh timer does not fire while WebSocket is connected (FR-009)', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      const { result } = renderHook(
        () => useBoardRefresh({ projectId: 'PVT_WS', isWebSocketConnected: true }),
        { wrapper: createWrapper(queryClient) },
      );

      expect(result.current.isRefreshing).toBe(false);

      // Advance past multiple auto-refresh intervals
      invalidateSpy.mockClear();
      await act(async () => {
        vi.advanceTimersByTime(5000); // 5x the 1s test interval
      });

      // No board data invalidation should occur while WS connected
      const boardCalls = invalidateSpy.mock.calls.filter((c) => {
        const qk = c[0]?.queryKey;
        return Array.isArray(qk) && qk[0] === 'board';
      });
      expect(boardCalls).toHaveLength(0);
    });

    it('T030: manual refresh calls backend with refresh=true for cache bypass (FR-006/SC-009)', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      const { result } = renderHook(
        () => useBoardRefresh({ projectId: 'PVT_MANUAL' }),
        { wrapper: createWrapper(queryClient) },
      );

      await act(async () => {
        result.current.refresh();
      });

      // Should call getBoardData with refresh=true
      expect(mockGetBoardData).toHaveBeenCalledWith('PVT_MANUAL', true);
    });

    it('manual refresh cancels pending debounced reload (Rule 3)', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      // Use isWebSocketConnected to suppress the auto-refresh interval timer
      // so it does not confound the debounce-cancellation assertions.
      const { result } = renderHook(
        () => useBoardRefresh({ projectId: 'PVT_DEBOUNCE', isWebSocketConnected: true }),
        { wrapper: createWrapper(queryClient) },
      );

      // Start from a clean slate
      mockGetBoardData.mockClear();
      invalidateSpy.mockClear();

      // 1) First reload request triggers an immediate auto-refresh
      //    (elapsed since lastBoardReloadRef=0 exceeds the debounce window).
      //    doRefresh(false) calls invalidateQueries, not getBoardData.
      //    Flush the async work so lastBoardReloadRef updates.
      await act(async () => {
        result.current.requestBoardReload();
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(invalidateSpy).toHaveBeenCalledTimes(1);

      // 2) Second reload request within the debounce window should be deferred
      //    (a debounce timeout is scheduled, no additional immediate call).
      await act(async () => {
        result.current.requestBoardReload();
      });
      expect(invalidateSpy).toHaveBeenCalledTimes(1);

      // 3) Manual refresh should take priority and cancel the pending debounced reload.
      //    refresh() calls doRefresh(true) which uses getBoardData, not invalidateQueries.
      await act(async () => {
        result.current.refresh();
        await vi.advanceTimersByTimeAsync(0);
      });

      expect(mockGetBoardData).toHaveBeenCalledTimes(1);
      expect(mockGetBoardData).toHaveBeenCalledWith('PVT_DEBOUNCE', true);

      const invalidateCountAfterManual = invalidateSpy.mock.calls.length;

      // 4) Advance timers past the debounce interval; the debounced reload
      //    should NOT fire because manual refresh cancelled it.
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });

      // No additional invalidateQueries calls from the cancelled debounce
      expect(invalidateSpy).toHaveBeenCalledTimes(invalidateCountAfterManual);
    });
  });
});
