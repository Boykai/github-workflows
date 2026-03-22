/**
 * Adaptive polling hook implementing activity-based interval adjustment.
 *
 * Adjusts the polling frequency based on detected changes in board data:
 * - **high** tier: >60% of recent polls detected changes → 3s interval
 * - **medium** tier: 20–60% of recent polls detected changes → 10s interval
 * - **low** tier: <20% of recent polls detected changes → 30s interval
 * - **backoff** tier: poll failures → exponential backoff up to 60s
 *
 * Integrates with TanStack Query via `getRefetchInterval` and with
 * the Page Visibility API for tab-awareness.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// ── Configuration ──

export interface AdaptivePollingConfig {
  /** Base polling interval in ms (default: 10_000). */
  baseInterval?: number;
  /** Minimum polling interval in ms (default: 3_000). */
  minInterval?: number;
  /** Maximum polling interval in ms (default: 30_000). */
  maxInterval?: number;
  /** Maximum backoff interval in ms (default: 60_000). */
  maxBackoffInterval?: number;
  /** Sliding window size for activity detection (default: 5). */
  windowSize?: number;
  /** Activity score threshold for high tier (default: 0.6). */
  highActivityThreshold?: number;
  /** Activity score threshold for medium tier (default: 0.2). */
  mediumActivityThreshold?: number;
}

// ── State ──

export type PollingTier = 'high' | 'medium' | 'low' | 'backoff';

export interface AdaptivePollingState {
  /** Current polling interval in ms. */
  currentInterval: number;
  /** Current activity tier. */
  tier: PollingTier;
  /** Current activity score (0.0–1.0). */
  activityScore: number;
  /** Whether polling is currently paused (tab hidden). */
  isPaused: boolean;
}

// ── Return type ──

export interface UseAdaptivePollingReturn {
  /** Dynamic refetchInterval function for TanStack Query. */
  getRefetchInterval: () => number | false;
  /** Report whether the last poll detected changes. */
  reportPollResult: (hasChanges: boolean) => void;
  /** Report a poll failure (triggers backoff). */
  reportPollFailure: () => void;
  /** Report a poll success after failures (resets backoff). */
  reportPollSuccess: () => void;
  /** Force an immediate poll (e.g., on tab focus). */
  triggerImmediatePoll: () => void;
  /** Current polling state. */
  state: AdaptivePollingState;
}

// ── Defaults ──

const DEFAULT_CONFIG: Required<AdaptivePollingConfig> = {
  baseInterval: 10_000,
  minInterval: 3_000,
  maxInterval: 30_000,
  maxBackoffInterval: 60_000,
  windowSize: 5,
  highActivityThreshold: 0.6,
  mediumActivityThreshold: 0.2,
};

// ── Tier → interval mapping ──

function tierInterval(
  tier: PollingTier,
  cfg: Required<AdaptivePollingConfig>,
  backoffMultiplier: number,
): number {
  switch (tier) {
    case 'high':
      return cfg.minInterval;
    case 'medium':
      return cfg.baseInterval;
    case 'low':
      return cfg.maxInterval;
    case 'backoff':
      return Math.min(cfg.baseInterval * backoffMultiplier, cfg.maxBackoffInterval);
  }
}

function computeActivityScore(activityWindow: boolean[]): number {
  if (activityWindow.length === 0) return 0;
  return activityWindow.filter(Boolean).length / activityWindow.length;
}

function computeTier(
  score: number,
  consecutiveFailures: number,
  cfg: Required<AdaptivePollingConfig>,
): PollingTier {
  if (consecutiveFailures > 0) return 'backoff';
  if (score > cfg.highActivityThreshold) return 'high';
  if (score > cfg.mediumActivityThreshold) return 'medium';
  return 'low';
}

// ── Hook ──

export function useAdaptivePolling(
  config?: AdaptivePollingConfig,
): UseAdaptivePollingReturn {
  const cfg = useMemo<Required<AdaptivePollingConfig>>(
    () => ({
      baseInterval: config?.baseInterval ?? DEFAULT_CONFIG.baseInterval,
      minInterval: config?.minInterval ?? DEFAULT_CONFIG.minInterval,
      maxInterval: config?.maxInterval ?? DEFAULT_CONFIG.maxInterval,
      maxBackoffInterval: config?.maxBackoffInterval ?? DEFAULT_CONFIG.maxBackoffInterval,
      windowSize: config?.windowSize ?? DEFAULT_CONFIG.windowSize,
      highActivityThreshold:
        config?.highActivityThreshold ?? DEFAULT_CONFIG.highActivityThreshold,
      mediumActivityThreshold:
        config?.mediumActivityThreshold ?? DEFAULT_CONFIG.mediumActivityThreshold,
    }),
    // Individual primitive values as deps so the object identity stays stable
    // when callers pass a new config object literal on every render.
    [
      config?.baseInterval,
      config?.minInterval,
      config?.maxInterval,
      config?.maxBackoffInterval,
      config?.windowSize,
      config?.highActivityThreshold,
      config?.mediumActivityThreshold,
    ],
  );

  const windowRef = useRef<boolean[]>([]);
  const failuresRef = useRef(0);
  const immediateRef = useRef(false);

  const [pollingState, setPollingState] = useState<AdaptivePollingState>({
    currentInterval: cfg.baseInterval,
    tier: 'medium',
    activityScore: 0,
    isPaused: false,
  });

  // ── Activity reporting ──

  const reportPollResult = useCallback(
    (hasChanges: boolean) => {
      const w = windowRef.current;
      w.push(hasChanges);
      if (w.length > cfg.windowSize) w.shift();

      const score = computeActivityScore(w);
      const tier = computeTier(score, failuresRef.current, cfg);
      const interval = tierInterval(tier, cfg, Math.pow(2, failuresRef.current));

      setPollingState((prev) => ({
        ...prev,
        activityScore: score,
        tier,
        currentInterval: interval,
      }));
    },
    [cfg],
  );

  const reportPollFailure = useCallback(() => {
    failuresRef.current += 1;
    const multiplier = Math.pow(2, failuresRef.current);
    const interval = tierInterval('backoff', cfg, multiplier);

    setPollingState((prev) => ({
      ...prev,
      tier: 'backoff',
      currentInterval: interval,
    }));
  }, [cfg]);

  const reportPollSuccess = useCallback(() => {
    if (failuresRef.current > 0) {
      failuresRef.current = 0;
      const score = computeActivityScore(windowRef.current);
      const tier = computeTier(score, 0, cfg);
      const interval = tierInterval(tier, cfg, 1);

      setPollingState((prev) => ({
        ...prev,
        tier,
        currentInterval: interval,
      }));
    }
  }, [cfg]);

  // ── Tab visibility ──

  useEffect(() => {
    function handleVisibilityChange() {
      const isVisible = document.visibilityState === 'visible';

      setPollingState((prev) => ({ ...prev, isPaused: !isVisible }));

      if (isVisible) {
        // Trigger immediate poll on tab regain
        immediateRef.current = true;
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // ── TanStack Query integration ──

  const getRefetchInterval = useCallback((): number | false => {
    if (pollingState.isPaused) return false;

    if (immediateRef.current) {
      immediateRef.current = false;
      return 100; // near-immediate poll
    }

    return pollingState.currentInterval;
  }, [pollingState.isPaused, pollingState.currentInterval]);

  const triggerImmediatePoll = useCallback(() => {
    immediateRef.current = true;
    // Reset to medium tier on manual trigger
    const score = computeActivityScore(windowRef.current);
    const tier = computeTier(score, 0, cfg);
    const interval = tierInterval(tier, cfg, 1);
    setPollingState((prev) => ({
      ...prev,
      tier,
      currentInterval: interval,
      isPaused: false,
    }));
  }, [cfg]);

  return {
    getRefetchInterval,
    reportPollResult,
    reportPollFailure,
    reportPollSuccess,
    triggerImmediatePoll,
    state: pollingState,
  };
}
