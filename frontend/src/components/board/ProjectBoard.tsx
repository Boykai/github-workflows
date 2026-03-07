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
      <div className="flex h-full min-w-max gap-6">
        {boardData.columns.map((column) => (
          <BoardColumn
            key={column.status.option_id}
            column={column}
            onCardClick={onCardClick}
          />
        ))}
        <button
          className="celestial-panel flex h-12 w-[320px] shrink-0 items-center justify-center gap-2 rounded-[1.25rem] border border-dashed border-border/80 text-sm font-medium text-muted-foreground/70 transition-colors hover:border-primary/35 hover:text-foreground"
          title="Coming soon"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 3v10M3 8h10" /></svg>
          Add column
        </button>
      </div>
    </div>
  );
}
