# Quickstart: Undo/Redo Support for Destructive Actions

**Feature**: 054-undoable-delete
**Date**: 2026-03-20

## Overview

This feature introduces a generic `useUndoableDelete` hook that wraps existing delete operations with a soft-delete + undo toast pattern. On delete confirmation, the item is optimistically hidden from the UI and a toast with an "Undo" button appears. If the user clicks "Undo" within the grace window (~5s), the item is restored. Otherwise, the permanent API delete fires automatically.

## Prerequisites

- Existing TanStack Query v5 setup with `QueryClient` provider
- Sonner `<Toaster>` component rendered in `AppLayout.tsx` (already configured)
- Existing entity hooks (`useAgents`, `useChores`, `useTools`, `useApps`, `usePipelineConfig`)

## Step 1: Create the useUndoableDelete Hook

**File**: `solune/frontend/src/hooks/useUndoableDelete.ts`

```typescript
import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient, type QueryKey } from '@tanstack/react-query';
import { toast } from 'sonner';

interface UseUndoableDeleteOptions {
  queryKey: QueryKey;
  undoTimeoutMs?: number;
}

interface UndoableDeleteParams {
  id: string;
  entityLabel: string;
  onDelete: () => Promise<void>;
}

interface PendingEntry {
  timeoutId: NodeJS.Timeout;
  toastId: string;
  snapshot: unknown;
  onDelete: () => Promise<void>;
  queryKey: QueryKey;
}

export function useUndoableDelete({ queryKey, undoTimeoutMs = 5000 }: UseUndoableDeleteOptions) {
  const queryClient = useQueryClient();
  const pendingRef = useRef<Map<string, PendingEntry>>(new Map());
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

  // Restore a single item from its snapshot
  const restoreItem = useCallback(
    (entityId: string, entry: PendingEntry) => {
      clearTimeout(entry.timeoutId);
      toast.dismiss(entry.toastId);
      queryClient.setQueryData(entry.queryKey, entry.snapshot);
      pendingRef.current.delete(entityId);
      setPendingIds((prev) => {
        const next = new Set(prev);
        next.delete(entityId);
        return next;
      });
    },
    [queryClient]
  );

  // Trigger an undoable deletion
  const undoableDelete = useCallback(
    ({ id, entityLabel, onDelete }: UndoableDeleteParams) => {
      // If already pending, clear the existing timer
      const existing = pendingRef.current.get(id);
      if (existing) {
        clearTimeout(existing.timeoutId);
        toast.dismiss(existing.toastId);
      }

      // Snapshot current cache
      const snapshot = queryClient.getQueryData(queryKey);

      // Optimistically remove item from cache
      queryClient.setQueryData(queryKey, (old: unknown) => {
        if (Array.isArray(old)) {
          return old.filter((item: Record<string, unknown>) => item.id !== id);
        }
        return old;
      });

      const toastId = `undo-delete-${id}`;

      // Start grace timer
      const timeoutId = setTimeout(async () => {
        toast.dismiss(toastId);
        pendingRef.current.delete(id);
        setPendingIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });

        try {
          await onDelete();
          queryClient.invalidateQueries({ queryKey });
        } catch {
          // Restore on failure
          queryClient.setQueryData(queryKey, snapshot);
          toast.error(`Failed to delete ${entityLabel}`, { duration: Infinity });
        }
      }, undoTimeoutMs);

      // Store pending entry
      const entry: PendingEntry = { timeoutId, toastId, snapshot, onDelete, queryKey };
      pendingRef.current.set(id, entry);
      setPendingIds((prev) => new Set(prev).add(id));

      // Show undo toast
      toast(`${entityLabel} deleted`, {
        id: toastId,
        duration: undoTimeoutMs,
        action: {
          label: 'Undo',
          onClick: () => {
            restoreItem(id, entry);
            toast.success(`${entityLabel} restored`);
          },
        },
      });
    },
    [queryClient, queryKey, undoTimeoutMs, restoreItem]
  );

  // Cleanup on unmount: restore all pending items
  useEffect(() => {
    return () => {
      pendingRef.current.forEach((entry, entityId) => {
        clearTimeout(entry.timeoutId);
        queryClient.setQueryData(entry.queryKey, entry.snapshot);
      });
      pendingRef.current.clear();
    };
  }, [queryClient]);

  return { undoableDelete, pendingIds };
}
```

## Step 2: Integrate with Entity Hooks

### Agents (useAgents.ts)

Replace the immediate `mutateAsync` call with `undoableDelete`:

```typescript
import { useUndoableDelete } from './useUndoableDelete';

// Inside the component:
const { undoableDelete, pendingIds } = useUndoableDelete({
  queryKey: agentKeys.list(projectId),
});

// In delete handler (after confirmation dialog):
undoableDelete({
  id: agentId,
  entityLabel: `Agent: ${agent.name}`,
  onDelete: () => agentsApi.delete(projectId, agentId),
});
```

### Chores, Tools, Apps

Same pattern — swap the direct mutation call for `undoableDelete`, passing the appropriate `queryKey`, `entityLabel`, and `onDelete` callback.

### Pipelines (usePipelineConfig.ts)

The pipeline hook uses `useCallback` + `useReducer` instead of `useMutation`. Integration happens at the consumer level:

```typescript
const { undoableDelete, pendingIds } = useUndoableDelete({
  queryKey: pipelineKeys.list(projectId),
});

// Instead of calling deletePipeline() directly:
undoableDelete({
  id: pipeline.id,
  entityLabel: `Pipeline: ${pipeline.name}`,
  onDelete: () => deletePipeline(),
});
```

## Step 3: Filter Pending Items from Rendered Lists

In list views, filter out pending items:

```tsx
const visibleItems = items.filter(item => !pendingIds.has(item.id));
```

## Key Integration Points

| Component | Change | Complexity |
|-----------|--------|-----------|
| `useUndoableDelete.ts` | New file — generic hook | Medium |
| `useAgents.ts` / `useDeleteAgent` | Wire to undoable pattern | Low |
| `useChores.ts` / `useDeleteChore` | Wire to undoable pattern | Low |
| `useTools.ts` / delete mutation | Wire to undoable pattern | Low |
| `useApps.ts` / `useDeleteApp` | Wire to undoable pattern | Low |
| `usePipelineConfig.ts` / `deletePipeline` | Wire at consumer level | Low |
| `AppLayout.tsx` | No change — Toaster already configured | None |
| `api.ts` | No change — API layer untouched | None |

## Verification

After implementation, verify by:

1. Delete any entity → item disappears, undo toast appears
2. Click "Undo" → item reappears, "Restored" toast shows
3. Let timer expire → item permanently deleted (verify via page refresh)
4. Delete 3 items quickly → all 3 toasts appear, each independently undoable
5. Delete item, navigate away → item reappears on return (pending delete cancelled)
6. Delete item, let timer expire with network error → error toast, item reappears
