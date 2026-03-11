# Data Model: Add Confirmation Step to Critical Actions

**Feature**: 035-confirm-critical-actions | **Date**: 2026-03-11

## Overview

This feature is frontend-only. No new database tables, backend models, or API endpoints are introduced. The data model describes the TypeScript types and state structures used by the confirmation infrastructure.

## Existing Types (No Modifications)

### ConfirmationVariant

```typescript
// Location: frontend/src/hooks/useConfirmation.tsx
type ConfirmationVariant = 'danger' | 'warning' | 'info';
```

Determines the visual style and severity level of the confirmation dialog:
- `danger` (red) — Irreversible actions: deletions, permanent removals
- `warning` (amber) — Significant but reversible actions: discarding unsaved changes
- `info` (blue) — Informational confirmations: non-destructive but consequential actions

### ConfirmationOptions

```typescript
// Location: frontend/src/hooks/useConfirmation.tsx
interface ConfirmationOptions {
  title: string;
  description: string;
  variant?: ConfirmationVariant;       // Default: 'danger'
  confirmLabel?: string;               // Default: 'Confirm'
  cancelLabel?: string;                // Default: 'Cancel'
  onConfirm?: () => Promise<void>;     // Optional async callback
}
```

Input to the `confirm()` function. Each critical action provides these options to customize the prompt.

### DialogState

```typescript
// Location: frontend/src/hooks/useConfirmation.tsx (internal)
interface DialogState {
  isOpen: boolean;
  options: {
    title: string;
    description: string;
    variant: ConfirmationVariant;
    confirmLabel: string;
    cancelLabel: string;
    onConfirm?: () => Promise<void>;
  };
  isLoading: boolean;
  error: string | null;
}
```

Internal state of the confirmation dialog provider. Managed by `ConfirmationDialogProvider`.

### QueuedRequest

```typescript
// Location: frontend/src/hooks/useConfirmation.tsx (internal)
interface QueuedRequest {
  options: ConfirmationOptions;
  resolve: (value: boolean) => void;
}
```

Queued confirmations when multiple critical actions are triggered while a dialog is already open.

### ConfirmationDialogProps

```typescript
// Location: frontend/src/components/ui/confirmation-dialog.tsx
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

Props for the `ConfirmationDialog` UI component. Driven entirely by `DialogState` from the provider.

## Existing Types (Used by Consumers)

### CleanupPreflightResponse

```typescript
// Location: frontend/src/types/ (existing)
interface CleanupPreflightResponse {
  has_permission: boolean;
  permission_error?: string;
  branches_to_delete: Array<{ name: string; deletion_reason?: string }>;
  prs_to_close: Array<{ number: number; title: string; deletion_reason?: string }>;
  orphaned_issues?: Array<{ number: number; title: string; labels: string[] }>;
  branches_to_preserve: Array<{ name: string; preservation_reason?: string }>;
  prs_to_preserve: Array<{ number: number; title: string; preservation_reason?: string }>;
  open_issues_on_board: number;
}
```

Used by `CleanUpConfirmModal` to display the impact summary. No changes needed.

### CleanupState

```typescript
// Location: frontend/src/hooks/useCleanup.ts
type CleanupState =
  | 'idle'
  | 'loading'        // Preflight check running
  | 'confirming'     // Review modal shown
  | 'executing'      // Cleanup running
  | 'summary'        // Results shown
  | 'auditHistory';  // History modal shown
```

State machine for the repository cleanup workflow. No changes needed.

### Tool Deletion Types

```typescript
// Location: frontend/src/services/api.ts (existing)
interface ToolDeleteResult {
  success: boolean;
  affected_agents: Array<{ id: string; name: string }>;
}
```

Used by `ToolsPanel` when deleting a tool. The `affected_agents` array is displayed in the confirmation description when non-empty.

## State Flow Diagrams

### Standard Confirmation Flow

```
User Action (click delete/destructive button)
  │
  ▼
confirm({title, description, variant, confirmLabel}) called
  │
  ▼
┌─────────────────────────────┐
│ DialogState.isOpen = true   │ ← Focus captured, dialog rendered
│ isLoading = false           │
│ error = null                │
└─────────────────────────────┘
  │                     │
  ▼                     ▼
[Cancel / Escape]    [Confirm click]
  │                     │
  ▼                     ▼
resolve(false)       onConfirm? ──► async execution
  │                     │              │         │
  ▼                     │           success    failure
Dialog closes           │              │         │
Focus restored          │           resolve   setState
                        │           (true)    ({error})
                        │              │         │
                        │              ▼         ▼
                        │         Dialog      Error shown
                        │         closes      in dialog
                        │         Focus       (retry/cancel)
                        │         restored
                        │
                        ▼ (no onConfirm)
                     resolve(true)
                        │
                        ▼
                     Dialog closes
                     Focus restored
                     Consumer executes action
```

### Tool Deletion Flow (After Migration)

```
User clicks delete on ToolCard
  │
  ▼
handleDelete(toolId) called
  │
  ▼
confirm({
  title: "Delete Tool",
  description: "Remove tool '{name}'? This cannot be undone.",
  variant: 'danger',
  confirmLabel: 'Yes, Delete'
})
  │
  ▼
User confirms
  │
  ▼
deleteTool({ toolId, confirm: false }) ── API call
  │                                          │
  ▼                                          ▼
result.success = true               result.affected_agents.length > 0
  │                                          │
  ▼                                          ▼
Done (tool deleted)                 confirm({
                                     title: "Tool In Use",
                                     description: "This tool is assigned to: {agent list}...",
                                     variant: 'danger',
                                     confirmLabel: 'Delete Anyway',
                                     onConfirm: () => deleteTool({ toolId, confirm: true })
                                   })
```

### Unsaved Changes Flow

```
User has isDirty = true in editor
  │
  ▼
Navigation attempt (link click / browser back)
  │
  ▼
useBlocker triggers (SPA)  OR  beforeunload fires (browser close)
  │                              │
  ▼                              ▼
UnsavedChangesDialog shown      Browser native prompt shown
  │         │         │
  ▼         ▼         ▼
[Save]   [Discard]  [Cancel]
  │         │         │
  ▼         ▼         ▼
onSave() blocker.    blocker.
  │      proceed()   reset()
  ▼         │         │
proceed     ▼         ▼
           Navigate   Stay on page
```

## Entity Relationships

```
ConfirmationDialogProvider (context)
  ├── manages → DialogState (single active dialog)
  ├── manages → QueuedRequest[] (pending confirmations)
  ├── manages → previousFocusRef (focus restoration target)
  │
  └── renders → ConfirmationDialog (UI component)
                  ├── receives → ConfirmationDialogProps
                  ├── handles → keyboard events (Tab, Escape)
                  └── handles → pointer events (backdrop click)

Consumer Components (AgentCard, ChoreCard, ToolsPanel, PipelineToolbar, etc.)
  ├── call → useConfirmation().confirm(ConfirmationOptions)
  └── receive → Promise<boolean> (resolved on user decision)
```

## Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| `title` | Required, non-empty string | TypeScript compile-time enforcement |
| `description` | Required, non-empty string | TypeScript compile-time enforcement |
| `variant` | Must be `'danger'` \| `'warning'` \| `'info'` | TypeScript union type enforcement |
| `confirmLabel` | Optional; defaults to `'Confirm'` | N/A |
| `cancelLabel` | Optional; defaults to `'Cancel'` | N/A |
| `onConfirm` | Optional; must return `Promise<void>` if provided | TypeScript type enforcement |

## Database Schema

**No changes.** This feature is entirely frontend — no new tables, columns, or migrations.
