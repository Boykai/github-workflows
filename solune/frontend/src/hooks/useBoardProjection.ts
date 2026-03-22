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
  // Keep a stable ref to boardData for use inside callbacks without stale closures.
  // Updated in an effect (not during render) to satisfy the react-hooks/refs rule.
  const boardDataRef = useRef(boardData);
  useEffect(() => {
    boardDataRef.current = boardData;
  }, [boardData]);

  // Track per-column expanded end indexes beyond the initial buffer.
  // Using a Map<columnId, expandedEndIndex> avoids a full projection copy on expand.
  const [expansions, setExpansions] = useState<Map<string, number>>(new Map());

  // Reset expansions when boardData changes.
  // React idiom: calling setState during render (before effects) triggers an
  // immediate re-render with the new state, avoiding the setState-in-effect
  // anti-pattern while still resetting on every new dataset.
  const [prevBoardData, setPrevBoardData] = useState(boardData);
  if (boardData !== prevBoardData) {
    setPrevBoardData(boardData);
    setExpansions(new Map());
  }

  const [isInitialRenderComplete, setIsInitialRenderComplete] = useState(false);

  // Compute projections from boardData + expansions (pure derivation — no effect).
  const projections = useMemo(() => {
    if (!boardData?.columns) return new Map<string, ColumnProjection>();
    const result = new Map<string, ColumnProjection>();
    for (const col of boardData.columns) {
      const statusName = col.status.name;
      const totalItems = col.items.length;
      const expandedEnd = expansions.get(statusName);
      const end = Math.min(expandedEnd ?? bufferSize, totalItems);
      result.set(statusName, {
        columnId: statusName,
        renderedRange: { start: 0, end },
        totalItems,
        hasMore: end < totalItems,
      });
    }
    return result;
  }, [boardData, bufferSize, expansions]);

  // Signal initial render complete after the DOM has painted.
  // Both branches use requestAnimationFrame so setState is never called
  // synchronously inside the effect body.
  useEffect(() => {
    let raf: number;
    if (boardData?.columns) {
      raf = requestAnimationFrame(() => setIsInitialRenderComplete(true));
    } else {
      raf = requestAnimationFrame(() => setIsInitialRenderComplete(false));
    }
    return () => cancelAnimationFrame(raf);
  }, [boardData]);

  // Expand rendered range for a column (triggered by scroll / intersection).
  // boardDataRef is used instead of boardData to keep the callback stable.
  const expandColumn = useCallback(
    (columnId: string) => {
      const bd = boardDataRef.current;
      setExpansions((prev) => {
        const col = bd?.columns?.find((c) => c.status.name === columnId);
        if (!col) return prev;
        const totalItems = col.items.length;
        const currentEnd = prev.get(columnId) ?? Math.min(bufferSize, totalItems);
        if (currentEnd >= totalItems) return prev;
        const newEnd = Math.min(currentEnd + bufferSize, totalItems);
        const updated = new Map(prev);
        updated.set(columnId, newEnd);
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
    const observers = observersRef.current;
    const debounceTimers = debounceTimersRef.current;
    return () => {
      for (const observer of observers.values()) {
        observer.disconnect();
      }
      observers.clear();
      for (const timer of debounceTimers.values()) {
        clearTimeout(timer);
      }
      debounceTimers.clear();
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
