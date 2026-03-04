# Research: Chat Message History Navigation

**Feature**: `018-chat-history-navigation` | **Date**: 2026-03-04

## Research Tasks

### R1: localStorage vs IndexedDB for History Persistence

**Decision**: Use `localStorage` with a JSON-serialized string array. Wrap access in a utility module (`chatHistoryStorage.ts`) that catches exceptions for graceful degradation.

**Rationale**: The history is a simple array of strings with a maximum of 100 entries. At an average of 200 characters per message, 100 entries ≈ 20KB — well within `localStorage`'s typical 5MB limit. `localStorage` is synchronous, which simplifies the hook implementation and avoids async complexity in keyboard event handlers. The spec explicitly suggests `localStorage` as the primary approach.

**Alternatives considered**:
- **IndexedDB**: More powerful but adds unnecessary async complexity for a bounded, small dataset. The spec suggests migrating to IndexedDB only if payloads grow large or multi-tab sync is required — neither applies to the initial implementation.
- **sessionStorage**: Rejected — does not persist across browser sessions (FR-006).
- **In-memory only**: Rejected — fails FR-006 (persistence across sessions).

### R2: Multi-Line Cursor Position Detection Strategy

**Decision**: Use `selectionStart` / `selectionEnd` and scan for newline characters (`\n`) in the textarea value to determine whether the cursor is on the first or last line.

**Rationale**: The spec requires that Up/Down Arrow keys only trigger history navigation when the cursor is on the first line (Up) or last line (Down) of a multi-line input. The detection algorithm:
- **Up Arrow**: Check if the substring `value.slice(0, selectionStart)` contains any `\n`. If no `\n` → cursor is on the first line → allow history navigation. If `\n` exists → cursor is below the first line → let default browser behavior handle cursor movement.
- **Down Arrow**: Check if the substring `value.slice(selectionEnd)` contains any `\n`. If no `\n` → cursor is on the last line → allow history navigation. If `\n` exists → cursor is above the last line → let default behavior handle it.

**Alternatives considered**:
- **`getClientRects()` / visual line detection**: Over-complex; handles word-wrap but the textarea uses `resize-none` with `max-h-[400px]` and `overflow-y-auto`, so logical lines (based on `\n`) are sufficient for the current UI.
- **Disable history in multi-line entirely**: Simpler but violates FR-008/FR-009 acceptance scenarios which require first/last line detection.

### R3: Draft Preservation Strategy

**Decision**: Store the draft as an ephemeral value in the hook's React state (not persisted to `localStorage`). When the user first presses Up Arrow (transitioning from index -1 to 0), capture the current input value as the draft. When the user presses Down Arrow past the newest history entry (transitioning to index -1), restore the draft.

**Rationale**: The draft is transient — it only matters during a single navigation session. Persisting it to storage adds complexity without user benefit. The navigation index uses -1 to represent "not navigating / showing draft" and 0..N to represent positions in the history array (0 = most recent).

**Alternatives considered**:
- **Persist draft to localStorage**: Over-engineering for a transient value; the draft is only relevant while the user is actively navigating.
- **No draft preservation**: Violates FR-003 (must restore draft when navigating past newest entry).

### R4: Integration Point in ChatInterface

**Decision**: The `useChatHistory` hook exposes a `handleHistoryKeyDown` function that is called from the existing `handleKeyDown` handler in `ChatInterface.tsx`. The hook also exposes `addToHistory` which is called when a message is successfully sent (inside `doSubmit`). The hook directly manages the input value when navigating history.

**Rationale**: The existing `ChatInterface` already has a `handleKeyDown` handler that manages autocomplete navigation. History navigation is added as an additional check after autocomplete handling. The hook pattern (`useChatHistory`) follows the established codebase convention (`useChat`, `useCommands`, `useBoardRefresh`).

**Alternatives considered**:
- **Modify `useChat` hook directly**: Rejected — `useChat` manages server-side message fetching and mutations, not client-side input state. Mixing concerns would violate SRP.
- **HOC or context provider**: Over-abstraction for a single component integration. The hook pattern is simpler and matches existing patterns.

### R5: History Storage Key and Scoping

**Decision**: Use a single `localStorage` key: `"chat-message-history"`. History is shared across all conversations (not scoped per conversation/project).

**Rationale**: The spec's assumptions state "History is scoped per user/session context — if multiple chat conversations exist, history may be shared or scoped per conversation (assumed shared unless otherwise specified)." The app is single-user (one authenticated session at a time), so a single key is sufficient. The storage key is defined as a constant for easy future change.

**Alternatives considered**:
- **Per-project key** (e.g., `chat-history-{projectId}`): More granular but adds complexity. Would require passing `projectId` into the hook. Not required by spec.
- **Per-conversation key**: Even more granular but conversations are transient (server-managed sessions). Not practical.

### R6: Consecutive Deduplication Strategy

**Decision**: Before adding a new message to history, compare it with the last entry in the array. If they are identical (exact string match after trimming), skip the addition. This is a SHOULD requirement (FR-007).

**Rationale**: Simple string comparison is sufficient. The spec only requires deduplicating *consecutive* identical messages, not all duplicates across the entire history. This prevents the common case of a user re-sending the same command multiple times in a row from cluttering history.

**Alternatives considered**:
- **Full deduplication across all entries**: Over-scoped — the spec explicitly says "consecutive identical messages."
- **Case-insensitive deduplication**: Not specified; exact match is simpler and more predictable.

### R7: Clear History UX Pattern

**Decision**: Add a "Clear History" option accessible via a button or link near the chat input area. Use a `window.confirm()` dialog for confirmation before deletion. This aligns with the P3 user story.

**Rationale**: `window.confirm()` is the simplest confirmation mechanism and matches the requirement for a confirmation prompt. A custom modal would be over-engineering for a P3 feature. The clear action resets both `localStorage` and the in-memory history array.

**Alternatives considered**:
- **Custom confirmation modal**: More polished but higher implementation cost for a P3 feature. Can be upgraded later.
- **Settings page integration**: The spec suggests "a settings option or a dedicated clear-history button." A button near the input is more discoverable and doesn't require navigation.

### R8: `event.preventDefault()` Strategy

**Decision**: Call `event.preventDefault()` only when history navigation is actually triggered (i.e., when the arrow key press results in a history entry being loaded or the draft being restored). Do not prevent default when the key press is a no-op (e.g., Up at oldest entry, Down when not navigating).

**Rationale**: This preserves native browser behavior (cursor movement in multi-line text, scrolling) when history navigation doesn't apply. The spec states: "calling `event.preventDefault()` to suppress default cursor movement only when navigation is valid."

**Alternatives considered**:
- **Always prevent default on Up/Down**: Would break normal cursor movement in multi-line input.
- **Never prevent default**: Would cause cursor movement simultaneously with history navigation, creating jarring UX.

## Summary

All research tasks resolved. No NEEDS CLARIFICATION items remain. Key architectural decisions:
1. Use `localStorage` with JSON-serialized string array (bounded at 100 entries)
2. Detect cursor line position via `selectionStart`/`selectionEnd` + newline scanning
3. Ephemeral draft stored in React state, not persisted
4. New `useChatHistory` hook integrated into existing `ChatInterface.handleKeyDown`
5. Shared history (single `localStorage` key), not scoped per conversation
6. Consecutive deduplication via simple last-entry comparison
7. `window.confirm()` for clear history confirmation (P3)
8. `event.preventDefault()` only when navigation is valid
