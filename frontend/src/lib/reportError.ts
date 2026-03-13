/**
 * Report frontend errors to the backend for server-side logging.
 * Fire-and-forget — failures are silently ignored.
 */
export function reportError(error: { message: string; stack?: string }): void {
  try {
    const payload = {
      message: (error.message || 'Unknown error').slice(0, 2_000),
      stack: (error.stack || '').slice(0, 10_000),
      url: window.location.pathname,
      timestamp: new Date().toISOString(),
      user_agent: navigator.userAgent,
    };
    // Fire-and-forget: use sendBeacon for reliability, fall back to fetch
    const body = JSON.stringify(payload);
    if (!navigator.sendBeacon?.('/api/v1/errors', new Blob([body], { type: 'application/json' }))) {
      fetch('/api/v1/errors', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true }).catch(() => {});
    }
  } catch {
    // Never throw from error reporting
  }
}
