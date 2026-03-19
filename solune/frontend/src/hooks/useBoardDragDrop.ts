/**
 * useBoardDragDrop — manages drag-and-drop state for the project board.
 */

import { useState, useCallback } from 'react';
import type { DragStartEvent, DragOverEvent, DragEndEvent } from '@dnd-kit/core';
import { toast } from 'sonner';
import type { BoardItem, BoardDataResponse } from '@/types';

export interface BoardDndHandlers {
  onDragStart: (event: DragStartEvent) => void;
  onDragOver: (event: DragOverEvent) => void;
  onDragEnd: (event: DragEndEvent) => void;
  onDragCancel: () => void;
}

export interface UseBoardDndReturn {
  activeCard: BoardItem | null;
  overColumnId: string | null;
  handlers: BoardDndHandlers;
}

export function useBoardDragDrop(
  boardData: BoardDataResponse,
  onStatusUpdate?: (itemId: string, newStatus: string) => void | Promise<void>,
): UseBoardDndReturn {
  const [activeCard, setActiveCard] = useState<BoardItem | null>(null);
  const [overColumnId, setOverColumnId] = useState<string | null>(null);
  const [sourceColumnStatus, setSourceColumnStatus] = useState<string | null>(null);

  const findItemById = useCallback(
    (itemId: string): BoardItem | undefined => {
      for (const column of boardData.columns) {
        const found = column.items.find((item) => item.item_id === itemId);
        if (found) return found;
      }
      return undefined;
    },
    [boardData.columns],
  );

  const findColumnByItemId = useCallback(
    (itemId: string): string | undefined => {
      for (const column of boardData.columns) {
        if (column.items.some((item) => item.item_id === itemId)) {
          return column.status.name;
        }
      }
      return undefined;
    },
    [boardData.columns],
  );

  const onDragStart = useCallback(
    (event: DragStartEvent) => {
      const itemId = String(event.active.id);
      const item = findItemById(itemId);
      if (item) {
        setActiveCard(item);
        setSourceColumnStatus(findColumnByItemId(itemId) ?? null);
      }
    },
    [findItemById, findColumnByItemId],
  );

  const onDragOver = useCallback((event: DragOverEvent) => {
    const overId = event.over?.id;
    if (overId) {
      setOverColumnId(String(overId));
    } else {
      setOverColumnId(null);
    }
  }, []);

  const onDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event;
      setActiveCard(null);
      setOverColumnId(null);
      setSourceColumnStatus(null);

      if (!over || !onStatusUpdate) return;

      const itemId = String(active.id);
      const targetColumnId = String(over.id);
      // Extract status name from column id (format: "column-StatusName")
      const targetStatus = targetColumnId.startsWith('column-')
        ? targetColumnId.slice('column-'.length)
        : targetColumnId;

      // No-op if dropping on same column
      if (sourceColumnStatus === targetStatus) return;

      try {
        await Promise.resolve(onStatusUpdate(itemId, targetStatus));
        toast.success('Issue moved');
      } catch {
        toast.error('Failed to move issue', { duration: Infinity });
      }
    },
    [onStatusUpdate, sourceColumnStatus],
  );

  const onDragCancel = useCallback(() => {
    setActiveCard(null);
    setOverColumnId(null);
    setSourceColumnStatus(null);
  }, []);

  return {
    activeCard,
    overColumnId,
    handlers: { onDragStart, onDragOver, onDragEnd, onDragCancel },
  };
}
