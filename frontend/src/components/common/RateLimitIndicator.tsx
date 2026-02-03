/**
 * Rate limit indicator component.
 */

interface RateLimitIndicatorProps {
  remaining: number | null;
  total?: number;
}

export function RateLimitIndicator({ remaining, total = 4000 }: RateLimitIndicatorProps) {
  if (remaining === null) return null;

  const percentage = (remaining / total) * 100;
  const isLow = percentage < 20;
  const isCritical = percentage < 5;

  return (
    <div className={`rate-limit-indicator ${isLow ? 'low' : ''} ${isCritical ? 'critical' : ''}`}>
      <div className="rate-limit-bar">
        <div
          className="rate-limit-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="rate-limit-text">
        {remaining.toLocaleString()} / {total.toLocaleString()} API calls remaining
      </span>
      {isCritical && (
        <span className="rate-limit-warning">
          ⚠️ Rate limit nearly exhausted. Requests may be throttled.
        </span>
      )}
    </div>
  );
}
