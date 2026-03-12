/**
 * Unit tests for useVoiceInput hook — browser detection, state management,
 * and error handling for the Web Speech API integration.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVoiceInput } from './useVoiceInput';

// Helper to flush microtasks (for promise chains inside the hook)
function flushPromises() {
  return new Promise<void>((resolve) => setTimeout(resolve, 0));
}

// Helper to create a mock SpeechRecognition constructor.
// Returns { Ctor, getInstance } — Ctor is the constructor mock,
// getInstance returns the last-created instance for handler invocation.
function createMockSpeechRecognition() {
  const instances: Record<string, unknown>[] = [];
  const Ctor = vi.fn().mockImplementation(function (this: Record<string, unknown>) {
    this.continuous = false;
    this.interimResults = false;
    this.lang = '';
    this.start = vi.fn();
    this.stop = vi.fn();
    this.abort = vi.fn();
    this.onresult = null;
    this.onerror = null;
    this.onend = null;
    instances.push(this);
  });
  return { Ctor, getInstance: () => instances[instances.length - 1] };
}

// Simple constructor mock for detection-only tests (no instance tracking needed)
function createSimpleSpeechRecognition() {
  return createMockSpeechRecognition().Ctor;
}

function mockMediaDevices(overrides: Partial<MediaDevices> = {}) {
  Object.defineProperty(navigator, 'mediaDevices', {
    value: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop: vi.fn() }] }), ...overrides },
    writable: true,
    configurable: true,
  });
}

describe('useVoiceInput', () => {
  let originalSpeechRecognition: unknown;
  let originalWebkitSpeechRecognition: unknown;
  let originalMediaDevices: unknown;

  beforeEach(() => {
    originalSpeechRecognition = (window as Record<string, unknown>).SpeechRecognition;
    originalWebkitSpeechRecognition = (window as Record<string, unknown>).webkitSpeechRecognition;
    originalMediaDevices = navigator.mediaDevices;
  });

  afterEach(() => {
    (window as Record<string, unknown>).SpeechRecognition = originalSpeechRecognition;
    (window as Record<string, unknown>).webkitSpeechRecognition = originalWebkitSpeechRecognition;
    Object.defineProperty(navigator, 'mediaDevices', {
      value: originalMediaDevices,
      writable: true,
      configurable: true,
    });
  });

  // ── Browser detection ──

  describe('browser support detection', () => {
    it('reports supported when SpeechRecognition is available (Firefox)', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      delete (window as Record<string, unknown>).webkitSpeechRecognition;

      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.isSupported).toBe(true);
    });

    it('reports supported when webkitSpeechRecognition is available (Chrome)', () => {
      delete (window as Record<string, unknown>).SpeechRecognition;
      (window as Record<string, unknown>).webkitSpeechRecognition = createSimpleSpeechRecognition();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.isSupported).toBe(true);
    });

    it('reports supported when both SpeechRecognition and webkitSpeechRecognition exist', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      (window as Record<string, unknown>).webkitSpeechRecognition = createSimpleSpeechRecognition();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.isSupported).toBe(true);
    });

    it('reports unsupported when neither API is available', () => {
      delete (window as Record<string, unknown>).SpeechRecognition;
      delete (window as Record<string, unknown>).webkitSpeechRecognition;

      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.isSupported).toBe(false);
    });

    it('prefers SpeechRecognition over webkitSpeechRecognition when both exist', async () => {
      const { Ctor: unprefixedCtor } = createMockSpeechRecognition();
      const { Ctor: webkitCtor } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = unprefixedCtor;
      (window as Record<string, unknown>).webkitSpeechRecognition = webkitCtor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      expect(unprefixedCtor).toHaveBeenCalled();
      expect(webkitCtor).not.toHaveBeenCalled();
    });
  });

  // ── Initial state ──

  describe('initial state', () => {
    it('starts with isRecording false', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.isRecording).toBe(false);
    });

    it('starts with empty interimTranscript', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.interimTranscript).toBe('');
    });

    it('starts with null error', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput(vi.fn()));
      expect(result.current.error).toBeNull();
    });
  });

  // ── startRecording ──

  describe('startRecording', () => {
    it('sets error when speech recognition is not supported', () => {
      delete (window as Record<string, unknown>).SpeechRecognition;
      delete (window as Record<string, unknown>).webkitSpeechRecognition;

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      act(() => {
        result.current.startRecording();
      });

      expect(result.current.error).toBe('Voice input is not supported in this browser.');
    });

    it('sets error when mediaDevices is not available', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      Object.defineProperty(navigator, 'mediaDevices', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      act(() => {
        result.current.startRecording();
      });

      expect(result.current.error).toBe('Microphone access is not available in this browser.');
    });

    it('requests microphone permission and starts recognition on success', async () => {
      const { Ctor } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true });
      expect(result.current.isRecording).toBe(true);
    });

    it('configures recognition with continuous, interimResults, and lang', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      const instance = getInstance()!;
      expect(instance.continuous).toBe(true);
      expect(instance.interimResults).toBe(true);
      expect(instance.lang).toBe('en-US');
    });

    it('stops stream tracks immediately after getUserMedia succeeds', async () => {
      const stopFn = vi.fn();
      const { Ctor } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices({
        getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop: stopFn }] }),
      } as unknown as MediaDevices);

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      expect(stopFn).toHaveBeenCalled();
    });

    it('clears previous error when starting a new recording', async () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      Object.defineProperty(navigator, 'mediaDevices', {
        value: undefined,
        writable: true,
        configurable: true,
      });

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      // Trigger an error first
      act(() => {
        result.current.startRecording();
      });
      expect(result.current.error).toBe('Microphone access is not available in this browser.');

      // Now restore mediaDevices and try again
      const { Ctor } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      // Error should be cleared even though we're in the same hook instance
      // Note: The error from the first attempt gets cleared by setError(null) at start
      expect(result.current.error).toBeNull();
    });

    it('sets permission error when getUserMedia is denied', async () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();
      mockMediaDevices({
        getUserMedia: vi.fn().mockRejectedValue(new DOMException('Permission denied', 'NotAllowedError')),
      } as unknown as MediaDevices);

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      expect(result.current.error).toBe(
        'Microphone access is required for voice input. Please allow microphone access in your browser settings.'
      );
      expect(result.current.isRecording).toBe(false);
    });
  });

  // ── stopRecording ──

  describe('stopRecording', () => {
    it('stops recognition and resets isRecording', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      expect(result.current.isRecording).toBe(true);

      act(() => {
        result.current.stopRecording();
      });

      expect(getInstance()!.stop).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(false);
    });

    it('is a no-op when not currently recording', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      // Should not throw
      act(() => {
        result.current.stopRecording();
      });

      expect(result.current.isRecording).toBe(false);
    });
  });

  // ── cancelRecording ──

  describe('cancelRecording', () => {
    it('aborts recognition and clears interim transcript', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        result.current.cancelRecording();
      });

      expect(getInstance()!.abort).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(false);
      expect(result.current.interimTranscript).toBe('');
    });

    it('is a no-op when not currently recording', () => {
      (window as Record<string, unknown>).SpeechRecognition = createSimpleSpeechRecognition();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      // Should not throw
      act(() => {
        result.current.cancelRecording();
      });

      expect(result.current.isRecording).toBe(false);
      expect(result.current.interimTranscript).toBe('');
    });
  });

  // ── Error handling ──

  describe('error handling', () => {
    it('sets permission error on not-allowed recognition error', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const instance = getInstance()!;
        (instance.onerror as (event: { error: string }) => void)({ error: 'not-allowed' });
      });

      expect(result.current.error).toBe(
        'Microphone access is required for voice input. Please allow microphone access in your browser settings.'
      );
      expect(result.current.isRecording).toBe(false);
    });

    it('sets permission error on permission-denied recognition error', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const instance = getInstance()!;
        (instance.onerror as (event: { error: string }) => void)({ error: 'permission-denied' });
      });

      expect(result.current.error).toBe(
        'Microphone access is required for voice input. Please allow microphone access in your browser settings.'
      );
      expect(result.current.isRecording).toBe(false);
    });

    it('sets generic error on non-abort recognition error', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const instance = getInstance()!;
        (instance.onerror as (event: { error: string }) => void)({ error: 'network' });
      });

      expect(result.current.error).toBe('Voice input error: network');
    });

    it('ignores aborted recognition error', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const instance = getInstance()!;
        (instance.onerror as (event: { error: string }) => void)({ error: 'aborted' });
      });

      expect(result.current.error).toBeNull();
    });

    it('resets isRecording and interimTranscript when onend fires', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      expect(result.current.isRecording).toBe(true);

      // Simulate an interim result to verify it gets cleared
      act(() => {
        const mockEvent = {
          resultIndex: 0,
          results: { length: 1, 0: { 0: { transcript: 'partial' }, isFinal: false, length: 1 } },
        };
        const instance = getInstance()!;
        (instance.onresult as (event: unknown) => void)(mockEvent);
      });

      expect(result.current.interimTranscript).toBe('partial');

      // Trigger onend
      act(() => {
        const instance = getInstance()!;
        (instance.onend as () => void)();
      });

      expect(result.current.isRecording).toBe(false);
      expect(result.current.interimTranscript).toBe('');
    });
  });

  // ── Transcription ──

  describe('transcription', () => {
    it('calls onTranscript with final transcript text', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const onTranscript = vi.fn();
      const { result } = renderHook(() => useVoiceInput(onTranscript));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const mockEvent = {
          resultIndex: 0,
          results: { length: 1, 0: { 0: { transcript: 'hello world' }, isFinal: true, length: 1 } },
        };
        const instance = getInstance()!;
        (instance.onresult as (event: unknown) => void)(mockEvent);
      });

      expect(onTranscript).toHaveBeenCalledWith('hello world');
    });

    it('updates interimTranscript for non-final results', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const mockEvent = {
          resultIndex: 0,
          results: { length: 1, 0: { 0: { transcript: 'hello' }, isFinal: false, length: 1 } },
        };
        const instance = getInstance()!;
        (instance.onresult as (event: unknown) => void)(mockEvent);
      });

      expect(result.current.interimTranscript).toBe('hello');
    });

    it('handles multiple results in a single onresult event', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const onTranscript = vi.fn();
      const { result } = renderHook(() => useVoiceInput(onTranscript));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const mockEvent = {
          resultIndex: 0,
          results: {
            length: 3,
            0: { 0: { transcript: 'hello ' }, isFinal: true, length: 1 },
            1: { 0: { transcript: 'world ' }, isFinal: true, length: 1 },
            2: { 0: { transcript: 'partial' }, isFinal: false, length: 1 },
          },
        };
        const instance = getInstance()!;
        (instance.onresult as (event: unknown) => void)(mockEvent);
      });

      expect(onTranscript).toHaveBeenCalledWith('hello world ');
      expect(result.current.interimTranscript).toBe('partial');
    });

    it('does not call onTranscript when there are only interim results', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const onTranscript = vi.fn();
      const { result } = renderHook(() => useVoiceInput(onTranscript));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      act(() => {
        const mockEvent = {
          resultIndex: 0,
          results: { length: 1, 0: { 0: { transcript: 'typing...' }, isFinal: false, length: 1 } },
        };
        const instance = getInstance()!;
        (instance.onresult as (event: unknown) => void)(mockEvent);
      });

      expect(onTranscript).not.toHaveBeenCalled();
      expect(result.current.interimTranscript).toBe('typing...');
    });
  });

  // ── Cleanup ──

  describe('cleanup', () => {
    it('aborts recognition on unmount', async () => {
      const { Ctor, getInstance } = createMockSpeechRecognition();
      (window as Record<string, unknown>).SpeechRecognition = Ctor;
      mockMediaDevices();

      const { result, unmount } = renderHook(() => useVoiceInput(vi.fn()));

      await act(async () => {
        result.current.startRecording();
        await flushPromises();
      });

      unmount();

      expect(getInstance()!.abort).toHaveBeenCalled();
    });
  });
});
