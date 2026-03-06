/**
 * Custom hook for chat message history navigation.
 * Provides shell-like up/down arrow key navigation through previously sent messages.
 *
 * **Privacy**: Only lightweight references (message IDs with timestamps)
 * are persisted to localStorage — never full message content.
 * All local data is cleared on logout via {@link clearChatStorage}.
 */

import { useState, useRef, useCallback } from 'react';

/** A lightweight reference stored in localStorage (no message content). */
interface MessageRef {
  /** Unique message identifier */
  id: string;
  /** ISO-8601 timestamp when the message was recorded */
  ts: string;
}

/** Time-to-live for stored references (24 hours in milliseconds). */
const STORAGE_TTL_MS = 24 * 60 * 60 * 1000;

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
}

/**
 * Load lightweight message refs from localStorage, pruning expired entries.
 * Returns the IDs only — actual content must be fetched from the backend.
 */
function loadRefs(storageKey: string): MessageRef[] {
  try {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const now = Date.now();
        // Filter out expired entries and validate shape
        return parsed.filter(
          (item): item is MessageRef =>
            item != null &&
            typeof item === 'object' &&
            typeof item.id === 'string' &&
            typeof item.ts === 'string' &&
            now - new Date(item.ts).getTime() < STORAGE_TTL_MS,
        );
      }
    }
  } catch {
    // Graceful fallback
  }
  return [];
}

function saveRefs(storageKey: string, refs: MessageRef[]): void {
  try {
    localStorage.setItem(storageKey, JSON.stringify(refs));
  } catch {
    // Silently fail — in-session history still works
  }
}

/** Clear all chat-related data from localStorage.  Call on logout. */
export function clearChatStorage(): void {
  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith('chat-message-history')) {
      keysToRemove.push(key);
    }
  }
  keysToRemove.forEach((k) => localStorage.removeItem(k));
}

export function useChatHistory(options?: UseChatHistoryOptions): UseChatHistoryReturn {
  const storageKey = options?.storageKey ?? 'chat-message-history';
  const maxHistory = options?.maxHistory ?? 100;

  // In-memory history stores full messages for the current session only
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const draftBuffer = useRef<string>('');

  // Load refs (IDs only) on mount — kept for pruning/TTL bookkeeping
  const refsRef = useRef<MessageRef[]>(loadRefs(storageKey));

  const isNavigating = historyIndex >= 0;

  const addToHistory = useCallback(
    (message: string) => {
      setHistory((prev) => {
        const next = [...prev, message];
        // Enforce cap by removing oldest entries
        while (next.length > maxHistory) {
          next.shift();
        }
        return next;
      });

      // Persist lightweight reference (ID + timestamp) — no content
      const ref: MessageRef = { id: crypto.randomUUID(), ts: new Date().toISOString() };
      const refs = [...refsRef.current, ref];
      while (refs.length > maxHistory) {
        refs.shift();
      }
      refsRef.current = refs;
      saveRefs(storageKey, refs);

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

  return {
    addToHistory,
    navigateUp,
    navigateDown,
    isNavigating,
    resetNavigation,
    history,
    selectFromHistory,
  };
}
