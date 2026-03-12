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
