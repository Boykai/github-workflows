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

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient, type QueryKey } from '@tanstack/react-query';
import { toast } from 'sonner';

interface UseUndoableDeleteOptions {
  queryKey?: QueryKey;
  queryKeys?: QueryKey[];
  undoTimeoutMs?: number;
  restoreOnUnmount?: boolean;
}

interface UndoableDeleteParams {
  id: string;
  entityLabel: string;
  onDelete: () => Promise<void>;
}

interface PendingEntry {
  timeoutId: ReturnType<typeof setTimeout>;
  toastId: string;
  snapshots: CacheSnapshot[];
}

interface CacheSnapshot {
  queryKey: QueryKey;
  snapshot: unknown;
  existed: boolean;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function areQueryKeyPartsEqual(left: unknown, right: unknown): boolean {
  if (Object.is(left, right)) {
    return true;
  }

  if (Array.isArray(left) && Array.isArray(right)) {
    return left.length === right.length && left.every((part, index) => areQueryKeyPartsEqual(part, right[index]));
  }

  if (isPlainObject(left) && isPlainObject(right)) {
    const leftKeys = Object.keys(left);
    const rightKeys = Object.keys(right);
    return (
      leftKeys.length === rightKeys.length &&
      leftKeys.every((key) => key in right && areQueryKeyPartsEqual(left[key], right[key]))
    );
  }

  return false;
}

function areQueryKeysEqual(left: QueryKey, right: QueryKey) {
  return left.length === right.length && left.every((part, index) => areQueryKeyPartsEqual(part, right[index]));
}

function shouldKeepEntity(item: Record<string, unknown>, id: string) {
  return item.id !== id && item.name !== id;
}

function removeEntityFromCache(old: unknown, id: string): unknown {
  if (Array.isArray(old)) {
    return old.filter((item) => shouldKeepEntity(item as Record<string, unknown>, id));
  }

  if (!old || typeof old !== 'object') {
    return old;
  }

  if ('pages' in old && Array.isArray(old.pages)) {
    return {
      ...old,
      pages: old.pages.map((page) => {
        if (!page || typeof page !== 'object' || !('items' in page) || !Array.isArray(page.items)) {
          return page;
        }

        return {
          ...page,
          items: page.items.filter((item: unknown) =>
            shouldKeepEntity(item as Record<string, unknown>, id),
          ),
        };
      }),
    };
  }

  if ('items' in old && Array.isArray(old.items)) {
    return {
      ...old,
      items: old.items.filter((item) => shouldKeepEntity(item as Record<string, unknown>, id)),
    };
  }

  if ('tools' in old && Array.isArray(old.tools)) {
    return {
      ...old,
      tools: old.tools.filter((item) => shouldKeepEntity(item as Record<string, unknown>, id)),
    };
  }

  if ('pipelines' in old && Array.isArray(old.pipelines)) {
    return {
      ...old,
      pipelines: old.pipelines.filter((item) =>
        shouldKeepEntity(item as Record<string, unknown>, id),
      ),
    };
  }

  return old;
}

export function useUndoableDelete({
  queryKey,
  queryKeys,
  undoTimeoutMs = 5000,
  restoreOnUnmount = true,
}: UseUndoableDeleteOptions) {
  const queryClient = useQueryClient();
  const pendingRef = useRef<Map<string, PendingEntry>>(new Map());
  const isMountedRef = useRef(true);
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());
  const normalizedQueryKeys = useMemo(
    () => queryKeys ?? (queryKey ? [queryKey] : []),
    [queryKey, queryKeys],
  );

  const setPendingState = useCallback((updater: (prev: Set<string>) => Set<string>) => {
    if (!isMountedRef.current) return;
    setPendingIds(updater);
  }, []);

  const restoreSnapshots = useCallback(
    (snapshots: CacheSnapshot[]) => {
      snapshots.forEach(({ queryKey: snapshotKey, snapshot, existed }) => {
        if (existed) {
          queryClient.setQueryData(snapshotKey, snapshot);
          return;
        }
        queryClient.removeQueries({ queryKey: snapshotKey, exact: true });
      });
    },
    [queryClient],
  );

  const restoreItem = useCallback(
    (entityId: string, entry: PendingEntry) => {
      clearTimeout(entry.timeoutId);
      toast.dismiss(entry.toastId);
      restoreSnapshots(entry.snapshots);
      pendingRef.current.delete(entityId);
      setPendingState((prev) => {
        const next = new Set(prev);
        next.delete(entityId);
        return next;
      });
    },
    [restoreSnapshots, setPendingState],
  );

  const undoableDelete = useCallback(
    ({ id, entityLabel, onDelete }: UndoableDeleteParams) => {
      // If already pending, clear the existing timer and toast
      const existing = pendingRef.current.get(id);
      if (existing) {
        clearTimeout(existing.timeoutId);
        toast.dismiss(existing.toastId);
      }

      const snapshots = normalizedQueryKeys.map((currentQueryKey) => {
        const existingSnapshot = existing?.snapshots.find((snapshot) =>
          areQueryKeysEqual(snapshot.queryKey, currentQueryKey),
        );
        const existed = queryClient.getQueryState(currentQueryKey) !== undefined;
        return (
          existingSnapshot ?? {
            queryKey: currentQueryKey,
            snapshot: queryClient.getQueryData(currentQueryKey),
            existed,
          }
        );
      });

      normalizedQueryKeys.forEach((currentQueryKey) => {
        if (queryClient.getQueryState(currentQueryKey) === undefined) {
          return;
        }
        queryClient.setQueryData(currentQueryKey, (old: unknown) => removeEntityFromCache(old, id));
      });

      const toastId = `undo-delete-${id}`;

      // Start grace timer — fires the real API delete when it expires
      const timeoutId = setTimeout(async () => {
        toast.dismiss(toastId);
        pendingRef.current.delete(id);
        setPendingState((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });

        try {
          await onDelete();
          await Promise.all(
            normalizedQueryKeys.map((currentQueryKey) =>
              queryClient.invalidateQueries({ queryKey: currentQueryKey }),
            ),
          );
        } catch {
          // Restore on failure
          restoreSnapshots(snapshots);
          toast.error(`Failed to delete ${entityLabel}`, { duration: Infinity });
        }
      }, undoTimeoutMs);

      // Store pending entry
      const entry: PendingEntry = {
        timeoutId,
        toastId,
        snapshots,
      };
      pendingRef.current.set(id, entry);
      setPendingState((prev) => new Set(prev).add(id));

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
    [normalizedQueryKeys, queryClient, restoreItem, restoreSnapshots, setPendingState, undoTimeoutMs],
  );

  // Cleanup on unmount: restore all pending items silently
  useEffect(() => {
    const ref = pendingRef;
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (!restoreOnUnmount) {
        return;
      }
      ref.current.forEach((entry) => {
        clearTimeout(entry.timeoutId);
        restoreSnapshots(entry.snapshots);
      });
      ref.current.clear();
    };
  }, [restoreOnUnmount, restoreSnapshots]);

  return { undoableDelete, pendingIds };
}
