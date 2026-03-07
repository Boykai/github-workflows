# Research: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering

**Feature Branch**: `026-chat-help-optimistic-render`
**Date**: 2026-03-07

## R1: Root Cause of #help Auto-Repeat Bug

**Decision**: The bug is caused by the chat history navigation system (`useChatHistory`) combined with how `ChatInterface.tsx` handles command submission. When a user sends `#help`, the command string is added to the message history via `addToHistory(content)` in `doSubmit()`. On subsequent messages, if the user presses ArrowUp or the history state is not properly reset, the `#help` command is re-injected into the input field. Additionally, the `onSendMessage` callback receives `{ isCommand: true }` as the options parameter — if any upstream component or state holds a reference to the previous message's options (e.g., reply context), the command flag could persist.

**Rationale**: Code inspection reveals the following flow in `ChatInterface.tsx`:
1. `doSubmit()` calls `addToHistory(content)` — this stores `#help` in the history array
2. `doSubmit()` calls `onSendMessage(content, { isCommand: commandInput })` — this correctly dispatches once
3. `setInput('')` clears the input — this works correctly
4. The `useChat.ts` hook processes the command locally, adding user + system messages to `localMessages`

The auto-repeat is most likely caused by the `isCommand` check being triggered on the response or reply-to context rather than just the input. The fix must ensure: (a) command history entries don't re-trigger command execution, (b) no reply-to or context state carries command references after dispatch.

**Alternatives considered**:
- Backend-side fix — Not applicable; the `#help` command is handled entirely on the frontend. The backend never receives it.
- Removing commands from history entirely — This would prevent users from recalling commands via ArrowUp, which is a valid UX. Instead, commands should be stored in history but not auto-dispatched.

## R2: Optimistic Message Rendering Pattern

**Decision**: Use the existing `localMessages` state in `useChat.ts` to append an optimistic user message immediately on `sendMessage()` call, before the `sendMutation.mutateAsync()` call. Assign a temporary ID (via `generateId()`) and a `status: 'pending'` field. On server response, reconcile by updating the status to `'sent'` or, on failure, to `'failed'`.

**Rationale**: The `useChat` hook already has a `localMessages` state array used for command responses. The same mechanism can support optimistic rendering:
1. On `sendMessage(content)` for non-command messages, immediately create a `ChatMessage` with `sender_type: 'user'`, `status: 'pending'`, and a temp `message_id`
2. Append it to `localMessages` — this makes it visible in the UI instantly
3. Call `sendMutation.mutateAsync({ content })` — on success, the server returns the confirmed message and `queryClient.invalidateQueries` refetches the full message list
4. On `invalidateQueries` success, remove the optimistic message from `localMessages` (the server-confirmed version appears in `messagesData`)
5. On mutation error, update the optimistic message status to `'failed'`

**Alternatives considered**:
- TanStack Query's built-in optimistic updates (`onMutate` + `onError` rollback) — This would modify the query cache directly, which is more complex and harder to reason about with the existing `localMessages` pattern. The `localMessages` approach is simpler and already established.
- Separate `pendingMessages` state — Unnecessary additional state; `localMessages` already serves this purpose.

## R3: Thinking Indicator Placement Strategy

**Decision**: The existing thinking indicator in `ChatInterface.tsx` (three animated bounce dots, rendered when `isSending` is true) is already positioned correctly at the bottom of the message list. The change is to ensure it appears *after* the optimistic user message rather than instead of it.

**Rationale**: Current code renders the thinking indicator only when `isSending` is true, which is derived from `sendMutation.isPending`. The timing is:
1. User clicks send → `sendMutation.mutateAsync()` starts → `isPending` becomes true → thinking indicator appears
2. But the user's message hasn't been added to the list yet (it only appears after server response + refetch)

With optimistic rendering, the sequence becomes:
1. User clicks send → optimistic message appended to `localMessages` → message appears in UI
2. `sendMutation.mutateAsync()` starts → `isPending` becomes true → thinking indicator appears below the user's message
3. Server responds → `invalidateQueries` refetches → server-confirmed messages replace the view

This is the correct UX — user message first, then thinking indicator.

**Alternatives considered**:
- Custom thinking indicator per-message — Overkill; there's only one pending send at a time (mutation is sequential). A single global indicator at the bottom suffices.

## R4: Failed Message UX Pattern

**Decision**: When `sendMutation.mutateAsync()` rejects, update the optimistic message in `localMessages` to have `status: 'failed'`. Render failed messages with a red accent border and a retry button. On retry, re-execute `sendMessage()` with the original content.

**Rationale**: The spec requires (FR-013, FR-014, FR-015) that failed messages are visually marked and retryable. The simplest approach is:
1. In `useChat.ts`, wrap `sendMutation.mutateAsync()` in try/catch
2. On catch, find the optimistic message in `localMessages` by its temp ID and set `status: 'failed'`
3. In `ChatInterface.tsx` / `MessageBubble.tsx`, render failed messages with distinctive styling
4. Add an `onRetry` callback prop to `MessageBubble` that calls `onSendMessage(message.content)` again

**Alternatives considered**:
- Toast notification for failures — Doesn't meet the requirement of marking the specific message as failed in-thread.
- Automatic retry with exponential backoff — Over-engineering for a chat UI; user-initiated retry is simpler and gives the user control.

## R5: Message Reconciliation Strategy

**Decision**: Use a "remove optimistic, replace with server data" approach rather than in-place ID reconciliation.

**Rationale**: The current `useChat` hook returns `[...serverMessages, ...localMessages]`. When the server response arrives and `invalidateQueries` refetches, the server messages include both the user's message and the agent's response. At that point, the optimistic message in `localMessages` should be removed to avoid duplication.

Implementation:
1. Track the optimistic message's temp ID
2. In the `sendMutation.onSuccess` callback, remove the optimistic message from `localMessages` by filtering out the temp ID
3. The refetched server data naturally includes the confirmed user message

This avoids complex ID mapping between temp IDs and server IDs.

**Alternatives considered**:
- Keep optimistic message and deduplicate by content — Fragile; two identical messages could be sent.
- Use TanStack Query's `setQueryData` to splice the confirmed message in — More complex, higher risk of cache inconsistency.

## R6: Command State Isolation After Dispatch

**Decision**: No additional state clearing is needed beyond what already exists. The `doSubmit()` function in `ChatInterface.tsx` already calls `setInput('')` after dispatch. The `useChat.ts` hook processes commands synchronously and returns immediately. The real fix is ensuring the `isCommand` check in `useChat.ts > sendMessage()` only fires based on the current message content, not any persisted state.

**Rationale**: Code review confirms:
1. `ChatInterface.doSubmit()` calls `setInput('')` — input is cleared ✓
2. `ChatInterface.doSubmit()` calls `resetNavigation()` — history navigation is reset ✓
3. `useChat.sendMessage()` checks `isCommand(content)` based on the content string, not stored state ✓
4. `useCommands.executeCommand()` is stateless — it parses and dispatches, no side effects ✓
5. The command registry itself is stateless — handlers return results, no mutations ✓

The auto-repeat bug must therefore be in either (a) the chat history replaying the command, or (b) a React re-render causing `sendMessage` to be called multiple times with stale closure values. The fix should include defensive clearing of any reply-to context and ensure `sendMessage` is not called from an effect that re-triggers.

**Alternatives considered**:
- Adding a `lastCommandSent` state and filtering it out — Unnecessary complexity if the root cause is properly addressed.
- Debouncing `sendMessage` — Masks the bug rather than fixing it; users should be able to send messages rapidly.
