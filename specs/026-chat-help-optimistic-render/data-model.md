# Data Model: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering

**Feature Branch**: `026-chat-help-optimistic-render`
**Date**: 2026-03-07

> This feature is frontend-only. No new backend entities or API endpoints are created. This document describes the **frontend data model** changes — type modifications, state shapes, and component prop additions needed for the bug fix and optimistic rendering.

## Existing Entities (Modified)

### ChatMessage (modified)

**File**: `frontend/src/types/index.ts`

Current definition:

```typescript
export interface ChatMessage {
  message_id: string;
  session_id: string;
  sender_type: SenderType;
  content: string;
  action_type?: ActionType;
  action_data?: ActionData;
  timestamp: string;
}
```

**Change**: Add optional `status` field for optimistic rendering states.

```typescript
export type MessageStatus = 'pending' | 'sent' | 'failed';

export interface ChatMessage {
  message_id: string;
  session_id: string;
  sender_type: SenderType;
  content: string;
  action_type?: ActionType;
  action_data?: ActionData;
  timestamp: string;
  status?: MessageStatus;  // NEW: undefined = server-confirmed, 'pending' = optimistic, 'failed' = send error
}
```

**Rationale**: The `status` field is optional so existing server-returned messages (which lack this field) continue to work without changes. Only optimistic messages set this field. `undefined` and `'sent'` are treated equivalently — both represent confirmed messages.

### UseChatReturn (modified)

**File**: `frontend/src/hooks/useChat.ts`

**Change**: Add `retryMessage` callback for failed message retry.

```typescript
interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: Error | null;
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  sendMessage: (content: string, options?: { isCommand?: boolean }) => Promise<void>;
  retryMessage: (messageId: string) => Promise<void>;  // NEW
  confirmProposal: (proposalId: string, edits?: ProposalConfirmRequest) => Promise<void>;
  confirmStatusChange: (proposalId: string) => Promise<void>;
  rejectProposal: (proposalId: string) => Promise<void>;
  removePendingRecommendation: (recommendationId: string) => void;
  clearChat: () => Promise<void>;
}
```

## New State Patterns

### Optimistic Message Lifecycle

State transitions for a user message sent to the backend:

```text
[User presses Send]
       │
       ▼
  ┌──────────┐    localMessages += { status: 'pending', message_id: tempId }
  │  pending  │    UI: Message appears immediately in thread
  └────┬─────┘
       │
  sendMutation.mutateAsync()
       │
       ├── onSuccess ──▶ ┌──────────┐  localMessages -= tempId
       │                 │   sent    │  queryClient.invalidateQueries() refetches server data
       │                 └──────────┘  UI: Server messages replace optimistic, agent response appears
       │
       └── onError ───▶ ┌──────────┐  localMessages[tempId].status = 'failed'
                        │  failed   │  UI: Message shows error styling + retry button
                        └────┬─────┘
                             │
                     [User clicks Retry]
                             │
                             ▼
                       ┌──────────┐  Reset status to 'pending', re-execute sendMutation
                       │  pending  │
                       └──────────┘
```

### Command Message Lifecycle

State transitions for a command message (e.g., `#help`):

```text
[User presses Send]
       │
       ▼
  isCommand(content) === true
       │
       ├── passthrough ──▶ [Same as regular message — forwarded to backend]
       │
       └── local ────────▶ localMessages += userMsg + systemMsg
                           Command state fully consumed — no persistence
                           UI: User message + system response appear immediately
```

## Component Props Changes

### ChatInterfaceProps (modified)

**File**: `frontend/src/components/chat/ChatInterface.tsx`

**Change**: Add `onRetryMessage` callback prop.

```typescript
interface ChatInterfaceProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  isSending: boolean;
  onSendMessage: (content: string, options?: { isCommand?: boolean }) => void;
  onRetryMessage: (messageId: string) => void;  // NEW
  onConfirmProposal: (proposalId: string) => void;
  onConfirmStatusChange: (proposalId: string) => void;
  onConfirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  onRejectProposal: (proposalId: string) => void;
  onRejectRecommendation: (recommendationId: string) => Promise<void>;
  onNewChat: () => void;
}
```

### MessageBubbleProps (modified)

**File**: `frontend/src/components/chat/MessageBubble.tsx`

**Change**: Add optional `onRetry` callback for failed messages.

```typescript
interface MessageBubbleProps {
  message: ChatMessage;
  onRetry?: () => void;  // NEW: Called when user clicks retry on a failed message
}
```

### ChatPopupProps (modified)

**File**: `frontend/src/components/chat/ChatPopup.tsx`

**Change**: Add `onRetryMessage` callback prop (pass-through to ChatInterface).

```typescript
interface ChatPopupProps {
  // ... existing props ...
  onRetryMessage: (messageId: string) => void;  // NEW
}
```

## Validation Rules

### Command Detection

Commands are recognized by `parseCommand()` in `registry.ts`:
- Input starts with `#` after trimming → is a command
- Exact text `help` (case-insensitive) → is a command (alias)
- Commands are one-time: no state persists after `executeCommand()` returns

### Message Status

- `status` is optional on `ChatMessage` — server-returned messages have no `status` field
- Only messages in `localMessages` with `sender_type: 'user'` can have `status: 'pending'` or `'failed'`
- System messages (from command responses) always have `status: undefined` (they are local-only and never fail)
- The `status` field is never sent to or received from the backend API

## Entities Not Changed

| Entity | Reason |
|---|---|
| `ChatMessageRequest` | Backend API contract unchanged |
| `ChatMessagesResponse` | Backend API contract unchanged |
| `CommandResult` | Already has `clearInput` and `passthrough` — sufficient |
| `CommandDefinition` | No structural changes to command registry |
| `ParsedCommand` | No changes to parsing logic |
| `AITaskProposal` | Unrelated to this feature |
| `StatusChangeProposal` | Unrelated to this feature |
| `IssueCreateActionData` | Unrelated to this feature |
