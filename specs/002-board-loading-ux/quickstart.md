# Quickstart: Board Loading UX — Skeleton, Stale-While-Revalidate, Refetch Indicator

**Feature**: 002-board-loading-ux
**Date**: 2026-03-23

## Overview

This guide covers how to implement the board loading UX improvements. All changes are frontend-only within `solune/frontend/`.

## Prerequisites

- Node.js and npm installed
- Repository cloned and on the feature branch

```bash
cd solune/frontend
npm install
```

## Implementation Steps

### Step 1: Modify `useProjectBoard.ts` — Add Stale-While-Revalidate

**File**: `src/hooks/useProjectBoard.ts`

1. Import `keepPreviousData` from `@tanstack/react-query`
2. Add `placeholderData: keepPreviousData` to the board data query options
3. Destructure `isPlaceholderData` from the board data query result
4. Add `isPlaceholderData` to the hook's return object and type interface

```typescript
// Import
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';

// In board data query
const {
  data: boardData,
  isLoading: boardLoading,
  isFetching,
  isPlaceholderData,  // NEW
  error: boardError,
} = useQuery({
  queryKey: ['board', 'data', selectedProjectId],
  queryFn: /* unchanged */,
  enabled: !!selectedProjectId,
  staleTime: STALE_TIME_SHORT,
  refetchInterval: getRefetchInterval,
  placeholderData: keepPreviousData,  // NEW
});

// Return from hook
return {
  // ... existing fields
  isPlaceholderData,  // NEW
};
```

### Step 2: Create `BoardSkeleton.tsx` — Skeleton Grid Component

**File**: `src/components/board/BoardSkeleton.tsx`

Create a new component that renders a grid of 5 `BoardColumnSkeleton` columns matching the real board layout.

```typescript
import { BoardColumnSkeleton } from './BoardColumnSkeleton';

const DEFAULT_COLUMN_COUNT = 5;

export function BoardSkeleton({ columnCount = DEFAULT_COLUMN_COUNT }: { columnCount?: number }) {
  return (
    <div
      className="flex h-full w-full flex-1 overflow-x-auto overflow-y-visible pb-6"
      role="region"
      aria-busy="true"
      aria-label="Loading board"
    >
      <div
        className="grid min-h-full min-w-full items-stretch gap-5 pb-2"
        style={{
          gridTemplateColumns: `repeat(${columnCount}, minmax(min(16rem, 85vw), 1fr))`,
        }}
      >
        {Array.from({ length: columnCount }, (_, i) => (
          <BoardColumnSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
```

### Step 3: Modify `ProjectsPage.tsx` — Replace Spinner with Skeleton + Add Indicator

**File**: `src/pages/ProjectsPage.tsx`

1. Import `BoardSkeleton`
2. Replace the `CelestialLoader` block with `BoardSkeleton` for initial loads
3. Add opacity dimming and "Updating…" indicator for background refreshes
4. Add `useEffect` for background error toast

```typescript
// Import
import { BoardSkeleton } from '@/components/board/BoardSkeleton';

// Replace spinner with skeleton (around line 455-459)
{selectedProjectId && boardLoading && !boardData && (
  <BoardSkeleton />
)}

// Wrap board in opacity container
{selectedProjectId && !boardLoading && boardData && (
  <div className={`relative transition-opacity duration-300 ${
    (isFetching && !boardLoading) || isPlaceholderData ? 'opacity-60' : 'opacity-100'
  }`}>
    {((isFetching && !boardLoading) || isPlaceholderData) && (
      <div className="absolute top-2 right-4 z-10 text-xs text-muted-foreground">
        Updating…
      </div>
    )}
    {/* existing board rendering */}
  </div>
)}

// Background error toast
useEffect(() => {
  if (boardError && boardData) {
    toast.error('Failed to refresh board');
  }
}, [boardError, boardData]);
```

## Verification

Run the following commands to verify the implementation:

```bash
cd solune/frontend
npm run lint
npx tsc --noEmit
npm run test
npm run build
```

### Manual Testing Scenarios

1. **First load → skeleton**: Clear browser cache, navigate to a project → skeleton columns appear → board replaces them
2. **Re-visit cached project → instant**: Navigate away, then back to the same project → board appears instantly (no skeleton, no spinner)
3. **Switch projects → stale display**: View Project A, switch to Project B → Project A's board dims with "Updating…" → Project B's board replaces it
4. **Background refetch → indicator**: Wait for background refetch → board dims briefly with "Updating…" → restores to full opacity
5. **Refetch failure → toast**: Simulate network failure during background refetch → toast "Failed to refresh board" appears → board stays visible with cached data
