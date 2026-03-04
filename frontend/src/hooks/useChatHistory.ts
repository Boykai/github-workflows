/**
 * Chat message history navigation hook.
 *
 * Provides terminal-style Up/Down Arrow key navigation through previously
 * sent messages, with localStorage persistence, consecutive deduplication,
 * configurable max-entries cap, draft preservation, and multi-line awareness.
 */

import { useState, useCallback, useRef } from 'react';
import { loadHistory, saveHistory, clearStoredHistory } from '@/utils/chatHistoryStorage';

/** Maximum number of stored history entries */
export const CHAT_HISTORY_MAX_ENTRIES = 100;

export interface UseChatHistoryReturn {
  /** Current history array, oldest first. Read-only. */
  history: readonly string[];

  /**
   * Add a sent message to history.
   * - Trims the message; no-ops on empty/whitespace-only input.
   * - Skips consecutive duplicate entries.
   * - Enforces the max-entries cap (removes oldest on overflow).
   * - Persists to localStorage.
   * - Resets navigation index.
   */
  addToHistory: (message: string) => void;

  /**
   * Handle Up/Down Arrow key events for history navigation.
   * Call this from the textarea's onKeyDown handler.
   *
   * @param e - The keyboard event from the textarea
   * @param currentInput - The current value of the input field
   * @param setInput - State setter to update the input field value
   * @returns true if the event was consumed (caller should skip further handling)
   */
  handleHistoryNavigation: (
    e: React.KeyboardEvent<HTMLTextAreaElement>,
    currentInput: string,
    setInput: (value: string) => void,
  ) => boolean;

  /**
   * Clear all stored history.
   * Shows a window.confirm() dialog before deletion.
   * Resets localStorage and in-memory state.
   */
  clearHistory: () => void;

  /** Whether the user is currently navigating history (index >= 0). */
  isNavigating: boolean;
}

export function useChatHistory(): UseChatHistoryReturn {
  const [history, setHistory] = useState<string[]>(() => loadHistory());
  const [historyIndex, setHistoryIndex] = useState(-1);
  const draftRef = useRef('');

  const isNavigating = historyIndex >= 0;

  const addToHistory = useCallback((message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return;

    setHistory((prev) => {
      // Skip consecutive duplicate
      if (prev.length > 0 && prev[prev.length - 1] === trimmed) {
        return prev;
      }

      let next = [...prev, trimmed];

      // Enforce max cap
      if (next.length > CHAT_HISTORY_MAX_ENTRIES) {
        next = next.slice(next.length - CHAT_HISTORY_MAX_ENTRIES);
      }

      saveHistory(next);
      return next;
    });

    setHistoryIndex(-1);
  }, []);

  const handleHistoryNavigation = useCallback(
    (
      e: React.KeyboardEvent<HTMLTextAreaElement>,
      currentInput: string,
      setInput: (value: string) => void,
    ): boolean => {
      const target = e.currentTarget;

      if (e.key === 'ArrowUp') {
        // Multi-line: only navigate if cursor is on the first line
        const textBeforeCursor = currentInput.slice(0, target.selectionStart);
        if (textBeforeCursor.includes('\n')) {
          return false;
        }

        // Access current history snapshot
        const currentHistory = history;
        if (currentHistory.length === 0) return false;

        let newIndex: number;
        if (historyIndex < 0) {
          // First Up press — save draft and load newest entry
          draftRef.current = currentInput;
          newIndex = currentHistory.length - 1;
        } else if (historyIndex > 0) {
          // Subsequent Up — go further back
          newIndex = historyIndex - 1;
        } else {
          // Already at oldest entry — do nothing
          return false;
        }

        e.preventDefault();
        const value = currentHistory[newIndex];
        setInput(value);
        setHistoryIndex(newIndex);

        // Position cursor at end of restored text
        setTimeout(() => {
          target.selectionStart = value.length;
          target.selectionEnd = value.length;
        }, 0);

        return true;
      }

      if (e.key === 'ArrowDown') {
        // Only handle Down if we're navigating history
        if (historyIndex < 0) return false;

        // Multi-line: only navigate if cursor is on the last line
        const textAfterCursor = currentInput.slice(target.selectionEnd);
        if (textAfterCursor.includes('\n')) {
          return false;
        }

        e.preventDefault();

        const currentHistory = history;
        if (historyIndex < currentHistory.length - 1) {
          // Move forward in history
          const newIndex = historyIndex + 1;
          const value = currentHistory[newIndex];
          setInput(value);
          setHistoryIndex(newIndex);

          setTimeout(() => {
            target.selectionStart = value.length;
            target.selectionEnd = value.length;
          }, 0);
        } else {
          // Past newest entry — restore draft
          const draft = draftRef.current;
          setInput(draft);
          setHistoryIndex(-1);

          setTimeout(() => {
            target.selectionStart = draft.length;
            target.selectionEnd = draft.length;
          }, 0);
        }

        return true;
      }

      return false;
    },
    [history, historyIndex],
  );

  const clearHistory = useCallback(() => {
    if (window.confirm('Are you sure you want to clear your chat message history?')) {
      clearStoredHistory();
      setHistory([]);
      setHistoryIndex(-1);
      draftRef.current = '';
    }
  }, []);

  return {
    history,
    addToHistory,
    handleHistoryNavigation,
    clearHistory,
    isNavigating,
  };
}
