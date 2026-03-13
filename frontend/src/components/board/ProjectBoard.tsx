/**
 * ProjectBoard component - horizontal columns container for the Kanban board.
 * Uses CSS grid matching AgentConfigRow for aligned columns.
 * Supports optional grouping within columns via getGroups callback.
 */

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

  return (
    <div className="celestial-fade-in w-full overflow-x-auto overflow-y-visible pb-6" role="region" aria-label="Project board">
      <div
        className="grid min-h-[56rem] min-w-full items-start gap-5 pb-2"
        style={{ gridTemplateColumns: `repeat(${columnCount}, minmax(min(16rem, 85vw), 1fr))` }}
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
