import { describe, expect, it } from 'vitest';

import { ApiError } from '@/services/api';
import { extractRateLimitInfo, isRateLimitApiError } from '@/utils/rateLimit';

describe('rateLimit utils', () => {
  it('extracts rate limit info from ApiError details', () => {
    const rateLimit = { limit: 5000, remaining: 0, reset_at: 1700000000, used: 5000 };
    const error = new ApiError(429, {
      error: 'GitHub API rate limit exceeded',
      details: { rate_limit: rateLimit },
    });

    expect(extractRateLimitInfo(error)).toEqual(rateLimit);
  });

  it('returns null when the payload does not include a valid rate limit object', () => {
    const error = new ApiError(429, {
      error: 'GitHub API rate limit exceeded',
      details: { rate_limit: { remaining: 0 } },
    });

    expect(extractRateLimitInfo(error)).toBeNull();
  });

  it('treats 429 responses as rate limit errors even without structured details', () => {
    const error = new ApiError(429, { error: 'Too Many Requests' });

    expect(isRateLimitApiError(error)).toBe(true);
  });

  it('treats 403 responses as rate limit errors only when rate limit details are present', () => {
    const limited = new ApiError(403, {
      error: 'Forbidden',
      details: {
        rate_limit: { limit: 5000, remaining: 0, reset_at: 1700000000, used: 5000 },
      },
    });
    const forbidden = new ApiError(403, { error: 'Forbidden' });

    expect(isRateLimitApiError(limited)).toBe(true);
    expect(isRateLimitApiError(forbidden)).toBe(false);
  });
});
