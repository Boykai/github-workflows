/**
 * Contract: useUndoableDelete Hook
 *
 * Feature: 054-undoable-delete
 * Date: 2026-03-20
 *
 * This file defines the TypeScript interface contract for the useUndoableDelete hook.
 * It is a design artifact — not imported by production code.
 */

import type { QueryKey } from '@tanstack/react-query';

// ─── Input Types ───────────────────────────────────────────────────────────────

/**
 * Configuration for the useUndoableDelete hook.
 * Provided once when the hook is instantiated.
 */
export interface UseUndoableDeleteOptions {
  /**
   * TanStack Query key for the list query that contains the deletable entities.
   * Used for cache snapshot capture and restoration.
   *
   * @example ['agents', 'list', projectId]
   */
  queryKey: QueryKey;

  /**
   * Duration in milliseconds before the permanent deletion fires.
   * After this window, the real API DELETE is called.
   *
   * @default 5000
   */
  undoTimeoutMs?: number;
}

/**
 * Per-deletion parameters passed to the `undoableDelete` function.
 * Provided each time a delete is triggered.
 */
export interface UndoableDeleteParams {
  /**
   * Unique identifier of the entity being deleted.
   * Used as the key for tracking pending state and deduplication.
   */
  id: string;

  /**
   * Human-readable label for the entity, displayed in the toast notification.
   *
   * @example "Agent: MyBot"
   * @example "Chore: Weekly Cleanup"
   */
  entityLabel: string;

  /**
   * Callback that performs the actual API deletion.
   * Called only after the grace window expires without an undo.
   * Must return a Promise that resolves on success or rejects on failure.
   */
  onDelete: () => Promise<void>;
}

// ─── Output Types ──────────────────────────────────────────────────────────────

/**
 * Return value of the useUndoableDelete hook.
 */
export interface UseUndoableDeleteReturn {
  /**
   * Trigger an undoable deletion. Immediately hides the item from the cache,
   * shows an undo toast, and starts the grace timer.
   *
   * If called with an ID that is already pending, the existing timer is
   * cleared and reset.
   */
  undoableDelete: (params: UndoableDeleteParams) => void;

  /**
   * Set of entity IDs that are currently pending deletion.
   * Consumers can use this to filter items from rendered lists:
   *
   * @example
   * const visibleItems = items.filter(item => !pendingIds.has(item.id));
   */
  pendingIds: Set<string>;
}

// ─── Hook Signature ────────────────────────────────────────────────────────────

/**
 * Generic hook for undoable delete operations.
 *
 * Encapsulates the soft-delete + undo toast pattern:
 * 1. On trigger: optimistically removes item from TanStack Query cache,
 *    shows sonner toast with "Undo" action button, starts grace timer.
 * 2. On undo: clears timer, restores cache snapshot, shows "Restored" toast.
 * 3. On timer expiry: fires real API delete, handles success/failure.
 * 4. On unmount: clears all pending timers, restores all cached items.
 *
 * @example
 * ```tsx
 * const { undoableDelete, pendingIds } = useUndoableDelete({
 *   queryKey: agentKeys.list(projectId),
 * });
 *
 * // In delete handler:
 * undoableDelete({
 *   id: agent.id,
 *   entityLabel: `Agent: ${agent.name}`,
 *   onDelete: () => agentsApi.delete(projectId, agent.id),
 * });
 *
 * // In render:
 * const visibleAgents = agents.filter(a => !pendingIds.has(a.id));
 * ```
 */
export declare function useUndoableDelete(
  options: UseUndoableDeleteOptions
): UseUndoableDeleteReturn;
