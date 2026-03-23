# Research: Board Loading UX — Skeleton, Stale-While-Revalidate, Refetch Indicator

**Feature**: 002-board-loading-ux
**Date**: 2026-03-23
**Status**: Complete

## Research Areas

### 1. TanStack Query `keepPreviousData` / `placeholderData` Pattern

**Decision**: Use `keepPreviousData` (imported from `@tanstack/react-query`) as the `placeholderData` option on the board data query.

**Rationale**: In TanStack Query v5 (`^5.91.0`, the version installed in this project), the `keepPreviousData` behavior is achieved by passing `placeholderData: keepPreviousData` to `useQuery`. This retains the previous query's data as placeholder when the query key changes (e.g., switching projects), preventing the UI from flashing to a loading state. The hook also exposes `isPlaceholderData` to distinguish stale placeholder data from fresh data.

**Alternatives Considered**:
- **`initialData`**: Rejected — `initialData` makes the query think data is already loaded (no background refetch triggered), which defeats the stale-while-revalidate purpose.
- **Manual state management**: Rejected — would duplicate TanStack Query's built-in cache behavior and add unnecessary complexity.
- **`placeholderData` with a custom function**: Rejected — `keepPreviousData` is the canonical TanStack utility for exactly this use case; a custom function would be reinventing the wheel.

**Key Implementation Detail**: The `isPlaceholderData` boolean returned by `useQuery` is `true` when the currently displayed data comes from a previous query key (e.g., Project A's data shown while Project B loads). This is the signal used to trigger the dimming/indicator in the UI.

---

### 2. Skeleton Loading Screen — Pattern & Accessibility

**Decision**: Create a `BoardSkeleton` wrapper component that renders 5 `BoardColumnSkeleton` columns in the same CSS grid layout as `ProjectBoard.tsx`.

**Rationale**: Skeleton screens are a proven UX pattern (Google, Meta, Vercel) that reduce perceived loading time by showing placeholder content matching the final layout. The existing `BoardColumnSkeleton` and `IssueCardSkeleton` components are already built with matching dimensions — they just need a grid wrapper.

**Alternatives Considered**:
- **Content-shimmer placeholder (single block)**: Rejected — doesn't provide spatial layout continuity; users can't anticipate where columns and cards will appear.
- **Progressive/partial loading**: Rejected — the board query returns all columns at once; there's no partial data to progressively render.
- **Keep the CelestialLoader but add skeleton below it**: Rejected — defeats the purpose; the skeleton should replace the spinner entirely for first-load.

**Key Implementation Details**:
- Grid CSS from `ProjectBoard.tsx`: `gridTemplateColumns: repeat(5, minmax(min(16rem, 85vw), 1fr))` with `gap-5`
- Hardcode 5 columns (spec requirement FR-004; matches default board column count)
- Add `aria-busy="true"` on the skeleton container for accessibility (spec FR-005)
- `BoardColumnSkeleton` already includes `role="status"` and `aria-busy="true"` per-column

---

### 3. Background Refetch Indicator — UI Pattern

**Decision**: Overlay an "Updating…" text indicator with board opacity dimming (opacity-60 → opacity-100 transition) when a background refresh is in progress. Show a toast notification on background refresh failures.

**Rationale**: This pattern is non-intrusive (users can still interact), communicates data staleness to power users, and matches the existing sonner toast pattern used throughout the app.

**Alternatives Considered**:
- **Progress bar at top of board**: Rejected — adds visual complexity; a simple text indicator with dimming is sufficient for background refreshes.
- **Inline banner/alert**: Rejected — takes up vertical space and pushes board content down, disrupting layout.
- **No indicator (silent refresh)**: Rejected — users should know when data might be stale, especially during project switching.

**Key Implementation Details**:
- Trigger condition: `(isFetching && !boardLoading) || isPlaceholderData` — this covers both background refetch and project-switching scenarios
- Opacity transition: `transition-opacity duration-300` for smooth fade
- Toast pattern: `toast.error('Failed to refresh board')` using existing sonner import
- Only show toast for background errors — initial load errors continue to use the existing full error state

---

### 4. Rendering State Machine

**Decision**: Define three clear rendering states based on query state, replacing the current binary loading/loaded pattern.

**Rationale**: The current code has two states (loading → loaded). The new feature introduces a third state (stale/refreshing) that requires explicit state management to avoid visual glitches.

| State | Condition | UI Behavior |
|-------|-----------|-------------|
| **Initial Load** | `boardLoading && !boardData` | Show `BoardSkeleton` (5 skeleton columns) |
| **Loaded / Fresh** | `!boardLoading && boardData && !isFetching` | Show board at full opacity |
| **Stale / Refreshing** | `boardData && (isFetching \|\| isPlaceholderData)` | Show board at opacity-60 with "Updating…" indicator |
| **Error (initial)** | `boardError && !boardData` | Show existing error state (unchanged) |
| **Error (background)** | `boardError && boardData` | Toast notification, board stays visible at full opacity |

**Alternatives Considered**:
- **React state machine library (XState)**: Rejected — overkill for 5 states derived from existing query flags; YAGNI principle applies.
- **Custom `useReducer` state**: Rejected — TanStack Query already provides all the boolean flags needed; adding another layer of state management adds complexity without benefit.

---

### 5. Existing Component Reuse Assessment

**Decision**: Reuse existing `BoardColumnSkeleton` and `IssueCardSkeleton` as-is. No modifications needed.

**Rationale**: Both components were built with matching dimensions and styling for this exact use case. They include proper accessibility attributes (`role="status"`, `aria-busy="true"`).

**Findings**:
- `BoardColumnSkeleton.tsx`: Height `h-[72rem]` / `xl:h-[95rem]`, rounded corners `rounded-[1.4rem]`, header with skeleton title/count, 3 `IssueCardSkeleton` children — matches `ProjectBoard.tsx` column layout
- `IssueCardSkeleton.tsx`: Card with skeleton lines for title, description, tags, avatar — matches real `IssueCard` dimensions
- Both use Shadcn's `<Skeleton>` component for consistent animation

**No modifications needed** — components are ready to use as-is.

---

### 6. Toast Error Handling for Background Refreshes

**Decision**: Add `onError` callback to the board data query's `useEffect` or use `meta` + query cache global error handler — **or** add explicit error detection via `useEffect` watching `boardError` + `boardData` state.

**Rationale**: TanStack Query v5 removed the `onError` callback from `useQuery`. The recommended pattern is to use `useEffect` to react to error state changes. Since the hook already returns `boardError`, the consuming component (`ProjectsPage.tsx`) can handle this.

**Implementation Approach**: In `ProjectsPage.tsx`, add a `useEffect` that watches for `boardError` when `boardData` is already present (indicating a background refresh failure, not an initial load failure). This keeps the error notification logic in the rendering layer where the toast system is already used.

**Alternatives Considered**:
- **Global query cache `onError`**: Rejected — too broad; would affect all queries, not just board refreshes.
- **Custom query `meta` + global handler**: Rejected — adds indirection; a simple `useEffect` in the consuming component is clearer.
- **Error boundary**: Rejected — error boundaries catch render errors, not async data fetching errors; also would unmount the board, which defeats the purpose.
