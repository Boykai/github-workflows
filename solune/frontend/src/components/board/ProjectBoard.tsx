/**
 * ProjectBoard component - horizontal columns container for the Kanban board.
 * Uses CSS grid matching AgentConfigRow for aligned columns.
 * Supports optional grouping within columns via getGroups callback.
 * Wraps columns with DndContext + DragOverlay for card drag-and-drop.
 */

import { useMemo } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import type { BoardDataResponse, BoardItem, AvailableAgent } from '@/types';
import type { BoardGroup } from '@/hooks/useBoardControls';
import { useBoardDragDrop } from '@/hooks/useBoardDragDrop';
import { BoardColumn } from './BoardColumn';
import { BoardDragOverlay } from './BoardDragOverlay';

interface ProjectBoardProps {
  boardData: BoardDataResponse;
  onCardClick: (item: BoardItem) => void;
  availableAgents?: AvailableAgent[];
  getGroups?: (items: BoardItem[]) => BoardGroup[] | null;
  onStatusUpdate?: (itemId: string, newStatus: string) => void | Promise<void>;
}

export function ProjectBoard({
  boardData,
  onCardClick,
  availableAgents,
  getGroups,
  onStatusUpdate,
}: ProjectBoardProps) {
  const columnCount = Math.max(boardData.columns.length, 1);
  const gridStyle = useMemo(
    () => ({ gridTemplateColumns: `repeat(${columnCount}, minmax(min(16rem, 85vw), 1fr))` }),
    [columnCount]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  const { activeCard, handlers } = useBoardDragDrop(boardData, onStatusUpdate);

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handlers.onDragStart}
      onDragOver={handlers.onDragOver}
      onDragEnd={handlers.onDragEnd}
      onDragCancel={handlers.onDragCancel}
    >
      <div className="celestial-fade-in flex h-full w-full flex-1 overflow-x-auto overflow-y-visible pb-6" role="region" aria-label="Project board">
        <div
          className="grid min-h-full min-w-full items-stretch gap-5 pb-2"
          style={gridStyle}
        >
          {boardData.columns.map((column) => (
            <BoardColumn
              key={column.status.option_id}
              column={column}
              onCardClick={onCardClick}
              availableAgents={availableAgents}
              getGroups={getGroups}
            />
          ))}
        </div>
      </div>
      <DragOverlay>
        {activeCard ? <BoardDragOverlay item={activeCard} /> : null}
      </DragOverlay>
    </DndContext>
  );
}
