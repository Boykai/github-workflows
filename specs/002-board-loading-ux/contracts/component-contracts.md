# Component Contracts: Board Loading UX

**Feature**: 002-board-loading-ux
**Date**: 2026-03-23
**Status**: Complete

## Overview

This feature is frontend-only and does not introduce REST/GraphQL API changes. The contracts below define **component interfaces** and **hook contracts** that establish the boundaries between the modified/new modules.

---

## 1. `useProjectBoard` Hook Contract (Modified)

**File**: `solune/frontend/src/hooks/useProjectBoard.ts`
**Change Type**: Modify existing hook

### Input (unchanged)

The hook accepts no parameters — it manages its own internal state for project selection.

### Output (extended)

```typescript
interface UseProjectBoardReturn {
  // Existing fields (unchanged)
  projects: BoardProject[];
  projectsRateLimitInfo: RateLimitInfo | null;
  projectsLoading: boolean;
  projectsError: Error | null;
  selectedProjectId: string | null;
  boardData: BoardDataResponse | null;
  boardLoading: boolean;
  isFetching: boolean;
  boardError: Error | null;
  lastUpdated: Date | null;
  selectProject: (projectId: string) => void;
  pollingState: AdaptivePollingState;

  // NEW field
  isPlaceholderData: boolean;  // true when displaying cached data from a previous query key
}
```

### Query Configuration Changes

```typescript
// Board data query — add placeholderData option
useQuery({
  queryKey: ['board', 'data', selectedProjectId],
  queryFn: /* unchanged */,
  enabled: !!selectedProjectId,
  staleTime: STALE_TIME_SHORT,          // 60s (unchanged)
  refetchInterval: getRefetchInterval,   // adaptive polling (unchanged)
  placeholderData: keepPreviousData,      // NEW — retains previous project's data while new one loads
})
```

### Behavioral Contract

| Scenario | `boardLoading` | `boardData` | `isFetching` | `isPlaceholderData` |
|----------|---------------|-------------|--------------|-------------------|
| Initial load (no cache) | `true` | `null` | `true` | `false` |
| Data loaded (fresh) | `false` | `BoardDataResponse` | `false` | `false` |
| Background refetch | `false` | `BoardDataResponse` | `true` | `false` |
| Project switch (cached prev) | `false` | `BoardDataResponse` (prev) | `true` | `true` |
| Project switch (no cache) | `true` | `null` | `true` | `false` |

---

## 2. `BoardSkeleton` Component Contract (New)

**File**: `solune/frontend/src/components/board/BoardSkeleton.tsx`
**Change Type**: New component

### Props

```typescript
interface BoardSkeletonProps {
  columnCount?: number;  // default: 5
}
```

### Rendering Contract

- Renders a CSS grid matching `ProjectBoard.tsx` layout: `gridTemplateColumns: repeat(columnCount, minmax(min(16rem, 85vw), 1fr))`
- Each column is a `BoardColumnSkeleton` component (existing, unchanged)
- Container has `aria-busy="true"` and `role="region"` for accessibility
- Wrapped in the same outer container structure as the real board (flex, overflow-x-auto)

### Visual Contract

```text
┌─────────────────────────────────────────────────────────┐
│ aria-busy="true"                                        │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│ │Skel 1│ │Skel 2│ │Skel 3│ │Skel 4│ │Skel 5│          │
│ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │          │
│ │ │░░│ │ │ │░░│ │ │ │░░│ │ │ │░░│ │ │ │░░│ │          │
│ │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │          │
│ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │          │
│ │ │░░│ │ │ │░░│ │ │ │░░│ │ │ │░░│ │ │ │░░│ │          │
│ │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │          │
│ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │ │ ┌──┐ │          │
│ │ │░░│ │ │ │░░│ │ │ │░░│ │ │ │░░│ │ │ │░░│ │          │
│ │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │ │ └──┘ │          │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. `ProjectsPage.tsx` Rendering Contract (Modified)

**File**: `solune/frontend/src/pages/ProjectsPage.tsx`
**Change Type**: Modify rendering logic

### State-Based Rendering Rules

| Priority | Condition | Renders |
|----------|-----------|---------|
| 1 | `selectedProjectId && boardLoading && !boardData` | `<BoardSkeleton />` |
| 2 | `selectedProjectId && boardData && (isFetching \|\| isPlaceholderData)` | Board at `opacity-60` + "Updating…" indicator |
| 3 | `selectedProjectId && boardData && !isFetching && !isPlaceholderData` | Board at `opacity-100` (full) |
| 4 | `selectedProjectId && boardError && !boardData` | Existing error state (unchanged) |

### Background Error Toast Contract

- **Trigger**: `useEffect` watching `boardError` — fires only when `boardData` is present (background error)
- **Message**: `toast.error('Failed to refresh board')`
- **Behavior**: Non-blocking; board continues to display cached data at full opacity
- **No toast on initial error**: When `!boardData && boardError`, the existing error UI is shown instead

### Opacity Transition

```css
/* Applied to board container */
transition-opacity duration-300
opacity-60  /* when refreshing */
opacity-100 /* when fresh */
```

### "Updating…" Indicator

- Position: Top-right corner of board area or centered above the board
- Content: Text "Updating…" with subtle styling
- Visibility: Only during stale/refreshing state
- Interaction: Does not block any user interactions (no pointer-events blocking)
