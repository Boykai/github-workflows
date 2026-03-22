/**
 * Application-wide constants.
 *
 * Centralizes magic numbers (poll intervals, timeouts, cache durations)
 * so they are documented and easy to tune.
 */

// ============ React Query / Cache Durations ============

/** Default stale time for infrequently-changing data (5 minutes). */
export const STALE_TIME_LONG = 5 * 60 * 1000;

/** Stale time for project-list data (15 minutes). */
export const STALE_TIME_PROJECTS = 15 * 60 * 1000;

/** Stale time for moderately-changing data (1 minute). */
export const STALE_TIME_MEDIUM = 60 * 1000;

/** Stale time for frequently-changing data (60 seconds). */
export const STALE_TIME_SHORT = 60 * 1000;

// ============ Polling Intervals ============

/** Board data polling interval (60 seconds). */
export const BOARD_POLL_INTERVAL_MS = 60_000;

/** WebSocket fallback polling interval (30 seconds). */
export const WS_FALLBACK_POLL_MS = 30_000;

/** WebSocket reconnect delay after disconnect (5 seconds). */
export const WS_RECONNECT_DELAY_MS = 5_000;

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

// ============ Solune Navigation ============

import {
  LayoutDashboard,
  Kanban,
  GitBranch,
  Bot,
  Wrench,
  ListChecks,
  Settings,
  Boxes,
  Clock,
} from '@/lib/icons';
import type { NavRoute } from '@/types';

/** Sidebar navigation routes with Lucide icons. */
export const NAV_ROUTES: NavRoute[] = [
  { path: '/', label: 'App', icon: LayoutDashboard },
  { path: '/projects', label: 'Projects', icon: Kanban },
  { path: '/pipeline', label: 'Agents Pipelines', icon: GitBranch },
  { path: '/agents', label: 'Agents', icon: Bot },
  { path: '/tools', label: 'Tools', icon: Wrench },
  { path: '/chores', label: 'Chores', icon: ListChecks },
  { path: '/apps', label: 'Apps', icon: Boxes },
  { path: '/activity', label: 'Activity', icon: Clock },
  { path: '/settings', label: 'Settings', icon: Settings },
];

// ============ Priority Colors ============

/** Priority badge color mapping for IssueCard and other priority displays. */
export const PRIORITY_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  P0: {
    bg: 'bg-red-100/90 dark:bg-red-950/50',
    text: 'text-red-700 dark:text-red-300',
    label: 'Critical',
  },
  P1: {
    bg: 'bg-orange-100/90 dark:bg-orange-950/50',
    text: 'text-orange-700 dark:text-orange-300',
    label: 'High',
  },
  P2: {
    bg: 'bg-blue-100/90 dark:bg-blue-950/50',
    text: 'text-blue-700 dark:text-blue-300',
    label: 'Medium',
  },
  P3: {
    bg: 'bg-emerald-100/90 dark:bg-emerald-950/50',
    text: 'text-emerald-700 dark:text-emerald-300',
    label: 'Low',
  },
};
