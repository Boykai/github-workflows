# Quickstart: Add Confirmation Step to Critical Actions

**Feature**: 035-confirm-critical-actions | **Date**: 2026-03-11

## Prerequisites

- Node.js 20+
- npm (included with Node.js)

## Setup

```bash
# From repository root
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Backend must also be running for full integration testing:
```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

## What This Feature Changes

This feature modifies **existing files only** — no new files are created. The changes fall into three categories:

1. **Gap closure** — Adding confirmation prompts where they're missing
2. **Standardization** — Migrating ad-hoc modals to the standard `ConfirmationDialog`
3. **Accessibility hardening** — Ensuring all dialogs meet WCAG 2.1 AA

## Files to Modify

### Category 1: Gap Closure

**File**: Consumer component that provides `onDelete` to `PipelineToolbar`
- **What**: Wrap the pipeline config delete handler with a `useConfirmation` prompt
- **Why**: Pipeline deletion currently has no confirmation (FR-001 violation)
- **How**:
  ```typescript
  import { useConfirmation } from '@/hooks/useConfirmation';

  const { confirm } = useConfirmation();

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

### Category 2: Standardization

**File**: `frontend/src/components/tools/ToolsPanel.tsx`
- **What**: Replace the ad-hoc inline `<div>` modal (lines ~321–366) with `useConfirmation` calls
- **Why**: The custom modal lacks accessibility features, focus management, and visual consistency
- **How**:
  1. Remove the custom modal JSX and its state variables (`deleteConfirmId`, `handleConfirmDelete`)
  2. Add initial confirmation before the first `deleteTool` call
  3. For tools with affected agents, show a second `useConfirmation` dialog with the agent list in the description
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
      const agentList = result.affected_agents.map(a => `• ${a.name}`).join('\n');
      await confirm({
        title: 'Tool In Use',
        description: `This tool is assigned to the following agents:\n\n${agentList}\n\nDeleting it will remove it from these agents. Are you sure?`,
        variant: 'danger',
        confirmLabel: 'Delete Anyway',
        onConfirm: async () => {
          await deleteTool({ toolId, confirm: true });
        },
      });
    }
  };
  ```

### Category 3: Accessibility Hardening

**File**: `frontend/src/components/ui/confirmation-dialog.tsx`
- **What**: Add `aria-live` regions for error messages and loading state
- **How**:
  - Wrap the error display area with `aria-live="assertive"`
  - Wrap the loading text with `aria-live="polite"`
  - Add `aria-disabled` to buttons during loading state

**File**: `frontend/src/components/board/CleanUpConfirmModal.tsx`
- **What**: Verify and add ARIA attributes (`role="dialog"`, `aria-modal`, `aria-labelledby`, `aria-describedby`), focus trapping, and focus restoration
- **How**: Audit the modal container element and add missing attributes. Add a focus trap utility if Tab can escape the modal.

**File**: `frontend/src/components/pipeline/UnsavedChangesDialog.tsx`
- **What**: Verify ARIA attributes and focus management
- **How**: Same audit as CleanUpConfirmModal — add missing attributes if needed.

## Implementation Order

### Phase 1: Pipeline Deletion Confirmation (P1, highest gap)
1. Locate the consumer that passes `onDelete` to `PipelineToolbar`
2. Add `useConfirmation` hook usage
3. Wrap the delete handler with confirmation prompt
4. Test: Click delete on a pipeline config → confirmation should appear

### Phase 2: Tool Deletion Migration (P1, standardization)
1. Remove ad-hoc modal JSX from `ToolsPanel.tsx`
2. Remove `deleteConfirmId` state and `handleConfirmDelete` function
3. Rewrite `handleDelete` to use two-step `useConfirmation` flow
4. Test: Delete a tool with no agents → single confirmation
5. Test: Delete a tool with agents → two confirmations (initial + in-use)

### Phase 3: Accessibility Hardening (P1, compliance)
1. Add `aria-live` regions to `ConfirmationDialog`
2. Audit `CleanUpConfirmModal` for ARIA attributes and focus trapping
3. Audit `UnsavedChangesDialog` for ARIA attributes and focus trapping
4. Test: Use keyboard-only to trigger, navigate, and dismiss each dialog type

### Phase 4: Messaging Audit (P1, consistency)
1. Review all existing `confirm()` calls for messaging consistency
2. Update any messages that don't match the standardized pattern (see contracts/components.md)
3. Verify confirm button labels are action-specific (not generic "OK")

## Testing

### Automated Tests
```bash
cd frontend
npm run test                    # Run all frontend tests
npm run test -- --grep confirm  # Run confirmation-related tests
npm run lint                    # ESLint
npm run type-check              # TypeScript strict mode
```

### Manual Verification Checklist
- [ ] Delete an agent → confirmation appears with danger variant
- [ ] Delete a chore → confirmation appears with danger variant
- [ ] Delete a pipeline config → confirmation appears with danger variant
- [ ] Delete a tool (no agents) → confirmation appears with danger variant
- [ ] Delete a tool (with agents) → two-step confirmation with agent list
- [ ] Delete a repo MCP server → confirmation appears with danger variant
- [ ] Repository cleanup → preflight modal with impact summary
- [ ] Unsaved changes → warning dialog with save/discard/cancel
- [ ] Cancel any confirmation → no state change
- [ ] Escape key dismisses all dialogs (except during loading)
- [ ] Tab key cycles within dialog (focus trapped)
- [ ] Screen reader announces dialog title and description on open

## Key Architecture Decisions

1. **No new files**: The existing infrastructure (`useConfirmation`, `ConfirmationDialog`) is mature and extensible. Adding confirmation to uncovered actions requires only consumer-level changes.

2. **No backend changes**: All critical actions already have backend support. The frontend is the confirmation gatekeeper — the backend processes the request regardless of how it was initiated.

3. **Standard dialog for tools**: The ad-hoc tool deletion modal is replaced with the standard `ConfirmationDialog` to ensure consistent accessibility, focus management, and visual styling.

4. **Cleanup modal stays custom**: The `CleanUpConfirmModal` remains a separate component because it displays complex categorized data (branches, PRs, issues) that exceeds the generic dialog's description format. It receives accessibility hardening instead of replacement.

5. **Consumer-level confirmation for pipelines**: The confirmation is added in the component that provides `onDelete` to `PipelineToolbar`, not inside the toolbar itself. This maintains the toolbar as a presentation-only component.
