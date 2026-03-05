# Research: Chat Message History Navigation

**Feature**: 018-chat-history-navigation
**Date**: 2026-03-05
**Status**: Complete

## Research Tasks

### R1: localStorage Persistence Pattern for Chat History

**Context**: The feature requires persisting an array of message strings across sessions. Need to determine the best pattern consistent with the existing codebase.

**Decision**: Use direct `localStorage.getItem`/`setItem` with `JSON.parse`/`JSON.stringify` and `try-catch` error handling.

**Rationale**: This is the exact pattern already used in `ChatPopup.tsx` (lines 20–36) for persisting popup dimensions. It is simple, requires no additional dependencies, and handles storage unavailability gracefully (private browsing mode, quota exceeded). The codebase does not use a shared localStorage abstraction hook, so creating one would be premature.

**Alternatives Considered**:
- **IndexedDB**: More powerful but overkill for a simple string array of ≤100 entries. Adds async complexity.
- **sessionStorage**: Does not persist across browser tabs or page closes, violating FR-004.
- **Custom `useLocalStorage` hook (generic)**: Would be a new abstraction pattern not present in the codebase. Per Constitution Principle V (Simplicity/DRY), avoid premature abstraction.

---

### R2: Keyboard Event Handling for Arrow Key History Navigation

**Context**: The chat input already intercepts ArrowUp/ArrowDown for autocomplete navigation in `handleKeyDown`. Need to integrate history navigation without conflicting with autocomplete or multi-line cursor movement.

**Decision**: Add history navigation logic to the existing `handleKeyDown` function in `ChatInterface.tsx`, placed after the autocomplete guard block and before the Enter-to-submit logic. History navigation activates only when: (a) autocomplete is not active, (b) the cursor is on the first line of the textarea (for ArrowUp) or the last line (for ArrowDown), and (c) there is history to navigate.

**Rationale**: The existing `handleKeyDown` already has a clear pattern: check autocomplete first, then handle Enter. Adding history navigation between these two blocks maintains the priority order: autocomplete > history > default behavior. Checking `selectionStart` against the first newline position ensures multi-line editing is not disrupted (per FR-008 and the edge case in the spec).

**Alternatives Considered**:
- **Separate `onKeyDown` handler in the hook**: Would require merging two handlers or wrapping, adding complexity. The existing pattern is a single inline handler.
- **Global keyboard listener**: Would violate FR-007 (only intercept when input is focused). The textarea's `onKeyDown` naturally scopes to focus.

---

### R3: Multi-line Cursor Position Detection

**Context**: FR-008 requires that ArrowUp only triggers history navigation when the cursor is on the first line. Need a reliable way to detect this.

**Decision**: Check if `textarea.selectionStart` is less than or equal to the index of the first newline character in the input value (or the full length if no newline exists). If so, the cursor is on the first line and history navigation can activate. For ArrowDown, check if `selectionStart` is at or after the last newline.

**Rationale**: `selectionStart` is a standard DOM property available on all textarea elements. Comparing it to the first newline index is a simple, reliable heuristic. This avoids needing to measure rendered line wrapping (which would require complex DOM measurement).

**Alternatives Considered**:
- **Measuring rendered lines with `getClientRects`**: Accurate for wrapped lines but complex, fragile, and not needed — the spec only mentions "first line" in the context of multi-line content (newline-delimited), not visual wrapping.
- **Disabling history navigation entirely for multi-line inputs**: Too restrictive; users should still be able to navigate history when the cursor is at the top.

---

### R4: Draft Buffer Management

**Context**: The spec requires preserving any in-progress text when the user enters history navigation, and restoring it when they navigate past the most recent message.

**Decision**: Store the draft in a React `useRef` (not state) within the `useChatHistory` hook. Capture the current input value into the ref when `historyIndex` transitions from -1 (not navigating) to 0 (first history entry). Restore from the ref when navigating back to index -1.

**Rationale**: A `useRef` avoids unnecessary re-renders when the draft is captured. The draft is ephemeral (only needed during a single navigation session) and does not need to trigger UI updates itself — only the `historyIndex` change triggers the input value update.

**Alternatives Considered**:
- **React `useState` for draft**: Would cause an extra render cycle when capturing the draft. Since the draft value is not directly displayed (only restored later), `useRef` is more appropriate.
- **Storing draft in localStorage**: Unnecessary persistence; the draft is a transient UX concept within a single interaction.

---

### R5: Visual Feedback for History Navigation Mode

**Context**: FR-009 recommends a subtle visual indicator when the user is browsing history.

**Decision**: Apply a conditional CSS class to the textarea when `historyIndex >= 0` (navigating history). The class adds a distinct left border color (e.g., `border-l-4 border-l-primary`) and a subtle background tint. The `useChatHistory` hook exposes an `isNavigating` boolean for this purpose.

**Rationale**: A left border accent is visually subtle yet noticeable, consistent with common "quote" or "referenced content" UI patterns. It does not obscure the text or compete with the focus ring. Using Tailwind utility classes keeps it consistent with the existing styling approach.

**Alternatives Considered**:
- **Tooltip or floating label**: More intrusive; could obscure the input or surrounding UI.
- **Icon in the input field**: Requires absolute positioning within the textarea wrapper; more complex layout changes.
- **Background color change only**: Too subtle on its own; may not meet accessibility contrast requirements.

---

### R6: Mobile/Touch History Access (P3)

**Context**: FR-010 recommends an accessible alternative for devices without physical keyboards.

**Decision**: Add a small history button (clock/history icon from Lucide React) adjacent to the textarea. Tapping it opens a scrollable dropdown/popover listing the last N messages. Tapping a message populates the input field. The button is always visible but disabled when history is empty.

**Rationale**: A button is the simplest, most discoverable pattern for touch users. It does not require gesture detection (swipe) which is unreliable and conflicts with scroll. Lucide React is already a project dependency (used throughout the UI), so no new icon library is needed.

**Alternatives Considered**:
- **Swipe gesture on input**: Unreliable; conflicts with text selection and page scrolling. Not discoverable.
- **Long-press on input**: Not discoverable; no visual affordance.
- **Separate history panel/page**: Over-engineered for this scope; a simple popover is sufficient.

---

### R7: Storage Key Strategy

**Context**: The spec assumes a single chat context per page. Need to determine the localStorage key.

**Decision**: Use a single key `chat-message-history` storing a JSON-serialized string array. No per-user or per-conversation scoping.

**Rationale**: The spec's Assumptions section explicitly states "single chat context per page" and "history is not scoped per conversation or per user." Adding scoping would be premature (YAGNI per Constitution Principle V). The key name follows the pattern of `chat-popup-size` already used in the codebase.

**Alternatives Considered**:
- **Per-conversation key (e.g., `chat-history-{conversationId}`)**: Out of scope per spec assumptions.
- **Per-user key**: Out of scope; the app has a single chat context.

## Summary of Decisions

| Topic | Decision | Key Rationale |
|-------|----------|---------------|
| Persistence | Direct localStorage with try-catch | Matches existing ChatPopup.tsx pattern |
| Key handling | Extend existing `handleKeyDown` in ChatInterface | Maintains single-handler pattern; priority: autocomplete > history > default |
| Multi-line detection | Compare `selectionStart` to first newline index | Simple, reliable, standard DOM API |
| Draft buffer | `useRef` in useChatHistory hook | Avoids unnecessary re-renders |
| Visual feedback | Conditional left border + background tint via Tailwind classes | Subtle, accessible, consistent with codebase |
| Mobile access | History button with Lucide icon + popover | Discoverable, simple, uses existing icon library |
| Storage key | Single `chat-message-history` key | Matches spec's single-context assumption |
