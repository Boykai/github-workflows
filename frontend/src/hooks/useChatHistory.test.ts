/**
 * Tests for useChatHistory hook.
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatHistory } from './useChatHistory';

const STORAGE_KEY = 'chat-message-history';

beforeEach(() => {
  localStorage.removeItem(STORAGE_KEY);
});

describe('useChatHistory', () => {
  describe('addToHistory', () => {
    it('stores sent messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('hello'));
      act(() => result.current.addToHistory('world'));

      // Navigate up twice to confirm both were stored (newest first).
      let msg: string | null = null;
      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBe('world');

      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBe('hello');
    });

    it('ignores empty/whitespace-only messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('   '));
      act(() => result.current.addToHistory(''));

      let msg: string | null = null;
      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBeNull();
    });

    it('deduplicates consecutive identical messages', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('same'));
      act(() => result.current.addToHistory('same'));

      let msg: string | null = null;
      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBe('same');

      act(() => {
        msg = result.current.navigateUp('');
      });
      // Should be null — only one entry exists.
      expect(msg).toBeNull();
    });
  });

  describe('navigateUp / navigateDown', () => {
    it('steps through history oldest to newest', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('first'));
      act(() => result.current.addToHistory('second'));
      act(() => result.current.addToHistory('third'));

      let msg: string | null = null;

      // Up → newest
      act(() => {
        msg = result.current.navigateUp('draft');
      });
      expect(msg).toBe('third');

      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBe('second');

      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBe('first');

      // Can't go further up — returns null.
      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBeNull();
    });

    it('navigateDown restores draft after stepping past newest', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('alpha'));
      act(() => result.current.addToHistory('beta'));

      let msg: string | null = null;

      // Go up (stashing the draft "my draft")
      act(() => {
        msg = result.current.navigateUp('my draft');
      });
      expect(msg).toBe('beta');

      // Go down past newest → should restore draft
      act(() => {
        msg = result.current.navigateDown();
      });
      expect(msg).toBe('my draft');
    });

    it('navigateDown returns null when not browsing history', () => {
      const { result } = renderHook(() => useChatHistory());

      let msg: string | null = 'sentinel';
      act(() => {
        msg = result.current.navigateDown();
      });
      expect(msg).toBeNull();
    });

    it('isBrowsingHistory reflects navigation state', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('msg'));

      expect(result.current.isBrowsingHistory).toBe(false);

      act(() => {
        result.current.navigateUp('');
      });
      expect(result.current.isBrowsingHistory).toBe(true);

      act(() => {
        result.current.navigateDown();
      });
      expect(result.current.isBrowsingHistory).toBe(false);
    });
  });

  describe('resetNavigation', () => {
    it('clears browsing state', () => {
      const { result } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('msg'));
      act(() => {
        result.current.navigateUp('');
      });
      expect(result.current.isBrowsingHistory).toBe(true);

      act(() => result.current.resetNavigation());
      expect(result.current.isBrowsingHistory).toBe(false);
    });
  });

  describe('localStorage persistence', () => {
    it('persists history across hook instances', () => {
      const { result, unmount } = renderHook(() => useChatHistory());

      act(() => result.current.addToHistory('persisted'));
      unmount();

      // New instance should load from storage.
      const { result: result2 } = renderHook(() => useChatHistory());
      let msg: string | null = null;
      act(() => {
        msg = result2.current.navigateUp('');
      });
      expect(msg).toBe('persisted');
    });

    it('handles corrupt localStorage gracefully', () => {
      localStorage.setItem(STORAGE_KEY, 'not valid json!!!');
      const { result } = renderHook(() => useChatHistory());

      let msg: string | null = 'sentinel';
      act(() => {
        msg = result.current.navigateUp('');
      });
      expect(msg).toBeNull();
    });
  });
});
