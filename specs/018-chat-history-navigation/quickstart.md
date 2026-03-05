# Quickstart: Chat Message History Navigation

**Feature**: 018-chat-history-navigation
**Date**: 2026-03-05

## Overview

This feature adds shell-like message history navigation to the chat input. Users press Up/Down arrow keys to cycle through previously sent messages. History persists across sessions via localStorage.

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│                  ChatInterface.tsx                    │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ <textarea>                                    │   │
│  │   onKeyDown → ArrowUp/ArrowDown → hook calls │   │
│  │   value ← hook return values                  │   │
│  │   className ← isNavigating visual feedback    │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────┐  ┌──────────────────────────────┐    │
│  │ [History] │  │ useChatHistory hook           │    │
│  │  button   │  │   history[]  ← localStorage   │    │
│  │  (mobile) │  │   historyIndex (state)        │    │
│  └──────────┘  │   draftBuffer (ref)           │    │
│                 │   isNavigating (derived)       │    │
│                 └──────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Key Files

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/hooks/useChatHistory.ts` | **Create** | Custom hook: history storage, navigation state, localStorage persistence |
| `frontend/src/components/chat/ChatInterface.tsx` | **Modify** | Integrate hook: keydown handling, visual feedback, history button |
| `frontend/src/hooks/useChatHistory.test.ts` | **Create** (optional) | Unit tests for the hook |

## Implementation Steps (High Level)

### Step 1: Create `useChatHistory` Hook

```typescript
// frontend/src/hooks/useChatHistory.ts
export function useChatHistory(options?: { storageKey?: string; maxHistory?: number }) {
  // 1. Load history from localStorage on mount
  // 2. Manage historyIndex state (-1 = not navigating)
  // 3. Manage draftBuffer ref
  // 4. Expose: addToHistory, navigateUp, navigateDown, resetNavigation, isNavigating, history, selectFromHistory
}
```

### Step 2: Integrate into ChatInterface.tsx

1. Import and call the hook
2. Add history navigation to `handleKeyDown` (after autocomplete, before Enter)
3. Add `addToHistory(trimmed)` and `resetNavigation()` to `doSubmit`
4. Add visual feedback class to textarea
5. Add cursor-to-end effect when navigating
6. Add history button for mobile (P3 — can be deferred)

### Step 3: Test

```bash
cd frontend && npx vitest run src/hooks/useChatHistory.test.ts
```

## User Story → Code Mapping

| Story | Priority | Implementation |
|-------|----------|----------------|
| US1: Up arrow recall | P1 | `navigateUp()` in hook + ArrowUp in handleKeyDown |
| US2: Down arrow + draft restore | P1 | `navigateDown()` in hook + ArrowDown in handleKeyDown + draftBuffer ref |
| US3: Persist across sessions | P2 | localStorage read on mount, write on addToHistory |
| US4: Cursor at end | P2 | `useEffect` to set `selectionStart`/`selectionEnd` after input change |
| US5: Visual feedback | P2 | `isNavigating` boolean → conditional Tailwind class on textarea |
| US6: Mobile history button | P3 | History button + popover with `history[]` + `selectFromHistory()` |

## Dependencies

- **No new npm packages required**
- Uses existing: React 18.3, Tailwind CSS 3.4, Lucide React (History icon)
- localStorage API (browser built-in)

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| localStorage unavailable (private browsing) | try-catch with graceful fallback to in-session history |
| Conflict with autocomplete ArrowUp/Down | Autocomplete check runs first in handleKeyDown; history only activates when autocomplete is inactive |
| Multi-line cursor movement disrupted | `selectionStart` check against first newline index ensures ArrowUp only triggers history on first line |
| Performance with 100 entries | JSON parse of 100 strings is < 1ms; localStorage read is synchronous but fast for small payloads |
