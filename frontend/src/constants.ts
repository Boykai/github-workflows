/**
 * Application-wide constants.
 *
 * Centralizes magic numbers (poll intervals, timeouts, cache durations)
 * so they are documented and easy to tune.
 */

// ============ React Query / Cache Durations ============

/** Default stale time for infrequently-changing data (5 minutes). */
export const STALE_TIME_LONG = 5 * 60 * 1000;

/** Stale time for moderately-changing data (1 minute). */
export const STALE_TIME_MEDIUM = 60 * 1000;

/** Stale time for frequently-changing data (60 seconds). */
export const STALE_TIME_SHORT = 60 * 1000;

// ============ Polling Intervals ============

/** WebSocket fallback polling interval (30 seconds). */
export const WS_FALLBACK_POLL_MS = 30_000;

/** WebSocket connection timeout (5 seconds). */
export const WS_CONNECTION_TIMEOUT_MS = 5_000;

// ============ Auto-Refresh ============

/** Board auto-refresh interval (5 minutes). */
export const AUTO_REFRESH_INTERVAL_MS = 5 * 60 * 1000;

/** Rate limit remaining threshold for preemptive low-quota warning. */
export const RATE_LIMIT_LOW_THRESHOLD = 10;

// ============ Expiry / TTL ============

/** AI task proposal expiry duration (10 minutes). */
export const PROPOSAL_EXPIRY_MS = 10 * 60 * 1000;

// ============ UI Timing ============

/** Success toast auto-dismiss delay (2 seconds). */
export const TOAST_SUCCESS_MS = 2_000;

/** Error toast auto-dismiss delay (3 seconds). */
export const TOAST_ERROR_MS = 3_000;

/** Highlight animation duration for recently-updated items (2 seconds). */
export const HIGHLIGHT_DURATION_MS = 2_000;
