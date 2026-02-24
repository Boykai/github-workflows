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
