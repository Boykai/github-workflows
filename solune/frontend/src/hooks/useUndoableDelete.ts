/**
 * useUndoableDelete — generic hook for undoable delete operations.
 *
 * Encapsulates a soft-delete + undo toast pattern:
 * 1. On trigger: optimistically removes item from TanStack Query cache,
 *    shows sonner toast with "Undo" action button, starts grace timer.
 * 2. On undo: clears timer, restores cache snapshot, shows "Restored" toast.
 * 3. On timer expiry: fires real API delete, handles success/failure.
 * 4. On unmount: clears all pending timers, restores all cached items.
 */

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
  timeoutId: ReturnType<typeof setTimeout>;
  toastId: string;
  snapshot: unknown;
  onDelete: () => Promise<void>;
  queryKey: QueryKey;
}

export function useUndoableDelete({ queryKey, undoTimeoutMs = 5000 }: UseUndoableDeleteOptions) {
  const queryClient = useQueryClient();
  const pendingRef = useRef<Map<string, PendingEntry>>(new Map());
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

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
    [queryClient],
  );

  const undoableDelete = useCallback(
    ({ id, entityLabel, onDelete }: UndoableDeleteParams) => {
      // If already pending, clear the existing timer and toast
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
          return old.filter(
            (item: Record<string, unknown>) => item.id !== id && item.name !== id,
          );
        }
        return old;
      });

      const toastId = `undo-delete-${id}`;

      // Start grace timer — fires the real API delete when it expires
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
    [queryClient, queryKey, undoTimeoutMs, restoreItem],
  );

  // Cleanup on unmount: restore all pending items silently
  useEffect(() => {
    const ref = pendingRef;
    return () => {
      ref.current.forEach((entry) => {
        clearTimeout(entry.timeoutId);
        queryClient.setQueryData(entry.queryKey, entry.snapshot);
      });
      ref.current.clear();
    };
  }, [queryClient]);

  return { undoableDelete, pendingIds };
}
