/**
 * localStorage wrapper for chat message history persistence.
 *
 * All functions degrade gracefully when localStorage is unavailable
 * (e.g. private browsing, storage quota exceeded).
 */

export const CHAT_HISTORY_STORAGE_KEY = 'chat-message-history';

/**
 * Load history from localStorage.
 * Returns [] on parse error, missing data, or unavailable storage.
 */
export function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(CHAT_HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === 'string');
  } catch {
    return [];
  }
}

/**
 * Save history array to localStorage.
 * No-op if localStorage is unavailable.
 */
export function saveHistory(messages: string[]): void {
  try {
    localStorage.setItem(CHAT_HISTORY_STORAGE_KEY, JSON.stringify(messages));
  } catch {
    // Graceful degradation — storage may be full or unavailable
  }
}

/**
 * Remove history from localStorage.
 * No-op if localStorage is unavailable.
 */
export function clearStoredHistory(): void {
  try {
    localStorage.removeItem(CHAT_HISTORY_STORAGE_KEY);
  } catch {
    // Graceful degradation
  }
}
