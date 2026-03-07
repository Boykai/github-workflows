# Component Contracts: Frontend DRY Consolidation

**Feature**: 028-simplicity-dry-refactor | **Date**: 2026-03-07

## Overview

This document defines the interface contracts for new shared frontend components, hook factories, and the API endpoint factory.

---

## New Shared Components

### 1. `Modal` — Shared Dialog Wrapper

**Location**: `frontend/src/components/common/Modal.tsx`

**Props**:
```typescript
interface ModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when the modal is closed (via backdrop click, escape, or close button) */
  onClose: () => void;
  /** Modal title displayed in the header */
  title: string;
  /** Optional description text below the title */
  description?: string;
  /** Modal body content */
  children: React.ReactNode;
  /** Optional footer content (typically action buttons) */
  footer?: React.ReactNode;
  /** Optional CSS class override */
  className?: string;
}
```

**Behavior**:
- Renders a centered overlay dialog
- Closes on backdrop click and Escape key
- Traps focus within the modal when open
- Renders title in a header section
- Renders children in a scrollable body section
- Renders footer in a fixed bottom section (if provided)

**Adoption**: Replace dialog wrapper code in `AddAgentModal`, `AddChoreModal`, `ToolSelectorModal`, `UploadMcpModal`, `CleanUpConfirmModal`.

---

### 2. `PreviewCard` — Action Card with Confirm/Reject

**Location**: `frontend/src/components/common/PreviewCard.tsx`

**Props**:
```typescript
interface PreviewCardProps {
  /** Card title */
  title: string;
  /** Card body content */
  children: React.ReactNode;
  /** Confirm action callback */
  onConfirm?: () => void;
  /** Reject action callback */
  onReject?: () => void;
  /** Confirm button label (default: "Confirm") */
  confirmLabel?: string;
  /** Reject button label (default: "Dismiss") */
  rejectLabel?: string;
  /** Loading state for confirm button */
  isLoading?: boolean;
  /** Visual variant */
  variant?: 'default' | 'warning' | 'success';
  /** Optional CSS class override */
  className?: string;
}
```

**Behavior**:
- Renders a card with rounded corners and subtle border
- Shows title in a header area
- Renders children as card body
- Shows confirm/reject buttons in footer (when callbacks provided)
- Confirm button shows loading spinner when `isLoading=true`
- Variant controls border/accent color

**Adoption**: Replace shared layout in `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview`.

---

### 3. `ErrorAlert` — Error Display Component

**Location**: `frontend/src/components/common/ErrorAlert.tsx`

**Props**:
```typescript
interface ErrorAlertProps {
  /** Error to display (null = hidden) */
  error: Error | string | null;
  /** Alert title (default: "Error") */
  title?: string;
  /** Dismiss callback (shows dismiss button when provided) */
  onDismiss?: () => void;
  /** Optional CSS class override */
  className?: string;
}
```

**Behavior**:
- Hidden when `error` is null
- Displays error message in a red-tinted alert box
- Shows dismiss X button when `onDismiss` is provided
- Extracts message from Error objects or renders string directly

**Adoption**: Replace inline `{error && <div className="text-red-500">...</div>}` patterns across form components and settings panels.

---

## Hook Factories

### 4. `createCrudResource` — CRUD Hook Factory

**Location**: `frontend/src/hooks/useCrudResource.ts`

**Factory Signature**:
```typescript
function createCrudResource<T, CreateInput = Partial<T>, UpdateInput = Partial<T>>(
  config: CrudResourceConfig<T, CreateInput, UpdateInput>
): CrudResourceHooks<T, CreateInput, UpdateInput>;
```

**Config Interface**:
```typescript
interface CrudResourceConfig<T, CreateInput, UpdateInput> {
  /** Query key prefix (e.g., queryKeys.agents) */
  queryKey: {
    all: readonly string[];
    list: (projectId?: string) => readonly unknown[];
  };
  
  /** API methods */
  api: {
    list: (projectId: string) => Promise<T[]>;
    create?: (projectId: string, data: CreateInput) => Promise<T>;
    update?: (projectId: string, id: string, data: UpdateInput) => Promise<T>;
    delete?: (projectId: string, id: string) => Promise<void>;
  };
  
  /** Stale time for list query (default: STALE_TIME_LONG) */
  staleTime?: number;
  
  /** Additional query keys to invalidate on mutation */
  invalidateKeys?: readonly (readonly unknown[])[];
}
```

**Output Interface**:
```typescript
interface CrudResourceHooks<T, CreateInput, UpdateInput> {
  useList: (projectId: string | undefined) => UseQueryResult<T[]>;
  useCreate: () => UseMutationResult<T, Error, { projectId: string; data: CreateInput }>;
  useUpdate: () => UseMutationResult<T, Error, { projectId: string; id: string; data: UpdateInput }>;
  useDelete: () => UseMutationResult<void, Error, { projectId: string; id: string }>;
}
```

**Adoption**:
| Hook File | Current LOC | After Refactor | Savings |
|-----------|-------------|----------------|---------|
| `useAgents.ts` | 89 | ~30 (factory call + custom hooks) | ~59 lines |
| `useChores.ts` | 120 | ~40 (factory call + custom hooks) | ~80 lines |

---

### 5. `useSettingsHook` — Generic Settings Hook

**Location**: `frontend/src/hooks/useSettings.ts` (extracted generic)

**Signature**:
```typescript
function useSettingsHook<T>(config: {
  apiGet: (...args: any[]) => Promise<T>;
  apiUpdate: (...args: any[]) => Promise<T>;
  queryKey: readonly unknown[];
  enabled?: boolean;
  staleTime?: number;
}): {
  data: T | undefined;
  isLoading: boolean;
  error: Error | null;
  update: UseMutateFunction<T, Error, Partial<T>>;
  updateAsync: UseMutateAsyncFunction<T, Error, Partial<T>>;
  isUpdating: boolean;
};
```

**Adoption**:
| Hook | apiGet | apiUpdate | queryKey |
|------|--------|-----------|----------|
| `useUserSettings()` | `settingsApi.getUserSettings` | `settingsApi.updateUserSettings` | `queryKeys.settings.user` |
| `useGlobalSettings()` | `settingsApi.getGlobalSettings` | `settingsApi.updateGlobalSettings` | `queryKeys.settings.global` |
| `useProjectSettings(id)` | `settingsApi.getProjectSettings` | `settingsApi.updateProjectSettings` | `queryKeys.settings.project(id)` |

---

### 6. Query Key Registry

**Location**: `frontend/src/hooks/queryKeys.ts`

**Contract**: Single source of truth for all TanStack Query keys.

```typescript
export const queryKeys = {
  agents: {
    all: ['agents'] as const,
    list: (projectId?: string) => [...queryKeys.agents.all, 'list', projectId] as const,
    pending: (projectId?: string) => [...queryKeys.agents.all, 'pending', projectId] as const,
  },
  agentTools: { /* ... */ },
  chores: { /* ... */ },
  settings: { /* ... */ },
  signal: { /* ... */ },
  mcp: { /* ... */ },
  models: { /* ... */ },
  pipelines: { /* ... */ },
  tools: { /* ... */ },
} as const;
```

**Migration**: Each hook file replaces its local `xxxKeys` export with an import from `queryKeys.ts`. Local exports are removed.

---

## API Endpoint Factory

### 7. `createApiGroup` — API Client Factory

**Location**: `frontend/src/services/api.ts`

**Factory Signature**:
```typescript
function createApiGroup(
  basePath: string,
  methods: Record<string, ApiMethodDef>,
): Record<string, (...args: any[]) => Promise<any>>;
```

**Method Definition**:
```typescript
interface ApiMethodDef {
  /** HTTP method (default: 'GET') */
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  /** Path suffix appended to basePath (supports ':id' interpolation) */
  path?: string;
  /** Whether the function accepts a request body as last argument */
  hasBody?: boolean;
}
```

**Example Usage**:
```typescript
// Before (verbose):
export const agentsApi = {
  list(projectId: string): Promise<Agent[]> {
    return request<Agent[]>(`/agents?project_id=${projectId}`);
  },
  create(projectId: string, data: AgentCreate): Promise<Agent> {
    return request<Agent>('/agents', { method: 'POST', body: JSON.stringify({ ...data, project_id: projectId }) });
  },
  update(projectId: string, id: string, data: AgentUpdate): Promise<Agent> {
    return request<Agent>(`/agents/${id}`, { method: 'PUT', body: JSON.stringify({ ...data, project_id: projectId }) });
  },
  delete(projectId: string, id: string): Promise<void> {
    return request<void>(`/agents/${id}?project_id=${projectId}`, { method: 'DELETE' });
  },
};

// After (factory):
export const agentsApi = createApiGroup('/agents', {
  list: { path: '?project_id=:projectId' },
  create: { method: 'POST', hasBody: true },
  update: { method: 'PUT', path: '/:id', hasBody: true },
  delete: { method: 'DELETE', path: '/:id?project_id=:projectId' },
});
```

**Adoption Candidates** (standard CRUD groups):
| Group | Methods | Estimated Savings |
|-------|---------|-------------------|
| `agentsApi` | list, create, update, delete, + custom | ~20 lines |
| `choresApi` | list, listTemplates, create, update, delete, + custom | ~25 lines |
| `toolsApi` | list, sync, delete | ~15 lines |
| `pipelinesApi` | list, save, delete | ~15 lines |
| `cleanupApi` | preflight, execute, history | ~15 lines |

**Non-candidates** (keep manual): `authApi` (redirect logic), `chatApi` (streaming), `boardApi` (complex params), `settingsApi` (mixed patterns), `signalApi` (WebSocket integration).

---

## ChatInterface Decomposition

### 8. `ChatMessageList` — Message Display

**Location**: `frontend/src/components/chat/ChatMessageList.tsx`

**Contract**:
```typescript
interface ChatMessageListProps {
  messages: ChatMessage[];
  pendingProposals: Map<string, AITaskProposal>;
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  pendingRecommendations: Map<string, IssueCreateActionData>;
  onConfirmProposal: (id: string) => void;
  onRejectProposal: (id: string) => void;
  onConfirmStatusChange: (id: string) => void;
  onConfirmRecommendation: (id: string) => void;
  onRejectRecommendation: (id: string) => void;
  onRetryMessage: (id: string) => void;
}
```

**Behavior**:
- Renders messages list with auto-scroll to bottom on new messages
- Delegates to `MessageBubble` and `SystemMessage` for individual messages
- Renders inline `TaskPreview`, `StatusChangePreview`, `IssueRecommendationPreview` for pending proposals
- Target: <200 lines

---

### 9. `ChatInput` — Message Input

**Location**: `frontend/src/components/chat/ChatInput.tsx`

**Contract**:
```typescript
interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isSending: boolean;
  onNewChat: () => void;
}
```

**Behavior**:
- Renders textarea with auto-resize
- Integrates `useCommands()` for `#` prefix command autocomplete
- Integrates `useChatHistory()` for up/down arrow message history navigation
- Send on Enter (without Shift), new line on Shift+Enter
- Shows send button with loading state when `isSending`
- Shows "New Chat" button
- Target: <200 lines
