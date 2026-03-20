# Research: Optimistic UI Updates for Mutations

**Feature**: `054-optimistic-ui-updates` | **Date**: 2026-03-20

## R1: TanStack Query v5 Optimistic Update Pattern

**Decision**: Use TanStack Query v5's native `onMutate`/`onError`/`onSettled` callbacks within `useMutation`.

**Rationale**: The project already uses `@tanstack/react-query v5.91.0`. TanStack Query v5 provides first-class support for optimistic updates through mutation callbacks. The pattern is:

1. `onMutate`: Cancel outgoing refetches, snapshot current cache, apply optimistic update via `queryClient.setQueryData`, return snapshot as context
2. `onError`: Receive context from `onMutate`, restore snapshot via `queryClient.setQueryData`
3. `onSettled`: Invalidate queries to reconcile with server truth regardless of success/failure

This approach requires zero additional libraries and integrates directly with the existing hook architecture. All 14 mutation hooks already use `useMutation` — adding callbacks is purely additive.

**Alternatives Considered**:
- **Zustand/Jotai optimistic store**: Rejected — adds a parallel state layer that duplicates what TanStack Query already manages
- **Custom middleware/wrapper**: Rejected — adds abstraction complexity without benefit; each mutation's optimistic logic is distinct enough that a wrapper would be over-generalized
- **React `useOptimistic` hook (React 19)**: Rejected — designed for form submissions with server actions, not for cache-level optimistic updates across multiple query keys

## R2: Existing Backend Service for Board Status Updates

**Decision**: Reuse `update_item_status_by_name()` from `solune/backend/src/services/github_projects/projects.py`.

**Rationale**: The function already:
- Accepts `(access_token, project_id, item_id, status_name)` parameters
- Performs case-insensitive status name resolution via GraphQL
- Calls `update_item_status()` with resolved `field_id` and `option_id`
- Returns `bool` indicating success/failure
- Handles missing fields and invalid option names gracefully

No modifications to this function are needed. The new PATCH endpoint simply wraps it with HTTP request/response handling and authentication.

**Alternatives Considered**:
- **Accept `option_id` directly in the endpoint**: Rejected — forces the frontend to know internal GraphQL field/option IDs, breaking encapsulation
- **Create a new service function**: Rejected — `update_item_status_by_name()` already does exactly what's needed

## R3: FastAPI Endpoint Pattern for Board Status Updates

**Decision**: Follow the existing PATCH endpoint pattern from `solune/backend/src/api/chores.py` (the `update_chore` endpoint).

**Rationale**: The codebase has a consistent pattern for PATCH endpoints:
- Pydantic model for request body validation
- `Depends(get_session_dep)` for authentication
- Service call wrapped in error handling
- Custom exceptions (`NotFoundError`, `ValidationError`, `GitHubAPIError`) for error responses
- Minimal response model

The new endpoint will:
- Accept `StatusUpdateRequest(status: str)` as body
- Call `github_projects_service.update_item_status_by_name()`
- Return `{ success: bool }` on success
- Raise `GitHubAPIError` on failure

**Alternatives Considered**:
- **Return full `BoardDataResponse`**: Rejected — `onSettled` re-fetches anyway; full response adds ~2KB payload and additional processing for no benefit
- **PUT instead of PATCH**: Rejected — PATCH is semantically correct for partial resource update (changing only the status field)

## R4: Frontend API Method Pattern

**Decision**: Add `updateItemStatus(projectId, itemId, status)` to the existing `boardApi` object in `solune/frontend/src/services/api.ts`.

**Rationale**: All API methods follow the same pattern: `apiRequest<ResponseType>(url, options)` using the native `fetch()` wrapper. The `boardApi` object already groups board-related API calls. Adding a new method maintains consistency.

**Alternatives Considered**:
- **Separate API module**: Rejected — violates the existing single-file API service pattern
- **Direct fetch in the hook**: Rejected — bypasses CSRF token handling and error standardization provided by `apiRequest`

## R5: Optimistic Cache Manipulation Strategy

**Decision**: Use `queryClient.setQueryData` with inline updater functions per mutation type.

**Rationale**: Each mutation type requires a distinct cache manipulation:

| Mutation Type | Cache Manipulation |
|--------------|-------------------|
| Board status change | Move `BoardItem` between `BoardColumn.items` arrays |
| Create (chore/app) | Insert placeholder object with temp ID at start of list |
| Update (chore/app) | Map over list, replace matching item with merged fields |
| Delete (chore/app/tool/pipeline) | Filter item out of list by ID |
| Start/Stop (app) | Map over list, update `status` field for matching item |

Each manipulation uses `setQueryData` with a function updater: `(old) => { /* return modified copy */ }`. This is the standard TanStack Query approach and avoids direct cache mutation.

**Alternatives Considered**:
- **Immer for immutable updates**: Rejected — adds dependency; spread operators are sufficient for these shallow updates
- **Shared utility function**: Rejected per YAGNI — the manipulations are similar but not identical enough to justify a generic helper

## R6: Error Toast Integration

**Decision**: Reuse existing `toast.error()` from Sonner v2 in `onError` callbacks.

**Rationale**: Every existing mutation hook already imports and uses `toast` from `sonner`. The pattern is `toast.error(message, { duration: Infinity })` for persistent error notifications. Optimistic rollback errors will follow the same pattern, providing a consistent user experience.

**Alternatives Considered**:
- **Custom error boundary**: Rejected — mutation errors are recoverable (rollback handles state); error boundaries are for unrecoverable render errors
- **Error state in hook return**: Rejected — TanStack Query already exposes `mutation.error` for component-level error display; toast provides immediate feedback

## R7: Visual Pending Indicator for Optimistic Creates

**Decision**: Optimistically created items will include a `_optimistic: true` flag in their cached data. Components can use this to render with reduced opacity or a subtle spinner.

**Rationale**: Per FR-008, optimistically created items (new chores, new apps) should be visually distinguishable during the pending period. Adding a transient `_optimistic` flag to the placeholder object is the simplest approach — it's automatically removed when `onSettled` re-fetches server data (which won't include the flag).

Per FR-009, update and delete operations do not need visual distinction.

**Alternatives Considered**:
- **Separate pending state array**: Rejected — adds parallel state management outside the cache
- **CSS class based on temp ID prefix**: Rejected — fragile string matching; flag is more explicit
- **TanStack Query `isMutating` counter**: Rejected — too coarse; doesn't indicate which specific items are pending

## R8: Concurrent Mutation Handling

**Decision**: Each mutation captures its own independent snapshot in `onMutate`. No coordination between concurrent mutations.

**Rationale**: TanStack Query v5 handles concurrent mutations naturally. Each `onMutate` callback receives its own closure context. If mutation A and mutation B are both in-flight:
- Each has its own snapshot
- If A fails, its rollback restores the pre-A state; B's `onSettled` will then re-fetch and reconcile
- `queryClient.cancelQueries` in `onMutate` prevents stale refetches from interfering

The spec's edge case about rapid sequential creates (e.g., 5 chores in quick succession) is handled because each create appends to the current cache state (which already includes previous optimistic inserts).

**Alternatives Considered**:
- **Mutation queue with serial execution**: Rejected — adds complexity and defeats the purpose of instant feedback
- **Merge snapshots on conflict**: Rejected — unnecessary; `onSettled` invalidation resolves all state within seconds

## R9: Empty Cache Edge Case

**Decision**: If `queryClient.getQueryData(key)` returns `undefined` in `onMutate`, skip the optimistic update and let the mutation proceed normally (fire-and-wait).

**Rationale**: Per the spec's edge case, if no cached data exists to snapshot, there's nothing to optimistically update. The mutation still fires to the server; `onSettled` still invalidates. The user simply doesn't see an instant update in this rare scenario (e.g., navigating directly to a page before any data has loaded).

**Alternatives Considered**:
- **Initialize empty cache structure**: Rejected — creates risk of rendering empty state that conflicts with loading spinners
- **Defer mutation until cache is populated**: Rejected — adds unnecessary latency for an edge case
