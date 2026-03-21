# Research: ChoresPanel Pagination Migration

**Feature**: 057-chores-pagination-migration
**Date**: 2026-03-21
**Status**: Complete — all unknowns resolved

## Research Task 1: Server-Side Filtering Strategy

### Context
ChoresPanel currently fetches all chores via `service.list_chores(project_id)` (SQL: `SELECT * FROM chores WHERE project_id = ? ORDER BY created_at ASC`) and applies client-side filtering in a `useMemo` block. With pagination, client-side filtering only applies to loaded pages, producing incomplete results.

### Decision: Filter in the API layer before `apply_pagination()`
- **Rationale**: The existing `apply_pagination()` function accepts a pre-filtered `list[T]` and paginates it. The simplest approach is to add optional filter query parameters to the `GET /chores/{project_id}` endpoint and filter the fetched list in Python before passing it to `apply_pagination()`. This avoids modifying the service layer or the SQL query, keeping changes minimal and consistent with the in-memory pagination pattern already used.
- **Alternatives considered**:
  - **SQL-level filtering** (add WHERE clauses to `list_chores`): Would be more performant for very large datasets but requires modifying the service layer. Current chore counts per project are small enough that in-memory filtering after a full fetch is acceptable. The existing pattern in all other paginated endpoints (agents, tools, apps) also fetches all items then paginates in-memory.
  - **Elasticsearch/external search**: Overkill for the scale. Chores are per-project and counts are in the hundreds at most.

### Implementation Detail
Add optional query parameters to the endpoint:
- `status: str | None` — filter by chore status (`active`, `paused`)
- `schedule_type: str | None` — filter by schedule type (`time`, `count`, or `unscheduled` for null schedule)
- `search: str | None` — case-insensitive substring match on `name` or `template_path`
- `sort: str | None` — sort field (`name`, `updated_at`, `created_at`, `attention`). Default: `created_at`
- `order: str | None` — sort direction (`asc`, `desc`). Default: `asc`

Apply filters to the list returned by `service.list_chores()`, then sort, then pass to `apply_pagination()`.

## Research Task 2: Sort Mode — "Attention" Sort Server-Side

### Context
The current ChoresPanel client-side sort includes an "attention" mode that uses a custom scoring function:
```python
# Attention score (lower = more attention needed):
# 0 — active + no schedule (needs manual intervention)
# 1 — has current issue (in progress)
# 2 — normal (default)
# 3 — paused
```

### Decision: Replicate the attention sort in the backend filter logic
- **Rationale**: The attention sort is simple enough to replicate in Python using a key function. It doesn't require complex database queries — just a scoring function applied during the in-memory sort step before pagination.
- **Alternatives considered**:
  - **Remove attention sort**: Would reduce feature parity. Users who rely on it would lose functionality.
  - **SQL CASE expression**: Possible but would require modifying `list_chores` SQL. In-memory sorting on the already-fetched list is simpler and consistent with the current approach.

## Research Task 3: Frontend Hook Parameter Forwarding

### Context
The existing `useChoresListPaginated()` hook and `choresApi.listPaginated()` function only accept `projectId` and pagination params (`limit`, `cursor`). Filter params need to flow from ChoresPanel state → hook → API → backend.

### Decision: Extend the hook and API function signatures to accept optional filter params
- **Rationale**: This follows the principle of least surprise. The `useInfiniteList` hook already accepts a `queryKey` array — adding filter params to the query key causes TanStack Query to automatically refetch when any filter changes. The `queryFn` closure captures the filter params and passes them to the API call.
- **Alternatives considered**:
  - **Generic filter object**: Could create a `ChoresFilterParams` type and pass it as a single object. This is slightly cleaner but adds an abstraction layer. Given that only ChoresPanel uses these params, inline parameters are simpler and more explicit.
  - **URL search params builder**: Could build a generic query string builder, but `URLSearchParams` already handles this natively.

### Implementation Detail
```typescript
// api.ts
listPaginated(
  projectId: string,
  params: {
    limit: number;
    cursor?: string;
    status?: string;
    scheduleType?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
): Promise<PaginatedResponse<Chore>>

// useChores.ts
useChoresListPaginated(
  projectId: string | null | undefined,
  filters?: {
    status?: string;
    scheduleType?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
)
```

Filter values are included in `queryKey` so TanStack Query treats different filter combos as different queries, triggering refetch on change.

## Research Task 4: Pagination Reset on Filter Change

### Context
When the user changes a filter, the paginated results must restart from page 1. The existing `useInfiniteList` hook returns a `resetPagination()` function that calls `queryClient.resetQueries({ queryKey })`.

### Decision: Rely on TanStack Query's automatic refetch via queryKey changes
- **Rationale**: When filter params are part of the `queryKey`, changing any filter produces a new query key. TanStack Query treats this as a brand-new query — it discards the old pages and fetches page 1 fresh. This is the idiomatic TanStack Query approach and requires zero manual reset logic.
- **Alternatives considered**:
  - **Manual `resetPagination()` call via useEffect**: Would work but is redundant when queryKey already includes filters. Adding a useEffect to call resetPagination on filter change is unnecessary complexity.
  - **Explicit page state management**: Would duplicate what TanStack Query already handles. More code, more bugs.

### Key Insight
The `resetPagination()` function from `useInfiniteList` is NOT needed for filter-driven resets. It's useful for external triggers (e.g., "pull to refresh" or "new chore created"), but filter changes are handled automatically by queryKey reactivity.

## Research Task 5: Reference Implementation Patterns

### Context
Multiple panels already implement paginated infinite scroll. Need to confirm the pattern to follow.

### Decision: Follow the AgentsPanel + InfiniteScrollContainer pattern
- **Pattern identified across**: AgentsPanel.tsx, ActivityPage.tsx, ToolsPanel.tsx, AppsPage.tsx
- **Common pattern**:
  1. Hook: `useXxxListPaginated(projectId)` → returns `{ allItems, hasNextPage, isFetchingNextPage, fetchNextPage }`
  2. Panel: Destructures hook result, passes pagination props to grid/list component
  3. Grid: Wraps content in `<InfiniteScrollContainer>` when `fetchNextPage` is provided
  4. `InfiniteScrollContainer` uses `IntersectionObserver` with 200px root margin to trigger next page fetch

### Key Difference for ChoresPanel
- Unlike AgentsPanel (which still does client-side filtering on `allItems`), ChoresPanel will do server-side filtering. This means the `allItems` from the hook already contains only matching results — no client-side `useMemo` filter needed.
- The ChoresGrid already supports optional pagination props (`hasNextPage`, `isFetchingNextPage`, `fetchNextPage`) and wraps content in `InfiniteScrollContainer` when `fetchNextPage` is provided.

## Research Task 6: Cleanup — Non-Paginated Variants

### Context
After migration, the non-paginated `useChoresList()` hook and `choresApi.list()` function may be unused.

### Decision: Check usage and remove if not referenced elsewhere
- **Rationale**: Dead code increases maintenance burden and creates confusion about which function to use. If `useChoresList()` and `choresApi.list()` are only used in ChoresPanel, they should be removed.
- **Usage check needed during implementation**: Search for imports of `useChoresList` and `choresApi.list` across the codebase. If referenced elsewhere (e.g., in a different component or test), retain and add a deprecation comment.

## Research Task 7: Search Debouncing

### Context
ChoresPanel currently uses `useDeferredValue(search)` for search debouncing. With server-side filtering, the deferred value becomes a query parameter sent to the server.

### Decision: Keep `useDeferredValue` — no changes needed
- **Rationale**: `useDeferredValue` is a React 18 built-in that defers re-rendering with low-priority updates. When the deferred search value is part of the TanStack Query key, it naturally debounces API calls — the query only fires when React commits the deferred value. This is already the correct pattern.
- **Alternatives considered**:
  - **lodash.debounce / custom useDebounce**: Would work but adds a dependency or custom hook. `useDeferredValue` is built-in, already in use, and semantically correct for this use case.
