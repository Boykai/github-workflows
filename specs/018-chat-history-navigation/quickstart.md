# Quickstart: Chat Message History Navigation

**Feature**: `018-chat-history-navigation` | **Date**: 2026-03-04

## Overview

Chat message history navigation adds terminal-style Up/Down Arrow key support to the chat input field. Users can cycle through previously sent messages, reducing the need to retype repetitive commands or messages.

## Prerequisites

- Running frontend instance (`cd frontend && npm run dev` or via `docker compose up`)
- A chat session in the app (navigate to the project board and open the chat)

## Quick Walkthrough

### Navigating History

1. Open the chat interface on the project board page
2. Send a few messages (e.g., "Hello", "#help", "Create a task")
3. With the chat input focused, press **Up Arrow** — the input fills with your most recently sent message
4. Press **Up Arrow** again — the input shows the next older message
5. Press **Down Arrow** — the input moves forward to a more recent message
6. Press **Down Arrow** past the newest message — your original draft text is restored

### Persistence

1. Send several messages in the chat
2. Refresh the browser page (F5 or Cmd/Ctrl+R)
3. Focus the chat input and press **Up Arrow**
4. Your previously sent messages are still available

### Multi-Line Input

1. Type a multi-line message using **Shift+Enter** to create new lines
2. While the cursor is in the middle of the text, press **Up Arrow** — the cursor moves up within the text (normal behavior)
3. Move the cursor to the very first line, then press **Up Arrow** — history navigation activates

### Clearing History

1. Click the **Clear History** button (or invoke the clear action)
2. A confirmation dialog appears
3. Confirm to permanently delete all stored message history
4. Press **Up Arrow** — nothing happens (history is empty)

## Key Files

### Frontend (all changes)

| File | Role |
|------|------|
| `frontend/src/hooks/useChatHistory.ts` | Core hook — manages history array, navigation index, draft, persistence |
| `frontend/src/utils/chatHistoryStorage.ts` | localStorage wrapper — load, save, clear with graceful error handling |
| `frontend/src/components/chat/ChatInterface.tsx` | Integration point — calls hook in `handleKeyDown` and `doSubmit` |

### Specification

| File | Content |
|------|---------|
| `specs/018-chat-history-navigation/spec.md` | Feature spec with user stories and requirements |
| `specs/018-chat-history-navigation/plan.md` | Implementation plan (this feature) |
| `specs/018-chat-history-navigation/research.md` | Research decisions |
| `specs/018-chat-history-navigation/data-model.md` | Data model and state machine |
| `specs/018-chat-history-navigation/contracts/chat-history-hook.md` | Hook interface contract |

## How It Works

```
User types → input state
     │
     │ Press Up Arrow
     ▼
useChatHistory hook
     │
     ├─ Check: autocomplete active? → skip (let autocomplete handle)
     ├─ Check: multi-line, cursor not on first line? → skip (normal cursor movement)
     ├─ Check: empty history? → skip (no change)
     │
     ├─ First Up press: save draft, load newest history entry
     ├─ Subsequent Up: load next older entry (stop at oldest)
     ├─ Down press: load next newer entry
     └─ Down past newest: restore draft
          │
          ▼
     Update input field + position cursor at end
```

## Configuration

| Setting | Default | Location |
|---------|---------|----------|
| Storage key | `"chat-message-history"` | `chatHistoryStorage.ts` |
| Max entries | `100` | `useChatHistory.ts` |

These are constants defined in the source code. To change them, modify the values directly.
