/**
 * Error classification and recovery hint generation.
 *
 * Classifies errors by HTTP status code (never by parsing message strings)
 * and returns a structured hint object with actionable recovery suggestions.
 *
 * Error hint strings are hardcoded English — i18n is deferred as a broader
 * cross-cutting concern.
 */

export interface ErrorHint {
  title: string;
  hint: string;
  action?: { label: string; href: string };
}

/**
 * Extract an HTTP status code from an error, if available.
 * Uses duck-typing (checks for a numeric `status` property) rather than
 * importing `ApiError` to avoid test-mock conflicts.
 */
function getStatusCode(error: unknown): number | null {
  if (
    error != null &&
    typeof error === 'object' &&
    'status' in error &&
    typeof (error as Record<string, unknown>).status === 'number'
  ) {
    return (error as Record<string, unknown>).status as number;
  }
  return null;
}

/**
 * Detect whether the error is a network / CORS / fetch failure
 * (i.e. no HTTP status code was received at all).
 */
function isNetworkError(error: unknown): boolean {
  if (error instanceof TypeError) return true;
  if (
    error != null &&
    typeof error === 'object' &&
    'message' in error &&
    typeof (error as Record<string, unknown>).message === 'string'
  ) {
    const msg = ((error as Record<string, unknown>).message as string).toLowerCase();
    return msg.includes('failed to fetch') || msg.includes('network') || msg.includes('cors');
  }
  return false;
}

const FALLBACK_HINT: ErrorHint = {
  title: 'Unexpected error',
  hint: 'An unexpected error occurred — please try again or contact support if the issue persists.',
};

/**
 * Classify an error and return a structured recovery hint.
 *
 * Classification is based solely on HTTP status codes to stay robust across
 * API changes.  Network / CORS failures (no status code) are detected via
 * the error type (`TypeError` or fetch-failure messages).
 */
export function getErrorHint(error: unknown): ErrorHint {
  if (error == null) return FALLBACK_HINT;

  const status = getStatusCode(error);

  if (status !== null) {
    if (status === 401) {
      return {
        title: 'Authentication required',
        hint: 'Your session may have expired — try logging out and back in.',
        action: { label: 'Go to Login', href: '/login' },
      };
    }
    if (status === 403) {
      return {
        title: 'Access denied',
        hint: 'You may not have permission to access this resource. Check your GitHub permissions or ask your organization admin.',
      };
    }
    if (status === 404) {
      return {
        title: 'Not found',
        hint: 'The requested resource could not be found — it may have been moved or deleted.',
      };
    }
    if (status === 422) {
      return {
        title: 'Validation error',
        hint: 'The submitted data could not be processed — review your input and try again.',
      };
    }
    if (status === 429) {
      return {
        title: 'Rate limit exceeded',
        hint: 'Too many requests — reduce polling frequency in Settings or wait for the rate limit to reset.',
        action: { label: 'Open Settings', href: '/settings' },
      };
    }
    if (status >= 500) {
      return {
        title: 'Server error',
        hint: 'Something went wrong on the server — wait a moment and try again, or contact support if the issue persists.',
      };
    }
  }

  if (isNetworkError(error)) {
    return {
      title: 'Connection error',
      hint: 'Unable to reach the server — check your network connection and try again.',
    };
  }

  return FALLBACK_HINT;
}
