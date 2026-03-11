# Research: Add Confirmation Step to Critical Actions

**Feature**: 035-confirm-critical-actions | **Date**: 2026-03-11

## R1: Existing Confirmation Coverage Audit

**Decision**: Extend existing `useConfirmation` hook to cover all critical actions; do not create a new system.

**Rationale**: The codebase already has a mature confirmation infrastructure:
- `useConfirmation` hook (188 lines) — imperative, promise-based, with queuing, async `onConfirm`, focus restoration, and variant support
- `ConfirmationDialog` component (203 lines) — accessible modal with danger/warning/info variants, loading spinner, inline error display, focus trapping, Escape key handling
- `CleanUpConfirmModal` (250 lines) — specialized multi-step confirmation for repository cleanup with preflight data
- `UnsavedChangesDialog` (69 lines) — three-option dialog (save/discard/cancel) for navigation guards
- `useUnsavedChanges` hook (39 lines) — `beforeunload` + `useBlocker` integration

**Current coverage audit**:

| Critical Action | Component | Confirmation | Standard Dialog | Notes |
|----------------|-----------|:------------:|:---------------:|-------|
| Delete Agent | `AgentCard.tsx` | ✅ | ✅ | Uses `useConfirmation` with danger variant |
| Delete Chore | `ChoreCard.tsx` | ✅ | ✅ | Uses `useConfirmation` with danger variant |
| Delete Pipeline Config | `PipelineToolbar.tsx` | ⚠️ | ❌ | Calls `onDelete()` directly — **needs confirmation** |
| Delete Tool (no deps) | `ToolsPanel.tsx` | ✅ | ❌ | Backend auto-deletes; no frontend prompt shown |
| Delete Tool (with deps) | `ToolsPanel.tsx` | ✅ | ❌ | **Ad-hoc custom modal** — needs migration to standard dialog |
| Delete Repo MCP Server | `ToolsPanel.tsx` | ✅ | ✅ | Uses `useConfirmation` with danger variant |
| Repository Cleanup | `CleanUpConfirmModal.tsx` | ✅ | ⚠️ | Custom modal; acceptable due to complex preflight data display |
| Unsaved Changes | `UnsavedChangesDialog.tsx` | ✅ | ⚠️ | Custom 3-option dialog; acceptable but needs accessibility audit |

**Gaps identified**:
1. Pipeline config deletion lacks any confirmation prompt
2. Tool deletion (with affected agents) uses a non-standard ad-hoc modal instead of `ConfirmationDialog`
3. Tool deletion (no affected agents) silently succeeds without user confirmation

**Alternatives considered**:
- Creating a new confirmation library → Rejected; existing infrastructure is mature and well-tested
- Using a third-party modal library (e.g., Radix Dialog) → Rejected; adds dependency, existing component meets all requirements
- Browser `window.confirm()` → Rejected; not customizable, not accessible, breaks visual consistency

## R2: Accessibility Requirements for Modal Dialogs

**Decision**: Harden the existing `ConfirmationDialog` to fully meet WCAG 2.1 AA for modal dialog accessibility.

**Rationale**: The existing dialog has partial accessibility support (ARIA attributes, focus trapping via Tab key cycling, Escape key). The following gaps need to be addressed:

**Current accessibility features** (already implemented):
- `role="dialog"` and `aria-modal="true"` on the dialog container
- `aria-labelledby` pointing to the title element
- `aria-describedby` pointing to the description element
- Focus trapping with Tab/Shift+Tab cycling
- Escape key dismissal (when not loading)
- Backdrop click dismissal (when not loading)
- Focus capture on open (auto-focuses cancel button)

**Gaps to address**:
- Verify `aria-live` region for dynamic error messages within the dialog
- Ensure loading state changes are announced to screen readers
- Verify backdrop blocks pointer events on background content
- Ensure focus restoration returns to the exact triggering element (already implemented in `useConfirmation` via `previousFocusRef`)

**Best practices applied** (from WAI-ARIA Authoring Practices for Modal Dialogs):
1. Dialog container must have `role="dialog"` + `aria-modal="true"` ✅
2. Title referenced via `aria-labelledby` ✅
3. Description referenced via `aria-describedby` ✅
4. Focus moves into dialog on open ✅
5. Tab cycles within dialog (focus trap) ✅
6. Escape closes dialog ✅
7. Focus returns to trigger on close ✅
8. Background content is inert (backdrop) ✅

**Alternatives considered**:
- Radix UI Dialog primitive → Rejected; adds a dependency for something already 90% implemented
- HTML `<dialog>` element → Rejected; browser support varies, and the custom implementation provides more control over focus management and styling

## R3: Double-Click and Rapid Submission Prevention

**Decision**: Use the existing `isLoading` state in `useConfirmation` to prevent duplicate submissions; add `disabled` guard on confirm button during async operations.

**Rationale**: The existing infrastructure already handles this partially:
- `useConfirmation` sets `isLoading: true` during async `onConfirm` execution
- `ConfirmationDialog` disables both confirm and cancel buttons while `isLoading` is true
- The confirm button shows a loading spinner during processing

**Remaining gap**: Some consumers of `useConfirmation` do NOT use the `onConfirm` callback pattern — they check the boolean result and then call a mutation directly. In this pattern, the dialog closes before the mutation runs, so there's no loading state protection. The double-click risk exists in the brief window between the user clicking confirm and the dialog closing.

**Mitigation approach**:
1. For `onConfirm`-style consumers: Already protected ✅
2. For boolean-result consumers (AgentCard, ChoreCard): The mutation itself has `isPending` state that disables the trigger button. The risk is minimal because the dialog closes immediately and the underlying button becomes disabled. No change needed.
3. For the ad-hoc tool deletion modal: Migration to standard `ConfirmationDialog` with `onConfirm` will add proper loading protection.

**Alternatives considered**:
- Debouncing all confirm clicks → Rejected; adds unnecessary complexity when loading state already handles it
- Global event throttle → Rejected; too broad, could affect unrelated interactions
- Forcing all consumers to use `onConfirm` pattern → Rejected; the boolean-result pattern is valid and safe when mutations have their own `isPending` guards

## R4: Standardized Confirmation Messaging Patterns

**Decision**: Define a messaging convention for all confirmation prompts with specific title, description, and button label patterns.

**Rationale**: Current messaging is inconsistent:
- Agent deletion: title="Delete Agent", description includes PR creation context, confirmLabel="Delete"
- Chore deletion: title="Delete Chore", description="Remove chore '{name}'? This cannot be undone.", confirmLabel="Delete"
- Repo MCP deletion: title="Delete Repository MCP", description="Remove MCP server '{name}' from the repository config files?", confirmLabel="Delete"
- Tool deletion (custom modal): title="Tool in use", vague description, button="Delete anyway"

**Standardized pattern**:

| Element | Pattern | Example |
|---------|---------|---------|
| Title | `Delete {EntityType}` or `{Action} {EntityType}` | "Delete Agent", "Clean Up Repository" |
| Description | `{Consequence sentence}. {Downstream impact if any}. This cannot be undone.` | "This will permanently remove the agent 'ReviewerBot' and open a pull request to delete its configuration files. This cannot be undone." |
| Confirm label | `Yes, {Action}` or `{Action}` | "Yes, Delete", "Proceed with Cleanup" |
| Cancel label | `Cancel` (universal) | "Cancel" |
| Variant | `danger` for irreversible, `warning` for significant reversible, `info` for informational | danger for deletions, warning for unsaved changes |

**Alternatives considered**:
- Per-component custom messaging → Rejected; leads to inconsistency (as currently exists)
- Centralized message catalog/i18n → Rejected; over-engineering for current scale; messages should be co-located with the actions that trigger them

## R5: Tool Deletion Modal Migration Strategy

**Decision**: Replace the ad-hoc inline modal in `ToolsPanel.tsx` with a two-step flow using the standard `useConfirmation` dialog.

**Rationale**: The current tool deletion flow has two paths:
1. **No affected agents**: Backend auto-deletes the tool with `confirm: false`. No frontend prompt is shown.
2. **Affected agents**: A custom `<div>` modal is rendered inline with a list of affected agents and "Cancel" / "Delete anyway" buttons.

The custom modal lacks:
- Proper ARIA roles and accessibility attributes
- Focus trapping (Tab can escape the modal)
- Escape key handling
- Focus restoration on close
- Loading state during the confirm deletion API call
- Consistent visual styling with other confirmation dialogs
- Error display on failure

**Migration approach**:
1. For path 1 (no affected agents): Add a standard `useConfirmation` prompt before calling `deleteTool({ confirm: false })`. The user should always see a confirmation before any deletion.
2. For path 2 (affected agents): Use `useConfirmation` with a rich description that lists affected agent names. The `onConfirm` callback calls `deleteTool({ confirm: true })`.

The affected agents list can be formatted as a bullet list in the description string (the `ConfirmationDialog` description area supports scrollable content with `max-h-[60vh]`).

**Alternatives considered**:
- Keep the custom modal but add accessibility → Rejected; duplicates logic already in `ConfirmationDialog`
- Create a new `ToolDeletionDialog` component → Rejected; violates DRY principle when `ConfirmationDialog` can handle it
- Use a multi-step confirmation flow → Rejected; unnecessary complexity since the affected-agents info can be shown in a single confirmation step

## R6: Pipeline Config Deletion Confirmation

**Decision**: Add a `useConfirmation` prompt in the pipeline deletion flow before executing the delete action.

**Rationale**: The `PipelineToolbar` component has a Delete button that calls `onDelete()` directly when clicked (line ~164 of `PipelineToolbar.tsx`). No confirmation is shown. This is the most significant coverage gap — pipeline configurations can contain complex multi-stage setups that take time to recreate.

**Implementation approach**: The confirmation should be added at the consumer level (the component that provides `onDelete` to `PipelineToolbar`), using `useConfirmation` with:
- Title: "Delete Pipeline"
- Description: "This will permanently remove the pipeline configuration '{name}'. This cannot be undone."
- Variant: `danger`
- Confirm label: "Yes, Delete"

If the consumer already wraps `onDelete` with a mutation, the confirmation should gate the mutation call.

**Alternatives considered**:
- Adding confirmation inside PipelineToolbar → Rejected; the toolbar is a presentation component that should not own dialog state. The consumer knows the pipeline context and should manage confirmation.
- Keeping it unconfirmed → Rejected; violates FR-001 (all destructive actions require confirmation)

## R7: Unsaved Changes Dialog Accessibility

**Decision**: Audit and harden `UnsavedChangesDialog` for accessibility compliance while keeping its custom three-option structure.

**Rationale**: The `UnsavedChangesDialog` is a specialized dialog that offers three choices (Save, Discard, Cancel) rather than the standard two-button confirmation pattern. It cannot be replaced by `ConfirmationDialog` without losing the three-option capability. However, it should meet the same accessibility standards:
- `role="dialog"` + `aria-modal="true"`
- `aria-labelledby` / `aria-describedby`
- Focus trapping
- Escape key → cancel behavior
- Focus restoration to trigger element

The existing implementation already has Escape key handling and backdrop click dismissal. Focus trapping and ARIA attributes should be verified and added if missing.

**Alternatives considered**:
- Extending `ConfirmationDialog` with a third button → Rejected; over-complicates the generic dialog for a single use case
- Converting to a browser prompt → Rejected; not customizable, no save option
