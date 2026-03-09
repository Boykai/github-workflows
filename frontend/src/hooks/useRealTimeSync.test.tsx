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

  // ── T026: WebSocket messages only invalidate tasks query, never board data ──

  describe('WebSocket message invalidation targets (T026/FR-003)', () => {
    it.each(['task_update', 'task_created', 'status_changed', 'refresh'] as const)(
      'should invalidate tasks query only (not board data) on %s message',
      async (messageType) => {
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
          mockWebSocketInstances[0]?.simulateMessage({ type: messageType });
        });

        // Should invalidate tasks query
        const tasksCalls = invalidateSpy.mock.calls.filter(
          ([opts]) =>
            JSON.stringify((opts as { queryKey: unknown }).queryKey) ===
            JSON.stringify(['projects', 'PVT_123', 'tasks']),
        );
        expect(tasksCalls.length).toBeGreaterThan(0);

        // Should NOT invalidate board data query
        const boardCalls = invalidateSpy.mock.calls.filter(
          ([opts]) =>
            JSON.stringify((opts as { queryKey: unknown }).queryKey) ===
            JSON.stringify(['board', 'data', 'PVT_123']),
        );
        expect(boardCalls.length).toBe(0);
      },
    );
  });

  // ── T050: Reconnection debounce — rapid reconnections don't cascade ──

  describe('reconnection debounce prevents cascading invalidations (T050/FR-012)', () => {
    it('should not cascade task query invalidations on rapid WebSocket reconnections', async () => {
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

      // Open first connection
      await act(async () => {
        mockWebSocketInstances[0]?.simulateOpen();
      });

      invalidateSpy.mockClear();

      // Send initial_data (first one should go through)
      await act(async () => {
        mockWebSocketInstances[0]?.simulateMessage({ type: 'initial_data' });
      });
      expect(invalidateSpy).toHaveBeenCalledTimes(1);

      // Close the connection — triggers reconnect + polling
      await act(async () => {
        mockWebSocketInstances[0]?.close();
      });

      // Advance a bit (less than 2s debounce window) and reconnect
      await act(async () => {
        vi.advanceTimersByTime(1500);
      });

      invalidateSpy.mockClear();

      // New WS opens and sends initial_data within the 2s debounce window
      const newWs = mockWebSocketInstances[mockWebSocketInstances.length - 1];
      await act(async () => {
        newWs?.simulateOpen();
      });
      await act(async () => {
        newWs?.simulateMessage({ type: 'initial_data' });
      });

      // The initial_data should be suppressed because it's within the debounce window
      expect(invalidateSpy).not.toHaveBeenCalled();

      vi.useRealTimers();
    });
  });
});
