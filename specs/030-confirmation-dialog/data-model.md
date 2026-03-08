# Data Model: Confirmation Dialog for Critical User Actions

**Feature**: 030-confirmation-dialog | **Date**: 2026-03-08

## Frontend Types (TypeScript)

### ConfirmationOptions

Configuration object passed to the `confirm()` function to describe the dialog content and behavior.

```typescript
/** Severity variant controlling visual treatment */
type ConfirmationVariant = 'danger' | 'warning' | 'info';

/** Options for triggering a confirmation dialog */
interface ConfirmationOptions {
  title: string;                           // Dialog heading (e.g., "Delete Agent")
  description: string;                     // Detailed explanation of the action and consequences
  confirmLabel?: string;                   // Confirm button text (default: "Confirm")
  cancelLabel?: string;                    // Cancel button text (default: "Cancel")
  variant?: ConfirmationVariant;           // Visual severity (default: "info")
}
```

**Validation**:

- `title` must be a non-empty string.
- `description` must be a non-empty string.
- `confirmLabel` defaults to `"Confirm"` if not provided.
- `cancelLabel` defaults to `"Cancel"` if not provided.
- `variant` defaults to `"info"` if not provided.

### ConfirmationContextValue

The React Context value exposed by `ConfirmationProvider`.

```typescript
/** Context value for the confirmation system */
interface ConfirmationContextValue {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
}
```

**Behavior**:

- `confirm()` opens the dialog and returns a Promise that resolves to `true` (confirmed) or `false` (cancelled).
- If called while a dialog is already open, the request is queued and the promise remains pending until the current dialog resolves.

### ConfirmationDialogState

Internal state managed by the `ConfirmationProvider`.

```typescript
/** Internal state for the dialog — not exported */
interface ConfirmationDialogState {
  isOpen: boolean;
  options: ConfirmationOptions | null;
  resolve: ((value: boolean) => void) | null;
}
```

### ConfirmationDialogProps

Props for the presentational `ConfirmationDialog` component.

```typescript
/** Props for the ConfirmationDialog presentational component */
interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel: string;
  variant: ConfirmationVariant;
  onConfirm: () => void;
  onCancel: () => void;
}
```

---

## Existing Types (Unchanged)

The following existing types and APIs are referenced but not structurally modified:

- **AgentDeleteResult** (`frontend/src/services/api.ts`): Return type of `agentsApi.delete()`. Unchanged.
- **AgentPendingCleanupResult** (`frontend/src/services/api.ts`): Return type of `agentsApi.clearPending()`. Unchanged.
- **ChoreDeleteResult** (`frontend/src/hooks/useChores.ts`): Return type of `choresApi.delete()`. Unchanged.
- **Button** (`frontend/src/components/ui/button.tsx`): Used in the dialog for confirm/cancel buttons. Unchanged — uses existing `variant="destructive"` and `variant="outline"`.

---

## Variant Configuration Map

Maps each `ConfirmationVariant` to its visual properties:

```typescript
const VARIANT_CONFIG: Record<ConfirmationVariant, {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  confirmButtonVariant: 'destructive' | 'default';
}> = {
  danger: {
    icon: AlertTriangle,
    iconBg: 'bg-red-100 dark:bg-red-900/30',
    iconColor: 'text-red-600 dark:text-red-400',
    confirmButtonVariant: 'destructive',
  },
  warning: {
    icon: AlertTriangle,
    iconBg: 'bg-amber-100 dark:bg-amber-900/30',
    iconColor: 'text-amber-600 dark:text-amber-400',
    confirmButtonVariant: 'default',
  },
  info: {
    icon: Info,
    iconBg: 'bg-blue-100 dark:bg-blue-900/30',
    iconColor: 'text-blue-600 dark:text-blue-400',
    confirmButtonVariant: 'default',
  },
};
```

---

## State Machine

### Confirmation Dialog Lifecycle

```text
                    ┌───────────┐
                    │   IDLE     │  No dialog visible
                    └─────┬─────┘
                          │ confirm() called
                          │ (options provided, Promise created)
                          ▼
                    ┌───────────┐
                    │   OPEN     │  Dialog visible
                    │            │  Focus trapped within dialog
                    │            │  Escape key → Cancel
                    │            │  Backdrop click → Cancel
                    └─────┬─────┘
                          │
              ┌───────────┼───────────┐
              │                       │
        User clicks              User clicks
        "Confirm"                "Cancel" / Esc / Backdrop
              │                       │
              ▼                       ▼
       Promise resolves        Promise resolves
       with `true`             with `false`
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
                    ┌───────────┐
                    │  CLOSING   │  Focus restored to trigger element
                    │            │  Dialog removed from DOM
                    └─────┬─────┘
                          │
                    ┌─────┴─────┐
                    │           │
                  Queue       Queue
                  empty       has items
                    │           │
                    ▼           ▼
              ┌───────────┐ ┌───────────┐
              │   IDLE     │ │   OPEN     │ (next queued dialog)
              └───────────┘ └───────────┘
```

### Calling Component Flow (After Confirmation)

```text
Component calls confirm()
    │
    ▼
await confirm({ title, description, variant: 'danger' })
    │
    ├── returns true ──► Execute mutation (e.g., deleteMutation.mutate(id))
    │                     │
    │                     ├── mutation.isPending → disable trigger button
    │                     ├── mutation.isSuccess → show success feedback
    │                     └── mutation.isError → show error feedback
    │
    └── returns false ──► No action taken (component state unchanged)
```

---

## Database Changes

### No Schema Changes Required

This feature is entirely frontend. No database migrations, no backend API changes, no new endpoints.

---

## Existing `window.confirm()` Call Sites (To Be Replaced)

| File | Line | Current Message | Replacement Variant |
|------|------|----------------|-------------------|
| `AgentCard.tsx` | 63 | `Remove agent "{name}"? This opens a PR to delete the repo files.` | `danger` |
| `AgentsPanel.tsx` | 57 | `Delete all pending agent records from the local database?` | `warning` |
| `ChoreCard.tsx` | 120 | `Remove chore "{name}"? This cannot be undone.` | `danger` |
| `AgentsPipelinePage.tsx` | 126 | `Are you sure you want to delete this pipeline? This action cannot be undone.` | `danger` |

---

## Accessibility Attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `role` | `"alertdialog"` | Identifies the dialog as requiring immediate user response |
| `aria-modal` | `"true"` | Indicates background content is inert |
| `aria-labelledby` | `"{id}-title"` | Associates the dialog with its title element |
| `aria-describedby` | `"{id}-description"` | Associates the dialog with its description element |
| Focus trap | Tab cycles within dialog | Prevents focus from escaping to background content |
| Focus on open | Cancel button receives focus | Safe default — avoids accidental confirmation |
| Focus on close | Trigger element receives focus | Restores context after dialog dismissal |

---

## localStorage / Session Storage

No new storage keys introduced. The confirmation dialog is stateless — no user preferences or dialog history are persisted.
