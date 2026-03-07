# Component Contracts: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering

**Feature Branch**: `026-chat-help-optimistic-render`
**Date**: 2026-03-07

> No new API endpoints or routes are created. This feature modifies only frontend component interfaces. This document defines the contracts between modified components.

## Modified Component Interfaces

### useChat Hook → ChatInterface / ChatPopup

The `useChat` hook is the single source of truth for chat state. It provides messages, sending state, and action callbacks to the UI layer.

**Contract changes**:

| Property | Type | Change | Description |
|----------|------|--------|-------------|
| `messages` | `ChatMessage[]` | MODIFIED | Now includes optimistic messages with `status: 'pending'` in the array. Messages are ordered: `[...serverMessages, ...localMessages]`. Optimistic messages appear at the end. |
| `isSending` | `boolean` | UNCHANGED | Still derived from `sendMutation.isPending`. Now true *after* the optimistic message is appended. |
| `retryMessage` | `(messageId: string) => Promise<void>` | NEW | Retry a failed message. Finds the message in `localMessages` by ID, resets status to `'pending'`, and re-executes the send mutation. |
| `sendMessage` | `(content: string, options?) => Promise<void>` | MODIFIED | For non-command messages: now appends an optimistic user message to `localMessages` *before* calling `sendMutation`. On success, removes the optimistic message. On failure, marks it as `'failed'`. For command messages: behavior unchanged (local messages added synchronously). |

### ChatInterface → MessageBubble

The `ChatInterface` renders a `MessageBubble` for each message. The contract is extended to support failed message retry.

**Contract changes**:

| Prop | Type | Change | Description |
|------|------|--------|-------------|
| `message` | `ChatMessage` | MODIFIED | May now include `status: 'pending' \| 'failed' \| undefined`. The bubble renders differently based on status. |
| `onRetry` | `() => void` | NEW | Optional. When provided and `message.status === 'failed'`, renders a retry button. Clicking calls `onRetry()`. |

### ChatPopup → ChatInterface (pass-through)

`ChatPopup` is a thin wrapper that passes all props to `ChatInterface`. The only addition is the `onRetryMessage` prop.

| Prop | Type | Change | Description |
|------|------|--------|-------------|
| `onRetryMessage` | `(messageId: string) => void` | NEW | Passed through to `ChatInterface`, which passes it to `MessageBubble` as `onRetry` (bound to the specific message ID). |

## Visual Contracts

### Message States

| State | Visual Treatment | Trigger |
|-------|-----------------|---------|
| Default (no status) | Normal bubble styling (blue for user, gray for assistant) | Server-confirmed messages |
| `pending` | Normal bubble styling (identical to default — no jarring indicator during normal flow) | Optimistic message immediately after send |
| `failed` | Red/destructive border accent + error icon + "Failed to send" text + Retry button | `sendMutation` error |

### Thinking Indicator

| State | Visual | Position |
|-------|--------|----------|
| `isSending === true` | Three animated bouncing dots (existing implementation) | Below the last message in the thread (after optimistic user message) |
| `isSending === false` | Hidden | N/A |

### Message Ordering

```text
┌─────────────────────────────┐
│ Server message (assistant)  │  ← from messagesData.messages
│ Server message (user)       │  ← from messagesData.messages
│ Server message (assistant)  │  ← from messagesData.messages
│ Optimistic message (user)   │  ← from localMessages, status: 'pending'
│ [Thinking indicator]        │  ← shown when isSending === true
│                             │
│ ↕ auto-scroll anchor        │
└─────────────────────────────┘
```

## Behavioral Contracts

### Command Dispatch (Bug Fix)

**Precondition**: User sends a message starting with `#` or matching `help` exactly.

**Postcondition**: After command execution completes:
1. The input field is empty (`setInput('')` called)
2. The history navigation is reset (`resetNavigation()` called)
3. No command reference exists in any state that could be re-injected
4. The `isCommand` flag from `options` is not stored or persisted
5. Subsequent calls to `sendMessage()` evaluate `isCommand()` fresh on the new content

**Invariant**: `isCommand(content)` is a pure function of `content` only — no side effects, no stored state.

### Optimistic Message Dispatch

**Precondition**: User sends a non-command message.

**Postcondition (success path)**:
1. Optimistic `ChatMessage` with `status: 'pending'` appears in `messages` array within one React render cycle
2. `sendMutation` begins → `isSending` becomes true → thinking indicator appears
3. Server responds → `onSuccess` removes optimistic message from `localMessages` and invalidates query cache
4. Refetched `messagesData` includes server-confirmed user message + agent response
5. Thinking indicator disappears, agent response renders

**Postcondition (failure path)**:
1. Optimistic `ChatMessage` with `status: 'pending'` appears in `messages` array within one React render cycle
2. `sendMutation` begins → `isSending` becomes true → thinking indicator appears
3. Server error → `onError` sets optimistic message `status` to `'failed'`
4. Thinking indicator disappears, failed message shows error styling + retry button
5. User clicks retry → message status resets to `'pending'`, `sendMutation` re-executes

### No Backend API Changes

| Endpoint | Status |
|----------|--------|
| `POST /api/chat/messages` | UNCHANGED — request/response schema identical |
| `GET /api/chat/messages` | UNCHANGED — returns `ChatMessagesResponse` |
| `POST /api/chat/clear` | UNCHANGED |
| `POST /api/chat/proposals/:id/confirm` | UNCHANGED |
| `POST /api/chat/proposals/:id/cancel` | UNCHANGED |
