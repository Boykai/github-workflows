/**
 * Tests for chatHistoryStorage utility.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { loadHistory, saveHistory, clearStoredHistory, CHAT_HISTORY_STORAGE_KEY } from './chatHistoryStorage';

describe('chatHistoryStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('loadHistory', () => {
    it('returns empty array when no data exists', () => {
      expect(loadHistory()).toEqual([]);
    });

    it('returns parsed array from localStorage', () => {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(['hello', 'world']));
      expect(loadHistory()).toEqual(['hello', 'world']);
    });

    it('returns empty array on invalid JSON', () => {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, 'not-json');
      expect(loadHistory()).toEqual([]);
    });

    it('returns empty array when stored value is not an array', () => {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify({ not: 'array' }));
      expect(loadHistory()).toEqual([]);
    });

    it('filters out non-string entries', () => {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(['valid', 42, null, 'also-valid']));
      expect(loadHistory()).toEqual(['valid', 'also-valid']);
    });

    it('handles localStorage error gracefully', () => {
      const spy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('Storage unavailable');
      });
      expect(loadHistory()).toEqual([]);
      spy.mockRestore();
    });
  });

  describe('saveHistory', () => {
    it('saves array to localStorage', () => {
      saveHistory(['msg1', 'msg2']);
      const raw = localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
      expect(JSON.parse(raw!)).toEqual(['msg1', 'msg2']);
    });

    it('handles localStorage error gracefully', () => {
      const spy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('Quota exceeded');
      });
      expect(() => saveHistory(['msg'])).not.toThrow();
      spy.mockRestore();
    });
  });

  describe('clearStoredHistory', () => {
    it('removes history key from localStorage', () => {
      localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(['msg']));
      clearStoredHistory();
      expect(localStorage.getItem(CHAT_HISTORY_STORAGE_KEY)).toBeNull();
    });

    it('handles localStorage error gracefully', () => {
      const spy = vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
        throw new Error('Storage unavailable');
      });
      expect(() => clearStoredHistory()).not.toThrow();
      spy.mockRestore();
    });
  });
});
