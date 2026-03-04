# Research: Chat History Navigation

**Feature**: 001-chat-history-nav | **Date**: 2026-03-04 | **Phase**: 0

## Research Tasks

### 1. localStorage Persistence Strategy

**Context**: The feature requires chat history to persist across page refreshes and browser sessions (FR-006, FR-012).

**Decision**: Use `localStorage` with a namespaced key pattern `chat-history:{context}`, serialized as JSON array of strings.

**Rationale**:
- The existing codebase already uses `localStorage` for chat popup size persistence in `ChatPopup.tsx` (line 17: `const STORAGE_KEY = 'chat-popup-size'`), establishing a proven pattern.
- `localStorage` provides synchronous read/write, which is ideal for the instantaneous-feel requirement (SC-001).
- The 100-message cap (FR-007) with average message length of ~200 chars results in ~20KB storage, well within the ~5-10MB localStorage quota per origin.
- `sessionStorage` was rejected because it does not persist across browser tab closes (violates FR-006).
- IndexedDB was rejected as overkill for a simple string array — it adds async complexity for no benefit at this scale.

**Alternatives Considered**:
- `sessionStorage`: Does not persist across browser sessions. Rejected.
- `IndexedDB`: Asynchronous API adds unnecessary complexity for a small dataset. Rejected.
- Cookie storage: 4KB limit is too restrictive. Rejected.

### 2. Keyboard Event Interception Strategy

**Context**: The feature must intercept ArrowUp/ArrowDown key events without conflicting with autocomplete navigation, multiline cursor movement, or form submission (FR-008, FR-011, FR-013, FR-014).

**Decision**: Extend the existing `handleKeyDown` function in `ChatInterface.tsx` to check for history navigation conditions after the existing autocomplete logic, using cursor position detection to avoid conflicts with multiline editing.

**Rationale**:
- `ChatInterface.tsx` already has a `handleKeyDown` handler (line 112) that manages autocomplete ArrowUp/ArrowDown and Enter key events. Adding history navigation as a subsequent condition maintains the existing priority order: autocomplete first, then history navigation, then default behavior.
- `preventDefault()` must be called to stop the browser from moving the cursor to the start/end of the input (FR-011).
- Cursor position detection uses `textarea.selectionStart` and `textarea.selectionEnd` to determine if the cursor is at the beginning (for ArrowUp, FR-013) or end (for ArrowDown, FR-014) of the input.

**Alternatives Considered**:
- Separate event listener via `useEffect` + `addEventListener`: Creates ordering ambiguity with React's synthetic events. Rejected.
- Global keyboard shortcut system: Over-engineered for two keys in one component. Rejected.

### 3. History Navigation State Management

**Context**: The hook must manage a history array, a navigation pointer, and a draft buffer (spec Key Entities).

**Decision**: Implement a `useChatHistory` custom hook with `useState` for the history array and draft buffer, `useRef` for the navigation index (to avoid stale closures in event handlers), and `useEffect` for localStorage synchronization.

**Rationale**:
- `useRef` for the navigation index avoids the stale-closure problem that would occur if the index were in `useState` and read inside the `onKeyDown` handler (the handler captures the state value at render time, not at event time).
- `useState` for the history array triggers re-renders when history changes, which is needed for the `useEffect` that syncs to localStorage.
- The draft buffer captures the current input value when navigation begins (first ArrowUp press from the draft position) and restores it when navigating past the newest entry (ArrowDown from position 0).

**Alternatives Considered**:
- `useReducer`: Adds unnecessary boilerplate for this level of state complexity. The state transitions are simple enough for individual `useState` calls. Rejected.
- External state library (Zustand, Jotai): Over-engineered; the hook is self-contained and doesn't need cross-component state sharing. Rejected.

### 4. Sentinel Index Design for Draft Position

**Context**: The navigation pointer must represent both history positions and a "draft" position beyond the newest entry (FR-003, FR-010).

**Decision**: Use `history.length` as the sentinel value for the draft position. Navigation index ranges from `0` (oldest message) to `history.length` (draft position).

**Rationale**:
- `history.length` naturally represents "one past the end" of the array, making bounds checking intuitive: `index < history.length` means we're in history, `index === history.length` means we're at the draft.
- ArrowUp decrements the index (moving toward older messages), ArrowDown increments it (moving toward newer messages and eventually the draft).
- This avoids the confusion of negative sentinel values (e.g., `-1`) which would require special-case math throughout the navigation logic.

**Alternatives Considered**:
- Sentinel value `-1` for draft: Requires additional branching logic and is less intuitive when computing bounds. Rejected.
- Nullable index (`null` = draft): TypeScript null checks add friction without clarity benefit. Rejected.

### 5. Consecutive Deduplication Strategy

**Context**: The system should deduplicate consecutive identical messages in history (FR-009).

**Decision**: Before appending a new message to the history array, compare it with the last entry. If they are identical (strict string equality), skip the append.

**Rationale**:
- This is the simplest possible deduplication — a single string comparison at append time.
- Only consecutive duplicates are suppressed per the spec (FR-009): "sending the same message twice in a row should only add one history entry." Non-consecutive duplicates are preserved.
- No normalization (trim, case-insensitive) is applied — the comparison uses the exact sent message string, which is already trimmed by the existing `doSubmit` logic in `ChatInterface.tsx` (line 96: `const content = input.trim()`).

**Alternatives Considered**:
- Full deduplication (remove all duplicates): Violates spec — only consecutive duplicates should be suppressed. Rejected.
- Hash-based deduplication: Unnecessary complexity for a simple string comparison. Rejected.

### 6. localStorage Error Handling

**Context**: The system must gracefully handle unavailable or full localStorage (FR-012, edge case from spec).

**Decision**: Wrap all `localStorage` operations in try-catch blocks. On read failure (corrupt data or unavailable storage), initialize with an empty history array and log a console warning. On write failure (storage full), silently continue with in-memory-only history.

**Rationale**:
- This matches the existing pattern in `ChatPopup.tsx` (line 30: `catch { /* ignore */ }`).
- Private browsing modes in some browsers restrict localStorage. The feature should degrade to in-memory history without user-visible errors.
- Corrupt JSON data (e.g., manually edited localStorage) is handled by `JSON.parse` throwing, which the catch block handles.

**Alternatives Considered**:
- Show user notification on storage failure: Spec explicitly states "no errors should be shown to the user." Rejected.
- Retry with reduced history size on quota exceeded: Unnecessary complexity for an edge case. Rejected.
