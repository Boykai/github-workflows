/**
 * Regression tests for useFileUpload.
 *
 * Bug: setTimeout in addFiles was never stored in a ref and had no cleanup,
 * causing timer leaks on unmount and stacking timers on repeated error calls.
 */

import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useFileUpload } from './useFileUpload';

// Mock the chatApi to avoid real HTTP calls
vi.mock('@/services/api', () => ({
  chatApi: {
    uploadFile: vi.fn(),
  },
}));

function makeFileList(files: File[]): FileList {
  const dt = new DataTransfer();
  files.forEach((f) => dt.items.add(f));
  return dt.files;
}

function makeOversizedFile(name: string): File {
  // 11 MB file (exceeds 10 MB limit)
  return new File([new ArrayBuffer(11 * 1024 * 1024)], name, { type: 'image/png' });
}

describe('useFileUpload — error timer cleanup', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('clears error timer on unmount to prevent state update on unmounted component', () => {
    const { result, unmount } = renderHook(() => useFileUpload());

    // Add an oversized file to trigger an error
    act(() => {
      result.current.addFiles(makeFileList([makeOversizedFile('big.png')]));
    });

    expect(result.current.errors.length).toBeGreaterThan(0);

    // Unmount before the 5-second timer fires
    unmount();

    // Advance past the timer — should not throw or warn
    act(() => {
      vi.advanceTimersByTime(6000);
    });
  });

  it('replaces previous error timer when addFiles is called again with errors', () => {
    const clearTimeoutSpy = vi.spyOn(globalThis, 'clearTimeout');
    const { result } = renderHook(() => useFileUpload());

    // First call with an error
    act(() => {
      result.current.addFiles(makeFileList([makeOversizedFile('big1.png')]));
    });
    expect(result.current.errors.length).toBeGreaterThan(0);

    // Second call with another error — should clear the first timer
    act(() => {
      result.current.addFiles(makeFileList([makeOversizedFile('big2.png')]));
    });

    // clearTimeout should have been called for the first timer
    expect(clearTimeoutSpy).toHaveBeenCalled();

    clearTimeoutSpy.mockRestore();
  });

  it('clears errors automatically after 5 seconds', () => {
    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.addFiles(makeFileList([makeOversizedFile('big.png')]));
    });
    expect(result.current.errors.length).toBeGreaterThan(0);

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.errors).toEqual([]);
  });
});
