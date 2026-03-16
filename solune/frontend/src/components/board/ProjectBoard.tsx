/**
 * ProjectBoard component - horizontal columns container for the Kanban board.
 * Uses CSS grid matching AgentConfigRow for aligned columns.
 * Supports optional grouping within columns via getGroups callback.
 */

import { useMemo } from 'react';
import type { BoardDataResponse, BoardItem, AvailableAgent } from '@/types';
import type { BoardGroup } from '@/hooks/useBoardControls';
import { BoardColumn } from './BoardColumn';

interface ProjectBoardProps {
  boardData: BoardDataResponse;
  onCardClick: (item: BoardItem) => void;
  availableAgents?: AvailableAgent[];
  getGroups?: (items: BoardItem[]) => BoardGroup[] | null;
}

export function ProjectBoard({
  boardData,
  onCardClick,
  availableAgents,
  getGroups,
}: ProjectBoardProps) {
  const columnCount = Math.max(boardData.columns.length, 1);
  const gridStyle = useMemo(
    () => ({ gridTemplateColumns: `repeat(${columnCount}, minmax(min(16rem, 85vw), 1fr))` }),
    [columnCount]
  );

  return (
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
  );
}
