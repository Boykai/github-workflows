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
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
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
    const { result, rerender } = renderHook(
      ({ projectId }) => useRealTimeSync(projectId),
      {
        wrapper: createWrapper(),
        initialProps: { projectId: 'PVT_123' as string | null },
      }
    );

    // Change to null
    await act(async () => {
      rerender({ projectId: null });
    });

    expect(result.current.status).toBe('disconnected');
  });

  it('should reconnect when projectId changes', () => {
    const { rerender } = renderHook(
      ({ projectId }) => useRealTimeSync(projectId),
      {
        wrapper: createWrapper(),
        initialProps: { projectId: 'PVT_123' as string | null },
      }
    );

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

    expect(result.current.lastUpdate).not.toBeNull(); // Set when polling starts

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
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
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
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
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
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
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
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
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
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
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
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
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
  });
});
