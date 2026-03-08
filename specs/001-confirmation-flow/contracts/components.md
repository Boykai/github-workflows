# Component Contracts: Confirmation Flow for Critical Actions

**Feature**: 001-confirmation-flow | **Date**: 2026-03-08

## New Components

### ConfirmationDialog

**Location**: `frontend/src/components/ui/confirmation-dialog.tsx`
**Purpose**: A reusable, accessible modal dialog that prompts the user to confirm or cancel a critical action. Supports customizable messaging, severity variants, async loading states, and inline error display.

```typescript
interface ConfirmationDialogProps {
  isOpen: boolean;                    // Controls dialog visibility
  title: string;                      // Dialog heading (e.g., "Delete Agent")
  description: string;                // Body text explaining the action and consequences
  variant: ConfirmationVariant;       // 'danger' | 'warning' | 'info' — controls icon and button color
  confirmLabel: string;               // Text for the confirm/affirmative button (e.g., "Delete")
  cancelLabel: string;                // Text for the cancel/dismiss button (e.g., "Cancel")
  isLoading: boolean;                 // When true: spinner on confirm button, both buttons disabled
  error: string | null;               // When set: error message displayed inline above buttons
  onConfirm: () => void;              // Called when user clicks confirm button
  onCancel: () => void;               // Called when user clicks cancel, presses Escape, or clicks backdrop
}
```

**Behavior**:
- **Visual structure**: Fixed overlay (`inset-0 z-[60]`) with semi-transparent backdrop (`bg-black/50`). Centered inner container with `max-w-md rounded-2xl border shadow-xl bg-background`.
- **Header**: Icon (from variant config) + title text. Icon is `AlertTriangle` for danger/warning, `Info` for info variant.
- **Body**: Scrollable description area (`max-h-[60vh] overflow-y-auto`) containing the description text. Supports long content with scroll while keeping buttons visible.
- **Error**: When `error` is non-null, a red error banner appears above the button footer with the error message.
- **Footer**: Two buttons — Cancel (left, ghost/outline variant) and Confirm (right, colored per variant). During loading, confirm button shows a `Loader2` spinner icon and both buttons are disabled.
- **Backdrop**: Clicking the backdrop triggers `onCancel`. During loading state, backdrop clicks are ignored.
- **Keyboard**: Escape key triggers `onCancel` (unless loading). Focus is trapped within the dialog.
- **Accessibility**: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="confirmation-dialog-title"`, `aria-describedby="confirmation-dialog-description"`.
- **Icons**: `AlertTriangle`, `Info`, `Loader2`, `X` from lucide-react.
- **Styling**: Consistent with existing modals (`UnsavedChangesDialog`, `ConfirmChoreModal`).

**Variant Styling**:

| Variant | Icon | Icon Color | Confirm Button |
|---------|------|------------|----------------|
| `danger` | `AlertTriangle` | `text-red-500` | `bg-red-600 hover:bg-red-700 text-white` |
| `warning` | `AlertTriangle` | `text-amber-500` | `bg-amber-600 hover:bg-amber-700 text-white` |
| `info` | `Info` | `text-blue-500` | `bg-blue-600 hover:bg-blue-700 text-white` |

---

## New Hooks

### useConfirmation

**Location**: `frontend/src/hooks/useConfirmation.ts`
**Purpose**: Provides an imperative `confirm()` function via React Context. Manages dialog state, queue, focus, and rendering.

**Exports**:

```typescript
/** Provider component — wrap app root */
export function ConfirmationDialogProvider({ children }: { children: React.ReactNode }): JSX.Element;

/** Hook — use in any component that needs confirmation */
export function useConfirmation(): UseConfirmationReturn;

interface UseConfirmationReturn {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}

interface ConfirmationOptions {
  title: string;
  description: string;
  variant?: ConfirmationVariant;       // Default: 'danger'
  confirmLabel?: string;               // Default: 'Confirm'
  cancelLabel?: string;                // Default: 'Cancel'
  onConfirm?: () => Promise<void>;     // Optional async handler for in-dialog loading/error
}
```

**Behavior**:
- **`ConfirmationDialogProvider`**: Renders the `ConfirmationDialog` component at the provider level. Manages internal state (`isOpen`, `options`, `isLoading`, `error`, `resolve` callback, queue).
- **`useConfirmation()`**: Returns `{ confirm }`. Throws if used outside the provider.
- **`confirm(options)`**: Opens the dialog with the given options. Returns a `Promise<boolean>` that resolves when the user confirms (`true`) or cancels (`false`).
  - If a dialog is already open, the request is queued. The promise resolves when the queued dialog is eventually displayed and resolved.
  - If `onConfirm` is provided: clicking Confirm calls the async function, shows loading state, catches errors and displays them inline. The promise resolves `true` only on success.
  - If `onConfirm` is not provided: clicking Confirm immediately resolves the promise with `true`.
- **Focus management**:
  - On open: captures `document.activeElement`, moves focus to cancel button.
  - While open: traps Tab/Shift+Tab within dialog focusable elements.
  - On close: restores focus to the previously captured element.
- **Single dialog constraint**: Only one dialog is visible at a time. Additional `confirm()` calls are queued and processed in order after the current dialog resolves.

---

## Modified Components

### AgentCard

**Location**: `frontend/src/components/agents/AgentCard.tsx`
**Changes**: Replace `window.confirm()` in `handleDelete` with the `useConfirmation` hook.

**Before**:
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
  const confirmed = await confirm({
    title: 'Delete Agent',
    description: `Remove agent "${agent.name}"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main.`,
    variant: 'danger',
    confirmLabel: 'Delete',
  });
  if (confirmed) {
    deleteMutation.mutate(agent.id);
  }
};
```

---

### AgentsPanel

**Location**: `frontend/src/components/agents/AgentsPanel.tsx`
**Changes**: Replace `window.confirm()` in `handleClearPending` with the `useConfirmation` hook.

**Before**:
```typescript
const handleClearPending = () => {
  const confirmed = window.confirm(
    'Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.'
  );
  if (!confirmed) return;
  clearPendingMutation.mutate();
};
```

**After**:
```typescript
const { confirm } = useConfirmation();

const handleClearPending = async () => {
  const confirmed = await confirm({
    title: 'Clear Pending Records',
    description: 'Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.',
    variant: 'warning',
    confirmLabel: 'Clear Records',
  });
  if (!confirmed) return;
  clearPendingMutation.mutate();
};
```

---

### ChoreCard

**Location**: `frontend/src/components/chores/ChoreCard.tsx`
**Changes**: Replace `window.confirm()` in `handleDelete` with the `useConfirmation` hook.

**Before**:
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
  const confirmed = await confirm({
    title: 'Delete Chore',
    description: `Remove chore "${chore.name}"? This cannot be undone.`,
    variant: 'danger',
    confirmLabel: 'Delete',
  });
  if (confirmed) {
    deleteMutation.mutate(chore.id);
  }
};
```

---

### AgentsPipelinePage

**Location**: `frontend/src/pages/AgentsPipelinePage.tsx`
**Changes**: Replace `window.confirm()` in `handleDelete` with the `useConfirmation` hook.

**Before**:
```typescript
const handleDelete = useCallback(() => {
  if (window.confirm('Are you sure you want to delete this pipeline? This action cannot be undone.')) {
    pipelineConfig.deletePipeline();
  }
}, [pipelineConfig]);
```

**After**:
```typescript
const { confirm } = useConfirmation();

const handleDelete = useCallback(async () => {
  const confirmed = await confirm({
    title: 'Delete Pipeline',
    description: 'Are you sure you want to delete this pipeline? This action cannot be undone.',
    variant: 'danger',
    confirmLabel: 'Delete Pipeline',
  });
  if (confirmed) {
    pipelineConfig.deletePipeline();
  }
}, [pipelineConfig, confirm]);
```

---

### App

**Location**: `frontend/src/App.tsx`
**Changes**: Add `ConfirmationDialogProvider` wrapper.

**Before** (conceptual):
```tsx
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
```

**After** (conceptual):
```tsx
import { ConfirmationDialogProvider } from '@/hooks/useConfirmation';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfirmationDialogProvider>
        <RouterProvider router={router} />
      </ConfirmationDialogProvider>
    </QueryClientProvider>
  );
}
```

---

## UI Layout

### Confirmation Dialog (All Variants)

```
┌─────────────────────────────────────────────┐
│  (Semi-transparent backdrop: bg-black/50)    │
│                                              │
│       ┌─────────────────────────────┐       │
│       │                             │       │
│       │  ⚠️  Delete Agent           │       │
│       │                             │       │
│       │  Remove agent "Security     │       │
│       │  Reviewer"? This opens a PR │       │
│       │  to delete the repo files.  │       │
│       │  The catalog only updates   │       │
│       │  after that PR is merged    │       │
│       │  into main.                 │       │
│       │                             │       │
│       │  ┌─── Error (if present) ─┐ │       │
│       │  │ ❌ Failed to delete:   │ │       │
│       │  │    Network error       │ │       │
│       │  └────────────────────────┘ │       │
│       │                             │       │
│       │      [Cancel]   [Delete]    │       │
│       │       ghost      danger     │       │
│       │                             │       │
│       └─────────────────────────────┘       │
│                                              │
└─────────────────────────────────────────────┘
```

### Loading State

```
┌─────────────────────────────┐
│                             │
│  ⚠️  Delete Pipeline        │
│                             │
│  Are you sure you want to   │
│  delete this pipeline?      │
│  This action cannot be      │
│  undone.                    │
│                             │
│    [Cancel]  [⟳ Deleting…]  │
│    disabled   disabled+spin │
│                             │
└─────────────────────────────┘
```

### Scrollable Long Content

```
┌─────────────────────────────┐
│                             │
│  ⚠️  Bulk Delete Items       │
│                             │
│  ┌── Scrollable area ─────┐ │
│  │ This will delete the   │ │
│  │ following 47 items:    │ │
│  │ • Item 1               │ │
│  │ • Item 2               │ │
│  │ • Item 3               │ │
│  │ • ...                  │▼│
│  └────────────────────────┘ │
│                             │
│      [Cancel]   [Delete]    │  ← Always visible
│                             │
└─────────────────────────────┘
```
