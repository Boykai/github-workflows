# Component Contracts: Confirmation Dialog for Critical User Actions

**Feature**: 030-confirmation-dialog | **Date**: 2026-03-08

## New Components

### ConfirmationDialog

**Location**: `frontend/src/components/ui/confirmation-dialog.tsx`
**Purpose**: A reusable modal dialog that prompts users to confirm or cancel a critical action. Supports severity variants (danger, warning, info), customizable labels, and full WCAG 2.1 AA accessibility.

```typescript
interface ConfirmationDialogProps {
  isOpen: boolean;                        // Controls dialog visibility
  title: string;                          // Dialog heading text
  description: string;                    // Detailed explanation of the action
  confirmLabel: string;                   // Confirm button text (e.g., "Delete", "Confirm")
  cancelLabel: string;                    // Cancel button text (e.g., "Cancel", "Go Back")
  variant: 'danger' | 'warning' | 'info'; // Visual severity level
  onConfirm: () => void;                  // Called when user confirms
  onCancel: () => void;                   // Called when user cancels (button, Escape, backdrop)
}
```

**Behavior**:
- Renders a fixed-position overlay with a semi-transparent backdrop (`bg-black/50 backdrop-blur-sm`)
- Dialog card is centered vertically and horizontally (`fixed inset-0 flex items-center justify-center`)
- Displays an icon matching the variant (AlertTriangle for danger/warning, Info for info)
- Icon is wrapped in a colored circular background matching the variant
- Title rendered as `<h2>` with `id="{uniqueId}-title"` for `aria-labelledby`
- Description rendered as `<p>` with `id="{uniqueId}-description"` for `aria-describedby`
- Two action buttons:
  - **Cancel**: `Button variant="outline" size="sm"` — always on the left
  - **Confirm**: `Button variant="destructive" size="sm"` (danger) or `Button variant="default" size="sm"` (warning/info) — always on the right
- Dialog container has `role="alertdialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`
- Escape key triggers `onCancel()`
- Backdrop click triggers `onCancel()`
- Focus is trapped within the dialog (Tab cycles between Cancel and Confirm buttons)
- On open, focus moves to the Cancel button (safe default)
- When `isOpen` is false, returns `null` (no DOM rendered)
- Uses `createPortal()` to render at document body level

**Visual Layout**:
```
┌──────────────────────────────────────────┐
│  ┌────┐                                  │
│  │ ⚠️ │  Dialog Title                     │
│  └────┘                                  │
│                                          │
│  Description text explaining what will   │
│  happen and the consequences of the      │
│  action being confirmed.                 │
│                                          │
│                    [Cancel] [Confirm]     │
└──────────────────────────────────────────┘
```

---

### ConfirmationProvider

**Location**: `frontend/src/hooks/useConfirmation.ts`
**Purpose**: React Context provider that manages the confirmation dialog state and renders the single dialog instance. Wraps the app at the root level.

```typescript
interface ConfirmationProviderProps {
  children: React.ReactNode;
}
```

**Behavior**:
- Maintains internal state: current dialog options, open/close status, Promise resolver
- Maintains a queue of pending confirmation requests
- Renders `<ConfirmationDialog>` with current state
- When `confirm()` is called:
  1. If no dialog is open: opens the dialog, creates a new Promise, returns it
  2. If a dialog is already open: queues the request, returns a pending Promise
- When user confirms/cancels:
  1. Resolves the current Promise with `true`/`false`
  2. Closes the dialog
  3. If queue has items: dequeues the next request and opens it
- Stores `document.activeElement` before opening for focus restoration on close

---

## New Hook

### useConfirmation

**Location**: `frontend/src/hooks/useConfirmation.ts` (same file as ConfirmationProvider)
**Purpose**: Returns the imperative `confirm()` function from the ConfirmationContext.

```typescript
function useConfirmation(): {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}
```

**Usage Pattern**:
```typescript
// In any component
const { confirm } = useConfirmation();

const handleDelete = async () => {
  const ok = await confirm({
    title: 'Delete Agent',
    description: `Remove agent "${agent.name}"? This opens a PR to delete the repo files.`,
    confirmLabel: 'Delete',
    cancelLabel: 'Cancel',
    variant: 'danger',
  });
  if (ok) {
    deleteMutation.mutate(agent.id);
  }
};
```

**Error Handling**:
- Throws `Error` if called outside of `ConfirmationProvider` (context not available)

---

## Modified Components

### AgentCard.tsx

**Location**: `frontend/src/components/agents/AgentCard.tsx`
**Changes**: Replace `window.confirm()` with `useConfirmation()` hook.

**Before** (lines 61-68):
```typescript
const handleDelete = () => {
  if (
    window.confirm(
      `Remove agent "${agent.name}"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main.`
    )
  ) {
    deleteMutation.mutate(agent.id);
  }
};
```

**After**:
```typescript
const { confirm } = useConfirmation();

const handleDelete = async () => {
  const ok = await confirm({
    title: 'Remove Agent',
    description: `Remove agent "${agent.name}"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main.`,
    confirmLabel: 'Remove',
    cancelLabel: 'Cancel',
    variant: 'danger',
  });
  if (ok) {
    deleteMutation.mutate(agent.id);
  }
};
```

### AgentsPanel.tsx

**Location**: `frontend/src/components/agents/AgentsPanel.tsx`
**Changes**: Replace `window.confirm()` with `useConfirmation()` hook.

**Before** (lines 56-62):
```typescript
const handleClearPending = () => {
  const confirmed = window.confirm(
    'Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.'
  );
  if (confirmed) {
    clearPendingMutation.mutate();
  }
};
```

**After**:
```typescript
const { confirm } = useConfirmation();

const handleClearPending = async () => {
  const ok = await confirm({
    title: 'Clear Pending Agents',
    description: 'Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.',
    confirmLabel: 'Clear Records',
    cancelLabel: 'Cancel',
    variant: 'warning',
  });
  if (ok) {
    clearPendingMutation.mutate();
  }
};
```

### ChoreCard.tsx

**Location**: `frontend/src/components/chores/ChoreCard.tsx`
**Changes**: Replace `window.confirm()` with `useConfirmation()` hook.

**Before** (lines 119-123):
```typescript
const handleDelete = () => {
  if (window.confirm(`Remove chore "${chore.name}"? This cannot be undone.`)) {
    deleteMutation.mutate(chore.id);
  }
};
```

**After**:
```typescript
const { confirm } = useConfirmation();

const handleDelete = async () => {
  const ok = await confirm({
    title: 'Remove Chore',
    description: `Remove chore "${chore.name}"? This will delete the chore and close its associated GitHub issue. This cannot be undone.`,
    confirmLabel: 'Remove',
    cancelLabel: 'Cancel',
    variant: 'danger',
  });
  if (ok) {
    deleteMutation.mutate(chore.id);
  }
};
```

### AgentsPipelinePage.tsx

**Location**: `frontend/src/pages/AgentsPipelinePage.tsx`
**Changes**: Replace `window.confirm()` with `useConfirmation()` hook.

**Before** (lines 125-129):
```typescript
const handleDelete = () => {
  if (window.confirm('Are you sure you want to delete this pipeline? This action cannot be undone.')) {
    pipelineConfig.deletePipeline();
  }
};
```

**After**:
```typescript
const { confirm } = useConfirmation();

const handleDelete = async () => {
  const ok = await confirm({
    title: 'Delete Pipeline',
    description: 'Are you sure you want to delete this pipeline? This action cannot be undone.',
    confirmLabel: 'Delete',
    cancelLabel: 'Cancel',
    variant: 'danger',
  });
  if (ok) {
    pipelineConfig.deletePipeline();
  }
};
```

### App.tsx

**Location**: `frontend/src/App.tsx`
**Changes**: Wrap the application tree with `ConfirmationProvider`.

**Before**:
```tsx
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* ... existing providers and routes */}
    </QueryClientProvider>
  );
}
```

**After**:
```tsx
import { ConfirmationProvider } from './hooks/useConfirmation';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfirmationProvider>
        {/* ... existing providers and routes */}
      </ConfirmationProvider>
    </QueryClientProvider>
  );
}
```

---

## Integration Points

| Call Site | Hook Import | Variant | Confirm Label |
|-----------|------------|---------|---------------|
| `AgentCard.tsx` → `handleDelete` | `useConfirmation` | `danger` | "Remove" |
| `AgentsPanel.tsx` → `handleClearPending` | `useConfirmation` | `warning` | "Clear Records" |
| `ChoreCard.tsx` → `handleDelete` | `useConfirmation` | `danger` | "Remove" |
| `AgentsPipelinePage.tsx` → `handleDelete` | `useConfirmation` | `danger` | "Delete" |

---

## Query Keys (TanStack Query)

No new query keys. All mutations referenced by the confirmation dialog are existing:

| Operation | Hook | Invalidates |
|-----------|------|-------------|
| Delete agent | `useDeleteAgent(projectId)` | `['agents', 'pending', projectId]` |
| Clear pending agents | `useClearPendingAgents(projectId)` | `['agents', 'pending', projectId]` |
| Delete chore | `useDeleteChore(projectId)` | `['chores', 'list', projectId]` |
| Delete pipeline | `pipelineConfig.deletePipeline()` | Pipeline-specific keys |
