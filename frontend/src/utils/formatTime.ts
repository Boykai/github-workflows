/**
 * Format a Date as a human-readable "time ago" string.
 *
 * Returns:
 * - `"just now"` for < 60 s
 * - `"Xm ago"` for < 60 min
 * - locale time string otherwise
 */
export function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diffSec < 60) return 'just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  return date.toLocaleTimeString();
}

/**
 * Format a future Date as a human-readable "time until" string.
 *
 * Returns:
 * - `"in less than a minute"` for < 60 s
 * - `"in X minutes"` for < 60 min
 * - locale time string otherwise
 */
export function formatTimeUntil(date: Date): string {
  const now = new Date();
  const diffSec = Math.floor((date.getTime() - now.getTime()) / 1000);
  if (diffSec <= 0) return 'now';
  if (diffSec < 60) return 'in less than a minute';
  const mins = Math.ceil(diffSec / 60);
  if (mins < 60) return `in ${mins} minute${mins === 1 ? '' : 's'}`;
  return `at ${date.toLocaleTimeString()}`;
}
