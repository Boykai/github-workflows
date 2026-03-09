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
  blockingIssueNumbers?: Set<number>;
}

export function ProjectBoard({
  boardData,
  onCardClick,
  availableAgents,
  getGroups,
  blockingIssueNumbers,
}: ProjectBoardProps) {
  const columnCount = Math.max(boardData.columns.length, 1);

  return (
    <div className="celestial-fade-in flex-1 overflow-x-auto overflow-y-hidden pb-4">
      <div
        className="grid h-full min-w-full items-stretch gap-4"
        style={{ gridTemplateColumns: `repeat(${columnCount}, minmax(14rem, 1fr))` }}
      >
        {boardData.columns.map((column) => (
          <BoardColumn
            key={column.status.option_id}
            column={column}
            onCardClick={onCardClick}
            availableAgents={availableAgents}
            getGroups={getGroups}
            blockingIssueNumbers={blockingIssueNumbers}
          />
        ))}
      </div>
    </div>
  );
}
