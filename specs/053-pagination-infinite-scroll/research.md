# Research: Pagination & Infinite Scroll for All List Views

**Feature Branch**: `053-pagination-infinite-scroll`
**Date**: 2026-03-20
**Spec**: [spec.md](./spec.md)

## Research Tasks

### RT-001: Cursor-Based vs Offset-Based Pagination

**Context**: The spec requires consistent ordering across pages with no duplicated or skipped
items when loading successive pages (FR-004, SC-005). The backend currently returns full lists
from SQLite via aiosqlite. Need to choose a pagination strategy.

**Decision**: Use cursor-based pagination with opaque cursors. The cursor encodes the last item's
sort key (e.g., `id`, `created_at`) so the next page starts immediately after that item. The
cursor is base64-encoded for opacity. Fallback: when no cursor is provided, return the first page.

**Rationale**: Cursor-based pagination is immune to the "shifting window" problem that affects
offset-based pagination — when items are inserted or deleted between page requests, offset-based
pagination can duplicate or skip items. Since the spec explicitly requires zero duplicated/skipped
items (SC-005) and the system supports concurrent mutations (edge case: items created/deleted
while browsing), cursor-based is the correct choice. TanStack Query's `useInfiniteQuery` natively
supports `getNextPageParam` which maps cleanly to cursor-based responses.

**Alternatives considered**:
- Offset/limit pagination — simpler to implement but vulnerable to item shifting on insert/delete.
  Rejected because spec edge cases explicitly call out concurrent mutations.
- Keyset pagination (without opaque cursor) — exposes internal sort keys in API. Rejected because
  opaque cursors allow backend to change sort implementation without breaking clients.
- GraphQL Relay-style connections — overkill for this codebase's REST API pattern. Rejected to
  maintain consistency with existing endpoint conventions.

---

### RT-002: TanStack Query useInfiniteQuery Integration Pattern

**Context**: The frontend currently uses `useQuery` from TanStack React Query v5 for all list
fetches. Need to determine the migration pattern to `useInfiniteQuery` while preserving existing
query key factories, stale time configuration, and mutation invalidation.

**Decision**: Create a shared `useInfiniteList<T>` hook that wraps `useInfiniteQuery` with
project-standard defaults. The hook accepts a query key, fetch function, and optional config
overrides. It handles `getNextPageParam` (extract `next_cursor` from response), `initialPageParam`
(empty string or `undefined` for first page), and flattening pages into a single items array for
consumer convenience.

Each existing hook (e.g., `useAgentsList`) migrates by replacing `useQuery` with `useInfiniteList`
and updating the fetch function to pass `limit` and `cursor` params. Query key factories remain
unchanged — TanStack Query handles pagination state internally.

**Rationale**: A shared hook avoids duplicating pagination boilerplate across 6+ hooks. TanStack
Query v5's `useInfiniteQuery` is already included in the project dependency (it's part of
`@tanstack/react-query`) so no new dependencies are needed. The `getNextPageParam` callback maps
directly to the `next_cursor` field in the backend response.

**Alternatives considered**:
- Migrate each hook individually without shared abstraction — leads to 6 copies of the same
  `getNextPageParam` and page-flattening logic. Rejected per DRY principle (Constitution V).
- Use a custom pagination state manager outside React Query — loses cache invalidation,
  background refetching, and other TanStack Query benefits. Rejected as over-engineering.
- Keep `useQuery` and implement client-side pagination on the full list — defeats the purpose of
  reducing initial load size. Rejected because it doesn't solve the performance problem.

---

### RT-003: IntersectionObserver for Infinite Scroll Detection

**Context**: The spec requires infinite scroll (load-more-on-scroll) rather than traditional
numbered pagination (FR-005). Need to detect when the user has scrolled to the bottom of a list
to trigger the next page fetch.

**Decision**: Create a reusable `InfiniteScrollContainer` React component that renders a sentinel
`<div>` at the bottom of the list and uses `IntersectionObserver` to detect when it enters the
viewport. When the sentinel is visible and `hasNextPage` is true and `isFetchingNextPage` is
false, call `fetchNextPage()`. The component accepts `hasNextPage`, `isFetchingNextPage`,
`fetchNextPage`, and `isError` as props (all provided by `useInfiniteQuery`). It renders a
loading spinner when fetching, an error message with retry button on failure, and nothing when
all pages are loaded.

**Rationale**: `IntersectionObserver` is the modern browser standard for detecting element
visibility without expensive scroll event listeners. It's supported in all target browsers,
handles debouncing internally (no custom debounce needed for FR-014), and is performant even
with many observed elements. Wrapping it in a reusable component ensures consistent behavior
across all 6 list views and centralizes the error/loading/complete states.

**Alternatives considered**:
- Scroll event listener with manual position calculation — requires manual debouncing, causes
  layout thrashing with `getBoundingClientRect()`, and is harder to get right across different
  scroll containers. Rejected for complexity and performance.
- `react-intersection-observer` library — adds an external dependency for functionality that's
  straightforward to implement with the native API. Rejected to minimize dependencies.
- Manual "Load More" button (no scroll detection) — spec explicitly requires scroll-triggered
  loading (FR-005). Rejected as non-compliant with spec.

---

### RT-004: Board Column Pagination Strategy

**Context**: The project board has a unique layout: multiple columns (statuses) side by side,
each independently scrollable. The spec requires each column to manage its own pagination
independently (Assumption: "Board column pagination operates independently"). The existing
`BoardColumn` component renders all `column.items` in a flat list with `@dnd-kit` drag-and-drop.

**Decision**: Modify the board data endpoint to accept per-column pagination params (a map of
`status_option_id → cursor`). Each column receives its own `InfiniteScrollContainer` sentinel.
When a column's sentinel fires, only that column's next page is fetched. The `BoardDataResponse`
type is extended: each `BoardColumn` gains `next_cursor` and `has_more` fields alongside the
existing `items` array.

For drag-and-drop compatibility: dragged items are moved optimistically in the UI. The
`@dnd-kit` `useDroppable` configuration already operates on the rendered items array, so
pagination is transparent to the drag system — it only sees the items currently loaded in memory.

**Rationale**: Per-column pagination matches the spec's assumption and prevents one column's
large item count from blocking other columns. The endpoint modification is backward-compatible
because the per-column cursor map defaults to empty (returning all items when no cursors are
provided). Drag-and-drop works transparently because `@dnd-kit` operates on the rendered DOM,
not the server-side data set.

**Alternatives considered**:
- Single endpoint call with all columns paginated uniformly — forces all columns to the same
  page state, which doesn't match the independent-scroll UX. Rejected.
- Separate endpoint per column — increases HTTP request count by 5x on initial board load.
  Rejected for performance. The single endpoint with per-column params is more efficient.
- Virtual scrolling for board columns — spec explicitly defers virtual scrolling to a follow-up.
  Rejected per spec assumptions.

---

### RT-005: Filter and Sort Integration with Pagination

**Context**: The spec requires that pagination works with client-side filtering (FR-009) and
sorting (FR-010). Currently, filtering and sorting are applied client-side after data is fetched.
With pagination, the client only has a subset of items, so client-side filtering/sorting on partial
data would produce incorrect results.

**Decision**: For the first iteration, maintain the current approach where filtering and sorting
happen on the full server response. The backend's `apply_pagination()` helper accepts a pre-sorted,
pre-filtered list and paginates it. When the user changes a filter or sort order, the frontend
resets pagination to the first page by invalidating the query (TanStack Query's
`queryClient.resetQueries()`). This ensures the user sees fresh, correctly-ordered results.

If the full list is too large for the server to sort/filter before paginating, a future iteration
can add server-side filter/sort params. This is noted in the spec assumptions as out-of-scope
for this feature.

**Rationale**: The existing codebase applies filtering and sorting client-side. Moving to
server-side filtering/sorting is a significant architectural change beyond this feature's scope.
The spec explicitly states: "Existing client-side filtering and sorting continue to operate on
the loaded data set; server-side filtering and sorting are not in scope for this feature unless
pagination makes them necessary for correctness." Since the backend paginates a pre-filtered
list, correctness is maintained.

**Alternatives considered**:
- Server-side filtering and sorting from day one — correct long-term but significantly larger
  scope. Rejected per spec scope boundaries.
- Client-side filtering on loaded pages only — produces incomplete results (missing items from
  unloaded pages). Rejected for correctness.
- Load all data client-side and paginate display only — defeats the performance purpose of
  pagination. Rejected.

---

### RT-006: Scroll Position Preservation on Navigation

**Context**: The spec requires that when a user navigates away from a paginated list and returns,
their scroll position and previously loaded pages are preserved (FR-012, User Story 2 Scenario 4).

**Decision**: Rely on TanStack React Query's built-in cache. When the user navigates away and
back, `useInfiniteQuery` returns the cached pages without refetching (controlled by `staleTime`).
The existing stale time configurations (`STALE_TIME_PROJECTS`, `STALE_TIME_TOOLS`, etc.) already
prevent immediate refetching. For scroll position, the page components use React Router's
`ScrollRestoration` or a lightweight `useRef` to capture and restore scroll offset.

**Rationale**: TanStack Query's cache already preserves fetched pages across navigation. This is
the framework's intended usage pattern. Combining it with scroll position restoration via
`useRef`/`scrollTo` provides a complete solution without additional state management.

**Alternatives considered**:
- Custom scroll position store (Redux/Zustand) — adds state management complexity for a problem
  already solved by the browser and React Query. Rejected.
- `sessionStorage` for scroll position — survives page refreshes but is overkill for SPA
  navigation. Rejected.
- Always refetch on return — loses loaded pages, violates FR-012. Rejected.

---

### RT-007: Backward Compatibility Strategy

**Context**: The backend API endpoints currently return bare lists (e.g., `list[Agent]`,
`McpToolConfigListResponse`). Changing response shapes could break existing callers.

**Decision**: Make all pagination parameters optional with defaults that reproduce the current
behavior. When `limit` is not provided (or is `None`), the endpoint returns the full list wrapped
in a `PaginatedResponse` with `has_more=False` and `next_cursor=None`. Existing frontend code
that expects bare lists will be updated as part of the migration, but any external API consumers
(if any) can omit pagination params and receive the full data set.

For `McpToolConfigListResponse` which has an additional `presets` field alongside `tools`, the
paginated response wraps only the `tools` array. The `presets` field remains available via a
separate mechanism or is included in every response (since presets are typically few).

**Rationale**: Optional params with full-list defaults ensure zero breaking changes for any
consumer that doesn't opt into pagination. This is the standard backward-compatible pagination
pattern used across the industry.

**Alternatives considered**:
- New versioned endpoints (e.g., `/v2/agents`) — unnecessary overhead for a backward-compatible
  change. Rejected.
- Feature flag to toggle between old and new response format — adds complexity without benefit
  since the change is backward-compatible. Rejected.

## Summary of Decisions

| # | Topic | Decision | Risk |
|---|-------|----------|------|
| RT-001 | Pagination strategy | Cursor-based with opaque base64 cursors | Low — well-understood pattern |
| RT-002 | Frontend hook pattern | Shared `useInfiniteList<T>` wrapping `useInfiniteQuery` | Low — uses existing TanStack Query API |
| RT-003 | Scroll detection | `IntersectionObserver` in reusable `InfiniteScrollContainer` | Low — native browser API |
| RT-004 | Board column pagination | Per-column cursor map in single endpoint | Medium — board complexity |
| RT-005 | Filter/sort integration | Server-side pre-filter then paginate; reset on filter change | Low — maintains existing pattern |
| RT-006 | Scroll preservation | TanStack Query cache + scroll position ref | Low — framework-native |
| RT-007 | Backward compatibility | Optional params with full-list defaults | Low — standard pattern |
