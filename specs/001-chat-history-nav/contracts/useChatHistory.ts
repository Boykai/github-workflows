/**
 * Contract: useChatHistory Hook
 *
 * Feature: 001-chat-history-nav
 * Phase: 1 — Design & Contracts
 *
 * This file defines the TypeScript interface contract for the useChatHistory
 * custom React hook. It specifies inputs, outputs, and behavioral guarantees
 * without providing implementation.
 */

// ─── Configuration ───────────────────────────────────────────────────────

/** Maximum number of messages retained in history (FR-007) */
export const MAX_HISTORY_SIZE = 100;

/** localStorage key for persisting the history array (FR-006) */
export const STORAGE_KEY = 'chat-history';

// ─── Hook Options ────────────────────────────────────────────────────────

export interface UseChatHistoryOptions {
  /**
   * Override the default localStorage key.
   * Useful for namespacing per-chat-room or per-user.
   * @default 'chat-history'
   */
  storageKey?: string;

  /**
   * Override the maximum number of history entries.
   * Oldest entries are evicted when the cap is reached.
   * @default 100
   */
  maxSize?: number;
}

// ─── Hook Return Type ────────────────────────────────────────────────────

export interface UseChatHistoryReturn {
  /**
   * The full history array (oldest first, newest last).
   * Read-only — mutate only via addToHistory().
   */
  history: readonly string[];

  /**
   * Add a sent message to the history.
   * - Appends to the end of the array (FR-001)
   * - Skips append if message equals the last entry (FR-009 deduplication)
   * - Evicts oldest entry if at capacity (FR-007)
   * - Resets navigation pointer to draft position (FR-010)
   * - Syncs to localStorage (FR-006)
   *
   * @param message - The trimmed, non-empty message string that was sent.
   */
  addToHistory: (message: string) => void;

  /**
   * Handle keyboard events for history navigation.
   * Attach this to the textarea's onKeyDown handler.
   *
   * Behavior:
   * - ArrowUp: Navigate backward through history (FR-002)
   *   - Only activates when cursor is at position 0 or input is empty (FR-013)
   *   - Saves draft on first navigation away from draft position (FR-004)
   *   - Calls preventDefault() to stop cursor jump (FR-011)
   * - ArrowDown: Navigate forward through history (FR-003)
   *   - Only activates when cursor is at end of input (FR-014)
   *   - Restores draft when navigating past newest entry (FR-003)
   *   - Calls preventDefault() to stop cursor jump (FR-011)
   *
   * @param event - The React keyboard event from the textarea.
   * @param currentInput - The current value of the input field.
   * @returns The new input value if navigation occurred, or null if no navigation happened.
   */
  handleKeyDown: (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
    currentInput: string
  ) => string | null;

  /**
   * Whether the input is currently showing a historical message
   * (as opposed to the user's draft). Useful for optional visual indicators.
   */
  isNavigating: boolean;

  /**
   * Reset navigation state without adding to history.
   * Called internally by addToHistory, but exposed for edge cases
   * (e.g., clearing the chat).
   */
  resetNavigation: () => void;
}

// ─── Hook Signature ──────────────────────────────────────────────────────

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
 *
 * Integration:
 * 1. Call useChatHistory() in ChatInterface component
 * 2. Wire handleKeyDown into the textarea's onKeyDown (after autocomplete logic)
 * 3. Call addToHistory(message) in the doSubmit function after successful send
 * 4. Use isNavigating for optional visual indicators
 *
 * @param options - Optional configuration overrides.
 * @returns Hook API for history management and navigation.
 */
export type UseChatHistory = (options?: UseChatHistoryOptions) => UseChatHistoryReturn;
