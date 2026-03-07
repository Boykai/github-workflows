import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useVoiceInput } from './useVoiceInput';

describe('useVoiceInput', () => {
  it('reports unsupported browsers before recording starts', () => {
    const { result } = renderHook(() => useVoiceInput(() => {}));

    expect(result.current.isSupported).toBe(false);

    act(() => {
      result.current.startRecording();
    });

    expect(result.current.error).toBe('Voice input is not supported in this browser.');
    expect(result.current.isRecording).toBe(false);
  });
});