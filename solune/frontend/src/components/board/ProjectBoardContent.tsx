/**
 * ProjectBoardContent — The main board area including empty state handling.
 * Extracted from ProjectsPage to keep the page file ≤250 lines.
 * Phase 8: Wrapped with UndoRedoProvider for session-scoped undo/redo.
 */

import { Inbox, Search } from '@/lib/icons';
import { ProjectBoard } from '@/components/board/ProjectBoard';
import { Button } from '@/components/ui/button';
import type { BoardDataResponse, BoardItem, AvailableAgent } from '@/types';
import type { BoardGroup } from '@/hooks/useBoardControls';
import { UndoRedoProvider } from '@/context/UndoRedoContext';
import { useUndoRedo } from '@/hooks/useUndoRedo';

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

/** Inner content that consumes the UndoRedoContext. */
function ProjectBoardContentInner({
  boardData,
  boardControls,
  onCardClick,
  availableAgents,
  onStatusUpdate,
}: ProjectBoardContentProps) {
  const { nextUndoDescription, canUndo, undo } = useUndoRedo();
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
      {/* Undo toast banner — visible when an undoable action is available */}
      {canUndo && nextUndoDescription && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 flex items-center gap-3 rounded-full border border-border bg-card px-4 py-2 shadow-lg animate-in fade-in slide-in-from-bottom-4">
          <span className="text-sm text-muted-foreground">{nextUndoDescription}</span>
          <button
            type="button"
            onClick={() => undo()}
            className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
          >
            Undo
          </button>
        </div>
      )}
    </div>
  );
}

export function ProjectBoardContent(props: ProjectBoardContentProps) {
  return (
    <UndoRedoProvider>
      <ProjectBoardContentInner {...props} />
    </UndoRedoProvider>
  );
}
