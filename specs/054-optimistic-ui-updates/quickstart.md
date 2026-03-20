# Quickstart: Optimistic UI Updates for Mutations

**Feature**: `054-optimistic-ui-updates` | **Date**: 2026-03-20

## Overview

This feature adds TanStack Query v5 optimistic update callbacks (`onMutate`/`onError`/`onSettled`) to 14 existing mutations across the frontend, plus one new backend endpoint and frontend API method for board status changes.

## Prerequisites

- Node.js and npm installed (frontend)
- Python 3.13 with pip (backend)
- Repository cloned with `solune/` directory structure

## Setup

```bash
# Backend
cd solune/backend
pip install -r requirements.txt

# Frontend
cd solune/frontend
npm install
```

## Key Implementation Patterns

### 1. Backend: Add PATCH Endpoint (Phase 1)

**File**: `solune/backend/src/api/board.py`

Add the status update endpoint following the existing PATCH pattern from `chores.py`:

```python
from src.models.board import StatusUpdateRequest, StatusUpdateResponse

@router.patch(
    "/projects/{project_id}/items/{item_id}/status",
    response_model=StatusUpdateResponse,
)
async def update_item_status(
    project_id: str,
    item_id: str,
    body: StatusUpdateRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> StatusUpdateResponse:
    """Update a board item's status by name."""
    success = await github_projects_service.update_item_status_by_name(
        access_token=session.access_token,
        project_id=project_id,
        item_id=item_id,
        status_name=body.status,
    )
    if not success:
        raise NotFoundError("Status not found", details={"status": body.status})
    return StatusUpdateResponse(success=True)
```

**File**: `solune/backend/src/models/board.py`

```python
class StatusUpdateRequest(BaseModel):
    status: str

class StatusUpdateResponse(BaseModel):
    success: bool
```

### 2. Frontend: Add API Method (Phase 1)

**File**: `solune/frontend/src/services/api.ts`

Add to the `boardApi` object:

```typescript
updateItemStatus(
  projectId: string,
  itemId: string,
  status: string,
): Promise<{ success: boolean }> {
  return apiRequest(`${API_BASE_URL}/board/projects/${projectId}/items/${itemId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
},
```

### 3. Frontend: Optimistic Mutation Pattern (All Phases)

The core pattern applied to every mutation:

```typescript
const mutation = useMutation({
  mutationFn: (variables) => api.doSomething(variables),

  onMutate: async (variables) => {
    // 1. Cancel outgoing refetches to avoid overwriting optimistic update
    await queryClient.cancelQueries({ queryKey: QUERY_KEY });

    // 2. Snapshot current data for rollback
    const previousData = queryClient.getQueryData(QUERY_KEY);

    // 3. Skip optimistic update if cache is empty
    if (!previousData) return { previousData: undefined };

    // 4. Optimistically update the cache
    queryClient.setQueryData(QUERY_KEY, (old) => {
      // Apply mutation-specific transformation
      return transformedData;
    });

    // 5. Return snapshot for rollback
    return { previousData };
  },

  onError: (_error, _variables, context) => {
    // Rollback to snapshot
    if (context?.previousData !== undefined) {
      queryClient.setQueryData(QUERY_KEY, context.previousData);
    }
    toast.error('Operation failed', { duration: Infinity });
  },

  onSettled: () => {
    // Re-fetch to reconcile with server truth
    queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  },
});
```

### 4. Board Status Optimistic Update (Phase 1)

**File**: `solune/frontend/src/pages/ProjectsPage.tsx`

```typescript
const statusMutation = useMutation({
  mutationFn: ({ itemId, status }: { itemId: string; status: string }) =>
    boardApi.updateItemStatus(selectedProjectId!, itemId, status),

  onMutate: async ({ itemId, status }) => {
    await queryClient.cancelQueries({ queryKey: ['board', 'data', selectedProjectId] });
    const previous = queryClient.getQueryData<BoardDataResponse>(['board', 'data', selectedProjectId]);
    if (!previous) return { previous: undefined };

    queryClient.setQueryData<BoardDataResponse>(['board', 'data', selectedProjectId], (old) => {
      if (!old) return old;
      // Find item, remove from source column, add to target column
      let movedItem: BoardItem | undefined;
      const updated = old.columns.map((col) => ({
        ...col,
        items: col.items.filter((item) => {
          if (item.item_id === itemId) { movedItem = { ...item, status }; return false; }
          return true;
        }),
      }));
      if (movedItem) {
        const targetCol = updated.find((c) => c.status.name === status);
        if (targetCol) targetCol.items.push(movedItem);
      }
      return { ...old, columns: updated };
    });

    return { previous };
  },

  onError: (_err, _vars, context) => {
    if (context?.previous !== undefined) {
      queryClient.setQueryData(['board', 'data', selectedProjectId], context.previous);
    }
    toast.error('Failed to move item');
  },

  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['board', 'data', selectedProjectId] });
  },
});

// Pass to board component
const handleStatusUpdate = (itemId: string, newStatus: string) => {
  statusMutation.mutate({ itemId, status: newStatus });
};
```

### 5. Delete Optimistic Pattern (Phases 2–4)

Example for chore delete — same pattern applies to app, tool, pipeline deletes:

```typescript
onMutate: async (choreId) => {
  await queryClient.cancelQueries({ queryKey: choreKeys.list(projectId) });
  const previous = queryClient.getQueryData(choreKeys.list(projectId));
  if (!previous) return { previous: undefined };

  queryClient.setQueryData(choreKeys.list(projectId), (old) =>
    old?.filter((chore) => chore.id !== choreId)
  );

  return { previous };
},
```

### 6. Create Optimistic Pattern (Phase 2–3)

Example for chore create — placeholder with temp ID:

```typescript
onMutate: async (data) => {
  await queryClient.cancelQueries({ queryKey: choreKeys.list(projectId) });
  const previous = queryClient.getQueryData(choreKeys.list(projectId));
  if (!previous) return { previous: undefined };

  const placeholder = {
    ...data,
    id: `temp-${Date.now()}`,
    project_id: projectId,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    _optimistic: true,  // Visual pending indicator
    // ... fill remaining required fields with defaults
  };

  queryClient.setQueryData(choreKeys.list(projectId), (old) =>
    old ? [placeholder, ...old] : [placeholder]
  );

  return { previous };
},
```

## Validation

```bash
# Backend lint + type check
cd solune/backend
ruff check src/ tests/
pyright src/

# Frontend lint + type check + test
cd solune/frontend
npm run lint
npm run type-check
npm run test -- --run

# Full test suite (Vitest)
cd solune/frontend
npx vitest run
```

## File Change Summary

| File | Change Type | Description |
|------|------------|-------------|
| `backend/src/models/board.py` | ADD | `StatusUpdateRequest`, `StatusUpdateResponse` models |
| `backend/src/api/board.py` | ADD | PATCH endpoint for item status update |
| `frontend/src/services/api.ts` | ADD | `boardApi.updateItemStatus()` method |
| `frontend/src/pages/ProjectsPage.tsx` | MODIFY | Wire board status mutation with optimistic callbacks |
| `frontend/src/hooks/useChores.ts` | MODIFY | Add `onMutate`/`onError`/`onSettled` to 4 mutations |
| `frontend/src/hooks/useApps.ts` | MODIFY | Add `onMutate`/`onError`/`onSettled` to 5 mutations |
| `frontend/src/hooks/useTools.ts` | MODIFY | Add optimistic delete callbacks |
| `frontend/src/hooks/usePipelineConfig.ts` | MODIFY | Add optimistic delete callbacks |

## Architecture Notes

- **No new dependencies** — TanStack Query v5 and Sonner are already installed
- **No new files** — all changes are additions to existing files (except the contracts doc)
- **Backend change is isolated** — only 1 new endpoint wrapping an existing service function
- **Frontend changes are additive** — only adding mutation callbacks; no existing behavior removed
- **Rollback is automatic** — `onError` restores snapshots; `onSettled` invalidates to reconcile
