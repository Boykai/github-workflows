import { ApiError } from '@/services/api';
import type { RateLimitInfo } from '@/types';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isRateLimitInfo(value: unknown): value is RateLimitInfo {
  return (
    isRecord(value) &&
    typeof value.limit === 'number' &&
    typeof value.remaining === 'number' &&
    typeof value.reset_at === 'number' &&
    typeof value.used === 'number'
  );
}

export function extractRateLimitInfo(error: unknown): RateLimitInfo | null {
  if (!(error instanceof ApiError)) {
    return null;
  }

  const rateLimit = error.error.details?.rate_limit;
  return isRateLimitInfo(rateLimit) ? rateLimit : null;
}

export function isRateLimitApiError(error: unknown): boolean {
  if (!(error instanceof ApiError)) {
    return false;
  }

  return error.status === 429 || (error.status === 403 && extractRateLimitInfo(error) !== null);
}
