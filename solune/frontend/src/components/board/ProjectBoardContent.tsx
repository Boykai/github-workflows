/**
 * ProjectBoardContent — The main board area including empty state handling.
 * Extracted from ProjectsPage to keep the page file ≤250 lines.
 */

import { Inbox, Search } from '@/lib/icons';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { Button } from '@/components/ui/button';
import type { BoardDataResponse, BoardItem, AvailableAgent } from '@/types';
import type { BoardGroup } from '@/hooks/useBoardControls';

interface BoardControls {
  hasActiveControls: boolean;
  clearAll: () => void;
  getGroups: (items: BoardItem[]) => BoardGroup[] | null;
}

interface ProjectBoardContentProps {
  boardData: BoardDataResponse;
  boardControls: BoardControls;
  onCardClick: (item: BoardItem) => void;
  availableAgents: AvailableAgent[];
  onStatusUpdate?: (itemId: string, newStatus: string) => void | Promise<void>;
}

export function ProjectBoardContent({
  boardData,
  boardControls,
  onCardClick,
  availableAgents,
  onStatusUpdate,
}: ProjectBoardContentProps) {
  const allEmpty = boardData.columns.every((col) => col.items.length === 0);

  if (allEmpty) {
    return (
      <div id="board" className="flex flex-1 gap-6 scroll-mt-24">
        <div className="celestial-panel flex min-h-[32rem] flex-1 flex-col items-center justify-center gap-4 rounded-[1.4rem] border border-dashed border-border/80 p-8 text-center sm:min-h-[40rem]">
          {boardControls.hasActiveControls ? (
            <>
              <Search className="mb-2 h-10 w-10 text-primary/80" />
              <h3 className="text-xl font-semibold">No issues match the current view</h3>
              <p className="text-muted-foreground">
                Try adjusting your filter, sort, or group settings.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={boardControls.clearAll}
                className="mt-2"
                type="button"
              >
                Clear all filters
              </Button>
            </>
          ) : (
            <>
              <Inbox className="mb-2 h-10 w-10 text-primary/70" />
              <h3 className="text-xl font-semibold">No items yet</h3>
              <p className="text-muted-foreground">
                This project has no items. Add items in GitHub to see them here.
              </p>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div id="board" className="flex flex-1 gap-6 scroll-mt-24">
      <ProjectBoard
        boardData={boardData}
        onCardClick={onCardClick}
        availableAgents={availableAgents}
        getGroups={boardControls.getGroups}
        onStatusUpdate={onStatusUpdate}
      />
    </div>
  );
}
