# Contract: Frontend Shared Abstractions

**Feature**: `028-simplicity-dry-refactor` | **Phase**: 4

---

## 1. Generic CRUD Hook Factory

**File**: `frontend/src/hooks/useCrudResource.ts`

### Type Definitions

```typescript
interface CrudEndpoints<T, CreateInput, UpdateInput> {
  list: (projectId: string) => Promise<T[]>;
  create?: (projectId: string, input: CreateInput) => Promise<T>;
  update?: (projectId: string, id: string, input: UpdateInput) => Promise<T>;
  delete?: (projectId: string, id: string) => Promise<void>;
}

interface CrudResourceConfig<T, CreateInput, UpdateInput> {
  resourceKey: string;
  endpoints: CrudEndpoints<T, CreateInput, UpdateInput>;
  staleTime?: number;
  /** Additional query keys to invalidate on mutations */
  invalidateKeys?: string[][];
}

interface CrudResourceResult<T, CreateInput, UpdateInput> {
  /** List query result */
  items: T[] | undefined;
  isLoading: boolean;
  error: Error | null;
  /** Create mutation */
  create: UseMutationResult<T, Error, CreateInput>;
  /** Update mutation */
  update: UseMutationResult<T, Error, { id: string; input: UpdateInput }>;
  /** Delete mutation */
  remove: UseMutationResult<void, Error, string>;
}
```

### Hook Signature

```typescript
function useCrudResource<T, CreateInput = Partial<T>, UpdateInput = Partial<T>>(
  config: CrudResourceConfig<T, CreateInput, UpdateInput>,
  projectId: string | undefined,
): CrudResourceResult<T, CreateInput, UpdateInput>;
```

### Behavior

| Operation | Condition | Result |
|-----------|-----------|--------|
| List query | `projectId` defined | Fetches via `config.endpoints.list(projectId)` |
| List query | `projectId` undefined | Disabled (no fetch) |
| Create mutation | `projectId` defined | Calls `config.endpoints.create(projectId, input)`, invalidates list query |
| Update mutation | `projectId` defined | Calls `config.endpoints.update(projectId, id, input)`, invalidates list query |
| Delete mutation | `projectId` defined | Calls `config.endpoints.delete(projectId, id)`, invalidates list query |
| Any mutation | `projectId` undefined | No-op |

### Query Key Pattern

```typescript
// Generated internally by the factory
const keys = {
  all: [config.resourceKey] as const,
  list: (projectId: string) => [config.resourceKey, 'list', projectId] as const,
};
```

### Consumers

| Hook | Config | Lines Saved |
|------|--------|-------------|
| `useAgents.ts` | `{ resourceKey: 'agents', endpoints: agentsApi, ... }` | ~60 |
| `useChores.ts` | `{ resourceKey: 'chores', endpoints: choresApi, ... }` | ~80 |
| `useSettings.ts` (user) | `{ resourceKey: 'settings', endpoints: settingsApi, ... }` | ~30 |
| `useSettings.ts` (global) | Same pattern | ~30 |
| `useSettings.ts` (project) | Same pattern | ~30 |

### Validation

- Existing tests for `useAgents` and `useChores` pass unchanged after refactoring.
- Each refactored hook is ≤20 lines of configuration.

---

## 2. Shared UI Components

### 2.1 PreviewCard

**File**: `frontend/src/components/chat/PreviewCard.tsx`

```typescript
interface PreviewCardProps {
  /** Card title displayed in header */
  title: string;
  /** Confirm button handler */
  onConfirm: () => void;
  /** Cancel button handler */
  onCancel: () => void;
  /** Confirm button label (default: "Confirm") */
  confirmLabel?: string;
  /** Cancel button label (default: "Cancel") */
  cancelLabel?: string;
  /** Shows loading spinner on confirm button */
  isLoading?: boolean;
  /** Error message displayed above actions */
  error?: string | null;
  /** Card body content */
  children: React.ReactNode;
}
```

**Behavior**:
- Renders a card with title, body (children), optional error, and action buttons.
- Confirm button shows loading spinner when `isLoading=true` and is disabled.
- Error message renders as an inline alert above the action buttons.
- Styling matches existing preview card patterns (border, padding, rounded corners).

**Consumers**: `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview` use `PreviewCard` as their outer wrapper.

### 2.2 Modal

**File**: `frontend/src/components/common/Modal.tsx`

```typescript
interface ModalProps {
  /** Controls visibility */
  isOpen: boolean;
  /** Called on close (Escape key, backdrop click, or close button) */
  onClose: () => void;
  /** Modal title */
  title: string;
  /** Modal body content */
  children: React.ReactNode;
  /** Size variant (default: "md") */
  size?: 'sm' | 'md' | 'lg';
}
```

**Behavior**:
- When `isOpen=true`: renders backdrop overlay, sets `document.body.style.overflow = 'hidden'`.
- Escape key closes the modal (via `document.addEventListener('keydown')`).
- Backdrop click closes the modal (via `e.target === e.currentTarget` check).
- Cleanup on unmount: removes event listener, restores body overflow.
- Size variants control max-width (`sm: 28rem`, `md: 36rem`, `lg: 48rem`).

**Consumers**: `AddAgentModal`, `IssueDetailModal`, `AddChoreModal`, `ToolSelectorModal`, `CleanUpConfirmModal`.

### 2.3 ErrorAlert

**File**: `frontend/src/components/common/ErrorAlert.tsx`

```typescript
interface ErrorAlertProps {
  /** Error message or Error object */
  error: string | Error | null | undefined;
  /** Optional dismiss handler (shows X button when provided) */
  onDismiss?: () => void;
  /** Additional CSS class names */
  className?: string;
}
```

**Behavior**:
- Renders nothing when `error` is falsy.
- Extracts message from `Error` objects or uses string directly.
- Shows dismiss button when `onDismiss` is provided.
- Styled with red/destructive color scheme matching existing error patterns.

**Consumers**: Any component currently displaying errors inline.

### Validation

- All existing component tests pass after refactoring to use shared components.
- Visual browser check confirms no styling regressions.

---

## 3. Query Key Registry

**File**: `frontend/src/hooks/queryKeys.ts`

### Structure

```typescript
export const queryKeys = {
  agents: {
    all: ['agents'] as const,
    list: (projectId: string) => ['agents', 'list', projectId] as const,
    pending: (projectId: string) => ['agents', 'pending', projectId] as const,
  },
  chores: {
    all: ['chores'] as const,
    list: (projectId: string) => ['chores', 'list', projectId] as const,
    templates: (projectId: string) => ['chores', 'templates', projectId] as const,
  },
  settings: {
    all: ['settings'] as const,
    user: () => ['settings', 'user'] as const,
    global: () => ['settings', 'global'] as const,
    project: (projectId: string) => ['settings', 'project', projectId] as const,
    models: (provider: string) => ['settings', 'models', provider] as const,
  },
  signal: {
    all: ['signal'] as const,
    connection: () => ['signal', 'connection'] as const,
    linkStatus: () => ['signal', 'linkStatus'] as const,
    preferences: () => ['signal', 'preferences'] as const,
    banners: () => ['signal', 'banners'] as const,
  },
  projects: {
    all: ['projects'] as const,
    tasks: (projectId: string) => ['projects', projectId, 'tasks'] as const,
  },
  board: {
    all: ['board'] as const,
    projects: () => ['board', 'projects'] as const,
    data: (projectId: string) => ['board', 'data', projectId] as const,
  },
  chat: {
    all: ['chat'] as const,
    messages: () => ['chat', 'messages'] as const,
  },
  workflow: {
    all: ['workflow'] as const,
    config: () => ['workflow', 'config'] as const,
    agents: (projectId: string) => ['workflow', 'agents', projectId] as const,
  },
  tools: {
    all: ['tools'] as const,
    list: (projectId: string) => ['tools', 'list', projectId] as const,
  },
  agentTools: {
    all: ['agentTools'] as const,
    tools: (agentId: string) => ['agentTools', agentId, 'tools'] as const,
  },
  pipeline: {
    all: ['pipeline'] as const,
    list: (projectId: string) => ['pipeline', 'list', projectId] as const,
  },
  mcp: {
    all: ['mcp'] as const,
    list: () => ['mcp', 'list'] as const,
  },
  models: {
    all: ['models'] as const,
    copilot: () => ['models', 'copilot'] as const,
  },
  auth: {
    all: ['auth'] as const,
    me: () => ['auth', 'me'] as const,
  },
} as const;
```

### Migration Contract

| File | Current Key Definition | After |
|------|----------------------|-------|
| `useAgents.ts` | `export const agentKeys = { ... }` | `import { queryKeys } from './queryKeys'; export const agentKeys = queryKeys.agents;` |
| `useChores.ts` | `export const choreKeys = { ... }` | Same pattern — re-export from registry |
| `useSettings.ts` | `export const settingsKeys = { ... }; export const signalKeys = { ... }` | Same pattern |
| `useProjects.ts` | Inline `['projects']` | `queryKeys.projects.all` |
| `useChat.ts` | Inline `['chat', 'messages']` | `queryKeys.chat.messages()` |
| `useProjectBoard.ts` | Inline `['board', 'projects']` | `queryKeys.board.projects()` |
| `useWorkflow.ts` | Inline `['workflow', 'config']` | `queryKeys.workflow.config()` |

### Validation

- All existing tests pass unchanged (re-exports preserve backward compatibility).
- No inline query key array definitions remain in hook files.
- Type safety: all key factories return `readonly` tuples.

---

## 4. ChatInterface Split

### Component Boundaries

#### ChatMessageList

**File**: `frontend/src/components/chat/ChatMessageList.tsx`

```typescript
interface ChatMessageListProps {
  messages: ChatMessage[];
  pendingProposals: PendingProposal[];
  pendingStatusChanges: PendingStatusChange[];
  pendingRecommendations: PendingRecommendation[];
  isSending: boolean;
  onRetryMessage: (messageId: string) => void;
  onConfirmProposal: (proposalId: string) => void;
  onRejectProposal: (proposalId: string) => void;
  onConfirmStatusChange: (changeId: string) => void;
  onConfirmRecommendation: (recId: string) => void;
  onRejectRecommendation: (recId: string) => void;
}
```

**Behavior**: Renders message list with auto-scroll to bottom on new messages. Includes retry button for failed messages. Renders inline proposal/status/recommendation previews using `PreviewCard`.

#### ChatInput

**File**: `frontend/src/components/chat/ChatInput.tsx`

```typescript
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isSending: boolean;
  commands: Command[];
  chatHistory: ChatHistoryEntry[];
  onNewChat: () => void;
}
```

**Behavior**: Text input with command autocomplete (triggered by `/` prefix). History navigation via ↑/↓ arrow keys. Send on Enter. Shows loading state during send.

### Validation

- `ChatInterface.tsx` orchestrates `ChatMessageList` + `ChatInput`, passing props.
- All existing chat tests pass unchanged.
- Each sub-component is independently testable.
