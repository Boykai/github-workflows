# Quickstart: Chat History Navigation

**Feature**: 001-chat-history-nav | **Date**: 2026-03-04 | **Phase**: 1

## Overview

This feature adds terminal-style Up/Down Arrow key navigation through previously sent chat messages. It introduces one new file (`useChatHistory.ts` hook) and modifies one existing file (`ChatInterface.tsx`).

## Prerequisites

- Node.js 18+ and npm
- Frontend dev server: `cd frontend && npm install && npm run dev`
- Familiarity with the existing `ChatInterface.tsx` and `useChat.ts` hook patterns

## New Files

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useChatHistory.ts` | Custom React hook managing history array, navigation pointer, draft buffer, and localStorage sync |

## Modified Files

| File | Change |
|------|--------|
| `frontend/src/components/chat/ChatInterface.tsx` | Import and integrate `useChatHistory` hook; extend `handleKeyDown` for history navigation; call `addToHistory` on send |

## Implementation Steps

### Step 1: Create the `useChatHistory` Hook

Create `frontend/src/hooks/useChatHistory.ts` implementing the contract defined in `contracts/useChatHistory.ts`:

```typescript
// Key exports:
// - useChatHistory(options?) → { history, addToHistory, handleKeyDown, isNavigating, resetNavigation }
// - MAX_HISTORY_SIZE = 100
// - STORAGE_KEY = 'chat-history'
```

**Internal state**:
- `history: string[]` via `useState` — the message array, synced to localStorage via `useEffect`
- `indexRef: React.MutableRefObject<number>` via `useRef` — navigation pointer (avoids stale closures)
- `draftRef: React.MutableRefObject<string>` via `useRef` — captured draft buffer

**Key behaviors**:
- `addToHistory(msg)`: Append to array (skip if consecutive duplicate), cap at MAX_HISTORY_SIZE, reset index to `history.length + 1` (new draft position), sync to localStorage
- `handleKeyDown(event, currentInput)`: Check ArrowUp/ArrowDown, verify cursor position, save/restore draft, return new input value or null
- localStorage init: Load on mount with try-catch, validate as string array, fallback to `[]`

### Step 2: Integrate into `ChatInterface.tsx`

```typescript
// 1. Import the hook
import { useChatHistory } from '@/hooks/useChatHistory';

// 2. Call the hook inside the component
const { addToHistory, handleKeyDown: handleHistoryKeyDown, isNavigating } = useChatHistory();

// 3. Extend the existing handleKeyDown (after autocomplete logic, before Enter handler)
const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
  // ... existing autocomplete logic ...

  // History navigation
  const newValue = handleHistoryKeyDown(e, input);
  if (newValue !== null) {
    setInput(newValue);
    return;
  }

  // ... existing Enter key logic ...
};

// 4. Call addToHistory in doSubmit
const doSubmit = () => {
  const content = input.trim();
  if (content && !isSending) {
    addToHistory(content);  // ← Add this line
    onSendMessage(content, { isCommand: commandInput });
    setInput('');
  }
};
```

### Step 3: Test Manually

1. Start the dev server: `cd frontend && npm run dev`
2. Open the chat interface
3. Send several messages
4. Press Up Arrow — should show most recent sent message
5. Press Up Arrow again — should show previous message
6. Press Down Arrow — should step forward through history
7. Press Down Arrow past newest — should restore draft
8. Refresh page — history should persist
9. Type partial message, press Up Arrow, then Down Arrow — original draft should restore

### Step 4: Run Automated Tests (Optional)

```bash
cd frontend
npx vitest run src/hooks/useChatHistory.test.ts  # If test file exists
npx vitest run                                      # Full test suite
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `useRef` for navigation index | Avoids stale closures in event handlers (vs. `useState`) |
| `history.length` as draft sentinel | Natural "one past end" value; cleaner than `-1` or `null` |
| String comparison for dedup | Simplest approach; input is already trimmed by `doSubmit` |
| try-catch around localStorage | Graceful degradation in private browsing or full storage |
| Hook returns `string \| null` from handleKeyDown | Lets ChatInterface decide whether to update input state; null = no navigation occurred |
