/**
 * Unit tests for errorHints utility.
 */
import { describe, it, expect } from 'vitest';
import { getErrorHint } from './errorHints';

/** Helper to create an error-like object with a status code. */
function makeStatusError(status: number, message = 'Error'): { status: number; message: string } {
  return { status, message };
}

describe('getErrorHint', () => {
  it('returns auth hint for 401', () => {
    const hint = getErrorHint(makeStatusError(401));
    expect(hint.title).toBe('Authentication required');
    expect(hint.hint).toContain('session may have expired');
    expect(hint.action).toEqual({ label: 'Go to Login', href: '/login' });
  });

  it('returns access denied hint for 403', () => {
    const hint = getErrorHint(makeStatusError(403));
    expect(hint.title).toBe('Access denied');
    expect(hint.hint).toContain('permission');
  });

  it('returns not found hint for 404', () => {
    const hint = getErrorHint(makeStatusError(404));
    expect(hint.title).toBe('Not found');
    expect(hint.hint).toContain('moved or deleted');
  });

  it('returns validation hint for 422', () => {
    const hint = getErrorHint(makeStatusError(422));
    expect(hint.title).toBe('Validation error');
    expect(hint.hint).toContain('review your input');
  });

  it('returns rate limit hint for 429', () => {
    const hint = getErrorHint(makeStatusError(429));
    expect(hint.title).toBe('Rate limit exceeded');
    expect(hint.hint).toContain('polling frequency');
    expect(hint.action).toEqual({ label: 'Open Settings', href: '/settings' });
  });

  it('returns server error hint for 500', () => {
    const hint = getErrorHint(makeStatusError(500));
    expect(hint.title).toBe('Server error');
    expect(hint.hint).toContain('server');
  });

  it('returns server error hint for 502', () => {
    const hint = getErrorHint(makeStatusError(502));
    expect(hint.title).toBe('Server error');
  });

  it('returns connection error hint for TypeError', () => {
    const hint = getErrorHint(new TypeError('Failed to fetch'));
    expect(hint.title).toBe('Connection error');
    expect(hint.hint).toContain('network connection');
  });

  it('returns connection error for network failure message', () => {
    const hint = getErrorHint({ message: 'network error' });
    expect(hint.title).toBe('Connection error');
  });

  it('returns connection error for CORS failure message', () => {
    const hint = getErrorHint({ message: 'CORS policy blocked' });
    expect(hint.title).toBe('Connection error');
  });

  it('returns fallback hint for unknown error', () => {
    const hint = getErrorHint(new Error('Something else'));
    expect(hint.title).toBe('Unexpected error');
    expect(hint.hint).toContain('try again');
  });

  it('returns fallback hint for null', () => {
    const hint = getErrorHint(null);
    expect(hint.title).toBe('Unexpected error');
  });

  it('returns fallback hint for undefined', () => {
    const hint = getErrorHint(undefined);
    expect(hint.title).toBe('Unexpected error');
  });

  it('classifies by status code on plain object with status field', () => {
    const hint = getErrorHint({ status: 401, message: 'Auth failed' });
    expect(hint.title).toBe('Authentication required');
  });

  it('does not have action for 403 errors', () => {
    const hint = getErrorHint(makeStatusError(403));
    expect(hint.action).toBeUndefined();
  });

  it('does not have action for 404 errors', () => {
    const hint = getErrorHint(makeStatusError(404));
    expect(hint.action).toBeUndefined();
  });
});
