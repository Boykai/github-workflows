# Quickstart: Pagination & Infinite Scroll for All List Views

**Feature Branch**: `053-pagination-infinite-scroll`
**Date**: 2026-03-20
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Prerequisites

- Python 3.12+ with virtual environment at `solune/backend/.venv/`
- Node.js 18+ with dependencies installed in `solune/frontend/`
- Backend dev dependencies: `cd solune/backend && uv pip install -e ".[dev]"`
- Frontend dev dependencies: `cd solune/frontend && npm install`
- Familiarity with TanStack React Query v5 (`useInfiniteQuery`)
- Familiarity with FastAPI query parameter injection

## Quick Verification

Run these commands to verify the current baseline state:

```bash
# 1. Backend tests (expect all pass — baseline)
cd solune/backend
.venv/bin/python -m pytest tests/ -q --tb=short

# 2. Frontend tests (expect all pass — baseline)
cd solune/frontend
npx vitest run

# 3. Frontend type check (expect zero errors)
cd solune/frontend
npx tsc --noEmit

# 4. Backend lint + type check
cd solune/backend
.venv/bin/ruff check src/
```

## Implementation Order

### Phase A: Backend Pagination Foundation (Shared Infrastructure)

1. Create `solune/backend/src/models/pagination.py`:
   - Define `PaginatedResponse[T]` generic Pydantic model with `items`, `next_cursor`, `has_more`, `total_count`
   - Define `PaginationParams` model with `limit` (1–100, default 25) and `cursor` (optional base64 string)

2. Create `solune/backend/src/services/pagination.py`:
   - Implement `apply_pagination(items: list[T], limit: int, cursor: str | None) -> PaginatedResponse[T]`
   - Cursor is base64-encoded item ID; decode to find starting position
   - Slice list from cursor position to cursor + limit
   - Set `has_more = len(remaining) > limit`, `next_cursor = base64(last_item.id)` if more exist

3. Add tests `solune/backend/tests/unit/test_pagination.py`:
   - Empty list → `{ items: [], has_more: false, next_cursor: null }`
   - List smaller than limit → all items, `has_more: false`
   - List equal to limit → all items, `has_more: false` (no next page)
   - List larger than limit → first `limit` items, `has_more: true`, valid cursor
   - Cursor navigation → correct next page of items
   - Invalid cursor → appropriate error

**⚠️ GATE**: All pagination utility tests pass before proceeding to Phase B.

### Phase B: Backend Endpoint Migration (P1 first, then P2/P3)

4. Modify `solune/backend/src/api/agents.py`:
   - Add optional `limit: int | None = None` and `cursor: str | None = None` query params
   - Fetch full agent list, pass to `apply_pagination()`, return `PaginatedResponse[Agent]`
   - When both params are `None`, return all items (backward-compatible)

5. Modify `solune/backend/src/api/board.py`:
   - Add optional `column_limit: int | None = None` and `column_cursors: str | None = None` params
   - Parse `column_cursors` as JSON map `{ status_id: cursor }`
   - Apply `apply_pagination()` per column independently
   - Add `next_cursor` and `has_more` to each `BoardColumn` in response

6. Repeat Step 4 pattern for:
   - `solune/backend/src/api/tools.py`
   - `solune/backend/src/api/chores.py`
   - `solune/backend/src/api/apps.py`
   - `solune/backend/src/api/pipelines.py`

**⚠️ GATE**: All backend tests pass, `ruff check src/` clean, `pyright src/` clean.

### Phase C: Frontend Shared Infrastructure (P1)

7. Add TypeScript types in `solune/frontend/src/types/index.ts`:
   ```typescript
   export interface PaginatedResponse<T> {
     items: T[];
     next_cursor: string | null;
     has_more: boolean;
     total_count: number | null;
   }
   ```

8. Create `solune/frontend/src/hooks/useInfiniteList.ts`:
   ```typescript
   import { useInfiniteQuery } from '@tanstack/react-query';
   import type { PaginatedResponse } from '../types';

   export function useInfiniteList<T>(options: {
     queryKey: readonly unknown[];
     queryFn: (params: { limit: number; cursor?: string }) => Promise<PaginatedResponse<T>>;
     limit?: number;
     enabled?: boolean;
     staleTime?: number;
   }) {
     return useInfiniteQuery({
       queryKey: options.queryKey,
       queryFn: ({ pageParam }) =>
         options.queryFn({ limit: options.limit ?? 25, cursor: pageParam }),
       initialPageParam: undefined as string | undefined,
       getNextPageParam: (lastPage) =>
         lastPage.has_more ? (lastPage.next_cursor ?? undefined) : undefined,
       enabled: options.enabled,
       staleTime: options.staleTime,
     });
   }
   ```

9. Create `solune/frontend/src/components/common/InfiniteScrollContainer.tsx`:
   - Render children (the list items)
   - Place a sentinel `<div ref={sentinelRef} />` after children
   - Use `IntersectionObserver` on sentinel to call `fetchNextPage` when visible
   - Show loading spinner when `isFetchingNextPage`
   - Show error message with retry button when `isError`
   - Show nothing when `!hasNextPage` (all loaded)

10. Add paginated fetch helpers to `solune/frontend/src/services/api.ts`:
    - Each API module gets a `listPaginated(params: { limit: number; cursor?: string })` method
    - Returns `PaginatedResponse<T>`

**⚠️ GATE**: Frontend type check passes, lint clean.

### Phase D: Frontend Page Migration (P1 first, then P2/P3)

11. Migrate agents:
    - Update `useAgentsList` in `src/hooks/useAgents.ts` to use `useInfiniteList`
    - Update `AgentsPage.tsx` to render with `InfiniteScrollContainer`
    - Flatten pages for rendering: `data.pages.flatMap(p => p.items)`

12. Migrate board:
    - Update `useProjectBoard` to pass `column_limit` and `column_cursors`
    - Update `BoardColumn.tsx` to include `InfiniteScrollContainer` per column
    - Ensure `@dnd-kit` drag-and-drop works with paginated items

13. Repeat Step 11 pattern for:
    - Tools: `useTools.ts` + `ToolsPage.tsx`
    - Chores: `useChores.ts` + `ChoresPage.tsx`
    - Apps: `useApps.ts` + `AppsPage.tsx`
    - Pipelines: `usePipelineConfig.ts` + relevant page

**⚠️ GATE**: All frontend tests pass, type check clean, lint clean.

### Phase E: Edge Cases and Polish

14. Add debounce protection to `InfiniteScrollContainer` (prevent duplicate requests on rapid scroll)
15. Add filter/sort reset logic (reset to first page when filter or sort changes)
16. Handle concurrent mutations (query invalidation on create/delete while paginated)
17. Add retry UI for failed page loads
18. Verify scroll position preservation via TanStack Query cache

### Phase F: Final Verification

19. Performance testing with 200+ items per list view
20. Full test suite pass (backend + frontend)
21. Zero lint/type-check violations
22. Manual DnD verification on paginated board

## Key Files Reference

| Area | File | Purpose |
|------|------|---------|
| Pagination model (BE) | `solune/backend/src/models/pagination.py` | `PaginatedResponse[T]` Pydantic model |
| Pagination helper (BE) | `solune/backend/src/services/pagination.py` | `apply_pagination()` utility |
| Pagination tests (BE) | `solune/backend/tests/unit/test_pagination.py` | Unit tests |
| Agents API | `solune/backend/src/api/agents.py` | Paginated agents endpoint |
| Board API | `solune/backend/src/api/board.py` | Per-column paginated board |
| Tools API | `solune/backend/src/api/tools.py` | Paginated tools endpoint |
| Chores API | `solune/backend/src/api/chores.py` | Paginated chores endpoint |
| Apps API | `solune/backend/src/api/apps.py` | Paginated apps endpoint |
| Pipelines API | `solune/backend/src/api/pipelines.py` | Paginated pipelines endpoint |
| TS types | `solune/frontend/src/types/index.ts` | `PaginatedResponse<T>` type |
| Infinite list hook | `solune/frontend/src/hooks/useInfiniteList.ts` | Shared `useInfiniteQuery` wrapper |
| Scroll container | `solune/frontend/src/components/common/InfiniteScrollContainer.tsx` | Reusable scroll detection component |
| API service | `solune/frontend/src/services/api.ts` | Paginated fetch helpers |
| Agents hook | `solune/frontend/src/hooks/useAgents.ts` | Migrated to `useInfiniteQuery` |
| Board column | `solune/frontend/src/components/board/BoardColumn.tsx` | Per-column infinite scroll |

## Verification Checklist

- [ ] Backend pagination utility tests pass
- [ ] All backend endpoints accept `limit`/`cursor` params
- [ ] Backward compatibility: endpoints work without pagination params
- [ ] Frontend `PaginatedResponse<T>` type defined
- [ ] `useInfiniteList` hook works with `useInfiniteQuery`
- [ ] `InfiniteScrollContainer` detects scroll and triggers next page
- [ ] All list pages migrated (agents, tools, chores, apps, board, pipelines)
- [ ] Rapid scroll debouncing works
- [ ] Filter/sort reset clears pagination state
- [ ] Error retry preserves loaded data
- [ ] Drag-and-drop works on paginated board columns
- [ ] Initial load < 2s for 200+ items
- [ ] Per-page load < 1s
- [ ] Zero duplicated/skipped items
- [ ] All lint/type-check passes
- [ ] All existing tests pass
