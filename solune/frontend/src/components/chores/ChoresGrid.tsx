/**
 * ChoresGrid — renders the filterable grid of ChoreCards.
 *
 * Extracted from ChoresPanel for single-responsibility.
 */

import { ChoreCard } from './ChoreCard';
import { Button } from '@/components/ui/button';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';
import type { Chore, ChoreEditState, ChoreInlineUpdate } from '@/types';

interface ChoresGridProps {
  chores: Chore[];
  projectId: string;
  parentIssueCount: number;
  editState: Record<string, ChoreEditState>;
  onEditStart: (chore: Chore) => void;
  onEditChange: (choreId: string, updates: Partial<ChoreInlineUpdate>) => void;
  onEditSave: (choreId: string) => void;
  onEditDiscard: (choreId: string) => void;
  isSaving: boolean;
  onResetFilters: () => void;
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
  fetchNextPage?: () => void;
}

export function ChoresGrid({
  chores,
  projectId,
  parentIssueCount,
  editState,
  onEditStart,
  onEditChange,
  onEditSave,
  onEditDiscard,
  isSaving,
  onResetFilters,
  hasNextPage = false,
  isFetchingNextPage = false,
  fetchNextPage,
}: ChoresGridProps) {
  if (chores.length === 0) {
    return (
      <div className="mt-6 rounded-[1.35rem] border border-dashed border-border/80 bg-background/42 p-8 text-center">
        <p className="text-sm text-muted-foreground">
          No chores match the current filters.
        </p>
        <Button variant="ghost" className="mt-3" onClick={onResetFilters}>
          Reset filters
        </Button>
      </div>
    );
  }

  const gridContent = (
    <div className="constellation-grid mt-6 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
      {chores.map((chore) => (
        <ChoreCard
          key={chore.id}
          chore={chore}
          projectId={projectId}
          parentIssueCount={parentIssueCount}
          editState={editState[chore.id]}
          onEditStart={() => onEditStart(chore)}
          onEditChange={(updates) => onEditChange(chore.id, updates)}
          onEditSave={() => onEditSave(chore.id)}
          onEditDiscard={() => onEditDiscard(chore.id)}
          isSaving={isSaving}
        />
      ))}
    </div>
  );

  if (!fetchNextPage) {
    return gridContent;
  }

  return (
    <InfiniteScrollContainer
      hasNextPage={hasNextPage}
      isFetchingNextPage={isFetchingNextPage}
      fetchNextPage={fetchNextPage}
    >
      {gridContent}
    </InfiniteScrollContainer>
  );
}
