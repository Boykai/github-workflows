/**
 * Tests for useChatHistory hook.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatHistory, MAX_HISTORY_SIZE, STORAGE_KEY } from './useChatHistory';
import type React from 'react';

// Helper to create a mock KeyboardEvent for textarea
function createKeyEvent(
  key: string,
  selectionStart: number,
  inputLength: number,
): React.KeyboardEvent<HTMLTextAreaElement> {
  const prevented = { value: false };
  return {
    key,
    preventDefault: () => {
      prevented.value = true;
    },
    get defaultPrevented() {
      return prevented.value;
    },
    target: {
      selectionStart,
      value: 'x'.repeat(inputLength),
    },
  } as unknown as React.KeyboardEvent<HTMLTextAreaElement>;
}

describe('useChatHistory', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('constants', () => {
    it('exports MAX_HISTORY_SIZE as 100', () => {
      expect(MAX_HISTORY_SIZE).toBe(100);
    });

    it('exports STORAGE_KEY as chat-history', () => {
      expect(STORAGE_KEY).toBe('chat-history');
    });
  });

  describe('initial state', () => {
    it('starts with empty history', () => {
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
      expect(result.current.isNavigating).toBe(false);
    });

    it('loads history from localStorage on mount', () => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(['Hello', 'World']));
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual(['Hello', 'World']);
    });

    it('handles invalid localStorage data gracefully', () => {
      localStorage.setItem(STORAGE_KEY, 'not-json');
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });

    it('handles non-array localStorage data gracefully', () => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ foo: 'bar' }));
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });

    it('handles array with non-string items gracefully', () => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([1, 2, 3]));
      const { result } = renderHook(() => useChatHistory());
      expect(result.current.history).toEqual([]);
    });
  });

  describe('addToHistory', () => {
    it('appends messages in chronological order (FR-001)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));
      act(() => result.current.addToHistory('World'));
      expect(result.current.history).toEqual(['Hello', 'World']);
    });

    it('skips consecutive duplicate messages (FR-009)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));
      act(() => result.current.addToHistory('Hello'));
      expect(result.current.history).toEqual(['Hello']);
    });

    it('allows non-consecutive duplicate messages', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));
      act(() => result.current.addToHistory('World'));
      act(() => result.current.addToHistory('Hello'));
      expect(result.current.history).toEqual(['Hello', 'World', 'Hello']);
    });

    it('evicts oldest entry when at capacity (FR-007)', () => {
      const { result } = renderHook(() => useChatHistory({ maxSize: 3 }));
      act(() => result.current.addToHistory('A'));
      act(() => result.current.addToHistory('B'));
      act(() => result.current.addToHistory('C'));
      act(() => result.current.addToHistory('D'));
      expect(result.current.history).toEqual(['B', 'C', 'D']);
    });

    it('persists to localStorage (FR-006)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Persisted'));
      expect(JSON.parse(localStorage.getItem(STORAGE_KEY)!)).toEqual([
        'Persisted',
      ]);
    });

    it('resets isNavigating after send (FR-010)', async () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('First'));
      act(() => result.current.addToHistory('Second'));

      // Navigate into history
      act(() => {
        const e = createKeyEvent('ArrowUp', 0, 0);
        result.current.handleKeyDown(e, '');
      });
      expect(result.current.isNavigating).toBe(true);

      // Send a message (resets navigation)
      act(() => result.current.addToHistory('Third'));
      // Wait for the setTimeout in addToHistory
      await act(async () => {
        await new Promise((r) => setTimeout(r, 10));
      });
      expect(result.current.isNavigating).toBe(false);
    });
  });

  describe('ArrowUp navigation (FR-002)', () => {
    it('returns most recent message on first ArrowUp press', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));
      act(() => result.current.addToHistory('World'));

      let value: string | null = null;
      act(() => {
        const e = createKeyEvent('ArrowUp', 0, 0);
        value = result.current.handleKeyDown(e, '');
      });
      expect(value).toBe('World');
    });

    it('steps backward through history on successive presses', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('A'));
      act(() => result.current.addToHistory('B'));
      act(() => result.current.addToHistory('C'));

      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });
      expect(value).toBe('C');

      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 1), 'C');
      });
      expect(value).toBe('B');

      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 1), 'B');
      });
      expect(value).toBe('A');
    });

    it('stays at oldest message when pressing ArrowUp at start', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Only'));

      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 4), 'Only');
      });
      // At oldest, returns null (no change)
      expect(value).toBeNull();
    });

    it('returns null with empty history', () => {
      const { result } = renderHook(() => useChatHistory());
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });
      expect(value).toBeNull();
    });

    it('only activates when cursor is at start (FR-013)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      let value: string | null = null;
      // Cursor in the middle of text
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowUp', 3, 5), 'Hello');
      });
      expect(value).toBeNull();
    });

    it('calls preventDefault on navigation (FR-011)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      const e = createKeyEvent('ArrowUp', 0, 0);
      act(() => {
        result.current.handleKeyDown(e, '');
      });
      expect(e.defaultPrevented).toBe(true);
    });

    it('sets isNavigating to true', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });
      expect(result.current.isNavigating).toBe(true);
    });
  });

  describe('ArrowDown navigation (FR-003)', () => {
    it('returns null when at draft position (no history browsing)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowDown', 0, 0), '');
      });
      expect(value).toBeNull();
    });

    it('steps forward through history', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('A'));
      act(() => result.current.addToHistory('B'));
      act(() => result.current.addToHistory('C'));

      // Navigate to oldest
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 1), 'C');
      });
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 1), 'B');
      });

      // Navigate forward
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowDown', 1, 1), 'A');
      });
      expect(value).toBe('B');

      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowDown', 1, 1), 'B');
      });
      expect(value).toBe('C');
    });

    it('restores draft when navigating past newest entry (FR-003, FR-004)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      // Navigate up (saves draft "Hey there")
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 9), 'Hey there');
      });

      // Navigate down past newest → restore draft
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowDown', 5, 5), 'Hello');
      });
      expect(value).toBe('Hey there');
      expect(result.current.isNavigating).toBe(false);
    });

    it('restores empty draft correctly', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      // Navigate up from empty input
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });

      // Navigate down past newest → restore empty draft
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowDown', 5, 5), 'Hello');
      });
      expect(value).toBe('');
    });

    it('only activates when cursor is at end (FR-014)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      // Navigate up
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });

      // Cursor not at end
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('ArrowDown', 2, 5), 'Hello');
      });
      expect(value).toBeNull();
    });
  });

  describe('draft preservation (FR-004, FR-005)', () => {
    it('preserves draft when navigating into history', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Old message'));

      // Type something, then navigate up
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 12), 'My new draft');
      });

      // Navigate back down
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(
          createKeyEvent('ArrowDown', 11, 11),
          'Old message',
        );
      });
      expect(value).toBe('My new draft');
    });

    it('does not overwrite history when editing recalled message (FR-005)', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Original'));

      // Navigate up to recall
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });

      // User edits the recalled message (input changes to "Original edited")
      // Navigate away without sending - history should be unchanged
      act(() => {
        result.current.handleKeyDown(
          createKeyEvent('ArrowDown', 15, 15),
          'Original edited',
        );
      });

      expect(result.current.history).toEqual(['Original']);
    });
  });

  describe('localStorage persistence (FR-006, FR-012)', () => {
    it('syncs history changes to localStorage', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Sync me'));
      expect(JSON.parse(localStorage.getItem(STORAGE_KEY)!)).toEqual([
        'Sync me',
      ]);
    });

    it('uses custom storageKey', () => {
      const customKey = 'my-chat-room-history';
      const { result } = renderHook(() =>
        useChatHistory({ storageKey: customKey }),
      );
      act(() => result.current.addToHistory('Custom'));
      expect(JSON.parse(localStorage.getItem(customKey)!)).toEqual(['Custom']);
      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });

    it('handles localStorage write failure gracefully (FR-012)', () => {
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = vi.fn(() => {
        throw new Error('QuotaExceededError');
      });

      const { result } = renderHook(() => useChatHistory());
      // Should not throw
      act(() => result.current.addToHistory('Still works'));
      expect(result.current.history).toEqual(['Still works']);

      Storage.prototype.setItem = originalSetItem;
    });
  });

  describe('resetNavigation', () => {
    it('resets navigation state', () => {
      const { result } = renderHook(() => useChatHistory());
      act(() => result.current.addToHistory('Hello'));

      // Navigate into history
      act(() => {
        result.current.handleKeyDown(createKeyEvent('ArrowUp', 0, 0), '');
      });
      expect(result.current.isNavigating).toBe(true);

      // Reset
      act(() => result.current.resetNavigation());
      expect(result.current.isNavigating).toBe(false);
    });
  });

  describe('configurable maxSize', () => {
    it('uses custom maxSize for capacity cap', () => {
      const { result } = renderHook(() => useChatHistory({ maxSize: 2 }));
      act(() => result.current.addToHistory('A'));
      act(() => result.current.addToHistory('B'));
      act(() => result.current.addToHistory('C'));
      expect(result.current.history).toEqual(['B', 'C']);
    });
  });

  describe('non-intercepted keys', () => {
    it('returns null for non-arrow keys', () => {
      const { result } = renderHook(() => useChatHistory());
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(createKeyEvent('Enter', 0, 0), '');
      });
      expect(value).toBeNull();
    });

    it('returns null for ArrowLeft', () => {
      const { result } = renderHook(() => useChatHistory());
      let value: string | null = null;
      act(() => {
        value = result.current.handleKeyDown(
          createKeyEvent('ArrowLeft', 0, 0),
          '',
        );
      });
      expect(value).toBeNull();
    });
  });
});
