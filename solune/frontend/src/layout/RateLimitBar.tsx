/**
 * RateLimitBar — GitHub API rate limit health bar for the global TopBar.
 *
 * Reads shared rate limit state from RateLimitContext and renders a compact
 * pill with a colour-coded fill bar and remaining-quota label. Returns null
 * until the first rate limit snapshot is received (e.g. on the first project
 * board load).
 */

import { useRateLimitStatus } from '@/context/RateLimitContext';
import { formatTimeUntil } from '@/utils/formatTime';
import { cn } from '@/lib/utils';

function getRateLimitUsagePercent(limit?: number, remaining?: number): number {
  if (!limit || limit <= 0 || remaining === undefined) return 0;
  const used = Math.max(0, limit - remaining);
  return Math.min(100, Math.max(0, Math.round((used / limit) * 100)));
}

function getRateLimitFillClass(usagePercent: number): string {
  if (usagePercent >= 90) return 'bg-destructive shadow-[0_0_16px_hsl(var(--destructive)/0.45)]';
  if (usagePercent >= 70) return 'bg-accent shadow-[0_0_14px_hsl(var(--gold)/0.35)]';
  return 'bg-primary shadow-[0_0_14px_hsl(var(--primary)/0.28)]';
}

export function RateLimitBar() {
  const { rateLimitState } = useRateLimitStatus();
  const { info, hasError } = rateLimitState;

  if (!info && !hasError) return null;

  const usagePercent =
    getRateLimitUsagePercent(info?.limit, info?.remaining) || (hasError ? 100 : 0);

  const label = info
    ? `${info.remaining}/${info.limit} remaining`
    : hasError
      ? 'Limit reached'
      : null;

  const tooltip = info
    ? `GitHub API usage: ${info.used}/${info.limit} used. Resets ${formatTimeUntil(new Date(info.reset_at * 1000))}.`
    : hasError
      ? 'GitHub API rate limit reached. Retry after the reset window.'
      : null;

  return (
    <div
      className="hidden items-center gap-2 rounded-full border border-border/70 bg-background/58 px-3 py-2 backdrop-blur-sm md:flex"
      title={tooltip ?? undefined}
      aria-label="GitHub API rate limit"
    >
      <span className="text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground/80">
        GitHub API
      </span>
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted/70">
        <div
          className={cn('h-full rounded-full transition-all duration-300', getRateLimitFillClass(usagePercent))}
          style={{ width: `${usagePercent}%` }}
        />
      </div>
      <span
        className={cn('text-[11px]', hasError ? 'font-medium text-destructive' : 'text-muted-foreground')}
      >
        {label}
      </span>
    </div>
  );
}
