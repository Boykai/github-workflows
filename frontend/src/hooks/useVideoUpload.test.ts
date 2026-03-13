/**
 * Tests for useVideoUpload hook.
 */

import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useVideoUpload } from './useVideoUpload';

// Mock the video API
vi.mock('@/services/api', () => ({
  videoApi: {
    uploadVideo: vi.fn(),
  },
}));

function makeVideoFile(name: string, size = 1024): File {
  return new File([new ArrayBuffer(size)], name, { type: 'video/mp4' });
}

describe('useVideoUpload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('starts with empty state', () => {
    const { result } = renderHook(() => useVideoUpload());
    expect(result.current.files).toEqual([]);
    expect(result.current.errors).toEqual([]);
    expect(result.current.isUploading).toBe(false);
  });

  it('adds a valid video file', () => {
    const { result } = renderHook(() => useVideoUpload());
    const file = makeVideoFile('test.mp4');

    act(() => {
      result.current.addVideo(file);
    });

    expect(result.current.files).toHaveLength(1);
    expect(result.current.files[0].filename).toBe('test.mp4');
    expect(result.current.files[0].status).toBe('pending');
  });

  it('rejects unsupported format with error', () => {
    const { result } = renderHook(() => useVideoUpload());
    const file = new File([new ArrayBuffer(1024)], 'doc.pdf', { type: 'application/pdf' });

    act(() => {
      result.current.addVideo(file);
    });

    expect(result.current.files).toHaveLength(0);
    expect(result.current.errors).toHaveLength(1);
    expect(result.current.errors[0]).toContain('Unsupported format');
  });

  it('rejects empty files', () => {
    const { result } = renderHook(() => useVideoUpload());
    const file = new File([], 'empty.mp4', { type: 'video/mp4' });

    act(() => {
      result.current.addVideo(file);
    });

    expect(result.current.files).toHaveLength(0);
    expect(result.current.errors[0]).toContain('empty');
  });

  it('clears errors after 5 seconds', () => {
    const { result } = renderHook(() => useVideoUpload());
    const file = new File([], 'empty.mp4', { type: 'video/mp4' });

    act(() => {
      result.current.addVideo(file);
    });

    expect(result.current.errors.length).toBeGreaterThan(0);

    act(() => {
      vi.advanceTimersByTime(5000);
    });

    expect(result.current.errors).toEqual([]);
  });

  it('removes a video file by id', () => {
    const { result } = renderHook(() => useVideoUpload());
    const file = makeVideoFile('removable.mp4');

    act(() => {
      result.current.addVideo(file);
    });

    const fileId = result.current.files[0].id;

    act(() => {
      result.current.removeVideo(fileId);
    });

    expect(result.current.files).toHaveLength(0);
  });

  it('clears all files and errors', () => {
    const { result } = renderHook(() => useVideoUpload());
    const file = makeVideoFile('clear.mp4');

    act(() => {
      result.current.addVideo(file);
    });

    act(() => {
      result.current.clearAll();
    });

    expect(result.current.files).toHaveLength(0);
    expect(result.current.errors).toEqual([]);
  });

  it('clears error timer on unmount', () => {
    const { result, unmount } = renderHook(() => useVideoUpload());
    const emptyFile = new File([], 'empty.mp4', { type: 'video/mp4' });

    act(() => {
      result.current.addVideo(emptyFile);
    });

    unmount();

    // Advance past the timer — should not throw or warn
    act(() => {
      vi.advanceTimersByTime(6000);
    });
  });

  it('accepts all supported video extensions', () => {
    const { result } = renderHook(() => useVideoUpload());
    const extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];

    for (const ext of extensions) {
      act(() => {
        result.current.addVideo(makeVideoFile(`video${ext}`));
      });
    }

    expect(result.current.files).toHaveLength(5);
    expect(result.current.errors).toEqual([]);
  });
});
