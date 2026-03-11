export const MS_PER_HOUR = 60 * 60 * 1000;
export const MS_PER_DAY = 24 * MS_PER_HOUR;

/** Convert days to milliseconds. */
export function daysToMs(days: number): number {
  return days * MS_PER_DAY;
}

/** Format remaining ms as "Xd Yh remaining", "Xh remaining", or "Due now". */
export function formatMsRemaining(remainingMs: number): string {
  if (remainingMs <= 0) return 'Due now';
  const days = Math.floor(remainingMs / MS_PER_DAY);
  const hours = Math.floor((remainingMs % MS_PER_DAY) / MS_PER_HOUR);
  if (days > 0) return `${days}d ${hours}h remaining`;
  return `${hours}h remaining`;
}

/** Format elapsed ms as "Run Xd ago", "Run Xh ago", or "Run just now". */
export function formatMsAgo(elapsedMs: number): string {
  const hoursAgo = Math.floor(elapsedMs / MS_PER_HOUR);
  const daysAgo = Math.floor(hoursAgo / 24);
  if (daysAgo > 0) return `Run ${daysAgo}d ago`;
  if (hoursAgo > 0) return `Run ${hoursAgo}h ago`;
  return 'Run just now';
}

/** How many issues remain before a count-based schedule triggers. */
export function computeCountRemaining(
  scheduleValue: number,
  parentIssueCount: number,
  lastTriggeredCount: number,
): number {
  const issuesSince = parentIssueCount - lastTriggeredCount;
  return Math.max(0, scheduleValue - issuesSince);
}

/** Remaining ms and progress fraction for a time-based schedule. */
export function computeTimeProgress(
  baseDate: string,
  thresholdDays: number,
): { remainingMs: number; progress: number } {
  const thresholdMs = daysToMs(thresholdDays);
  const elapsedMs = Math.max(0, Date.now() - new Date(baseDate).getTime());
  const remainingMs = Math.max(0, thresholdMs - elapsedMs);
  const progress = thresholdMs > 0 ? Math.min(1, elapsedMs / thresholdMs) : 0;
  return { remainingMs, progress };
}

/** Progress fraction for a count-based schedule. */
export function computeCountProgress(scheduleValue: number, remaining: number): number {
  return scheduleValue > 0 ? (scheduleValue - remaining) / scheduleValue : 0;
}
