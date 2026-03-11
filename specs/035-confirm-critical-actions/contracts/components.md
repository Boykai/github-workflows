# Component Contracts: Add Confirmation Step to Critical Actions

**Feature**: 035-confirm-critical-actions | **Date**: 2026-03-11

## Overview

All changes are to existing components. No new components are created. The contracts below describe the behavioral changes and standardized messaging for each component that triggers a critical action.

---

## Modified Component: `ConfirmationDialog`

**Location**: `frontend/src/components/ui/confirmation-dialog.tsx`

**Changes**: Accessibility hardening

### Current Behavior (No Changes)
- Three visual variants: danger (red), warning (amber), info (blue)
- Loading spinner with disabled buttons during async operations
- Inline error display with retry capability
- Backdrop overlay blocks background interactions
- Focus trapping via Tab/Shift+Tab cycling
- Escape key dismissal (blocked during loading)
- Backdrop click dismissal (blocked during loading)

### Accessibility Enhancements
1. **ARIA live region for errors**: Error messages within the dialog should use `aria-live="assertive"` so screen readers announce errors immediately when they appear.
2. **Loading state announcement**: When `isLoading` transitions to `true`, the loading indicator text ("Processing…") should be in an `aria-live="polite"` region.
3. **Button `aria-disabled`**: During loading, confirm and cancel buttons should use `aria-disabled="true"` in addition to the `disabled` HTML attribute for screen reader compatibility.

### Props (Unchanged)
```typescript
interface ConfirmationDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  variant: ConfirmationVariant;  // 'danger' | 'warning' | 'info'
  confirmLabel: string;
  cancelLabel: string;
  isLoading: boolean;
  error: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}
```

---

## Modified Component: `ToolsPanel`

**Location**: `frontend/src/components/tools/ToolsPanel.tsx`

**Changes**: Migrate ad-hoc tool deletion modal to standard `useConfirmation` dialog

### Current Behavior
- Tool deletion (no affected agents): Backend auto-deletes without frontend confirmation
- Tool deletion (with affected agents): Custom inline `<div>` modal showing affected agent names

### New Behavior

**Path 1 — Initial deletion attempt (all tools)**:
```typescript
const handleDelete = async (toolId: string) => {
  const tool = tools.find(t => t.id === toolId);
  const confirmed = await confirm({
    title: 'Delete Tool',
    description: `Remove tool "${tool?.name}"? This cannot be undone.`,
    variant: 'danger',
    confirmLabel: 'Yes, Delete',
  });
  if (!confirmed) return;

  const result = await deleteTool({ toolId, confirm: false });
  if (!result.success && result.affected_agents.length > 0) {
    // Proceed to path 2
  }
};
```

**Path 2 — Tool with affected agents (second confirmation)**:
```typescript
const agentList = result.affected_agents
  .map(a => `• ${a.name}`)
  .join('\n');

const confirmedForce = await confirm({
  title: 'Tool In Use',
  description: `This tool is assigned to the following agents:\n\n${agentList}\n\nDeleting it will remove it from these agents. Are you sure?`,
  variant: 'danger',
  confirmLabel: 'Delete Anyway',
  onConfirm: async () => {
    await deleteTool({ toolId, confirm: true });
  },
});
```

### Removed
- Custom inline `<div className="fixed inset-0 z-50 ...">` modal markup (lines ~321–366)
- `deleteConfirmId` state variable
- `handleConfirmDelete` function

---

## Modified Component: `PipelineToolbar` (or its consumer)

**Location**: The consumer component that provides `onDelete` to `PipelineToolbar`

**Changes**: Add confirmation prompt before pipeline config deletion

### Current Behavior
- `PipelineToolbar` renders a Delete button that calls `onDelete()` directly
- No confirmation is shown

### New Behavior
The consumer wraps the deletion with a `useConfirmation` prompt:

```typescript
const handleDeletePipeline = async () => {
  const confirmed = await confirm({
    title: 'Delete Pipeline',
    description: `This will permanently remove the pipeline configuration "${pipelineName}". This cannot be undone.`,
    variant: 'danger',
    confirmLabel: 'Yes, Delete',
  });
  if (confirmed) {
    deletePipelineMutation.mutate(pipelineId);
  }
};
```

The `PipelineToolbar` component itself is unchanged — it remains a presentation component.

---

## Modified Component: `CleanUpConfirmModal`

**Location**: `frontend/src/components/board/CleanUpConfirmModal.tsx`

**Changes**: Accessibility alignment

### Current Behavior
- Portal-based modal with detailed cleanup impact summary
- Escape key and backdrop click dismissal
- Scroll lock on open
- Categorized lists (branches, PRs, orphaned issues)

### Accessibility Enhancements
1. **ARIA attributes**: Ensure `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `aria-describedby` are present on the modal container.
2. **Focus trapping**: Verify Tab/Shift+Tab cycles within the modal and does not escape to background content.
3. **Focus restoration**: On close, focus should return to the "Clean Up" button that triggered the modal.

### Props (Unchanged)
```typescript
interface CleanUpConfirmModalProps {
  preflightData: CleanupPreflightResponse;
  isExecuting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}
```

---

## Modified Component: `UnsavedChangesDialog`

**Location**: `frontend/src/components/pipeline/UnsavedChangesDialog.tsx`

**Changes**: Accessibility verification

### Current Behavior
- Three-option dialog: Save Changes, Discard, Cancel
- AlertTriangle icon with amber styling
- Escape key → cancel
- Backdrop click → cancel

### Accessibility Enhancements
1. **ARIA attributes**: Verify `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`.
2. **Focus trapping**: Verify Tab cycles between the three buttons.
3. **Focus restoration**: On close, focus returns to the element that triggered navigation.

### Props (Unchanged)
```typescript
interface UnsavedChangesDialogProps {
  isOpen: boolean;
  onSave: () => void;
  onDiscard: () => void;
  onCancel: () => void;
  description?: string;
}
```

---

## Standardized Messaging Catalog

The following table defines the exact messaging for each critical action confirmation:

| Action | Title | Description | Variant | Confirm Label |
|--------|-------|-------------|---------|---------------|
| Delete Agent | "Delete Agent" | "Remove agent \"{name}\"? This opens a PR to delete the repo files. The catalog only updates after that PR is merged into main." | `danger` | "Delete" |
| Delete Chore | "Delete Chore" | "Remove chore \"{name}\"? This cannot be undone." | `danger` | "Delete" |
| Delete Pipeline | "Delete Pipeline" | "This will permanently remove the pipeline configuration \"{name}\". This cannot be undone." | `danger` | "Yes, Delete" |
| Delete Tool | "Delete Tool" | "Remove tool \"{name}\"? This cannot be undone." | `danger` | "Yes, Delete" |
| Delete Tool (in use) | "Tool In Use" | "This tool is assigned to the following agents:\n\n{agent list}\n\nDeleting it will remove it from these agents. Are you sure?" | `danger` | "Delete Anyway" |
| Delete Repo MCP | "Delete Repository MCP" | "Remove MCP server \"{name}\" from the repository config files?" | `danger` | "Delete" |
| Repository Cleanup | "Confirm Cleanup" | (Detailed impact summary via `CleanUpConfirmModal`) | `danger` | "Execute Cleanup" |
| Unsaved Changes | "Unsaved Changes" | "You have unsaved changes. What would you like to do?" | `warning` | "Save Changes" / "Discard" |
