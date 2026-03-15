/**
 * Regression tests for useMetadata hook (bug-bash).
 *
 * Covers: race condition guard — state updates must not fire after unmount.
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMetadata } from './useMetadata';

// Controllable promise for simulating slow API responses
function deferred<T>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

vi.mock('@/services/api', () => ({
  metadataApi: {
    getMetadata: vi.fn(),
    refreshMetadata: vi.fn(),
  },
}));

import { metadataApi } from '@/services/api';

const mockGetMetadata = metadataApi.getMetadata as ReturnType<typeof vi.fn>;

describe('useMetadata', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should not update state after unmount (race condition guard)', async () => {
    const { promise, resolve } = deferred<{ labels: string[] }>();
    mockGetMetadata.mockReturnValue(promise);

    // Spy on console.error to detect React state-update-after-unmount warnings
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { unmount } = renderHook(() => useMetadata('owner', 'repo'));

    // Unmount before the API call resolves
    unmount();

    // Now resolve the pending API call — state updates should be skipped
    await act(async () => {
      resolve({ labels: ['bug'] });
    });

    // React should not have logged a state-update-after-unmount warning
    const unmountWarnings = consoleErrorSpy.mock.calls.filter(
      (args) =>
        typeof args[0] === 'string' &&
        args[0].includes("Can't perform a React state update on an unmounted component")
    );
    expect(unmountWarnings).toHaveLength(0);

    consoleErrorSpy.mockRestore();
  });
});
