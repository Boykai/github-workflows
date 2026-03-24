/**
 * Custom hook for chat message history navigation.
 * Provides shell-like up/down arrow key navigation through previously sent messages.
 *
 * Security: Message content is kept only in memory (React state) and is never
 * persisted to localStorage or any other browser storage.  This prevents
 * sensitive chat content from surviving page reloads or being readable by XSS.
 */

import { useState, useRef, useCallback } from 'react';

export interface UseChatHistoryOptions {
  /** Maximum number of messages to store in memory. Default: 100 */
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
  /** Clear in-memory chat history and any legacy localStorage data */
  clearHistory: () => void;
}

/**
 * @internal Security: clears pre-v2 localStorage data on logout.
 * Remove any legacy chat history that may have been persisted to localStorage
 * by earlier versions of this hook.
 */
function clearLegacyStorage(storageKey: string): void {
  try {
    localStorage.removeItem(storageKey);
  } catch {
    // Ignore storage errors
  }
}

/**
 * Clear chat history from localStorage.
 * Called during logout to ensure no stale data remains.
 */
export function clearChatHistory(storageKey: string = 'chat-message-history'): void {
  clearLegacyStorage(storageKey);
}

export function useChatHistory(options?: UseChatHistoryOptions): UseChatHistoryReturn {
  const maxHistory =
    typeof options?.maxHistory === 'number' && Number.isFinite(options.maxHistory)
      ? Math.max(0, Math.floor(options.maxHistory))
      : 100;

  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const draftBuffer = useRef<string>('');

  const isNavigating = historyIndex >= 0;

  const addToHistory = useCallback(
    (message: string) => {
      setHistory((prev) => {
        const next = [...prev, message];
        // Enforce cap by keeping only the most recent entries
        return next.length > maxHistory ? next.slice(next.length - maxHistory) : next;
      });
      setHistoryIndex(-1);
    },
    [maxHistory]
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
    [history, historyIndex]
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
    [history, historyIndex]
  );

  const clearHistory = useCallback(() => {
    clearLegacyStorage('chat-message-history');
    setHistory([]);
    setHistoryIndex(-1);
    draftBuffer.current = '';
  }, []);

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
