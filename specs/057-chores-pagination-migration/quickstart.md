# Quickstart: ChoresPanel Pagination Migration

**Feature**: 057-chores-pagination-migration
**Date**: 2026-03-21

## Overview

This guide provides the implementation approach for migrating ChoresPanel from client-side filtering with full data fetch to server-side filtering with cursor-based infinite scroll pagination. The migration touches 4 source files and 2 test files across backend and frontend.

## Prerequisites

- Python 3.13+ with `solune/backend` installed (`pip install -e ".[dev]"`)
- Node.js with `solune/frontend` dependencies (`npm ci`)
- Familiarity with the existing pagination pattern (see `AgentsPanel.tsx`, `useInfiniteList.ts`)

## Implementation Phases

### Phase 1: Backend — Add Server-Side Filtering

**File**: `solune/backend/src/api/chores.py`

**What to change**: Add optional query parameters for filtering and sorting to the `list_chores` endpoint. Apply filters to the chore list before passing to `apply_pagination()`.

**Approach**:

1. Add query parameters to the endpoint signature:
   ```python
   @router.get("/{project_id}")
   async def list_chores(
       project_id: str,
       session: Annotated[UserSession, Depends(get_session_dep)],
       limit: Annotated[int | None, Query(ge=1, le=100)] = None,
       cursor: Annotated[str | None, Query()] = None,
       status: Annotated[str | None, Query()] = None,
       schedule_type: Annotated[str | None, Query()] = None,
       search: Annotated[str | None, Query()] = None,
       sort: Annotated[str | None, Query()] = None,
       order: Annotated[str | None, Query()] = None,
   ) -> list[Chore] | dict:
   ```

2. After fetching all chores, apply filters:
   ```python
   chores = await service.list_chores(project_id)

   # Apply filters
   if status:
       chores = [c for c in chores if c.status == status]
   if schedule_type:
       if schedule_type == "unscheduled":
           chores = [c for c in chores if c.schedule_type is None]
       else:
           chores = [c for c in chores if c.schedule_type == schedule_type]
   if search:
       query = search.strip().lower()
       chores = [c for c in chores if query in c.name.lower() or query in c.template_path.lower()]
   ```

3. Apply sorting before pagination:
   ```python
   # Sort
   if sort == "name":
       chores.sort(key=lambda c: c.name.lower(), reverse=(order == "desc"))
   elif sort == "updated_at":
       chores.sort(key=lambda c: c.updated_at, reverse=(order == "desc"))
   elif sort == "attention":
       def attention_score(c):
           if c.status == "active" and not c.schedule_type:
               return 0
           if c.current_issue_number:
               return 1
           if c.status == "paused":
               return 3
           return 2
       chores.sort(key=attention_score, reverse=(order == "desc"))
   # Default: created_at (already sorted from DB query)
   elif sort == "created_at" and order == "desc":
       chores.reverse()
   ```

4. Pass filtered+sorted list to `apply_pagination()` (existing code, no changes).

**Testing**: Add pytest tests for filter combinations in `tests/unit/api/test_chores.py`.

---

### Phase 2: Frontend — Wire Up Paginated Hook

**Step 1 — Update API function** (`solune/frontend/src/services/api.ts`):

Extend `choresApi.listPaginated()` to accept optional filter parameters:

```typescript
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
): Promise<PaginatedResponse<Chore>> {
  const qs = new URLSearchParams({ limit: String(params.limit) });
  if (params.cursor) qs.set('cursor', params.cursor);
  if (params.status) qs.set('status', params.status);
  if (params.scheduleType) qs.set('schedule_type', params.scheduleType);
  if (params.search) qs.set('search', params.search);
  if (params.sort) qs.set('sort', params.sort);
  if (params.order) qs.set('order', params.order);
  return request<PaginatedResponse<Chore>>(`/chores/${projectId}?${qs}`);
},
```

**Step 2 — Update hook** (`solune/frontend/src/hooks/useChores.ts`):

Update `useChoresListPaginated()` to accept and forward filter params:

```typescript
export function useChoresListPaginated(
  projectId: string | null | undefined,
  filters?: {
    status?: string;
    scheduleType?: string;
    search?: string;
    sort?: string;
    order?: string;
  },
) {
  const queryClient = useQueryClient();
  const result = useInfiniteList<Chore>({
    queryKey: [...choreKeys.list(projectId ?? ''), 'paginated', filters ?? {}],
    queryFn: (params) =>
      choresApi.listPaginated(projectId!, { ...params, ...filters }),
    limit: 25,
    staleTime: STALE_TIME_LONG,
    enabled: !!projectId,
  });

  return {
    ...result,
    invalidate: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: choreKeys.list(projectId) });
      }
    },
  };
}
```

**Key**: Including `filters` in `queryKey` causes TanStack Query to automatically start a new query when any filter changes — no manual reset needed.

**Step 3 — Update ChoresPanel** (`solune/frontend/src/components/chores/ChoresPanel.tsx`):

1. Replace `useChoresList` with `useChoresListPaginated`, passing filter state:
   ```typescript
   const {
     allItems: chores,
     isLoading,
     hasNextPage,
     isFetchingNextPage,
     fetchNextPage,
   } = useChoresListPaginated(projectId, {
     status: statusFilter === 'all' ? undefined : statusFilter,
     scheduleType: scheduleFilter === 'all' ? undefined : scheduleFilter,
     search: deferredSearch || undefined,
     sort: sortMode,
     order: sortMode === 'updated' ? 'desc' : 'asc',
   });
   ```

2. Remove the `filteredChores` `useMemo` block (filtering is now server-side).

3. Pass `chores` (from `allItems`) and pagination props to ChoresGrid:
   ```typescript
   <ChoresGrid
     chores={chores}
     hasNextPage={hasNextPage ?? false}
     isFetchingNextPage={isFetchingNextPage}
     fetchNextPage={fetchNextPage}
     // ... other existing props
   />
   ```

**Testing**: Update Vitest tests for `useChoresListPaginated` with filter params in query key.

---

### Phase 3: Cleanup

1. Search codebase for references to `useChoresList` and `choresApi.list`
2. If not used elsewhere, remove both functions
3. If used elsewhere, add deprecation comment

## Verification Checklist

- [ ] Backend: `GET /chores/{project_id}?limit=25&status=active` returns only active chores, paginated
- [ ] Backend: `GET /chores/{project_id}?limit=25&search=deploy` returns only matching chores
- [ ] Backend: Combined filters work (status + schedule_type + search)
- [ ] Backend: Cursor pagination works correctly with active filters
- [ ] Frontend: ChoresPanel loads 25 chores initially
- [ ] Frontend: Scrolling loads next 25 chores
- [ ] Frontend: Changing status filter resets to page 1 and re-fetches
- [ ] Frontend: Search with `useDeferredValue` debounces correctly
- [ ] Frontend: Rapid filter toggling doesn't cause errors
- [ ] Frontend: Empty filter results show "No chores match" message
- [ ] Tests: pytest tests pass for all filter combinations
- [ ] Tests: Vitest tests pass for hook with filter params

## Key Decisions Summary

| Decision | Rationale |
|----------|-----------|
| Filter in API layer (Python) before `apply_pagination()` | Consistent with existing pattern; avoids service layer changes |
| Include filters in TanStack Query key | Automatic refetch on filter change; idiomatic approach |
| Keep `useDeferredValue` for search | Built-in, already working, no dependencies needed |
| Replicate "attention" sort in backend | Maintains feature parity; simple scoring function |
| Default page size: 25 | Consistent with all other paginated hooks |
