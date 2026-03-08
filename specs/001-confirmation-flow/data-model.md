# Data Model: Confirmation Flow for Critical Actions

**Feature**: 001-confirmation-flow | **Date**: 2026-03-08

## Frontend Types (TypeScript)

### ConfirmationDialog Types (New)

```typescript
/** Severity level controlling the visual appearance of the confirmation dialog */
type ConfirmationVariant = 'danger' | 'warning' | 'info';

/** Options passed to the confirm() function from useConfirmation hook */
interface ConfirmationOptions {
  title: string;                          // Dialog title (e.g., "Delete Agent")
  description: string;                    // Dialog body text explaining the action and consequences
  variant?: ConfirmationVariant;          // Visual severity: 'danger' (red), 'warning' (amber), 'info' (blue). Default: 'danger'
  confirmLabel?: string;                  // Confirm button text. Default: 'Confirm'
  cancelLabel?: string;                   // Cancel button text. Default: 'Cancel'
  onConfirm?: () => Promise<void>;        // Optional async callback for in-dialog loading/error handling
}

/** Internal state managed by the ConfirmationDialogProvider */
interface ConfirmationDialogState {
  isOpen: boolean;                        // Whether the dialog is currently visible
  options: ConfirmationOptions | null;    // Current dialog configuration
  isLoading: boolean;                     // Whether the async onConfirm is executing
  error: string | null;                   // Error message from failed onConfirm, displayed inline
  resolve: ((confirmed: boolean) => void) | null;  // Promise resolver for the confirm() call
}
```

**Validation**:
- `title` must be a non-empty string.
- `description` must be a non-empty string.
- `variant` defaults to `'danger'` if not provided.
- `confirmLabel` defaults to `'Confirm'` if not provided.
- `cancelLabel` defaults to `'Cancel'` if not provided.
- `onConfirm` is optional. When provided, the dialog shows loading/error states.

### ConfirmationDialog Props (New)

```typescript
/** Props for the ConfirmationDialog presentational component */
interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  variant: ConfirmationVariant;
  confirmLabel: string;
  cancelLabel: string;
  isLoading: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}
```

### useConfirmation Hook Return Type (New)

```typescript
/** Return type of the useConfirmation() hook */
interface UseConfirmationReturn {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}
```

### Context Type (New)

```typescript
/** Shape of the ConfirmationContext provided at the app root */
interface ConfirmationContextValue {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}
```

---

## Variant Styling Map

```typescript
/** Maps confirmation variant to visual properties */
const VARIANT_CONFIG: Record<ConfirmationVariant, {
  icon: LucideIcon;           // Icon component from lucide-react
  iconClassName: string;      // Icon color class
  buttonClassName: string;    // Confirm button color classes
}> = {
  danger: {
    icon: AlertTriangle,
    iconClassName: 'text-red-500',
    buttonClassName: 'bg-red-600 hover:bg-red-700 text-white',
  },
  warning: {
    icon: AlertTriangle,
    iconClassName: 'text-amber-500',
    buttonClassName: 'bg-amber-600 hover:bg-amber-700 text-white',
  },
  info: {
    icon: Info,
    iconClassName: 'text-blue-500',
    buttonClassName: 'bg-blue-600 hover:bg-blue-700 text-white',
  },
};
```

---

## State Machines

### Confirmation Dialog Lifecycle

```
                    ┌────────────┐
                    │   CLOSED    │  No dialog visible
                    └──────┬─────┘
                           │ confirm(options) called from any component
                           │ (captures document.activeElement for focus restoration)
                           ▼
                    ┌────────────┐
                    │   OPEN      │  Dialog visible, focus on cancel button
                    │  (idle)     │  Escape key / backdrop click → CLOSED (cancel)
                    └──────┬─────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        User clicks   User clicks   User presses
        "Cancel"      "Confirm"     Escape / clicks
                           │         backdrop
              │            │            │
              ▼            │            ▼
         ┌────────┐       │       ┌────────┐
         │ CLOSED  │       │       │ CLOSED  │
         │(resolve │       │       │(resolve │
         │ false)  │       │       │ false)  │
         └────────┘       │       └────────┘
                           │
                     ┌─────┴──────┐
                     │ Has async  │
                     │ onConfirm? │
                     └─────┬──────┘
                     No    │    Yes
                     │     │     │
                     ▼     │     ▼
               ┌────────┐ │ ┌────────────┐
               │ CLOSED  │ │ │  LOADING    │
               │(resolve │ │ │ Spinner on  │
               │ true)   │ │ │ confirm btn │
               └────────┘ │ │ Btns disabled│
                           │ └──────┬─────┘
                           │        │
                           │  ┌─────┴──────┐
                           │  │            │
                           │ Success    Error
                           │  │            │
                           │  ▼            ▼
                           │ ┌────────┐ ┌──────────┐
                           │ │ CLOSED  │ │  ERROR    │
                           │ │(resolve │ │ Message   │
                           │ │ true)   │ │ displayed │
                           │ └────────┘ │ Retry btn │
                           │            │ enabled   │
                           │            └──────┬───┘
                           │                   │
                           │              User clicks
                           │              "Retry"
                           │                   │
                           │                   ▼
                           │            ┌────────────┐
                           │            │  LOADING    │
                           │            │  (retry)    │
                           │            └────────────┘
                           │
                     (If dialog closed while queue has entries)
                           │
                           ▼
                    ┌────────────┐
                    │  QUEUE      │  Next queued confirm() is dequeued
                    │  PROCESS    │  → transitions to OPEN
                    └────────────┘
```

### Focus Management Flow

```
confirm() called
    │
    ├─ Capture document.activeElement → previousFocusRef
    │
    ▼
Dialog OPEN
    │
    ├─ Set focus to cancel button (safe default)
    ├─ Activate focus trap (Tab cycles within dialog)
    │
    ▼
Dialog interaction
    │
    ├─ Tab → next focusable in dialog (wraps at end)
    ├─ Shift+Tab → prev focusable in dialog (wraps at start)
    ├─ Escape → cancel action
    │
    ▼
Dialog CLOSED
    │
    ├─ Deactivate focus trap
    ├─ Restore focus to previousFocusRef.current
    │
    ▼
Done
```

### Queue Management

```
State: queue: ConfirmationRequest[] = []
       currentDialog: ConfirmationDialogState | null

When confirm(options) called:
  IF currentDialog is not null (dialog is open):
    → Push { options, resolve } to queue
    → Return new Promise (will be resolved when dequeued)
  ELSE:
    → Set currentDialog = { options, resolve, isOpen: true }
    → Return new Promise (resolved on confirm/cancel)

When dialog is resolved (confirm or cancel):
  → Set currentDialog = null
  → IF queue.length > 0:
    → Dequeue next request
    → Set currentDialog = { ...dequeued, isOpen: true }
```

---

## Database Changes

### No Schema Changes Required

This feature is entirely a frontend UI concern. No database schema changes, no new tables, no new columns, no new migrations.

---

## Existing Call Sites to Retrofit

| Call Site | File | Line | Current Message | Proposed Variant | Proposed Labels |
|-----------|------|------|-----------------|------------------|-----------------|
| Delete Agent | `AgentCard.tsx` | 63 | `Remove agent "${agent.name}"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main.` | `danger` | Confirm: "Delete", Cancel: "Cancel" |
| Clear Pending Agents | `AgentsPanel.tsx` | 57 | `Delete all pending agent records from the local database for this project? This only removes stale SQLite rows and does not change the repository.` | `warning` | Confirm: "Clear Records", Cancel: "Cancel" |
| Delete Chore | `ChoreCard.tsx` | 120 | `Remove chore "${chore.name}"? This cannot be undone.` | `danger` | Confirm: "Delete", Cancel: "Cancel" |
| Delete Pipeline | `AgentsPipelinePage.tsx` | 126 | `Are you sure you want to delete this pipeline? This action cannot be undone.` | `danger` | Confirm: "Delete Pipeline", Cancel: "Cancel" |

---

## localStorage Keys

No new localStorage keys introduced by this feature.
