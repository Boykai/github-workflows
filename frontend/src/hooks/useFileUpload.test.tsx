import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useFileUpload } from './useFileUpload';

describe('useFileUpload', () => {
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  beforeEach(() => {
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: vi.fn(() => 'blob:preview'),
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
  });

  afterEach(() => {
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      writable: true,
      value: originalCreateObjectURL,
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      writable: true,
      value: originalRevokeObjectURL,
    });
  });

  it('creates and revokes object URLs for image previews', () => {
    const { result, unmount } = renderHook(() => useFileUpload());
    const imageFile = new File(['image'], 'preview.png', { type: 'image/png' });

    act(() => {
      result.current.addFiles([imageFile]);
    });

    expect(result.current.files[0]?.previewUrl).toBe('blob:preview');

    act(() => {
      result.current.removeFile(result.current.files[0]!.id);
    });

    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview');

    act(() => {
      result.current.addFiles([imageFile]);
    });

    unmount();

    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(2);
  });
});
