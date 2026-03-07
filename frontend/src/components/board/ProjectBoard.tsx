/**
 * ProjectBoard component - horizontal columns container for the Kanban board.
 * Uses CSS grid matching AgentConfigRow for aligned columns.
 */

import type { BoardDataResponse, BoardItem } from '@/types';
import { BoardColumn } from './BoardColumn';

interface ProjectBoardProps {
  boardData: BoardDataResponse;
  onCardClick: (item: BoardItem) => void;
}

export function ProjectBoard({ boardData, onCardClick }: ProjectBoardProps) {
  const columnCount = Math.max(boardData.columns.length, 1);

  return (
    <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
      <div
        className="grid h-full min-w-full items-start gap-4"
        style={{ gridTemplateColumns: `repeat(${columnCount}, minmax(14rem, 1fr))` }}
      >
        {boardData.columns.map((column) => (
          <BoardColumn key={column.status.option_id} column={column} onCardClick={onCardClick} />
        ))}
      </div>
    </div>
  );
}
