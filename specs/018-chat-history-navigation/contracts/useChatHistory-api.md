# API Contract: useChatHistory Hook

**Feature**: 018-chat-history-navigation
**Date**: 2026-03-05
**Type**: React Custom Hook (frontend-only, no REST/GraphQL)

## Overview

This feature is entirely frontend-based. There are no REST API endpoints or GraphQL mutations. The primary contract is the `useChatHistory` custom React hook, which encapsulates all history navigation logic and exposes a clean interface to the `ChatInterface` component.

## Hook Contract: `useChatHistory`

### Import

```typescript
import { useChatHistory } from '@/hooks/useChatHistory';
```

### Signature

```typescript
function useChatHistory(options?: UseChatHistoryOptions): UseChatHistoryReturn;
```

### Options

```typescript
interface UseChatHistoryOptions {
  /** localStorage key for persistence. Default: 'chat-message-history' */
  storageKey?: string;
  /** Maximum number of messages to store. Default: 100 */
  maxHistory?: number;
}
```

### Return Type

```typescript
interface UseChatHistoryReturn {
  /**
   * Add a sent message to history.
   * Call after the message has been successfully sent.
   * Appends to the end of the history array.
   * If history exceeds maxHistory, the oldest entry is removed.
   * Persists to localStorage.
   * 
   * @param message - The message text that was sent
   */
  addToHistory: (message: string) => void;

  /**
   * Navigate to an older message in history (triggered by ArrowUp).
   * On first call, saves currentInput as the draft buffer.
   * Returns the historical message text to display in the input, or null if no action needed.
   * 
   * @param currentInput - Current value of the input field (for draft capture)
   * @returns Message text to set in input, or null if at end of history / no history
   */
  navigateUp: (currentInput: string) => string | null;

  /**
   * Navigate to a newer message in history (triggered by ArrowDown).
   * When navigating past the most recent message, restores the draft buffer.
   * Returns the message text to display in the input, or null if not navigating.
   * 
   * @returns Message text (or draft) to set in input, or null if not in navigation mode
   */
  navigateDown: () => string | null;

  /**
   * Whether the user is currently browsing history.
   * True when historyIndex >= 0.
   * Use for conditional visual feedback on the input field.
   */
  isNavigating: boolean;

  /**
   * Reset navigation state to default (not navigating).
   * Call after sending a message to clear historyIndex and draftBuffer.
   */
  resetNavigation: () => void;

  /**
   * The full history array (chronological order, oldest first).
   * Expose for the mobile history popover/dropdown.
   */
  history: string[];

  /**
   * Select a specific message from history by its index in the history array.
   * For use by the mobile history popover.
   * Saves currentInput as draft if not already navigating.
   * 
   * @param index - Index into the history array (0 = oldest)
   * @param currentInput - Current value of the input field (for draft capture)
   * @returns The selected message text, or null if index is invalid
   */
  selectFromHistory: (index: number, currentInput: string) => string | null;
}
```

## Integration Contract: ChatInterface.tsx

### handleKeyDown Modifications

The existing `handleKeyDown` function gains a new block between the autocomplete handler and the Enter-to-submit handler:

```typescript
// Priority order:
// 1. Autocomplete navigation (existing - when autocomplete is active)
// 2. History navigation (new - when cursor is on first/last line, not in autocomplete)
// 3. Enter to submit (existing)
// 4. Default browser behavior (implicit)

const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
  // ... existing autocomplete block ...

  // NEW: History navigation
  if (e.key === 'ArrowUp' && !autocompleteActive) {
    const textarea = e.currentTarget;
    const isOnFirstLine = textarea.selectionStart <= (input.indexOf('\n') === -1 ? input.length : input.indexOf('\n'));
    if (isOnFirstLine) {
      const result = navigateUp(input);
      if (result !== null) {
        e.preventDefault();
        setInput(result);
        // Cursor positioning handled in useEffect
      }
    }
  }

  if (e.key === 'ArrowDown' && !autocompleteActive) {
    const textarea = e.currentTarget;
    const lastNewline = input.lastIndexOf('\n');
    const isOnLastLine = textarea.selectionStart > lastNewline;
    if (isOnLastLine) {
      const result = navigateDown();
      if (result !== null) {
        e.preventDefault();
        setInput(result);
      }
    }
  }

  // ... existing Enter block ...
};
```

### doSubmit Modifications

After a successful send, integrate history:

```typescript
const doSubmit = () => {
  const trimmed = input.trim();
  if (!trimmed) return;
  
  addToHistory(trimmed);     // NEW: add to history
  resetNavigation();          // NEW: reset history state
  onSendMessage(trimmed);
  setInput('');
};
```

### Visual Feedback

Conditional class on textarea when `isNavigating` is true:

```typescript
<textarea
  className={`... ${isNavigating ? 'border-l-4 border-l-primary bg-primary/5' : ''}`}
/>
```

### Mobile History Button

New UI element adjacent to the textarea (inside the form):

```typescript
{history.length > 0 && (
  <button type="button" onClick={toggleHistoryPopover} aria-label="Message history">
    <History className="w-4 h-4" />
  </button>
)}
```

## localStorage Contract

### Key

`chat-message-history`

### Value Format

```json
["oldest message", "second oldest", "...", "most recent message"]
```

### Constraints

- Array of strings
- Maximum 100 entries
- Persisted on every `addToHistory` call
- Loaded once on hook mount
- Graceful fallback to `[]` on parse error or storage unavailability

### Error Handling

```typescript
// Read
try {
  const raw = localStorage.getItem('chat-message-history');
  return raw ? JSON.parse(raw) : [];
} catch {
  return [];
}

// Write
try {
  localStorage.setItem('chat-message-history', JSON.stringify(history));
} catch {
  // Silently fail - in-session history still works
}
```
