/**
 * ProjectBoard component - horizontal columns container for the Kanban board.
 */

import type { BoardDataResponse, BoardItem } from '@/types';
import { BoardColumn } from './BoardColumn';

interface ProjectBoardProps {
  boardData: BoardDataResponse;
  onCardClick: (item: BoardItem) => void;
}

export function ProjectBoard({ boardData, onCardClick }: ProjectBoardProps) {
  return (
    <div className="project-board">
      <div className="project-board-columns">
        {boardData.columns.map((column) => (
          <BoardColumn
            key={column.status.option_id}
            column={column}
            onCardClick={onCardClick}
          />
        ))}
      </div>
    </div>
  );
}
