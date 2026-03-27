/**
 * projectBoardUtils — Pure helper functions for the Projects page.
 *
 * Extracted from ProjectsPage to keep the page ≤ 250 lines (FR-001).
 */

import type { RateLimitInfo } from '@/types';

// ── Rate limit state ──

export interface RateLimitState {
  effectiveRateLimitInfo: RateLimitInfo | null;
  hasActiveRateLimitError: boolean;
  showRateLimitBanner: boolean;
  rateLimitRetryAfter: Date | undefined;
}

export function computeRateLimitState({
  projectsError,
  boardError,
  refreshError,
  rateLimitInfo,
  projectsRateLimitInfo,
  isRateLimitApiError,
  extractRateLimitInfo,
}: {
  projectsError: Error | null;
  boardError: Error | null;
  refreshError: { type?: string; rateLimitInfo?: RateLimitInfo; retryAfter?: Date } | null;
  rateLimitInfo: RateLimitInfo | null | undefined;
  projectsRateLimitInfo: RateLimitInfo | null | undefined;
  isRateLimitApiError: (err: unknown) => boolean;
  extractRateLimitInfo: (err: unknown) => RateLimitInfo | null;
}): RateLimitState {
  const projectsRateLimitError = isRateLimitApiError(projectsError);
  const boardRateLimitError = isRateLimitApiError(boardError);
  const refreshRateLimitError = refreshError?.type === 'rate_limit';
  const projectsRateLimitDetails = extractRateLimitInfo(projectsError);
  const boardRateLimitDetails = extractRateLimitInfo(boardError);

  const effectiveRateLimitInfo =
    rateLimitInfo ??
    projectsRateLimitInfo ??
    refreshError?.rateLimitInfo ??
    boardRateLimitDetails ??
    projectsRateLimitDetails ??
    null;

  const hasActiveRateLimitError =
    refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  const showRateLimitBanner =
    refreshRateLimitError || boardRateLimitError || projectsRateLimitError;

  const rateLimitRetryAfter =
    refreshError?.retryAfter ??
    (effectiveRateLimitInfo ? new Date(effectiveRateLimitInfo.reset_at * 1000) : undefined);

  return { effectiveRateLimitInfo, hasActiveRateLimitError, showRateLimitBanner, rateLimitRetryAfter };
}

// ── Sync status display ──

type SyncStatus = 'connected' | 'polling' | 'connecting' | 'disconnected';

const SYNC_LABELS: Record<SyncStatus, string> = {
  connected: 'Live sync',
  polling: 'Polling',
  connecting: 'Connecting',
  disconnected: 'Offline',
};

const SYNC_TONE_CLASSES: Record<SyncStatus, string> = {
  connected: 'bg-[hsl(var(--sync-connected))]',
  polling: 'bg-[hsl(var(--sync-polling))]',
  connecting: 'bg-[hsl(var(--sync-connecting))]',
  disconnected: 'bg-[hsl(var(--sync-disconnected))]',
};

export function getSyncStatusLabel(status: SyncStatus): string {
  return SYNC_LABELS[status] ?? 'Offline';
}

export function getSyncStatusToneClass(status: SyncStatus): string {
  return SYNC_TONE_CLASSES[status] ?? SYNC_TONE_CLASSES.disconnected;
}
