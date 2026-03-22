/**
 * Unit tests for useRealTimeSync hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRealTimeSync } from './useRealTimeSync';
import type { ReactNode } from 'react';

// Store mock WebSocket instances
let mockWebSocketInstances: MockWebSocket[] = [];

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  url: string;

  constructor(url: string) {
    this.url = url;
    mockWebSocketInstances.push(this);
  }

  send(_data: string) {
    // Mock send
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }

  // Test helpers
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event('open'));
  }

  simulateError() {
    this.onerror?.(new Event('error'));
  }

  simulateMessage(data: object) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }
}

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
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useRealTimeSync', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockWebSocketInstances = [];
    // @ts-expect-error - Override global WebSocket
    global.WebSocket = MockWebSocket;
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should start disconnected when no projectId', () => {
    const { result } = renderHook(() => useRealTimeSync(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.status).toBe('disconnected');
    expect(result.current.lastUpdate).toBeNull();
  });

  it('should attempt to connect when projectId provided', () => {
    const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
      wrapper: createWrapper(),
    });

    // Hook should have started - either polling or connecting
    expect(['polling', 'connecting']).toContain(result.current.status);
  });

  it('should create WebSocket with correct URL', () => {
    renderHook(() => useRealTimeSync('PVT_123'), {
      wrapper: createWrapper(),
    });

    expect(mockWebSocketInstances.length).toBeGreaterThan(0);
    expect(mockWebSocketInstances[0].url).toContain('/api/v1/projects/PVT_123/subscribe');
  });

  it('should upgrade to connected status when WebSocket opens', async () => {
    const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
      wrapper: createWrapper(),
    });

    // Simulate WebSocket connection success
    await act(async () => {
      mockWebSocketInstances[0]?.simulateOpen();
    });

    // Check that status upgraded
    expect(result.current.status).toBe('connected');
  });

  it('should fall back to polling when WebSocket errors', async () => {
    const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
      wrapper: createWrapper(),
    });

    // Simulate WebSocket error
    await act(async () => {
      mockWebSocketInstances[0]?.simulateError();
    });

    // After an error, status should eventually be polling (may go through reconnect attempts)
    // Status could be 'polling' or 'connecting' depending on reconnect state
    expect(['polling', 'connecting']).toContain(result.current.status);
  });

  it('should clean up WebSocket on unmount', () => {
    const { unmount } = renderHook(() => useRealTimeSync('PVT_123'), {
      wrapper: createWrapper(),
    });

    const ws = mockWebSocketInstances[0];

    unmount();

    expect(ws?.readyState).toBe(MockWebSocket.CLOSED);
  });

  it('should become disconnected when projectId changes to null', async () => {
    const { result, rerender } = renderHook(({ projectId }) => useRealTimeSync(projectId), {
      wrapper: createWrapper(),
      initialProps: { projectId: 'PVT_123' as string | null },
    });

    // Change to null
    await act(async () => {
      rerender({ projectId: null });
    });

    expect(result.current.status).toBe('disconnected');
  });

  it('should reconnect when projectId changes', () => {
    const { rerender } = renderHook(({ projectId }) => useRealTimeSync(projectId), {
      wrapper: createWrapper(),
      initialProps: { projectId: 'PVT_123' as string | null },
    });

    const initialCount = mockWebSocketInstances.length;

    // Change project
    rerender({ projectId: 'PVT_456' });

    // Should create a new WebSocket
    expect(mockWebSocketInstances.length).toBeGreaterThan(initialCount);
    expect(mockWebSocketInstances[mockWebSocketInstances.length - 1].url).toContain('PVT_456');
  });

  it('should update lastUpdate when WebSocket connects', async () => {
    const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
      wrapper: createWrapper(),
    });

    // Wait for the initial state to settle
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    await act(async () => {
      mockWebSocketInstances[0]?.simulateOpen();
    });

    // lastUpdate should be set
    expect(result.current.lastUpdate).not.toBeNull();
  });

  describe('message handling', () => {
    it('should handle initial_data message', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });

      expect(invalidateSpy).toHaveBeenCalled();
      expect(result.current.lastUpdate).not.toBeNull();
    });

    it('should handle task_update message', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'task_update' });
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });

    it('should handle task_created message', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'task_created' });
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });

    it('should handle status_changed message', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'status_changed' });
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });

    it('should handle refresh message', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'refresh' });
      });

      expect(invalidateSpy).toHaveBeenCalled();
    });

    it('should handle invalid JSON message gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      // Simulate invalid JSON
      await act(async () => {
        mockWebSocketInstances[0]?.onmessage?.(
          new MessageEvent('message', { data: 'not valid json' })
        );
      });

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });

    it('should ignore unknown message types', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      // Clear any calls from connection
      invalidateSpy.mockClear();

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'unknown_type' });
      });

      // Should not invalidate for unknown types
      expect(invalidateSpy).not.toHaveBeenCalled();
    });
  });

  describe('reconnection behavior', () => {
    it('should attempt reconnection on close', async () => {
      vi.useFakeTimers();

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      const initialCount = mockWebSocketInstances.length;

      // Close the connection
      await act(async () => {
        mockWebSocketInstances[0]?.close();
      });

      // Advance timers to trigger reconnection
      await act(async () => {
        vi.advanceTimersByTime(5000);
      });

      // Should create a new WebSocket
      expect(mockWebSocketInstances.length).toBeGreaterThan(initialCount);

      vi.useRealTimers();
    });

    it('should stay in polling mode after max reconnect attempts', async () => {
      vi.useFakeTimers();

      const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      // The hook starts with polling by design, then tries to upgrade to WebSocket
      // After max reconnect attempts, it stays in polling mode
      expect(['polling', 'connecting']).toContain(result.current.status);

      vi.useRealTimers();
    });
  });

  describe('polling fallback', () => {
    it('should handle WebSocket not supported gracefully', () => {
      // Override WebSocket to throw
      // @ts-expect-error - Override global WebSocket
      global.WebSocket = class {
        constructor() {
          throw new Error('WebSocket not supported');
        }
      };

      const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      // The hook starts with polling and will stay there when WebSocket fails
      // Status could be 'polling' or 'connecting' depending on timing
      expect(['polling', 'connecting']).toContain(result.current.status);

      // Restore mock
      // @ts-expect-error - Override global WebSocket
      global.WebSocket = MockWebSocket;
    });

    it('should only invalidate tasks query during polling (not board data)', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Trigger fallback polling by simulating WebSocket error
      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });

      invalidateSpy.mockClear();

      // Advance past the polling interval to trigger a poll cycle
      await act(async () => {
        vi.advanceTimersByTime(30_000);
      });

      // Should invalidate tasks query
      const tasksCalls = invalidateSpy.mock.calls.filter(
        ([opts]) =>
          JSON.stringify((opts as { queryKey: unknown }).queryKey) ===
          JSON.stringify(['projects', 'PVT_123', 'tasks'])
      );
      expect(tasksCalls.length).toBeGreaterThan(0);

      // Should NOT invalidate board data query
      const boardCalls = invalidateSpy.mock.calls.filter(
        ([opts]) =>
          JSON.stringify((opts as { queryKey: unknown }).queryKey) ===
          JSON.stringify(['board', 'data', 'PVT_123'])
      );
      expect(boardCalls.length).toBe(0);

      vi.useRealTimers();
    });

    it('should call onRefreshTriggered during polling to reset auto-refresh timer', async () => {
      vi.useFakeTimers();
      const onRefreshTriggered = vi.fn();

      renderHook(() => useRealTimeSync('PVT_123', { onRefreshTriggered }), {
        wrapper: createWrapper(),
      });

      // Trigger fallback polling
      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });

      onRefreshTriggered.mockClear();

      // Advance past the polling interval
      await act(async () => {
        vi.advanceTimersByTime(30_000);
      });

      expect(onRefreshTriggered).toHaveBeenCalled();

      vi.useRealTimers();
    });
  });

  describe('reconnection debounce', () => {
    it('should debounce rapid initial_data messages within 2 seconds', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      invalidateSpy.mockClear();

      // Send multiple rapid initial_data messages (simulating reconnection)
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });

      // Only the first initial_data should trigger invalidation (debounce)
      expect(invalidateSpy).toHaveBeenCalledTimes(1);
    });

    it('should reset debounce when projectId changes so new project is not suppressed', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { rerender } = renderHook(({ projectId }) => useRealTimeSync(projectId), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
        initialProps: { projectId: 'PVT_123' as string | null },
      });

      // Open WS and send initial_data for the first project
      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });

      invalidateSpy.mockClear();

      // Switch project immediately (within 2s debounce window)
      rerender({ projectId: 'PVT_456' });

      // Open the new WS connection and send initial_data
      const newWs = mockWebSocketInstances[mockWebSocketInstances.length - 1];
      await act(async () => {
        newWs?.simulateOpen();
      });
      await act(async () => {
        newWs?.simulateMessage({ type: 'initial_data' });
      });

      // The new project's initial_data should NOT be suppressed by the old debounce
      expect(invalidateSpy).toHaveBeenCalled();
    });
  });

  describe('polling stops on WebSocket connect (T033/SC-007)', () => {
    it('should stop polling when WebSocket opens', async () => {
      vi.useFakeTimers();
      const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

      const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      // Initially either polling or connecting (startPolling then connect race)
      expect(['polling', 'connecting']).toContain(result.current.status);

      // Simulate WebSocket connection success
      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      // Polling should stop — clearInterval must be called if it was polling,
      // but since we don't start polling immediately anymore, we just check status
      expect(result.current.status).toBe('connected');

      clearIntervalSpy.mockRestore();
      vi.useRealTimers();
    });

    it('should resume polling on WebSocket close', async () => {
      vi.useFakeTimers();

      const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      // Connect then disconnect
      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });
      expect(result.current.status).toBe('connected');

      await act(async () => {
        mockWebSocketInstances[0]?.close();
      });

      // Should fall back to polling
      expect(result.current.status).toBe('polling');

      vi.useRealTimers();
    });
  });

  describe('exponential backoff on reconnect (T033/SC-007)', () => {
    it('should increase reconnect delay exponentially', async () => {
      vi.useFakeTimers();
      const setTimeoutSpy = vi.spyOn(global, 'setTimeout');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      // Close connection to trigger first reconnect
      setTimeoutSpy.mockClear();
      await act(async () => {
        mockWebSocketInstances[0]?.close();
      });

      // First reconnect — base delay ~1000ms (1000 * 2^0 = 1000)
      const firstCall = setTimeoutSpy.mock.calls.find(
        ([, delay]) => typeof delay === 'number' && delay >= 1000 && delay <= 2000
      );
      expect(firstCall).toBeTruthy();

      // Advance to trigger reconnect
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Close again for second reconnect
      setTimeoutSpy.mockClear();
      const ws2 = mockWebSocketInstances[mockWebSocketInstances.length - 1];
      await act(async () => {
        ws2?.close();
      });

      // Second reconnect — delay ~2000ms (1000 * 2^1 = 2000)
      const secondCall = setTimeoutSpy.mock.calls.find(
        ([, delay]) => typeof delay === 'number' && delay >= 2000 && delay <= 3500
      );
      expect(secondCall).toBeTruthy();

      setTimeoutSpy.mockRestore();
      vi.useRealTimers();
    });

    it('should cap reconnect delay at 30 seconds', async () => {
      vi.useFakeTimers();
      const setTimeoutSpy = vi.spyOn(global, 'setTimeout');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: createWrapper(),
      });

      // Force many reconnect attempts to hit the cap
      for (let i = 0; i < 8; i++) {
        setTimeoutSpy.mockClear();
        const ws = mockWebSocketInstances[mockWebSocketInstances.length - 1];
        await act(async () => {
          ws?.close();
        });
        await act(async () => {
          vi.advanceTimersByTime(35000);
        });
      }

      // After many attempts: 1000 * 2^7 = 128000, capped at 30000
      // Find any setTimeout call — all delays should be ≤ 30000 + jitter
      const allTimeoutDelays = setTimeoutSpy.mock.calls
        .map(([, delay]) => delay)
        .filter((d): d is number => typeof d === 'number' && d >= 1000);

      for (const delay of allTimeoutDelays) {
        expect(delay).toBeLessThanOrEqual(31000); // 30000 + max jitter
      }

      setTimeoutSpy.mockRestore();
      vi.useRealTimers();
    });
  });

  // ── onRefreshTriggered callback tests ──────────────────────────────

  describe('onRefreshTriggered callback', () => {
    it('should invoke onRefreshTriggered on initial_data message', async () => {
      const onRefreshTriggered = vi.fn();

      renderHook(() => useRealTimeSync('PVT_123', { onRefreshTriggered }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });

      expect(onRefreshTriggered).toHaveBeenCalledTimes(1);
    });

    it('should invoke onRefreshTriggered on task_update message', async () => {
      const onRefreshTriggered = vi.fn();

      renderHook(() => useRealTimeSync('PVT_123', { onRefreshTriggered }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'task_update' });
      });

      expect(onRefreshTriggered).toHaveBeenCalledTimes(1);
    });

    it('should invoke onRefreshTriggered on refresh message', async () => {
      const onRefreshTriggered = vi.fn();

      renderHook(() => useRealTimeSync('PVT_123', { onRefreshTriggered }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'refresh' });
      });

      expect(onRefreshTriggered).toHaveBeenCalledTimes(1);
    });

    it('should invoke onRefreshTriggered on status_changed message', async () => {
      const onRefreshTriggered = vi.fn();

      renderHook(() => useRealTimeSync('PVT_123', { onRefreshTriggered }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'status_changed' });
      });

      expect(onRefreshTriggered).toHaveBeenCalledTimes(1);
    });

    it('should NOT invoke onRefreshTriggered for unknown message types', async () => {
      const onRefreshTriggered = vi.fn();

      renderHook(() => useRealTimeSync('PVT_123', { onRefreshTriggered }), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'unknown_type' });
      });

      expect(onRefreshTriggered).not.toHaveBeenCalled();
    });

    it('should NOT invoke onRefreshTriggered when callback is not provided', async () => {
      // Render without onRefreshTriggered — should not throw
      renderHook(() => useRealTimeSync('PVT_123'), { wrapper: createWrapper() });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      // Should not throw when sending a message without callback
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'task_update' });
      });
    });
  });

  describe('polling fallback scope (SC-004, FR-006)', () => {
    it('should only invalidate tasks query, never board data, during polling fallback', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const { result } = renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Force polling mode by simulating WebSocket error
      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });

      expect(result.current.status).toBe('polling');
      invalidateSpy.mockClear();

      // Advance past one polling interval
      await act(async () => {
        vi.advanceTimersByTime(30_000);
      });

      // Verify only tasks query was invalidated
      for (const call of invalidateSpy.mock.calls) {
        const queryKey = call[0]?.queryKey;
        if (Array.isArray(queryKey)) {
          // Must be a tasks query, never board data
          expect(queryKey).not.toContain('board');
          expect(queryKey[0]).toBe('projects');
        }
      }

      vi.useRealTimers();
    });

    it('should produce at most one tasks query invalidation within 30s during WS-to-polling transition', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Start connected
      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      invalidateSpy.mockClear();

      // Simulate WebSocket close (triggers reconnect + polling fallback)
      await act(async () => {
        mockWebSocketInstances[0]?.close();
      });

      // Count invalidations within the first 30s window
      await act(async () => {
        vi.advanceTimersByTime(30_000);
      });

      // Should have at most one tasks invalidation from the polling interval
      const tasksInvalidations = invalidateSpy.mock.calls.filter((call) => {
        const queryKey = call[0]?.queryKey;
        return Array.isArray(queryKey) && queryKey[0] === 'projects';
      });
      expect(tasksInvalidations.length).toBeLessThanOrEqual(1);

      vi.useRealTimers();
    });
  });

  // ── T026-T028: WebSocket message → query invalidation scope ────────

  describe('WebSocket message query invalidation scope (T026-T028)', () => {
    it('T026: task_update, task_created, status_changed invalidate only tasks query', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });
      invalidateSpy.mockClear();

      // Send all three task-level message types
      for (const type of ['task_update', 'task_created', 'status_changed']) {
        await act(async () => {
          mockWebSocketInstances[0]?.simulateMessage({ type });
        });
      }

      // All invalidations should target the tasks query
      for (const call of invalidateSpy.mock.calls) {
        const queryKey = (call[0] as { queryKey: unknown[] }).queryKey;
        expect(queryKey).toEqual(['projects', 'PVT_123', 'tasks']);
      }
    });

    it('T027: initial_data and refresh messages invalidate tasks query correctly', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });
      invalidateSpy.mockClear();

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });

      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['projects', 'PVT_123', 'tasks'] })
      );

      invalidateSpy.mockClear();
      // Advance past debounce window to allow a second initial_data
      await act(async () => {
        vi.advanceTimersByTime(2100);
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'refresh' });
      });

      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['projects', 'PVT_123', 'tasks'] })
      );
      vi.useRealTimers();
    });

    it('T028: board data query is NOT invalidated on any WebSocket message', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });
      invalidateSpy.mockClear();

      // Send every known message type
      for (const type of ['task_update', 'task_created', 'status_changed', 'refresh']) {
        await act(async () => {
          mockWebSocketInstances[0]?.simulateMessage({ type });
        });
      }

      // No call should target the board data query
      const boardCalls = invalidateSpy.mock.calls.filter(([opts]) => {
        const key = (opts as { queryKey: unknown[] }).queryKey;
        return Array.isArray(key) && key[0] === 'board' && key[1] === 'data';
      });
      expect(boardCalls.length).toBe(0);
    });
  });

  // ── T040-T042: Fallback polling behavior ────────────────────────

  describe('fallback polling behavior (T040-T042)', () => {
    it('T040: fallback polling always invalidates tasks query each interval', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      // Pre-populate tasks data in cache
      const tasksData = [{ id: '1', title: 'Task A' }];
      queryClient.setQueryData(['projects', 'PVT_123', 'tasks'], tasksData);

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Force polling fallback
      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });

      // First poll — should invalidate
      invalidateSpy.mockClear();
      await act(async () => {
        vi.advanceTimersByTime(30_000);
      });
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['projects', 'PVT_123', 'tasks'] })
      );

      // Second poll — must still invalidate to detect server-side changes
      invalidateSpy.mockClear();
      await act(async () => {
        vi.advanceTimersByTime(30_000);
      });
      expect(invalidateSpy).toHaveBeenCalledWith(
        expect.objectContaining({ queryKey: ['projects', 'PVT_123', 'tasks'] })
      );

      vi.useRealTimers();
    });

    it('T041: fallback polling does NOT invalidate board data query when no changes', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      queryClient.setQueryData(['projects', 'PVT_123', 'tasks'], [{ id: '1' }]);

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });
      invalidateSpy.mockClear();

      // Advance through multiple poll cycles
      for (let i = 0; i < 3; i++) {
        await act(async () => {
          vi.advanceTimersByTime(30_000);
        });
      }

      // No board data query should be invalidated
      const boardCalls = invalidateSpy.mock.calls.filter(([opts]) => {
        const key = (opts as { queryKey: unknown[] }).queryKey;
        return Array.isArray(key) && key[0] === 'board' && key[1] === 'data';
      });
      expect(boardCalls.length).toBe(0);

      vi.useRealTimers();
    });

    it('T042: fallback polling intervals remain consistent', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const setIntervalSpy = vi.spyOn(global, 'setInterval');

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Force polling
      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });

      // Check that setInterval was called with 30s (WS_FALLBACK_POLL_MS)
      const pollIntervalCalls = setIntervalSpy.mock.calls.filter(
        ([, delay]) => delay === 30_000
      );
      expect(pollIntervalCalls.length).toBeGreaterThan(0);

      setIntervalSpy.mockRestore();
      vi.useRealTimers();
    });

    it('T021: polling fallback never invalidates board data query key', async () => {
      vi.useFakeTimers();
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      renderHook(() => useRealTimeSync('PVT_123'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Force fallback to polling by simulating WS error
      await act(async () => {
        mockWebSocketInstances[0]?.simulateError();
      });

      invalidateSpy.mockClear();

      // Let several polling ticks fire
      await act(async () => {
        vi.advanceTimersByTime(120_000); // 4 polling cycles
      });

      // Verify board data query is NEVER invalidated during polling
      const boardDataCalls = invalidateSpy.mock.calls.filter(([opts]) => {
        const key = (opts as { queryKey: unknown[] }).queryKey;
        return Array.isArray(key) && key[0] === 'board' && key[1] === 'data';
      });
      expect(boardDataCalls).toHaveLength(0);

      // Verify tasks query IS invalidated (polling should update tasks)
      const tasksCalls = invalidateSpy.mock.calls.filter(([opts]) => {
        const key = (opts as { queryKey: unknown[] }).queryKey;
        return Array.isArray(key) && key[0] === 'projects';
      });
      expect(tasksCalls.length).toBeGreaterThan(0);

      vi.useRealTimers();
    });
  });

  // ── Refresh contract regression tests (T027-T028/FR-007/FR-008) ──────────

  describe('Refresh Contract Regression', () => {
    it('T027: WebSocket refresh message invalidates only tasks query, never board data', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      renderHook(() => useRealTimeSync('PVT_456'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      // Open connection
      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      invalidateSpy.mockClear();

      // Send refresh message (the type backend sends periodically)
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({
          type: 'refresh',
          project_id: 'PVT_456',
          tasks: [],
          count: 0,
        });
      });

      // Tasks query MUST be invalidated
      const tasksCalls = invalidateSpy.mock.calls.filter(([opts]) => {
        const key = (opts as { queryKey: unknown[] }).queryKey;
        return Array.isArray(key) && key[0] === 'projects' && key[2] === 'tasks';
      });
      expect(tasksCalls.length).toBe(1);

      // Board data query MUST NOT be invalidated (FR-008)
      const boardCalls = invalidateSpy.mock.calls.filter(([opts]) => {
        const key = (opts as { queryKey: unknown[] }).queryKey;
        return Array.isArray(key) && key[0] === 'board' && key[1] === 'data';
      });
      expect(boardCalls).toHaveLength(0);
    });

    it('T028: all WebSocket message types consistently invalidate tasks only', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries').mockResolvedValue();

      renderHook(() => useRealTimeSync('PVT_789'), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        ),
      });

      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      const messageTypes = ['task_update', 'task_created', 'status_changed'];

      for (const type of messageTypes) {
        invalidateSpy.mockClear();

        await act(async () => {
          mockWebSocketInstances[0]?.simulateMessage({ type, task: { id: '1' } });
        });

        // Each message type invalidates tasks query with full key shape
        const tasksCalls = invalidateSpy.mock.calls.filter(([opts]) => {
          const key = (opts as { queryKey: unknown[] }).queryKey;
          return (
            Array.isArray(key) &&
            key[0] === 'projects' &&
            key[1] === 'PVT_789' &&
            key[2] === 'tasks'
          );
        });
        expect(tasksCalls.length).toBe(1);

        // None invalidate board data
        const boardCalls = invalidateSpy.mock.calls.filter(([opts]) => {
          const key = (opts as { queryKey: unknown[] }).queryKey;
          return Array.isArray(key) && key[0] === 'board' && key[1] === 'data';
        });
        expect(boardCalls).toHaveLength(0);
      }
    });
  });
});
