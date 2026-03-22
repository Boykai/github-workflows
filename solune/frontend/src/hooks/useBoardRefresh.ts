/**
 * Hook for board refresh orchestration.
 *
 * Manages manual refresh, 5-minute auto-refresh timer,
 * Page Visibility API pause/resume, rate limit state, and board-reload
 * debouncing per the refresh contract (contracts/refresh-contract.md).
 *
 * Debounce Rule (Rule 3): If multiple full-board-reload triggers arrive
 * within a 2-second window, only one refetch executes.  Manual refresh
 * always wins and bypasses debounce.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AUTO_REFRESH_INTERVAL_MS, RATE_LIMIT_LOW_THRESHOLD } from '@/constants';
import type { RateLimitInfo, RefreshError, BoardDataResponse } from '@/types';
import { ApiError, boardApi } from '@/services/api';
import type { AdaptivePollingState } from './useAdaptivePolling';

/** Debounce window for board-reload triggers (Rule 3). */
const BOARD_RELOAD_DEBOUNCE_MS = 2_000;

interface UseBoardRefreshOptions {
  /** Currently selected project ID */
  projectId: string | null;
  /** Board data response (for extracting rate limit info reactively) */
  boardData?: BoardDataResponse | null;
  /** Whether a healthy WebSocket connection is actively delivering updates. */
  isWebSocketConnected?: boolean;
  /** Adaptive polling state from useAdaptivePolling (for refresh UI indicators). */
  adaptivePollingState?: AdaptivePollingState | null;
}

interface UseBoardRefreshReturn {
  /** Trigger a manual refresh */
  refresh: () => void;
  /** Whether a refresh is currently in progress */
  isRefreshing: boolean;
  /** Timestamp of last successful refresh */
  lastRefreshedAt: Date | null;
  /** Current error state */
  error: RefreshError | null;
  /** Rate limit information from last response */
  rateLimitInfo: RateLimitInfo | null;
  /** Whether rate limit is critically low (<10 remaining) */
  isRateLimitLow: boolean;
  /** Reset the auto-refresh timer (called by external sync events) */
  resetTimer: () => void;
  /** Request a debounced board reload (used by WebSocket refresh handler). */
  requestBoardReload: () => void;
  /** Current adaptive polling tier (for UI display). */
  pollingTier: string | null;
  /** Whether adaptive polling is currently paused (tab hidden). */
  isPollingPaused: boolean;
}

export function useBoardRefresh({
  projectId,
  boardData,
  isWebSocketConnected = false,
  adaptivePollingState = null,
}: UseBoardRefreshOptions): UseBoardRefreshReturn {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const [error, setError] = useState<RefreshError | null>(null);
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);

  // Seed lastRefreshedAt from the TanStack Query cache so the Page Visibility
  // handler doesn't treat every first tab-switch as "stale since epoch".
  // This runs once when boardData first arrives (lastRefreshedAt is still null).
  useEffect(() => {
    if (lastRefreshedAt !== null || !projectId) return;
    const queryState = queryClient.getQueryState(['board', 'data', projectId]);
    if (queryState?.dataUpdatedAt) {
      setLastRefreshedAt(new Date(queryState.dataUpdatedAt));
    }
  }, [projectId, lastRefreshedAt, queryClient, boardData]);

  // Update rate limit info reactively from board data responses
  useEffect(() => {
    if (boardData?.rate_limit) {
      setRateLimitInfo(boardData.rate_limit);
    }
  }, [boardData?.rate_limit]);

  const timerRef = useRef<number | null>(null);
  const isRefreshingRef = useRef(false);
  /** Timestamp of last board-reload execution for debounce gating. */
  const lastBoardReloadRef = useRef(0);
  /** Pending debounce timeout for board reload requests. */
  const debounceTimeoutRef = useRef<number | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const doRefresh = useCallback(
    async (forceRefresh = false) => {
      if (!projectId || isRefreshingRef.current) return;

      isRefreshingRef.current = true;
      setIsRefreshing(true);

      try {
        if (forceRefresh) {
          // Manual refresh: cancel any in-progress automatic refresh first,
          // then bypass the backend cache by fetching with refresh=true
          // and writing the result directly into TanStack Query.
          await queryClient.cancelQueries({ queryKey: ['board', 'data', projectId] });
          const data = await boardApi.getBoardData(projectId, /* refresh */ true);
          queryClient.setQueryData(['board', 'data', projectId], data);
        } else {
          // Auto-refresh: revalidate using the default queryFn which may
          // serve backend-cached data — acceptable for periodic background refreshes.
          await queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] });
        }
        lastBoardReloadRef.current = Date.now();
        setLastRefreshedAt(new Date());
        setError(null);
      } catch (err) {
        const refreshError = parseRefreshError(err);
        setError(refreshError);
        if (refreshError.rateLimitInfo) {
          setRateLimitInfo(refreshError.rateLimitInfo);
        }
      } finally {
        isRefreshingRef.current = false;
        setIsRefreshing(false);
      }
    },
    [projectId, queryClient]
  );

  const startTimer = useCallback(() => {
    clearTimer();
    if (!projectId || isWebSocketConnected) return;
    timerRef.current = window.setInterval(() => {
      doRefresh();
    }, AUTO_REFRESH_INTERVAL_MS);
  }, [projectId, isWebSocketConnected, clearTimer, doRefresh]);

  const resetTimer = useCallback(() => {
    startTimer();
  }, [startTimer]);

  const refresh = useCallback(() => {
    // Manual refresh bypasses server cache (forceRefresh=true) so the user
    // always sees the latest data from GitHub, not a stale backend cache hit.
    // Manual refresh also cancels any pending debounced reload (Rule 3: manual wins).
    if (debounceTimeoutRef.current !== null) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
    doRefresh(/* forceRefresh */ true);
    // Reset the auto-refresh timer on manual refresh
    startTimer();
  }, [doRefresh, startTimer]);

  /**
   * Request a debounced full-board reload.  If a board reload already
   * happened within the last BOARD_RELOAD_DEBOUNCE_MS, the request is
   * deferred until the debounce window closes, deduplicating concurrent
   * auto-refresh + WebSocket refresh triggers (Rule 3).
   */
  const requestBoardReload = useCallback(() => {
    if (!projectId) return;
    const now = Date.now();
    const elapsed = now - lastBoardReloadRef.current;
    if (elapsed >= BOARD_RELOAD_DEBOUNCE_MS) {
      doRefresh();
      resetTimer();
    } else if (debounceTimeoutRef.current === null) {
      // Reset auto-refresh timer immediately so it does not fire during the
      // debounce window and cause a duplicate refresh.
      resetTimer();
      debounceTimeoutRef.current = window.setTimeout(() => {
        debounceTimeoutRef.current = null;
        doRefresh();
        resetTimer();
      }, BOARD_RELOAD_DEBOUNCE_MS - elapsed);
    }
    // else: a debounced reload is already pending — deduplicate
  }, [projectId, doRefresh, resetTimer]);

  // Page Visibility API: pause timer when hidden, resume when visible
  useEffect(() => {
    if (!projectId) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        clearTimer();
      } else {
        // Check if data is stale (older than auto-refresh interval)
        const now = Date.now();
        const lastTime = lastRefreshedAt?.getTime() ?? 0;
        if (now - lastTime >= AUTO_REFRESH_INTERVAL_MS) {
          doRefresh();
        }
        startTimer();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [projectId, lastRefreshedAt, clearTimer, startTimer, doRefresh]);

  // Start auto-refresh timer when projectId changes.
  // Suppress the timer while a healthy WebSocket connection is actively
  // delivering updates — the timer is redundant in that case and only
  // adds unnecessary backend load (T017 / contracts/refresh-policy.md §3).
  useEffect(() => {
    if (projectId && !isWebSocketConnected) {
      startTimer();
    } else {
      clearTimer();
    }
    return () => {
      clearTimer();
      if (debounceTimeoutRef.current !== null) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }
    };
  }, [projectId, isWebSocketConnected, startTimer, clearTimer]);

  const isRateLimitLow =
    rateLimitInfo !== null && rateLimitInfo.remaining < RATE_LIMIT_LOW_THRESHOLD;

  return {
    refresh,
    isRefreshing,
    lastRefreshedAt,
    error,
    rateLimitInfo,
    isRateLimitLow,
    resetTimer,
    requestBoardReload,
    pollingTier: adaptivePollingState?.tier ?? null,
    isPollingPaused: adaptivePollingState?.isPaused ?? false,
  };
}

/** Parse an error into a typed RefreshError. */
function parseRefreshError(err: unknown): RefreshError {
  if (err instanceof ApiError) {
    if (err.status === 429 || err.status === 403) {
      // Try to extract rate_limit from the error details
      const rl = err.error?.details?.rate_limit as RateLimitInfo | undefined;
      if (err.status === 429 || rl) {
        return {
          type: 'rate_limit',
          message: 'GitHub API rate limit exceeded.',
          rateLimitInfo: rl,
          retryAfter: rl ? new Date(rl.reset_at * 1000) : undefined,
        };
      }
    }
    if (err.status === 401) {
      return { type: 'auth', message: 'Authentication failed. Please sign in again.' };
    }
    if (err.status >= 500) {
      return { type: 'server', message: 'Server error. Will retry automatically.' };
    }
  }

  if (err instanceof TypeError && err.message === 'Failed to fetch') {
    return { type: 'network', message: 'Network error. Check your connection.' };
  }

  return {
    type: 'unknown',
    message: err instanceof Error ? err.message : 'An unexpected error occurred.',
  };
}
