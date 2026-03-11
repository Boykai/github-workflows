/**
 * Real-time sync hook for WebSocket updates with polling fallback.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WS_FALLBACK_POLL_MS, WS_CONNECTION_TIMEOUT_MS } from '@/constants';

/** Maximum reconnection delay in milliseconds (30 seconds). */
const MAX_RECONNECT_DELAY_MS = 30_000;
/** Base reconnection delay in milliseconds. */
const BASE_RECONNECT_DELAY_MS = 1_000;
/** Debounce window for reconnection invalidations (milliseconds). */
const RECONNECT_DEBOUNCE_MS = 2_000;

type SyncStatus = 'disconnected' | 'connecting' | 'connected' | 'polling';

interface UseRealTimeSyncOptions {
  /** Callback when a WebSocket-triggered refresh occurs (resets auto-refresh timer). */
  onRefreshTriggered?: () => void;
  /** Request a debounced full-board reload (from useBoardRefresh). */
  onBoardReloadRequested?: () => void;
}

interface UseRealTimeSyncReturn {
  status: SyncStatus;
  lastUpdate: Date | null;
}

export function useRealTimeSync(
  projectId: string | null,
  options?: UseRealTimeSyncOptions
): UseRealTimeSyncReturn {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SyncStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const onRefreshTriggeredRef = useRef(options?.onRefreshTriggered);
  const onBoardReloadRequestedRef = useRef(options?.onBoardReloadRequested);
  /** Timestamp of the last reconnection invalidation for debounce. */
  const lastReconnectInvalidationRef = useRef(0);

  // Keep the callback refs up to date
  onRefreshTriggeredRef.current = options?.onRefreshTriggered;
  onBoardReloadRequestedRef.current = options?.onBoardReloadRequested;

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        const markUpdated = () => {
          setLastUpdate(new Date());
          onRefreshTriggeredRef.current?.();
        };

        // Handle initial data / reconnection — debounce to at most once per cycle
        if (data.type === 'initial_data') {
          const now = Date.now();
          if (now - lastReconnectInvalidationRef.current < RECONNECT_DEBOUNCE_MS) {
            // Skip — already invalidated within the debounce window
            return;
          }
          lastReconnectInvalidationRef.current = now;
          // Only invalidate tasks — board data refreshes on its own 5-minute schedule
          queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
          markUpdated();
          return;
        }

        if (data.type === 'refresh') {
          // Refresh contract: The backend already suppresses this message when
          // task data is unchanged (hash comparison). Invalidate only the tasks
          // query for task-level freshness and reset the auto-refresh timer via
          // markUpdated; board data continues to refresh on its own schedule.
          queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
          markUpdated();
          return;
        }

        // Handle real-time updates
        if (
          data.type === 'task_update' ||
          data.type === 'task_created' ||
          data.type === 'status_changed'
        ) {
          // Only invalidate tasks — board data refreshes on its own 5-minute schedule
          queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
          markUpdated();
        }

        // Handle blocking queue state changes
        if (data.type === 'blocking_queue_updated') {
          queryClient.invalidateQueries({ queryKey: ['blocking-queue', projectId] });
          markUpdated();
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    },
    [projectId, queryClient]
  );

  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return;

    setStatus('polling');
    setLastUpdate(new Date()); // Mark as updated when polling starts

    pollingIntervalRef.current = window.setInterval(() => {
      // Only invalidate tasks — board data refreshes on its own 5-minute schedule
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
      setLastUpdate(new Date());
      onRefreshTriggeredRef.current?.();
    }, WS_FALLBACK_POLL_MS);
  }, [projectId, queryClient]);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!projectId) return;

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Only show "Connecting..." on first attempt, otherwise stay in polling mode
    if (reconnectAttempts.current === 0) {
      setStatus('connecting');
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/projects/${projectId}/subscribe`;

    try {
      const ws = new WebSocket(wsUrl);

      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          ws.close();
          // Fall back to polling after timeout
          startPolling();
        }
      }, WS_CONNECTION_TIMEOUT_MS);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        stopPolling();
        setStatus('connected');
        setLastUpdate(new Date());
        reconnectAttempts.current = 0;
      };

      ws.onmessage = handleMessage;

      ws.onerror = () => {
        clearTimeout(connectionTimeout);
        // Silently fall back to polling without showing error
        startPolling();
      };

      ws.onclose = () => {
        clearTimeout(connectionTimeout);
        wsRef.current = null;

        // Resume polling immediately while we attempt reconnection
        startPolling();

        // Exponential backoff: delay = min(BASE * 2^attempt, MAX) + jitter
        const expDelay = Math.min(
          BASE_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts.current),
          MAX_RECONNECT_DELAY_MS
        );
        const jitter = Math.random() * BASE_RECONNECT_DELAY_MS;
        reconnectAttempts.current++;

        reconnectTimeoutRef.current = window.setTimeout(() => {
          if (projectId) {
            connect();
          }
        }, expDelay + jitter);
      };

      wsRef.current = ws;
    } catch {
      // WebSocket not supported or blocked, use polling
      startPolling();
    }
  }, [projectId, handleMessage, startPolling, stopPolling]);

  // Connect when project changes
  useEffect(() => {
    if (projectId) {
      reconnectAttempts.current = 0;
      // Reset debounce so the first initial_data for the new project is not suppressed
      lastReconnectInvalidationRef.current = 0;
      // Try WebSocket first. Polling starts only as a fallback
      // (on WS error/close/timeout). Starting both simultaneously
      // caused a polling storm that froze the UI.
      connect();
    } else {
      setStatus('disconnected');
      stopPolling();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      stopPolling();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- connect is stable enough; startPolling/stopPolling included via connect's closure
  }, [projectId, connect]);

  return {
    status,
    lastUpdate,
  };
}
