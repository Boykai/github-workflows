# Data Model: Chat Message History Navigation

**Feature**: 018-chat-history-navigation
**Date**: 2026-03-05
**Status**: Complete

## Entities

### 1. Message History (Persistent)

**Description**: An ordered list of previously sent message strings, stored in localStorage and loaded into memory on component mount.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `messages` | `string[]` | Array of sent message texts, ordered chronologically (oldest first, newest last) | Max 100 entries; each entry is a non-empty string |

**Storage**:
- **Key**: `chat-message-history`
- **Format**: JSON-serialized string array
- **Location**: `window.localStorage`
- **Max size**: 100 entries (~500KB worst case)

**Operations**:
- `load()`: Read from localStorage, parse JSON, return `string[]` (empty array on failure)
- `append(message: string)`: Add to end of array; if length > 100, remove first element; write to localStorage
- `clear()`: Remove key from localStorage (implicit via browser storage clear)

**Validation**:
- Messages must be non-empty strings (enforced by the existing send logic which trims and checks)
- Array must not exceed 100 entries (enforced on append)
- Graceful fallback to empty array if localStorage is unavailable or corrupt

---

### 2. History Index (Ephemeral State)

**Description**: A pointer tracking the user's current position in the message history during arrow-key navigation. Lives in React component state.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `historyIndex` | `number` | Current position in history; `-1` = not navigating | Range: `-1` to `history.length - 1` |

**State Transitions**:

```
                    ┌─────────────────────────────┐
                    │     historyIndex = -1        │
                    │   (Not navigating / Draft)   │
                    └──────────┬──────────────────┘
                               │ ArrowUp (has history)
                               ▼
                    ┌─────────────────────────────┐
                    │     historyIndex = 0         │
                    │   (Most recent message)      │◄─── ArrowDown from index 1
                    └──────────┬──────────────────┘
                               │ ArrowUp
                               ▼
                    ┌─────────────────────────────┐
                    │     historyIndex = 1         │
                    │   (Second most recent)       │◄─── ArrowDown from index 2
                    └──────────┬──────────────────┘
                               │ ArrowUp
                               ▼
                    ┌─────────────────────────────┐
                    │     historyIndex = N-1       │
                    │   (Oldest message)           │
                    │   ArrowUp → stays here       │
                    └─────────────────────────────┘

  ArrowDown from index 0 → historyIndex = -1 (restore draft)
  Send message → historyIndex = -1 (reset)
  User types/modifies → historyIndex unchanged (stays in nav mode)
```

**Mapping**: `historyIndex` maps to `history[history.length - 1 - historyIndex]` (reverse chronological access into a chronologically-ordered array).

---

### 3. Draft Buffer (Ephemeral)

**Description**: A temporary store for any in-progress text the user had typed before initiating history navigation. Stored in a React ref (not state).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `draftBuffer` | `string` | Text content of the input field at the moment navigation begins | Can be empty string |

**Lifecycle**:
1. **Capture**: When `historyIndex` transitions from `-1` to `0`, save current input value to `draftBuffer`
2. **Hold**: While navigating (historyIndex ≥ 0), draftBuffer is unchanged
3. **Restore**: When `historyIndex` transitions from `0` to `-1` (via ArrowDown), restore input to `draftBuffer` value
4. **Discard**: When a message is sent (either recalled or new), draftBuffer is implicitly discarded (input is cleared, historyIndex resets to -1)

---

### 4. Navigation Mode Flag (Derived)

**Description**: A computed boolean indicating whether the user is currently browsing history. Used for visual feedback.

| Field | Type | Description | Derivation |
|-------|------|-------------|------------|
| `isNavigating` | `boolean` | `true` when browsing history | `historyIndex >= 0` |

**Usage**: Controls conditional CSS class on the textarea for visual feedback (FR-009).

## Relationships

```
┌──────────────────────┐       ┌────────────────────┐
│   Message History     │       │   useChatHistory   │
│   (localStorage)      │◄──────│   Hook State       │
│                       │ load  │                    │
│   string[]            │──────►│ history: string[]  │
│   max 100 entries     │       │ historyIndex: num  │
└──────────────────────┘       │ draftBuffer: ref   │
                                │ isNavigating: bool │
                                └────────┬───────────┘
                                         │ provides
                                         ▼
                                ┌────────────────────┐
                                │  ChatInterface.tsx  │
                                │                    │
                                │  textarea value    │
                                │  onKeyDown handler │
                                │  visual feedback   │
                                │  history button    │
                                └────────────────────┘
```

## Type Definitions

```typescript
/**
 * Return type of the useChatHistory hook
 */
interface UseChatHistoryReturn {
  /** Add a message to history (call after successful send) */
  addToHistory: (message: string) => void;
  
  /** Navigate up (older) in history. Returns the message to display, or null if no action. */
  navigateUp: (currentInput: string) => string | null;
  
  /** Navigate down (newer) in history. Returns the message to display, or null if no action. */
  navigateDown: () => string | null;
  
  /** Whether the user is currently browsing history (for visual feedback) */
  isNavigating: boolean;
  
  /** Reset navigation state (call after sending a message) */
  resetNavigation: () => void;
  
  /** Full history array (for mobile history button popover) */
  history: string[];
  
  /** Select a specific message from history by index (for mobile popover) */
  selectFromHistory: (index: number, currentInput: string) => string | null;
}
```
