# Data Model: Chat History Navigation

**Feature**: 001-chat-history-nav | **Date**: 2026-03-04 | **Phase**: 1

## Entities

### 1. History List

An ordered array of previously sent message strings, persisted to localStorage.

| Field | Type | Description |
|-------|------|-------------|
| messages | `string[]` | Chronologically ordered array of sent message strings. Index 0 is the oldest, index `length - 1` is the most recent. |

**Validation Rules**:
- Maximum capacity: 100 entries (configurable via `MAX_HISTORY_SIZE` constant)
- Each entry is a non-empty trimmed string (guaranteed by existing `doSubmit` logic)
- Consecutive duplicates are rejected at append time (FR-009)
- When capacity is reached, the oldest entry (index 0) is evicted before appending (FR-007)

**Storage**:
- localStorage key: `chat-history` (single chat context for current app)
- Serialized as: `JSON.stringify(messages)`
- Deserialized with validation: must be a JSON array of strings; invalid data → empty array

### 2. Navigation Pointer

A numeric index tracking the user's current position within the history list during keyboard navigation.

| Field | Type | Description |
|-------|------|-------------|
| index | `number` | Current position in the history array. Range: `0` to `history.length`. Value `history.length` is the sentinel for the "draft" position. |

**State Transitions**:

```
                 ArrowUp (index > 0)
            ┌──────────────────────────┐
            │                          │
            ▼                          │
  ┌──────────────┐    ArrowUp    ┌─────┴────────┐    ArrowUp    ┌──────────────┐
  │  Oldest (0)  │◄─────────────│  Middle (1…n) │◄─────────────│  Draft (len) │
  └──────────────┘              └───────────────┘              └──────────────┘
            │                          ▲                          ▲
            │                          │                          │
            └──────────────────────────┘                          │
                 ArrowDown (index < len)                          │
                                       └──────────────────────────┘
                                           ArrowDown (index < len)
```

**Rules**:
- **ArrowUp**: If `index > 0`, decrement by 1. If `index === history.length` (at draft), save current input as draft first, then set `index = history.length - 1`.
- **ArrowDown**: If `index < history.length`, increment by 1. If new `index === history.length`, restore draft buffer to input.
- **On Send**: Reset `index` to `history.length` (new draft position, since history just grew by 1).
- **At bounds**: ArrowUp at index 0 → no change. ArrowDown at index `history.length` → no change.

### 3. Draft Buffer

A temporary string storing the user's in-progress input text at the moment history navigation begins.

| Field | Type | Description |
|-------|------|-------------|
| draft | `string` | The input value captured when the user first presses ArrowUp from the draft position. May be an empty string. |

**Lifecycle**:
1. **Captured**: When `index` transitions from `history.length` (draft) to `history.length - 1` (first ArrowUp into history), the current input value is saved.
2. **Restored**: When `index` transitions back to `history.length` (via ArrowDown past the newest entry), the draft value replaces the input.
3. **Cleared**: When a message is successfully sent, the draft buffer is reset to an empty string (the input is cleared by the send logic anyway).

## Relationships

```
┌─────────────────────────────────┐
│       useChatHistory Hook       │
│                                 │
│  ┌───────────┐  ┌───────────┐  │
│  │  History   │  │Navigation │  │
│  │  List      │  │ Pointer   │  │
│  │ string[]   │  │ number    │  │
│  └─────┬─────┘  └─────┬─────┘  │
│        │              │         │
│        │  ┌───────────┘         │
│        │  │                     │
│  ┌─────▼──▼──┐                  │
│  │   Draft   │                  │
│  │   Buffer  │                  │
│  │   string  │                  │
│  └───────────┘                  │
│                                 │
│  ← syncs to localStorage →     │
└────────────────┬────────────────┘
                 │
                 │ provides: handleKeyDown, addToHistory, currentValue
                 ▼
┌─────────────────────────────────┐
│      ChatInterface Component    │
│                                 │
│  textarea ←→ input state        │
│  onKeyDown → hook.handleKeyDown │
│  doSubmit → hook.addToHistory   │
└─────────────────────────────────┘
```

## Configuration Constants

| Constant | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_HISTORY_SIZE` | `number` | `100` | Maximum number of messages stored in history (FR-007) |
| `STORAGE_KEY` | `string` | `'chat-history'` | localStorage key for persisting history |
