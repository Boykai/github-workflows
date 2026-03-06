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
    <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
      <div className="flex h-full gap-6 min-w-max">
        {boardData.columns.map((column) => (
          <BoardColumn
            key={column.status.option_id}
            column={column}
            onCardClick={onCardClick}
          />
        ))}
        <button
          className="flex items-center justify-center gap-2 w-[320px] shrink-0 h-12 rounded-lg border-2 border-dashed border-border text-muted-foreground/60 hover:border-primary/40 hover:text-muted-foreground transition-colors text-sm font-medium"
          title="Coming soon"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 3v10M3 8h10" /></svg>
          Add column
        </button>
      </div>
    </div>
  );
}
