# Research: Undo/Redo Support for Destructive Actions

**Feature**: 054-undoable-delete
**Date**: 2026-03-20
**Status**: Complete

## Research Task 1: Sonner Toast Action Button API

**Context**: The undo toast requires an interactive "Undo" button inside the toast and control over toast duration and dismissal behavior.

**Decision**: Use sonner's built-in `action` option on `toast()` calls.

**Rationale**: Sonner v2.x (currently ^2.0.7 in the project) natively supports action buttons via the `action` property: `toast('Deleted', { action: { label: 'Undo', onClick: handler } })`. This provides:
- A styled action button rendered inside the toast
- An `onClick` callback that fires when the user clicks the button
- Compatible with the existing `<Toaster>` configuration in `AppLayout.tsx`
- `duration` parameter controls auto-dismiss timing (already defaulting to 5000ms)
- `onDismiss` callback fires when the toast is dismissed (by timeout, manual close, or programmatic `toast.dismiss(id)`)
- `id` parameter enables programmatic dismissal: `toast.dismiss(toastId)`

**Alternatives Considered**:
- **Custom toast component**: More control but unnecessary — sonner's action API provides everything needed.
- **react-hot-toast**: Would require swapping the existing toast library for no benefit.
- **Custom overlay/snackbar**: Over-engineered for this use case.

---

## Research Task 2: TanStack Query v5 Optimistic Update Pattern for Deletions

**Context**: Items must be optimistically removed from lists on delete confirmation and restored on undo. The project already uses TanStack Query v5's optimistic mutation pattern (onMutate/onError/onSettled) in useChores, useApps, and useTools.

**Decision**: Use `queryClient.getQueryData()` for snapshot capture and `queryClient.setQueryData()` for optimistic removal/restoration, following the existing codebase pattern.

**Rationale**: The project already establishes this pattern across multiple hooks:
1. `onMutate`: Cancel outgoing queries, snapshot current data, set optimistically updated data
2. `onError`: Roll back to snapshot
3. `onSettled`: Invalidate queries to refetch from server

For the undoable delete, this pattern is adapted:
- **On delete trigger**: Capture snapshot via `getQueryData()`, remove item from cache via `setQueryData()`, start grace timer
- **On undo**: Restore snapshot via `setQueryData()`, cancel grace timer
- **On timer expiry**: Fire real API delete, then `invalidateQueries()` on success or restore snapshot on failure

Key difference from standard optimistic mutations: the actual mutation (`mutationFn`) is deferred — it fires after the grace window, not immediately. The snapshot must be held in a `useRef` Map keyed by entity ID.

**Alternatives Considered**:
- **Server-side soft delete**: Requires backend changes (adding `deleted_at` columns, modifying queries). Over-engineered for a client-side grace window.
- **React state-based hiding**: Would duplicate cache state and cause inconsistencies. Using TanStack Query cache directly is more reliable.
- **Zustand/Jotai store**: Introducing a new state management library for a single feature violates Simplicity (Constitution V).

---

## Research Task 3: setTimeout Cleanup and React Lifecycle

**Context**: Pending delete timers must be cleaned up on component unmount (FR-016, FR-017) to prevent memory leaks and orphaned API calls.

**Decision**: Store timeout IDs in a `useRef<Map<string, NodeJS.Timeout>>` and clear all pending timeouts in a `useEffect` cleanup function.

**Rationale**:
- `useRef` persists across renders without causing re-renders
- `Map<string, NodeJS.Timeout>` supports multiple concurrent pending deletions keyed by entity ID
- `useEffect(() => () => { /* cleanup */ }, [])` guarantees cleanup on unmount
- On cleanup (unmount/navigation): clear all timeouts, restore all cached snapshots, preventing both memory leaks and orphaned deletes
- This pattern is standard React and requires no additional dependencies

**Alternatives Considered**:
- **AbortController**: Useful for cancelling fetch requests but doesn't apply to setTimeout-based deferred execution.
- **Custom event system**: Unnecessary complexity for local component state.
- **useReducer-based state machine**: Over-engineered — the hook needs only a Set of pending IDs and a Map of timeouts/snapshots.

---

## Research Task 4: Multiple Concurrent Deletions and Toast Stacking

**Context**: Users may delete multiple items rapidly (SC-004 requires ≥3 concurrent). The existing Toaster is configured with `visibleToasts={3}`.

**Decision**: Each deletion gets its own toast with a unique ID. The `useUndoableDelete` hook tracks pending deletions in a `Set<string>` (pendingIds) and stores per-deletion state (timeout, snapshot, toast ID) in a `Map`.

**Rationale**:
- Sonner naturally stacks toasts up to the `visibleToasts` limit (3)
- Each toast receives a unique `id` (e.g., `undo-delete-${entityId}`) for independent lifecycle management
- The hook's `pendingIds` Set enables consumers to conditionally hide items from rendered lists via `filter(item => !pendingIds.has(item.id))`
- No toast library configuration changes needed — the existing `<Toaster>` setup already supports this

**Alternatives Considered**:
- **Single undo toast with batch info**: Loses independent undo capability per item. Rejected per FR-010.
- **Increasing visibleToasts limit**: Unnecessary — 3 concurrent visible toasts is sufficient per SC-004. Older toasts remain in the queue.

---

## Research Task 5: Pipeline Delete Integration (Reducer-Based vs. Mutation-Based)

**Context**: Unlike other entity hooks (useAgents, useChores, useTools, useApps) which use `useMutation`, `usePipelineConfig.ts` uses a `useCallback` + `useReducer` dispatch pattern for deletions. The hook already has its own undo/redo stack which resets on delete.

**Decision**: Wrap the pipeline delete callback with `useUndoableDelete` at the consumer level rather than inside `usePipelineConfig`. The hook's `undoableDelete` function accepts an `onDelete` callback, making it agnostic to the caller's state management pattern.

**Rationale**:
- `useUndoableDelete` is designed to be generic: it accepts `onDelete: () => Promise<void>` as a callback
- For mutation-based hooks (agents, chores, tools, apps): wrap `mutateAsync()` as the `onDelete` callback
- For reducer-based hooks (pipeline): wrap the existing `deletePipeline()` callback
- Cache operations (snapshot/restore) happen at the TanStack Query cache level, which is shared
- Pipeline's internal `clearUndoRedo()` and `resetPending()` calls should only fire after the grace window — not immediately on delete trigger

**Alternatives Considered**:
- **Refactor usePipelineConfig to useMutation**: Would be a large, risky refactor touching the pipeline editor's state machine. Violates minimal-change principle.
- **Separate useUndoablePipelineDelete hook**: Unnecessary duplication — the generic hook handles this case.

---

## Research Task 6: Navigation Cancellation Behavior

**Context**: FR-016 requires cancelling pending deletions when the component unmounts due to navigation. The spec states: "Navigation away cancels pending deletions and restores items."

**Decision**: On `useEffect` cleanup (triggered by unmount/navigation), iterate over all pending deletions: clear each timeout, restore each cached snapshot, and show no toast (component is already unmounted).

**Rationale**:
- React's `useEffect` cleanup runs synchronously on unmount, including route changes
- Restoring items on navigation is the safest default (spec assumption: "users who navigate away likely did not intend to complete the deletion")
- TanStack Query's `setQueryData` is callable from cleanup functions — the `queryClient` remains valid
- Dismissed toasts auto-clean on unmount — sonner handles this internally

**Alternatives Considered**:
- **Complete deletions on navigation**: Would violate FR-016 and the spec's explicit assumption. Also risks data loss if navigation was accidental.
- **Global pending-delete store**: Would survive navigation but contradicts the spec requirement. Also adds unnecessary global state.
- **Route-change listener**: Redundant — `useEffect` cleanup already handles this natively.

---

## Summary

All NEEDS CLARIFICATION items have been resolved. Key technology decisions:

| Area | Decision | Key Reason |
|------|----------|------------|
| Toast UI | Sonner `action` API | Already in use, native action button support |
| Cache management | TanStack Query `getQueryData`/`setQueryData` | Existing pattern in codebase |
| Timer management | `useRef<Map>` + `useEffect` cleanup | Standard React, no new dependencies |
| Concurrent deletes | Per-entity `Set` + `Map` tracking | Supports independent undo per item |
| Pipeline integration | Generic callback-based hook | Works with both useMutation and useCallback patterns |
| Navigation cleanup | `useEffect` cleanup restores items | Safest default per spec assumptions |
