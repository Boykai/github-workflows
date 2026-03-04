# Chat History Hook Contract

**Feature**: `018-chat-history-navigation` | **Date**: 2026-03-04

This feature is entirely frontend/client-side and does not introduce any REST API
endpoints. The "contract" is the TypeScript interface of the `useChatHistory` hook.

## Hook: `useChatHistory`

### Import

```typescript
import { useChatHistory } from '@/hooks/useChatHistory';
```

### Usage

```typescript
const {
  history,
  addToHistory,
  handleHistoryNavigation,
  clearHistory,
  isNavigating,
} = useChatHistory();
```

### Return Type

```typescript
interface UseChatHistoryReturn {
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
   *
   * Behavior:
   * - Up Arrow: Navigate to older history entry (if on first line of multi-line)
   * - Down Arrow: Navigate to newer entry or restore draft (if on last line)
   * - Calls e.preventDefault() only when navigation actually occurs
   * - Positions cursor at end of restored text via setTimeout
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
```

### Configuration

```typescript
/** localStorage key for persistence */
const CHAT_HISTORY_STORAGE_KEY = 'chat-message-history';

/** Maximum number of stored history entries */
const CHAT_HISTORY_MAX_ENTRIES = 100;
```

### Storage Utility: `chatHistoryStorage.ts`

```typescript
/**
 * Load history from localStorage.
 * Returns [] on parse error, missing data, or unavailable storage.
 */
export function loadHistory(): string[];

/**
 * Save history array to localStorage.
 * No-op if localStorage is unavailable.
 */
export function saveHistory(messages: string[]): void;

/**
 * Remove history from localStorage.
 * No-op if localStorage is unavailable.
 */
export function clearStoredHistory(): void;
```

## Integration Contract

### ChatInterface.tsx Changes

The `ChatInterface` component integrates the hook as follows:

1. **Import and call** `useChatHistory()` at the top of the component
2. **In `doSubmit()`**: Call `addToHistory(content)` before clearing the input
3. **In `handleKeyDown()`**: After autocomplete handling, call `handleHistoryNavigation(e, input, setInput)` — if it returns `true`, return early

No props changes to `ChatInterface`. No changes to parent components.

## Multi-Line Detection Contract

The `handleHistoryNavigation` function determines whether history navigation
should activate based on cursor position:

| Key | Condition for Navigation | Condition for Default Behavior |
|-----|--------------------------|-------------------------------|
| Up Arrow | No `\n` in `value.slice(0, selectionStart)` (cursor on first line) | `\n` found before cursor (cursor below first line) |
| Down Arrow | No `\n` in `value.slice(selectionEnd)` (cursor on last line) | `\n` found after cursor (cursor above last line) |

When conditions indicate "Default Behavior," the function returns `false` and
does **not** call `preventDefault()`, allowing normal cursor movement.
