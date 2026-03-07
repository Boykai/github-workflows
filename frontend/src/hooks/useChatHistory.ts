/**
 * Custom hook for chat message history navigation.
 * Provides shell-like up/down arrow key navigation through previously sent messages.
 * Persists history across sessions via localStorage with TTL-based expiration.
 */

import { useState, useRef, useCallback } from 'react';

/** TTL for persisted chat history entries (24 hours in milliseconds). */
const HISTORY_TTL_MS = 24 * 60 * 60 * 1000;

export interface UseChatHistoryOptions {
  /** localStorage key for persistence. Default: 'chat-message-history' */
  storageKey?: string;
  /** Maximum number of messages to store. Default: 100 */
  maxHistory?: number;
}

export interface UseChatHistoryReturn {
  /** Add a sent message to history */
  addToHistory: (message: string) => void;
  /** Navigate to an older message (ArrowUp). Returns message text or null. */
  navigateUp: (currentInput: string) => string | null;
  /** Navigate to a newer message (ArrowDown). Returns message text or null. */
  navigateDown: () => string | null;
  /** Whether the user is currently browsing history */
  isNavigating: boolean;
  /** Reset navigation state (call after sending) */
  resetNavigation: () => void;
  /** Full history array (chronological, oldest first) */
  history: string[];
  /** Select a specific message by index (for mobile popover) */
  selectFromHistory: (index: number, currentInput: string) => string | null;
  /** Clear all chat history from localStorage */
  clearHistory: () => void;
}

/** Wrapper stored in localStorage with TTL. */
interface PersistedHistory {
  entries: string[];
  expiresAt: number;
}

function loadHistory(storageKey: string): string[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      // Support new TTL format
      if (parsed && typeof parsed === 'object' && 'entries' in parsed && 'expiresAt' in parsed) {
        const wrapper = parsed as PersistedHistory;
        if (Date.now() > wrapper.expiresAt) {
          // Expired — clear and return empty
          localStorage.removeItem(storageKey);
          return [];
        }
        if (Array.isArray(wrapper.entries)) {
          return wrapper.entries.filter((item): item is string => typeof item === 'string');
        }
      }
      // Legacy format: plain array
      if (Array.isArray(parsed)) {
        return parsed.filter((item): item is string => typeof item === 'string');
      }
    }
  } catch {
    // Graceful fallback
  }
  return [];
}

function saveHistory(storageKey: string, history: string[]): void {
  try {
    const wrapper: PersistedHistory = {
      entries: history,
      expiresAt: Date.now() + HISTORY_TTL_MS,
    };
    localStorage.setItem(storageKey, JSON.stringify(wrapper));
  } catch {
    // Silently fail — in-session history still works
  }
}

/**
 * Clear all chat history from localStorage.
 * Called during logout to prevent sensitive data from persisting.
 */
export function clearChatHistory(storageKey: string = 'chat-message-history'): void {
  try {
    localStorage.removeItem(storageKey);
  } catch {
    // Ignore storage errors
  }
}

export function useChatHistory(options?: UseChatHistoryOptions): UseChatHistoryReturn {
  const storageKey = options?.storageKey ?? 'chat-message-history';
  const maxHistory = options?.maxHistory ?? 100;

  const [history, setHistory] = useState<string[]>(() => loadHistory(storageKey));
  const [historyIndex, setHistoryIndex] = useState(-1);
  const draftBuffer = useRef<string>('');

  const isNavigating = historyIndex >= 0;

  const addToHistory = useCallback(
    (message: string) => {
      setHistory((prev) => {
        const next = [...prev, message];
        // Enforce cap by removing oldest entries
        while (next.length > maxHistory) {
          next.shift();
        }
        saveHistory(storageKey, next);
        return next;
      });
      setHistoryIndex(-1);
    },
    [storageKey, maxHistory],
  );

  const resetNavigation = useCallback(() => {
    setHistoryIndex(-1);
    draftBuffer.current = '';
  }, []);

  const navigateUp = useCallback(
    (currentInput: string): string | null => {
      if (history.length === 0) return null;

      let newIndex: number;
      if (historyIndex === -1) {
        // Starting navigation — capture draft
        draftBuffer.current = currentInput;
        newIndex = 0;
      } else {
        // Go further back in history (capped at oldest)
        newIndex = Math.min(historyIndex + 1, history.length - 1);
        if (newIndex === historyIndex) return null; // Already at oldest
      }

      setHistoryIndex(newIndex);
      return history[history.length - 1 - newIndex];
    },
    [history, historyIndex],
  );

  const navigateDown = useCallback((): string | null => {
    if (historyIndex < 0) return null; // Not navigating

    const newIndex = historyIndex - 1;
    setHistoryIndex(newIndex);

    if (newIndex === -1) {
      // Exited history — restore draft
      return draftBuffer.current;
    }

    return history[history.length - 1 - newIndex];
  }, [history, historyIndex]);

  const selectFromHistory = useCallback(
    (index: number, currentInput: string): string | null => {
      if (index < 0 || index >= history.length) return null;

      if (historyIndex === -1) {
        // Capture draft before entering navigation
        draftBuffer.current = currentInput;
      }

      // Map array index to historyIndex (reverse chronological)
      const newHistoryIndex = history.length - 1 - index;
      setHistoryIndex(newHistoryIndex);
      return history[index];
    },
    [history, historyIndex],
  );

  const clearHistory = useCallback(() => {
    clearChatHistory(storageKey);
    setHistory([]);
    setHistoryIndex(-1);
    draftBuffer.current = '';
  }, [storageKey]);

  return {
    addToHistory,
    navigateUp,
    navigateDown,
    isNavigating,
    resetNavigation,
    history,
    selectFromHistory,
    clearHistory,
  };
}
