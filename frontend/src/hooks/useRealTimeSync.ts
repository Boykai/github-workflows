/**
 * Real-time sync hook for WebSocket updates with polling fallback.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WS_FALLBACK_POLL_MS, WS_CONNECTION_TIMEOUT_MS, WS_RECONNECT_DELAY_MS } from '@/constants';

type SyncStatus = 'disconnected' | 'connecting' | 'connected' | 'polling';

interface UseRealTimeSyncReturn {
  status: SyncStatus;
  lastUpdate: Date | null;
}

export function useRealTimeSync(projectId: string | null): UseRealTimeSyncReturn {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SyncStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle initial data with all tasks
        if (data.type === 'initial_data' || data.type === 'refresh') {
          // Force refresh to get the updated data
          queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
          setLastUpdate(new Date());
          return;
        }

        // Handle real-time updates
        if (data.type === 'task_update' || data.type === 'task_created' || data.type === 'status_changed') {
          // Invalidate tasks query to refetch
          queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
          setLastUpdate(new Date());
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
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'tasks'] });
      setLastUpdate(new Date());
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
        setStatus('connected');
        setLastUpdate(new Date());
        // Keep polling as backup even with WebSocket
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

        // Only attempt reconnect a few times before giving up
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (projectId) {
              connect();
            }
          }, WS_RECONNECT_DELAY_MS);
        } else {
          // After max attempts, stay in polling mode
          startPolling();
        }
      };

      wsRef.current = ws;
    } catch {
      // WebSocket not supported or blocked, use polling
      startPolling();
    }
  }, [projectId, handleMessage, startPolling]);

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
    };
  }, [projectId, connect, startPolling, stopPolling]);

  return {
    status,
    lastUpdate,
  };
}
