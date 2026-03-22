/**
 * BoardColumn component - displays a status column with header and scrollable card list.
 * Supports optional grouping of items within the column.
 * Phase 8: Supports board projection with scroll sentinel for lazy loading.
 */

import { memo, useMemo } from 'react';
import { useDroppable } from '@dnd-kit/core';
import type { BoardColumn as BoardColumnType, BoardItem, AvailableAgent } from '@/types';
import type { BoardGroup } from '@/hooks/useBoardControls';
import { cn } from '@/lib/utils';
import { statusColorToCSS } from './colorUtils';
import { IssueCard } from './IssueCard';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';

interface BoardColumnProps {
  column: BoardColumnType;
  onCardClick: (item: BoardItem) => void;
  availableAgents?: AvailableAgent[];
  getGroups?: (items: BoardItem[]) => BoardGroup[] | null;
  hasNextPage?: boolean;
  isFetchingNextPage?: boolean;
  fetchNextPage?: () => void;
  /** Whether more items are available beyond the rendered range (projection). */
  hasMore?: boolean;
  /** Ref callback from useBoardProjection for the scroll sentinel. */
  scrollSentinelRef?: (node: HTMLElement | null) => void;
}

export const BoardColumn = memo(function BoardColumn({
  column,
  onCardClick,
  availableAgents,
  getGroups,
  hasNextPage = false,
  isFetchingNextPage = false,
  fetchNextPage,
  hasMore = false,
  scrollSentinelRef,
}: BoardColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${column.status.name}`,
    data: { status: column.status.name },
  });
  const dotColor = statusColorToCSS(column.status.color);
  const groups = useMemo(() => getGroups?.(column.items), [getGroups, column.items]);

  return (
    <div ref={setNodeRef} className={cn(
      "project-board-column pipeline-column-surface flex h-[72rem] max-h-[72rem] min-h-[44rem] min-w-0 shrink-0 flex-col overflow-x-hidden rounded-[1.4rem] border border-border/70 shadow-sm xl:h-[95rem] xl:max-h-[95rem]",
      isOver && 'ring-2 ring-primary/50 bg-primary/5'
    )}>
      {/* Column Header */}
      <div className="project-board-column-header flex items-center justify-between border-b border-border/70 p-4 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: dotColor }} />
          <span className="font-semibold text-sm">{column.status.name}</span>
          <span className="flex items-center justify-center rounded-full border border-border/70 bg-background/78 px-2.5 py-0.5 text-xs font-medium text-muted-foreground shadow-sm">
            {column.item_count}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {column.estimate_total > 0 && (
            <span
              className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground"
              title="Total estimate points"
            >
              {column.estimate_total}pt
            </span>
          )}
          <button
            className="rounded-full p-1.5 text-muted-foreground/60 transition-colors hover:bg-primary/10 hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
            title="Coming soon"
            disabled
            aria-disabled="true"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M8 3v10M3 8h10" />
            </svg>
          </button>
        </div>
      </div>

      {/* Column description */}
      {column.status.description && (
        <div className="border-b border-border/70 bg-background/24 px-4 py-2 text-xs leading-5 text-muted-foreground">
          {column.status.description}
        </div>
      )}

      {/* Card list */}
      <div className="project-board-column-list constellation-grid flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-3 pb-4">
        {column.items.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 rounded-[1.1rem] border border-dashed border-border/70 bg-background/34 p-6 text-center">
            <svg className="h-10 w-10 text-muted-foreground/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
              <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 16.8l-6.2 4.5 2.4-7.4L2 9.4h7.6z" />
            </svg>
            <p className="text-sm text-muted-foreground">No items yet</p>
            <p className="text-xs text-muted-foreground/70">Create your first issue to get started</p>
          </div>
        ) : groups ? (
          groups.map((group, idx) => (
            <div key={group.name} className={idx > 0 ? 'mt-3' : ''}>
              <div className="text-xs font-semibold uppercase text-muted-foreground tracking-wide border-b border-border/50 pb-1 mb-2">
                {group.name}
              </div>
              <div className="flex flex-col gap-3">
                {group.items.map((item) => (
                  <IssueCard
                    key={item.item_id}
                    item={item}
                    onClick={onCardClick}
                    availableAgents={availableAgents}
                  />
                ))}
              </div>
            </div>
          ))
        ) : (
          /* Flat rendering */
          column.items.map((item) => (
            <IssueCard
              key={item.item_id}
              item={item}
              onClick={onCardClick}
              availableAgents={availableAgents}
            />
          ))
        )}
        {/* Per-column infinite scroll sentinel */}
        {(hasNextPage || isFetchingNextPage) && fetchNextPage && (
          <InfiniteScrollContainer
            hasNextPage={hasNextPage}
            isFetchingNextPage={isFetchingNextPage}
            fetchNextPage={fetchNextPage}
          >
            <span />
          </InfiniteScrollContainer>
        )}
        {/* Board projection scroll sentinel — triggers lazy loading of additional items */}
        {hasMore && scrollSentinelRef && (
          <div
            ref={scrollSentinelRef}
            className="flex items-center justify-center py-2 text-xs text-muted-foreground/60"
            aria-hidden="true"
          >
            Loading more items…
          </div>
        )}
      </div>
    </div>
  );
});
