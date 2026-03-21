# Research: Optimistic Updates for Mutations

**Feature**: 001-optimistic-updates-mutations  
**Date**: 2026-03-21  
**Status**: Complete

## Research Task 1: Existing Optimistic Update Pattern

**Question**: What is the established pattern for optimistic updates in this codebase?

**Decision**: Follow the existing `onMutate` → snapshot → rollback pattern used by `useChores` and `useApps`.

**Rationale**: The codebase has a well-established, consistent pattern across `useCreateChore`, `useUpdateChore`, `useDeleteChore`, `useCreateApp`, `useUpdateApp`, `useDeleteApp`, `useStartApp`, and `useStopApp`. The pattern is:

1. **`onMutate`**: Cancel in-flight queries, snapshot current cache, write optimistic placeholder, return `{ snapshot, queryKey }` as context.
2. **`onError`**: Restore cache from snapshot if context exists; show error toast with `{ duration: Infinity }`.
3. **`onSettled`**: Invalidate queries to reconcile with server state.
4. **`onSuccess`**: Show success toast.

**Alternatives considered**:
- *Separate optimistic layer* — rejected; would diverge from established patterns and increase complexity.
- *React state-based optimism* — rejected; TanStack Query's `onMutate` is purpose-built and already in use.

**Key code references**:
- `useCreateChore` (`useChores.ts:81–138`) — create with placeholder entity
- `useDeleteChore` (`useChores.ts:181–213`) — delete with filter
- `useCreateApp` (`useApps.ts:82–132`) — create with full placeholder object
- `useDeleteApp` (`useApps.ts:183–210`) — delete with filter

## Research Task 2: Paginated Cache Structure (InfiniteData)

**Question**: How does TanStack Query's `useInfiniteQuery` structure cached data and how should optimistic updates interact with it?

**Decision**: Optimistic updates must handle the `InfiniteData<PaginatedResponse<T>>` structure, which contains `{ pages: PaginatedResponse<T>[], pageParams: (string | undefined)[] }`.

**Rationale**: The `useInfiniteList` hook (shared wrapper) produces data in the TanStack `InfiniteData` shape:
```typescript
{
  pages: [
    { items: T[], next_cursor: string | null, has_more: boolean, total_count: number | null },
    { items: T[], next_cursor: string | null, has_more: boolean, total_count: number | null },
    // ...
  ],
  pageParams: [undefined, "cursor-1", "cursor-2", ...]
}
```

The paginated query key follows the pattern `[...baseKey, 'paginated']` (e.g., `['agents', 'list', projectId, 'paginated']`).

**Existing reference implementation**: `useUndoableDelete.ts:74–125` contains `removeEntityFromCache()` which already handles `InfiniteData` structures for deletions. For creates, items should be prepended to the first page's `items` array.

**Alternatives considered**:
- *Invalidate-only for paginated queries* — rejected; would cause visible delay, defeating the purpose.
- *Reset paginated cache on mutation* — rejected; would lose scroll position and loaded pages.

## Research Task 3: Query Key Conventions

**Question**: What are the query key patterns for each entity affected?

**Decision**: Use existing key factories. Paginated keys append `'paginated'` to the base list key.

| Entity | List key | Paginated key |
|--------|----------|---------------|
| Agent | `['agents', 'list', projectId]` | `['agents', 'list', projectId, 'paginated']` |
| Tool | `['tools', 'list', projectId]` | `['tools', 'list', projectId, 'paginated']` |
| Project | `['projects']` | N/A (not paginated) |
| Chore | `['chores', 'list', projectId]` | `['chores', 'list', projectId, 'paginated']` |
| App | `['apps', 'list']` | `['apps', 'list', 'paginated']` |

**Rationale**: Each hook already defines a key factory (e.g., `agentKeys`, `toolKeys`, `choreKeys`, `appKeys`). The paginated variants consistently append `'paginated'` to the list key. Projects use a simple `['projects']` key and are not paginated.

## Research Task 4: Error Notification Pattern

**Question**: What toast/notification pattern is used for mutation errors?

**Decision**: Use `toast.error(error.message || 'Fallback message', { duration: Infinity })` from the Sonner library.

**Rationale**: All existing mutation error handlers follow this exact pattern. The `{ duration: Infinity }` ensures the error persists until manually dismissed. Success toasts use `toast.success('Entity action')` without duration override (auto-dismiss).

The `uploadTool` mutation currently has NO error handler (no `onError`), which is the specific gap mentioned in the spec (FR-004). Adding `onError` with the standard toast pattern closes this gap.

## Research Task 5: Placeholder Entity Construction

**Question**: How should optimistic placeholder entities be constructed?

**Decision**: Follow the existing `satisfies Entity & { _optimistic: boolean }` pattern with temporary IDs and user-provided data.

**Rationale**: `useCreateChore` and `useCreateApp` both construct full placeholder objects:
- Temporary ID: `temp-${Date.now()}`
- User-supplied fields: copied from mutation input
- Server-generated fields: set to sensible defaults (`null`, empty string, `new Date().toISOString()`)
- Marker: `_optimistic: true` flag (used by `satisfies` for type safety, not consumed at runtime)

For new mutations:
- **Agent create**: Name, description, system_prompt from input; temp ID; status `'pending_pr'`
- **Tool upload**: Name, command from input; temp ID; `_optimistic: true`
- **Project create**: Title from input; temp project_id; minimal defaults

## Research Task 6: Cache Data Shapes for Non-Array Caches

**Question**: Some caches use wrapper objects instead of raw arrays. What shapes exist?

**Decision**: Handle three cache shapes: raw array (`T[]`), wrapper object (`{ tools: T[] }`), and `InfiniteData` (`{ pages: PaginatedResponse<T>[] }`).

**Rationale**:
- **Agents list**: `AgentConfig[]` (raw array)
- **Tools list**: `McpToolConfigListResponse` = `{ tools: McpToolConfig[] }` (wrapper object)
- **Projects list**: `ProjectListResponse` = `{ projects: Project[] }` (wrapper object)
- **Chores list**: `Chore[]` (raw array)
- **Apps list**: `App[]` (raw array)
- **Paginated (all)**: `InfiniteData<PaginatedResponse<T>>` (pages structure)

Each optimistic update must match the shape of the cache it's modifying.

## Research Task 7: Paginated Cache Gap — Affected Hooks

**Question**: Which existing `onMutate` handlers need paginated cache awareness?

**Decision**: All hooks with `onMutate` that modify flat caches need parallel updates for paginated keys.

| Hook | Current onMutate | Paginated key exists? | Fix needed? |
|------|------------------|-----------------------|-------------|
| `useCreateChore` | ✅ flat array | ✅ `choreKeys.list + 'paginated'` | ✅ Yes |
| `useUpdateChore` | ✅ flat array | ✅ | ✅ Yes |
| `useDeleteChore` | ✅ flat array | ✅ | ✅ Yes |
| `useInlineUpdateChore` | ✅ flat array | ✅ | ✅ Yes |
| `useCreateApp` | ✅ flat array | ✅ `appKeys.list + 'paginated'` | ✅ Yes |
| `useUpdateApp` | ✅ flat array + detail | ✅ | ✅ Yes |
| `useDeleteApp` | ✅ flat array | ✅ | ✅ Yes |
| `useStartApp` | ✅ flat array | ✅ | ✅ Yes |
| `useStopApp` | ✅ flat array | ✅ | ✅ Yes |
| Tool delete (`useToolsList`) | ✅ wrapper object | ✅ `toolKeys.list + 'paginated'` | ✅ Yes |
| `useUndoableDelete*` | ✅ paginated-aware | ✅ | ❌ Already handled |

## Research Task 8: TanStack Query Best Practices for Optimistic Updates

**Question**: What are TanStack Query's recommended patterns for optimistic updates with `useInfiniteQuery`?

**Decision**: Use `queryClient.setQueryData` with the paginated query key, mapping over `pages` to insert/remove/update items within the appropriate page.

**Rationale**: TanStack Query v5 documentation recommends:
1. Cancel any outgoing refetches with `cancelQueries`
2. Snapshot the previous value with `getQueryData`
3. Optimistically update with `setQueryData`
4. Return a context object with the snapshot
5. On error, rollback with `setQueryData` using the snapshot
6. On settled, always invalidate to reconcile

For `InfiniteData` specifically:
- **Create**: Prepend to `pages[0].items` (newest first)
- **Delete**: Filter across all `pages[n].items`
- **Update**: Map across all `pages[n].items`, replacing matching entity

This matches the pattern already used in `removeEntityFromCache` from `useUndoableDelete.ts`.
