/**
 * Custom React hook for chat message history navigation.
 *
 * Manages:
 * - Ordered history list with localStorage persistence (FR-001, FR-006)
 * - Up/Down Arrow keyboard navigation (FR-002, FR-003)
 * - Draft buffer preservation and restoration (FR-004)
 * - Capacity management with oldest-first eviction (FR-007)
 * - Consecutive duplicate suppression (FR-009)
 * - Graceful degradation when localStorage is unavailable (FR-012)
 */

import { useState, useRef, useEffect, useCallback } from 'react';

// ─── Configuration ───────────────────────────────────────────────────────

/** Maximum number of messages retained in history (FR-007) */
export const MAX_HISTORY_SIZE = 100;

/** localStorage key for persisting the history array (FR-006) */
export const STORAGE_KEY = 'chat-history';

// ─── Types ───────────────────────────────────────────────────────────────

export interface UseChatHistoryOptions {
  /** Override the default localStorage key. */
  storageKey?: string;
  /** Override the maximum number of history entries. */
  maxSize?: number;
}

export interface UseChatHistoryReturn {
  history: readonly string[];
  addToHistory: (message: string) => void;
  handleKeyDown: (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
    currentInput: string,
  ) => string | null;
  isNavigating: boolean;
  resetNavigation: () => void;
}

// ─── localStorage helpers ────────────────────────────────────────────────

function loadHistory(key: string): string[] {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return [];
    const parsed: unknown = JSON.parse(raw);
    if (
      Array.isArray(parsed) &&
      parsed.every((item) => typeof item === 'string')
    ) {
      return parsed as string[];
    }
    return [];
  } catch {
    return [];
  }
}

function saveHistory(key: string, history: string[]): void {
  try {
    localStorage.setItem(key, JSON.stringify(history));
  } catch {
    // Silently handle write failures (quota exceeded, private browsing)
  }
}

// ─── Hook ────────────────────────────────────────────────────────────────

export function useChatHistory(
  options?: UseChatHistoryOptions,
): UseChatHistoryReturn {
  const storageKey = options?.storageKey ?? STORAGE_KEY;
  const maxSize = options?.maxSize ?? MAX_HISTORY_SIZE;

  const [history, setHistory] = useState<string[]>(() => loadHistory(storageKey));
  const indexRef = useRef<number>(history.length);
  const draftRef = useRef<string>('');
  const [isNavigating, setIsNavigating] = useState(false);

  // Sync history to localStorage on every change
  useEffect(() => {
    saveHistory(storageKey, history);
  }, [history, storageKey]);

  // Keep indexRef in sync when history changes externally
  // (e.g., on mount after loading from localStorage)
  useEffect(() => {
    if (indexRef.current > history.length) {
      indexRef.current = history.length;
    }
  }, [history.length]);

  const resetNavigation = useCallback(() => {
    indexRef.current = history.length;
    draftRef.current = '';
    setIsNavigating(false);
  }, [history.length]);

  const addToHistory = useCallback(
    (message: string) => {
      setHistory((prev) => {
        // Consecutive duplicate check (FR-009)
        if (prev.length > 0 && prev[prev.length - 1] === message) {
          // Reset navigation even if dedup skips the append (FR-010)
          indexRef.current = prev.length;
          draftRef.current = '';
          setIsNavigating(false);
          return prev;
        }
        const next = [...prev, message];
        // Evict oldest entries if over capacity (FR-007)
        while (next.length > maxSize) {
          next.shift();
        }
        // Reset navigation pointer to new draft position (FR-010)
        indexRef.current = next.length;
        draftRef.current = '';
        setIsNavigating(false);
        return next;
      });
    },
    [maxSize],
  );

  const handleKeyDown = useCallback(
    (
      event: React.KeyboardEvent<HTMLTextAreaElement>,
      currentInput: string,
    ): string | null => {
      const target = event.target as HTMLTextAreaElement;

      if (event.key === 'ArrowUp') {
        // Only activate when cursor is at start or input is empty (FR-013)
        if (currentInput.length > 0 && target.selectionStart !== 0) {
          return null;
        }

        if (history.length === 0) return null;

        // Save draft on first navigation away from draft position (FR-004)
        if (indexRef.current === history.length) {
          draftRef.current = currentInput;
        }

        // Decrement index (don't go below 0)
        if (indexRef.current > 0) {
          indexRef.current -= 1;
        } else {
          // Already at oldest — prevent default but don't change value
          event.preventDefault();
          return null;
        }

        event.preventDefault();
        setIsNavigating(true);
        return history[indexRef.current];
      }

      if (event.key === 'ArrowDown') {
        // Only activate when cursor is at end of input (FR-014)
        if (currentInput.length > 0 && target.selectionStart !== currentInput.length) {
          return null;
        }

        // Do nothing if already at draft position
        if (indexRef.current >= history.length) {
          return null;
        }

        // Increment index
        indexRef.current += 1;

        event.preventDefault();

        // If we've moved past the newest entry, restore draft (FR-003)
        if (indexRef.current === history.length) {
          setIsNavigating(false);
          return draftRef.current;
        }

        setIsNavigating(true);
        return history[indexRef.current];
      }

      return null;
    },
    [history],
  );

  return {
    history,
    addToHistory,
    handleKeyDown,
    isNavigating,
    resetNavigation,
  };
}
