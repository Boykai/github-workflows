/**
 * Tests for useChatHistory hook.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatHistory, CHAT_HISTORY_MAX_ENTRIES } from './useChatHistory';
import * as storage from '@/utils/chatHistoryStorage';

vi.mock('@/utils/chatHistoryStorage', () => ({
  CHAT_HISTORY_STORAGE_KEY: 'chat-message-history',
  loadHistory: vi.fn(() => []),
  saveHistory: vi.fn(),
  clearStoredHistory: vi.fn(),
}));

function createKeyEvent(key: string, overrides: Partial<React.KeyboardEvent<HTMLTextAreaElement>> = {}) {
  return {
    key,
    preventDefault: vi.fn(),
    currentTarget: {
      selectionStart: 0,
      selectionEnd: 0,
      ...overrides.currentTarget,
    },
    ...overrides,
  } as unknown as React.KeyboardEvent<HTMLTextAreaElement>;
}

describe('useChatHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(storage.loadHistory).mockReturnValue([]);
  });

  describe('addToHistory', () => {
    it('adds a message to history', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.addToHistory('hello');
      });

      expect(result.current.history).toEqual(['hello']);
      expect(storage.saveHistory).toHaveBeenCalledWith(['hello']);
    });

    it('trims whitespace from messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.addToHistory('  hello  ');
      });

      expect(result.current.history).toEqual(['hello']);
    });

    it('rejects empty and whitespace-only messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.addToHistory('');
        result.current.addToHistory('   ');
      });

      expect(result.current.history).toEqual([]);
      expect(storage.saveHistory).not.toHaveBeenCalled();
    });

    it('skips consecutive duplicate messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.addToHistory('hello');
      });
      act(() => {
        result.current.addToHistory('hello');
      });

      expect(result.current.history).toEqual(['hello']);
    });

    it('allows non-consecutive duplicate messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.addToHistory('hello');
      });
      act(() => {
        result.current.addToHistory('world');
      });
      act(() => {
        result.current.addToHistory('hello');
      });

      expect(result.current.history).toEqual(['hello', 'world', 'hello']);
    });

    it('enforces max cap by removing oldest entries', () => {
      const initial = Array.from({ length: CHAT_HISTORY_MAX_ENTRIES }, (_, i) => `msg-${i}`);
      vi.mocked(storage.loadHistory).mockReturnValue(initial);
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.addToHistory('new-msg');
      });

      expect(result.current.history).toHaveLength(CHAT_HISTORY_MAX_ENTRIES);
      expect(result.current.history[0]).toBe('msg-1');
      expect(result.current.history[CHAT_HISTORY_MAX_ENTRIES - 1]).toBe('new-msg');
    });
  });

  describe('handleHistoryNavigation - Up Arrow', () => {
    it('returns false when history is empty', () => {
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();
      const e = createKeyEvent('ArrowUp');

      let consumed: boolean;
      act(() => {
        consumed = result.current.handleHistoryNavigation(e, '', setInput);
      });

      expect(consumed!).toBe(false);
      expect(setInput).not.toHaveBeenCalled();
      expect(e.preventDefault).not.toHaveBeenCalled();
    });

    it('loads newest history entry on first Up press', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1', 'msg2', 'msg3']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();
      const e = createKeyEvent('ArrowUp');

      act(() => {
        result.current.handleHistoryNavigation(e, 'draft text', setInput);
      });

      expect(setInput).toHaveBeenCalledWith('msg3');
      expect(e.preventDefault).toHaveBeenCalled();
      expect(result.current.isNavigating).toBe(true);
    });

    it('loads older entries on subsequent Up presses', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1', 'msg2', 'msg3']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();

      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), '', setInput);
      });
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), 'msg3', setInput);
      });

      expect(setInput).toHaveBeenLastCalledWith('msg2');
    });

    it('stops at oldest entry without wrap-around', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();

      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), '', setInput);
      });

      const e2 = createKeyEvent('ArrowUp');
      let consumed: boolean;
      act(() => {
        consumed = result.current.handleHistoryNavigation(e2, 'msg1', setInput);
      });

      expect(consumed!).toBe(false);
    });

    it('does not navigate when cursor is not on first line of multi-line input', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();
      const e = createKeyEvent('ArrowUp', {
        currentTarget: { selectionStart: 10, selectionEnd: 10 } as HTMLTextAreaElement,
      });

      let consumed: boolean;
      act(() => {
        consumed = result.current.handleHistoryNavigation(e, 'line1\nline2', setInput);
      });

      expect(consumed!).toBe(false);
      expect(setInput).not.toHaveBeenCalled();
    });
  });

  describe('handleHistoryNavigation - Down Arrow', () => {
    it('returns false when not navigating', () => {
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();
      const e = createKeyEvent('ArrowDown');

      let consumed: boolean;
      act(() => {
        consumed = result.current.handleHistoryNavigation(e, '', setInput);
      });

      expect(consumed!).toBe(false);
    });

    it('moves forward through history', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1', 'msg2', 'msg3']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();

      // Navigate up twice
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), '', setInput);
      });
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), 'msg3', setInput);
      });

      // Navigate down once
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowDown'), 'msg2', setInput);
      });

      expect(setInput).toHaveBeenLastCalledWith('msg3');
    });

    it('restores draft when pressing Down past newest entry', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();

      // Navigate up (saves 'my draft')
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), 'my draft', setInput);
      });

      // Navigate down past newest
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowDown'), 'msg1', setInput);
      });

      expect(setInput).toHaveBeenLastCalledWith('my draft');
      expect(result.current.isNavigating).toBe(false);
    });

    it('does not navigate when cursor is not on last line of multi-line input', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1']);
      const { result } = renderHook(() => useChatHistory());
      const setInput = vi.fn();

      // Enter navigation mode first
      act(() => {
        result.current.handleHistoryNavigation(createKeyEvent('ArrowUp'), '', setInput);
      });

      const e = createKeyEvent('ArrowDown', {
        currentTarget: { selectionStart: 0, selectionEnd: 0 } as HTMLTextAreaElement,
      });

      let consumed: boolean;
      act(() => {
        consumed = result.current.handleHistoryNavigation(e, 'line1\nline2', setInput);
      });

      expect(consumed!).toBe(false);
    });
  });

  describe('clearHistory', () => {
    it('clears history after confirmation', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1', 'msg2']);
      globalThis.confirm = vi.fn(() => true);
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.clearHistory();
      });

      expect(globalThis.confirm).toHaveBeenCalled();
      expect(storage.clearStoredHistory).toHaveBeenCalled();
      expect(result.current.history).toEqual([]);
    });

    it('does not clear history when confirmation is cancelled', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['msg1', 'msg2']);
      globalThis.confirm = vi.fn(() => false);
      const { result } = renderHook(() => useChatHistory());

      act(() => {
        result.current.clearHistory();
      });

      expect(storage.clearStoredHistory).not.toHaveBeenCalled();
      expect(result.current.history).toEqual(['msg1', 'msg2']);
    });
  });

  describe('initialization', () => {
    it('loads history from storage on initialization', () => {
      vi.mocked(storage.loadHistory).mockReturnValue(['stored-msg1', 'stored-msg2']);
      const { result } = renderHook(() => useChatHistory());

      expect(result.current.history).toEqual(['stored-msg1', 'stored-msg2']);
      expect(storage.loadHistory).toHaveBeenCalled();
    });

    it('starts with isNavigating false', () => {
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.isNavigating).toBe(false);
    });
  });
});
