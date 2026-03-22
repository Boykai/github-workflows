/**
 * Board projection hook for lazy-loading large boards.
 *
 * Uses IntersectionObserver to detect which columns are visible and
 * limits the number of rendered items per column to a configurable
 * buffer around the viewport.  The full dataset remains in the
 * TanStack Query cache for accurate filtering and searching.
 *
 * Performance targets:
 * - Initial render: visible items within 2 seconds for 500+ item boards.
 * - Scroll batch load: under 500ms per batch.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { BoardDataResponse } from '@/types';

// ── Configuration ──

export interface BoardProjectionConfig {
  /** Number of items to render beyond the viewport per column (default: 10). */
  bufferSize?: number;
  /** Debounce time for scroll events in ms (default: 150). */
  scrollDebounce?: number;
  /** Threshold for intersection observer (0.0–1.0, default: 0.1). */
  intersectionThreshold?: number;
}

// ── Per-Column Projection State ──

export interface ColumnProjection {
  /** Column identifier (status name). */
  columnId: string;
  /** Index range of rendered items in this column. */
  renderedRange: { start: number; end: number };
  /** Total item count in this column. */
  totalItems: number;
  /** Whether more items exist beyond rendered range. */
  hasMore: boolean;
}

// ── Return Type ──

export interface UseBoardProjectionReturn {
  /** Per-column projection state. */
  columnProjections: Map<string, ColumnProjection>;
  /**
   * Ref callback factory: returns a ref callback to attach to each
   * scrollable column container.
   */
  observerRef: (columnId: string) => (node: HTMLElement | null) => void;
  /** Whether initial render is complete. */
  isInitialRenderComplete: boolean;
  /** Total items rendered across all columns. */
  totalRenderedItems: number;
  /** Total items in full dataset. */
  totalDatasetItems: number;
}

// ── Defaults ──

const DEFAULT_BUFFER = 10;
const DEFAULT_SCROLL_DEBOUNCE = 150;
const DEFAULT_THRESHOLD = 0.1;

// ── Hook ──

export function useBoardProjection(
  boardData: BoardDataResponse | null,
  config?: BoardProjectionConfig,
): UseBoardProjectionReturn {
  const bufferSize = config?.bufferSize ?? DEFAULT_BUFFER;
  const scrollDebounce = config?.scrollDebounce ?? DEFAULT_SCROLL_DEBOUNCE;
  const threshold = config?.intersectionThreshold ?? DEFAULT_THRESHOLD;

  const observersRef = useRef<Map<string, IntersectionObserver>>(new Map());
  const debounceTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const [projections, setProjections] = useState<Map<string, ColumnProjection>>(new Map());
  const [isInitialRenderComplete, setIsInitialRenderComplete] = useState(false);

  // Build initial projections when board data changes
  useEffect(() => {
    if (!boardData?.columns) {
      setProjections(new Map());
      setIsInitialRenderComplete(false);
      return;
    }

    const initial = new Map<string, ColumnProjection>();
    for (const col of boardData.columns) {
      const statusName = col.status.name;
      const totalItems = col.items.length;
      // Initially render only the first buffer-sized batch
      const end = Math.min(bufferSize, totalItems);
      initial.set(statusName, {
        columnId: statusName,
        renderedRange: { start: 0, end },
        totalItems,
        hasMore: end < totalItems,
      });
    }
    setProjections(initial);

    // Mark initial render complete after a microtask
    requestAnimationFrame(() => setIsInitialRenderComplete(true));
  }, [boardData, bufferSize]);

  // Expand rendered range for a column (triggered by scroll / intersection)
  const expandColumn = useCallback(
    (columnId: string) => {
      setProjections((prev) => {
        const current = prev.get(columnId);
        if (!current || !current.hasMore) return prev;

        const newEnd = Math.min(current.renderedRange.end + bufferSize, current.totalItems);
        if (newEnd === current.renderedRange.end) return prev;

        const updated = new Map(prev);
        updated.set(columnId, {
          ...current,
          renderedRange: { start: current.renderedRange.start, end: newEnd },
          hasMore: newEnd < current.totalItems,
        });
        return updated;
      });
    },
    [bufferSize],
  );

  // Create ref callbacks for each column's scroll container
  const observerRef = useCallback(
    (columnId: string) => {
      return (node: HTMLElement | null) => {
        // Clean up previous observer for this column
        const existingObserver = observersRef.current.get(columnId);
        if (existingObserver) {
          existingObserver.disconnect();
          observersRef.current.delete(columnId);
        }

        if (!node) return;

        const observer = new IntersectionObserver(
          (entries) => {
            for (const entry of entries) {
              if (entry.isIntersecting) {
                // Debounce scroll-triggered expansion
                const existingTimer = debounceTimersRef.current.get(columnId);
                if (existingTimer) clearTimeout(existingTimer);

                debounceTimersRef.current.set(
                  columnId,
                  setTimeout(() => {
                    expandColumn(columnId);
                    debounceTimersRef.current.delete(columnId);
                  }, scrollDebounce),
                );
              }
            }
          },
          { threshold },
        );

        observer.observe(node);
        observersRef.current.set(columnId, observer);
      };
    },
    [expandColumn, scrollDebounce, threshold],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      for (const observer of observersRef.current.values()) {
        observer.disconnect();
      }
      observersRef.current.clear();
      for (const timer of debounceTimersRef.current.values()) {
        clearTimeout(timer);
      }
      debounceTimersRef.current.clear();
    };
  }, []);

  // Computed totals
  const totalRenderedItems = useMemo(() => {
    let total = 0;
    for (const p of projections.values()) {
      total += p.renderedRange.end - p.renderedRange.start;
    }
    return total;
  }, [projections]);

  const totalDatasetItems = useMemo(() => {
    if (!boardData?.columns) return 0;
    return boardData.columns.reduce((sum, col) => sum + col.items.length, 0);
  }, [boardData]);

  return {
    columnProjections: projections,
    observerRef,
    isInitialRenderComplete,
    totalRenderedItems,
    totalDatasetItems,
  };
}
