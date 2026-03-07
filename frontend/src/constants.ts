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

import { LayoutDashboard, Kanban, GitBranch, Bot, ListChecks, Settings } from 'lucide-react';
import type { NavRoute } from '@/types';

/** Sidebar navigation routes with Lucide icons. */
export const NAV_ROUTES: NavRoute[] = [
  { path: '/', label: 'App', icon: LayoutDashboard },
  { path: '/projects', label: 'Projects', icon: Kanban },
  { path: '/pipeline', label: 'Agents Pipeline', icon: GitBranch },
  { path: '/agents', label: 'Agents', icon: Bot },
  { path: '/chores', label: 'Chores', icon: ListChecks },
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

// ============ Status Colors ============

/** Centralized color classes for operational states used across multiple components. */
export const STATUS_COLORS = {
  success: {
    bg: 'bg-green-500/10 dark:bg-green-500/15',
    text: 'text-green-600 dark:text-green-400',
    border: 'border-green-500/30 dark:border-green-500/20',
    dot: 'bg-green-500',
  },
  warning: {
    bg: 'bg-yellow-500/10 dark:bg-yellow-500/15',
    text: 'text-yellow-600 dark:text-yellow-400',
    border: 'border-yellow-500/30 dark:border-yellow-500/20',
    dot: 'bg-yellow-500',
  },
  error: {
    bg: 'bg-red-500/10 dark:bg-red-500/15',
    text: 'text-red-600 dark:text-red-400',
    border: 'border-red-500/30 dark:border-red-500/20',
    dot: 'bg-red-500',
  },
  info: {
    bg: 'bg-blue-500/10 dark:bg-blue-500/15',
    text: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-500/30 dark:border-blue-500/20',
    dot: 'bg-blue-500',
  },
  neutral: {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-border',
    dot: 'bg-muted-foreground',
  },
} as const;

// ============ Agent Source Colors ============

/** Color mappings for agent source types. */
export const AGENT_SOURCE_COLORS: Record<string, { bg: string; text: string }> = {
  builtin: {
    bg: 'bg-blue-500/10 dark:bg-blue-500/15',
    text: 'text-blue-600 dark:text-blue-400',
  },
  repository: {
    bg: 'bg-green-500/10 dark:bg-green-500/15',
    text: 'text-green-600 dark:text-green-400',
  },
  custom: {
    bg: 'bg-purple-500/10 dark:bg-purple-500/15',
    text: 'text-purple-600 dark:text-purple-400',
  },
  community: {
    bg: 'bg-emerald-500/10 dark:bg-emerald-500/15',
    text: 'text-emerald-600 dark:text-emerald-400',
  },
};
