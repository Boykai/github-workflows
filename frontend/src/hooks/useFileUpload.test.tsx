import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useFileUpload } from './useFileUpload';
import { chatApi } from '@/services/api';

vi.mock('@/services/api', () => ({
  chatApi: {
    uploadFile: vi.fn(),
  },
}));

function createFileList(files: File[]): FileList {
  return {
    ...files,
    length: files.length,
    item: (index: number) => files[index] ?? null,
  } as FileList;
}

describe('useFileUpload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('clears scheduled validation timers on unmount', () => {
    const clearTimeoutSpy = vi.spyOn(window, 'clearTimeout');
    const { result, unmount } = renderHook(() => useFileUpload());

    act(() => {
      result.current.addFiles(
        createFileList([new File(['bad'], 'script.exe', { type: 'application/octet-stream' })])
      );
    });

    expect(result.current.errors).toHaveLength(1);

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it('returns upload errors without discarding failed files', async () => {
    vi.mocked(chatApi.uploadFile).mockRejectedValue(new Error('Upload failed'));
    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.addFiles(
        createFileList([new File(['hello'], 'notes.txt', { type: 'text/plain' })])
      );
    });

    let uploadResult: Awaited<ReturnType<typeof result.current.uploadAll>> | undefined;
    await act(async () => {
      uploadResult = await result.current.uploadAll();
    });

    expect(uploadResult).toEqual({ urls: [], hasErrors: true });
    expect(result.current.files).toHaveLength(1);
    expect(result.current.files[0]?.status).toBe('error');
    expect(result.current.errors).toContain(
      'One or more files failed to upload. Remove the failed file and try again.'
    );

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(result.current.errors).toEqual([]);
  });
});