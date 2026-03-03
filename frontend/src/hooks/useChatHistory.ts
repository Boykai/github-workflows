/**
 * Hook for navigating previously sent chat messages via arrow keys.
 *
 * Stores sent messages in memory (and optionally localStorage) and lets the
 * user step through them with the Up / Down arrow keys — similar to a shell's
 * command history.
 */

import { useState, useCallback, useRef } from 'react';

const STORAGE_KEY = 'chat-message-history';
const MAX_HISTORY = 50;

/** Load persisted history from localStorage (most-recent last). */
function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed.filter((m): m is string => typeof m === 'string').slice(-MAX_HISTORY);
      }
    }
  } catch {
    /* ignore corrupt data */
  }
  return [];
}

function saveHistory(history: string[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
  } catch {
    /* storage full — silently ignore */
  }
}

export interface ChatHistoryControls {
  /** Call when the user sends a message to record it in history. */
  addToHistory: (message: string) => void;
  /**
   * Navigate backward (older) in history.
   * Returns the historical message to display, or `null` if already at the
   * oldest entry.  The current draft is stashed on the first call so it can
   * be restored when navigating forward past the newest entry.
   */
  navigateUp: (currentInput: string) => string | null;
  /**
   * Navigate forward (newer) in history.
   * Returns the next message, or the original draft when stepping past the
   * newest history entry, or `null` if not currently browsing history.
   */
  navigateDown: () => string | null;
  /** Whether the user is currently browsing history. */
  isBrowsingHistory: boolean;
  /** Reset browsing state (e.g. after sending). */
  resetNavigation: () => void;
}

export function useChatHistory(): ChatHistoryControls {
  const [history, setHistory] = useState<string[]>(loadHistory);
  // Index into `history`:  -1 means "not browsing" (showing current draft).
  // 0 = oldest, history.length-1 = newest.
  const [index, setIndex] = useState(-1);
  // Stash the user's in-progress draft so we can restore it.
  const draftRef = useRef('');

  const addToHistory = useCallback((message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return;

    setHistory((prev) => {
      // Deduplicate: remove the previous occurrence if it matches the last entry.
      const deduped = prev[prev.length - 1] === trimmed ? prev : prev;
      const next =
        deduped[deduped.length - 1] === trimmed
          ? deduped // already the most-recent entry
          : [...deduped, trimmed].slice(-MAX_HISTORY);
      saveHistory(next);
      return next;
    });
    // Reset navigation state after sending.
    setIndex(-1);
    draftRef.current = '';
  }, []);

  const navigateUp = useCallback(
    (currentInput: string): string | null => {
      if (history.length === 0) return null;

      if (index === -1) {
        // First press — stash the current draft and jump to newest entry.
        draftRef.current = currentInput;
        const newIndex = history.length - 1;
        setIndex(newIndex);
        return history[newIndex];
      }

      if (index > 0) {
        const newIndex = index - 1;
        setIndex(newIndex);
        return history[newIndex];
      }

      // Already at oldest — stay put.
      return null;
    },
    [history, index],
  );

  const navigateDown = useCallback((): string | null => {
    if (index === -1) return null; // not browsing

    if (index < history.length - 1) {
      const newIndex = index + 1;
      setIndex(newIndex);
      return history[newIndex];
    }

    // Past the newest entry — restore the original draft.
    setIndex(-1);
    return draftRef.current;
  }, [history, index]);

  const resetNavigation = useCallback(() => {
    setIndex(-1);
    draftRef.current = '';
  }, []);

  return {
    addToHistory,
    navigateUp,
    navigateDown,
    isBrowsingHistory: index !== -1,
    resetNavigation,
  };
}
