# Quickstart: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering

**Feature Branch**: `026-chat-help-optimistic-render`
**Date**: 2026-03-07

## Prerequisites

- Node.js 20+ (check with `node --version`)
- Git (on branch `026-chat-help-optimistic-render`)
- Backend running at `localhost:8000` (for API proxy)

## Setup

```bash
# Switch to feature branch
git checkout 026-chat-help-optimistic-render

# Install dependencies (no new packages — existing deps only)
cd frontend
npm install

# Start dev server
npm run dev
```

The app is available at `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

## Verifying the Bug Fix (#help Auto-Repeat)

After applying the changes, verify the command state isolation:

1. Open the chat popup (click the chat bubble icon, bottom-right)
2. Type `#help` and press Enter
3. Verify: The help response appears (list of available commands)
4. Verify: The input field is empty
5. Type a normal message (e.g., "Hello") and press Enter
6. Verify: Only "Hello" is sent — no `#help` re-injection
7. Check the network tab: Only one `POST /api/chat/messages` request with `{ content: "Hello" }`

## Verifying Optimistic Message Rendering

1. Open the chat popup
2. Type any message and press Enter
3. Verify: Your message appears in the chat thread **immediately** (before server responds)
4. Verify: An animated thinking indicator (three bouncing dots) appears below your message
5. Wait for the agent response
6. Verify: The thinking indicator disappears and is replaced by the agent's response
7. Verify: No layout shift or duplicate messages

## Verifying Failed Message Handling

1. Stop the backend server (or disconnect from the network)
2. Open the chat popup and type a message
3. Press Enter
4. Verify: Your message appears immediately (optimistic)
5. Verify: After the request times out, the message shows a red error accent and "Failed to send" text
6. Verify: A retry button appears on the failed message
7. Restart the backend server
8. Click the retry button
9. Verify: The message re-sends successfully

## Running Tests

```bash
cd frontend

# Run only the useChat hook tests (fast — ~2 seconds)
npx vitest run src/hooks/useChat.test.tsx

# Run all chat-related component tests
npx vitest run src/components/chat/

# Run the full frontend test suite
npx vitest run

# Type checking
npx tsc --noEmit

# Linting
npx eslint src/
```

## Key Files Modified

| File | Purpose |
|------|---------|
| `frontend/src/types/index.ts` | Added `MessageStatus` type and optional `status` field to `ChatMessage` |
| `frontend/src/hooks/useChat.ts` | Optimistic message rendering, command state cleanup, retry logic |
| `frontend/src/hooks/useChat.test.tsx` | Regression tests for command isolation + optimistic rendering |
| `frontend/src/components/chat/ChatInterface.tsx` | Renders optimistic messages, passes retry callback |
| `frontend/src/components/chat/ChatPopup.tsx` | Passes `onRetryMessage` through to ChatInterface |
| `frontend/src/components/chat/MessageBubble.tsx` | Visual treatment for pending/failed states, retry button |

## Architecture Notes

### State Flow

```text
User input → ChatInterface.doSubmit()
  → useChat.sendMessage(content)
    → If command: execute locally, add to localMessages, return
    → If regular: add optimistic msg to localMessages, then sendMutation.mutateAsync()
      → onSuccess: remove optimistic msg, invalidate query cache
      → onError: mark optimistic msg as 'failed'

Messages rendered = [...serverMessages, ...localMessages]
```

### Why No Backend Changes?

The `#help` command is intercepted entirely on the frontend by the `useCommands` hook. It never reaches the backend API. The optimistic rendering is a UI-only concern — the backend API contract (`POST /api/chat/messages`, `GET /api/chat/messages`) is unchanged.
