/**
 * Hook for board refresh orchestration.
 *
 * Manages manual refresh, 5-minute auto-refresh timer,
 * Page Visibility API pause/resume, and rate limit state.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { AUTO_REFRESH_INTERVAL_MS, RATE_LIMIT_LOW_THRESHOLD } from '@/constants';
import type { RateLimitInfo, RefreshError } from '@/types';
import { ApiError } from '@/services/api';

interface UseBoardRefreshOptions {
  /** Currently selected project ID */
  projectId: string | null;
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
}

export function useBoardRefresh({ projectId }: UseBoardRefreshOptions): UseBoardRefreshReturn {
  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const [error, setError] = useState<RefreshError | null>(null);
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo | null>(null);

  const timerRef = useRef<number | null>(null);
  const isRefreshingRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const doRefresh = useCallback(async () => {
    if (!projectId || isRefreshingRef.current) return;

    isRefreshingRef.current = true;
    setIsRefreshing(true);

    try {
      await queryClient.invalidateQueries({ queryKey: ['board', 'data', projectId] });
      // Fetch the latest data from the query cache after invalidation
      const data = queryClient.getQueryData<{ rate_limit?: RateLimitInfo | null }>(['board', 'data', projectId]);
      if (data?.rate_limit) {
        setRateLimitInfo(data.rate_limit);
      }
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
  }, [projectId, queryClient]);

  const startTimer = useCallback(() => {
    clearTimer();
    if (!projectId) return;
    timerRef.current = window.setInterval(() => {
      doRefresh();
    }, AUTO_REFRESH_INTERVAL_MS);
  }, [projectId, clearTimer, doRefresh]);

  const resetTimer = useCallback(() => {
    startTimer();
  }, [startTimer]);

  const refresh = useCallback(() => {
    doRefresh();
    // Reset the auto-refresh timer on manual refresh
    startTimer();
  }, [doRefresh, startTimer]);

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

  // Start auto-refresh timer when projectId changes
  useEffect(() => {
    if (projectId) {
      startTimer();
    } else {
      clearTimer();
    }
    return clearTimer;
  }, [projectId, startTimer, clearTimer]);

  const isRateLimitLow = rateLimitInfo !== null && rateLimitInfo.remaining < RATE_LIMIT_LOW_THRESHOLD;

  return {
    refresh,
    isRefreshing,
    lastRefreshedAt,
    error,
    rateLimitInfo,
    isRateLimitLow,
    resetTimer,
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
