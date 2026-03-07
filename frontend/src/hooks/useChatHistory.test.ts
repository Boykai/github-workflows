/**
 * Unit tests for useChatHistory hook
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatHistory } from './useChatHistory';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
    get length() { return Object.keys(store).length; },
    key: vi.fn((index: number) => Object.keys(store)[index] ?? null),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useChatHistory', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
  });

  describe('initialization', () => {
    it('should initialize with empty history when localStorage is empty', () => {
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
      expect(result.current.isNavigating).toBe(false);
    });

    it('should initialize with empty in-memory history even when localStorage has refs', () => {
      // localStorage stores only lightweight refs (id + ts), not message content.
      // In-memory history starts empty; content is session-only.
      const refs = [
        { id: 'ref-1', ts: new Date().toISOString() },
        { id: 'ref-2', ts: new Date().toISOString() },
      ];
      localStorageMock.setItem('chat-message-history', JSON.stringify(refs));
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });

    it('should use custom storage key for refs', () => {
      const refs = [{ id: 'ref-1', ts: new Date().toISOString() }];
      localStorageMock.setItem('custom-key', JSON.stringify(refs));
      const { result } = renderHook(() => useChatHistory({ storageKey: 'custom-key' }));
      // In-memory history is still empty — only refs are persisted
      expect(result.current.history).toEqual([]);
    });

    it('should gracefully handle corrupt localStorage data', () => {
      localStorageMock.setItem('chat-message-history', 'invalid json');
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });

    it('should gracefully handle non-MessageRef values in localStorage', () => {
      // Old-format strings or invalid objects are filtered out during ref loading
      localStorageMock.setItem('chat-message-history', JSON.stringify(['msg1', 42, null, 'msg2']));
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });
  });

  describe('addToHistory', () => {
    it('should add a message to history', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('hello'));
      expect(result.current.history).toEqual(['hello']);
    });

    it('should persist lightweight refs to localStorage', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('hello'));
      // localStorage receives MessageRef objects (id + ts), not message content
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'chat-message-history',
        expect.stringMatching(/^\[.*"id".*"ts".*\]$/),
      );
      // Verify the stored value is a valid JSON array of refs
      const storedValue = localStorageMock.setItem.mock.calls[0][1];
      const parsed = JSON.parse(storedValue);
      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed).toHaveLength(1);
      expect(parsed[0]).toHaveProperty('id');
      expect(parsed[0]).toHaveProperty('ts');
    });

    it('should store duplicate messages as separate entries', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('hello'));
      act(() => result.current.addToHistory('hello'));
      expect(result.current.history).toEqual(['hello', 'hello']);
    });

    it('should cap history at maxHistory (default 100)', () => {
      const { result } = renderHook(() => useChatHistory({ maxHistory: 3 }));
      act(() => result.current.addToHistory('msg1'));
      act(() => result.current.addToHistory('msg2'));
      act(() => result.current.addToHistory('msg3'));
      act(() => result.current.addToHistory('msg4'));
      expect(result.current.history).toEqual(['msg2', 'msg3', 'msg4']);
    });
  });

  describe('navigateUp', () => {
    it('should return null when history is empty', () => {
      const { result } = renderHook(() => useChatHistory());
      let nav: string | null = null;
      act(() => { nav = result.current.navigateUp('draft'); });
      expect(nav).toBeNull();
    });

    it('should return most recent message on first up press', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));
      act(() => result.current.addToHistory('msg2'));
      act(() => result.current.addToHistory('msg3'));

      let nav: string | null = null;
      act(() => { nav = result.current.navigateUp(''); });
      expect(nav).toBe('msg3');
      expect(result.current.isNavigating).toBe(true);
    });

    it('should step through history in reverse chronological order', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));
      act(() => result.current.addToHistory('msg2'));
      act(() => result.current.addToHistory('msg3'));

      let nav: string | null = null;
      act(() => { nav = result.current.navigateUp(''); });
      expect(nav).toBe('msg3');

      act(() => { nav = result.current.navigateUp(''); });
      expect(nav).toBe('msg2');

      act(() => { nav = result.current.navigateUp(''); });
      expect(nav).toBe('msg1');
    });

    it('should return null when at oldest message', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));

      let nav: string | null = null;
      act(() => { nav = result.current.navigateUp(''); });
      expect(nav).toBe('msg1');

      act(() => { nav = result.current.navigateUp(''); });
      expect(nav).toBeNull(); // Already at oldest
    });
  });

  describe('navigateDown', () => {
    it('should return null when not navigating', () => {
      const { result } = renderHook(() => useChatHistory());
      let nav: string | null = null;
      act(() => { nav = result.current.navigateDown(); });
      expect(nav).toBeNull();
    });

    it('should navigate forward to more recent messages', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));
      act(() => result.current.addToHistory('msg2'));
      act(() => result.current.addToHistory('msg3'));

      // Navigate up to msg1
      act(() => { result.current.navigateUp('draft'); });
      act(() => { result.current.navigateUp(''); });
      act(() => { result.current.navigateUp(''); });

      // Navigate back down
      let nav: string | null = null;
      act(() => { nav = result.current.navigateDown(); });
      expect(nav).toBe('msg2');

      act(() => { nav = result.current.navigateDown(); });
      expect(nav).toBe('msg3');
    });

    it('should restore draft when navigating past most recent', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));

      // Navigate up (captures draft)
      act(() => { result.current.navigateUp('my draft text'); });

      // Navigate down past newest → restore draft
      let nav: string | null = null;
      act(() => { nav = result.current.navigateDown(); });
      expect(nav).toBe('my draft text');
      expect(result.current.isNavigating).toBe(false);
    });
  });

  describe('resetNavigation', () => {
    it('should reset historyIndex to -1', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));
      act(() => { result.current.navigateUp(''); });
      expect(result.current.isNavigating).toBe(true);

      act(() => result.current.resetNavigation());
      expect(result.current.isNavigating).toBe(false);
    });
  });

  describe('selectFromHistory', () => {
    it('should return null for invalid index', () => {
      const { result } = renderHook(() => useChatHistory());
      let nav: string | null = null;
      act(() => { nav = result.current.selectFromHistory(-1, ''); });
      expect(nav).toBeNull();
      act(() => { nav = result.current.selectFromHistory(0, ''); });
      expect(nav).toBeNull(); // empty history
    });

    it('should return message at given index', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));
      act(() => result.current.addToHistory('msg2'));

      let nav: string | null = null;
      act(() => { nav = result.current.selectFromHistory(0, 'draft'); });
      expect(nav).toBe('msg1');
      expect(result.current.isNavigating).toBe(true);
    });

    it('should capture draft on first selection', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('msg1'));
      act(() => result.current.addToHistory('msg2'));

      // Select from history (captures draft)
      act(() => { result.current.selectFromHistory(1, 'my draft'); });
      // After selectFromHistory(1, ...), historyIndex = history.length-1-1 = 0

      // Navigate down → historyIndex goes to -1 → returns draft
      let nav: string | null = null;
      act(() => { nav = result.current.navigateDown(); });
      expect(nav).toBe('my draft');
    });
  });

  describe('localStorage error handling', () => {
    it('should handle localStorage.getItem throwing', () => {
      localStorageMock.getItem.mockImplementationOnce(() => { throw new Error('denied'); });
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });

    it('should handle localStorage.setItem throwing', () => {
      localStorageMock.setItem.mockImplementationOnce(() => { throw new Error('quota'); });
      const { result } = renderHook(() => useChatHistory());
      // Should not throw
      act(() => result.current.addToHistory('hello'));
      expect(result.current.history).toEqual(['hello']);
    });
  });
});
