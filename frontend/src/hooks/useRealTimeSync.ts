/**
 * Real-time sync hook for WebSocket updates with polling fallback.
 *
 * Optimized to reduce GitHub API requests:
 * - Polling is stopped when WebSocket is connected (no dual-sync)
 * - Polling fallback interval increased from 5s to 30s
 * - WebSocket message invalidations are debounced (2s window)
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

type SyncStatus = 'disconnected' | 'connecting' | 'connected' | 'polling';

interface UseRealTimeSyncReturn {
  status: SyncStatus;
  lastUpdate: Date | null;
}

/** Polling fallback interval in ms (only used when WebSocket is unavailable). */
const POLLING_INTERVAL_MS = 30_000;

/** Debounce window for WebSocket-triggered cache invalidations. */
const INVALIDATION_DEBOUNCE_MS = 2_000;

export function useRealTimeSync(projectId: string | null): UseRealTimeSyncReturn {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SyncStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;
  const debounceTimerRef = useRef<number | null>(null);

  /** Debounced query invalidation — collapses rapid WebSocket messages. */
  const debouncedInvalidate = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = window.setTimeout(() => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
      setLastUpdate(new Date());
      debounceTimerRef.current = null;
    }, INVALIDATION_DEBOUNCE_MS);
  }, [projectId, queryClient]);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle initial data with all tasks
        if (data.type === 'initial_data' || data.type === 'refresh') {
          debouncedInvalidate();
          return;
        }

        // Handle real-time updates
        if (data.type === 'task_update' || data.type === 'task_created' || data.type === 'status_changed') {
          debouncedInvalidate();
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    },
    [debouncedInvalidate]
  );

  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) return;

    setStatus('polling');
    setLastUpdate(new Date()); // Mark as updated when polling starts

    pollingIntervalRef.current = window.setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
      setLastUpdate(new Date());
    }, POLLING_INTERVAL_MS);
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
      }, 5000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        setStatus('connected');
        setLastUpdate(new Date());
        // Stop polling — WebSocket provides real-time updates
        stopPolling();
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

        // Resume polling as fallback while attempting reconnect
        startPolling();

        // Only attempt reconnect a few times before giving up
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (projectId) {
              connect();
            }
          }, 5000);
        }
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
      // Start with polling immediately so UI shows "Polling mode" instead of "Offline"
      startPolling();
      // Then try to upgrade to WebSocket
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
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [projectId, connect, startPolling, stopPolling]);

  return {
    status,
    lastUpdate,
  };
}
