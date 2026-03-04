# Data Model: Chat Message History Navigation

**Feature**: `018-chat-history-navigation` | **Date**: 2026-03-04

## Entities

### ChatHistory (localStorage — persisted)

The message history is stored as a JSON-serialized array of strings in `localStorage`. No database tables or backend changes are required.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `messages` | `string[]` | Max length: configurable (default 100) | Ordered array of previously sent messages, chronological (oldest first, newest last) |

**Storage key**: `"chat-message-history"`
**Serialization**: `JSON.stringify(messages)` / `JSON.parse(raw)`

### NavigationState (React state — ephemeral)

In-memory state managed by the `useChatHistory` hook. Not persisted.

| Field | Type | Description |
|-------|------|-------------|
| `historyIndex` | `number` | Current position in history during navigation. `-1` = not navigating (showing current input/draft). `0` = most recent entry, `N` = Nth entry from the end. |
| `draft` | `string` | Snapshot of the input field value captured when the user first presses Up Arrow. Restored when navigating past the newest entry with Down Arrow. |

### useChatHistory Hook Interface

Public API returned by the `useChatHistory` hook.

| Member | Type | Description |
|--------|------|-------------|
| `history` | `string[]` | Current history array (read-only) |
| `addToHistory` | `(message: string) => void` | Add a sent message to history. Handles deduplication, trimming, max cap, and persistence. |
| `handleHistoryNavigation` | `(e: React.KeyboardEvent<HTMLTextAreaElement>, currentInput: string, setInput: (v: string) => void) => boolean` | Process Up/Down Arrow keys for history navigation. Returns `true` if the event was handled (caller should not process further). Manages draft, index, cursor positioning, and multi-line detection. |
| `clearHistory` | `() => void` | Clear all stored history (with confirmation). Resets localStorage and in-memory state. |
| `isNavigating` | `boolean` | Whether the user is currently in history-navigation mode (index ≥ 0). |

### ChatHistoryStorage Utility Interface

Low-level storage abstraction in `chatHistoryStorage.ts`.

| Function | Signature | Description |
|----------|-----------|-------------|
| `loadHistory` | `() => string[]` | Read and parse history from localStorage. Returns `[]` on error or missing data. |
| `saveHistory` | `(messages: string[]) => void` | Serialize and write history to localStorage. No-op on error (graceful degradation). |
| `clearStoredHistory` | `() => void` | Remove the history key from localStorage. |

### Configuration Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `CHAT_HISTORY_STORAGE_KEY` | `"chat-message-history"` | localStorage key |
| `CHAT_HISTORY_MAX_ENTRIES` | `100` | Maximum number of stored messages |

## Relationships

```text
ChatInterface (component)
    │
    │ uses
    ▼
useChatHistory (hook)
    │
    │ reads/writes
    ▼
ChatHistoryStorage (utility)
    │
    │ persists to
    ▼
localStorage (browser)
```

## State Transitions

### Navigation State Machine

```text
                    ┌──────────────┐
   User types text  │  IDLE        │  historyIndex = -1
   normally         │  (draft = "") │  draft = ""
                    └───────┬──────┘
                            │
                            │ Up Arrow pressed
                            │ (save draft = current input)
                            ▼
                    ┌──────────────────┐
                    │  NAVIGATING      │  historyIndex = 0..N
                    │  (showing entry) │  draft = saved input
                    └───────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
     Up Arrow │    Down Arrow│    Down past│ newest
     (older)  │    (newer)  │             │
              ▼             ▼             ▼
        index + 1      index - 1   ┌──────────────┐
        (capped at     (if > 0)    │  IDLE        │
         history.len-1)            │  (restored)  │
                                   │  input=draft │
                                   └──────────────┘
                                         │
                                         │ User sends message
                                         │ or types new text
                                         ▼
                                   index reset to -1
                                   draft cleared
```

### History Array Lifecycle

```text
1. User sends non-empty message
2. Trim message, check not whitespace-only → skip if empty
3. Compare with last entry in history → skip if consecutive duplicate
4. If history.length >= MAX_ENTRIES → remove oldest (shift)
5. Append message to end (push)
6. Persist to localStorage
7. Reset navigation index to -1
```

## Validation Rules

- **Message content**: Must be non-empty after trimming (FR-012). Only whitespace → not stored.
- **Consecutive deduplication**: New message compared to `history[history.length - 1]`; skip if identical (FR-007).
- **History cap**: If `history.length >= CHAT_HISTORY_MAX_ENTRIES`, remove `history[0]` before appending (FR-005).
- **Multi-line detection**: Up Arrow blocked when `value.slice(0, selectionStart)` contains `\n` (FR-008). Down Arrow blocked when `value.slice(selectionEnd)` contains `\n` (FR-009).
- **Storage availability**: All `localStorage` operations wrapped in try/catch. On failure, history works in-memory only for the current session (FR-013).
