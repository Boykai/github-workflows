/**
 * BoardColumn component - displays a status column with header and scrollable card list.
 * Supports optional grouping of items within the column.
 */

import { memo } from 'react';
import type { BoardColumn as BoardColumnType, BoardItem, AvailableAgent } from '@/types';
import type { BoardGroup } from '@/hooks/useBoardControls';
import { statusColorToCSS } from './colorUtils';
import { IssueCard } from './IssueCard';

interface BoardColumnProps {
  column: BoardColumnType;
  onCardClick: (item: BoardItem) => void;
  availableAgents?: AvailableAgent[];
  getGroups?: (items: BoardItem[]) => BoardGroup[] | null;
}

export const BoardColumn = memo(function BoardColumn({ column, onCardClick, availableAgents, getGroups }: BoardColumnProps) {
  const dotColor = statusColorToCSS(column.status.color);
  const groups = getGroups?.(column.items);

  return (
    <div className="celestial-panel flex min-w-0 shrink-0 flex-col h-full overflow-hidden rounded-[1.4rem] border border-border/70 shadow-sm">
      {/* Column Header */}
      <div className="flex items-center justify-between border-b border-border/70 bg-background/58 p-4 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: dotColor }}
          />
          <span className="font-semibold text-sm">{column.status.name}</span>
          <span className="flex items-center justify-center rounded-full border border-border/70 bg-background/78 px-2.5 py-0.5 text-xs font-medium text-muted-foreground shadow-sm">{column.item_count}</span>
        </div>
        <div className="flex items-center gap-1">
          {column.estimate_total > 0 && (
            <span className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground" title="Total estimate points">
              {column.estimate_total}pt
            </span>
          )}
          <button
            className="rounded-full p-1.5 text-muted-foreground/60 transition-colors hover:bg-primary/10 hover:text-foreground"
            title="Coming soon"
          >
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2"><path d="M8 3v10M3 8h10" /></svg>
          </button>
        </div>
      </div>

      {/* Column description */}
      {column.status.description && (
        <div className="border-b border-border/70 bg-background/42 px-4 py-2 text-xs leading-5 text-muted-foreground">{column.status.description}</div>
      )}

      {/* Card list */}
      <div className="flex flex-1 flex-col gap-3 overflow-y-auto bg-background/10 p-3">
        {column.items.length === 0 ? (
          <div className="rounded-[1.1rem] border border-dashed border-border/70 bg-background/38 py-8 text-center text-sm italic text-muted-foreground">No items</div>
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
            <IssueCard key={item.item_id} item={item} onClick={onCardClick} availableAgents={availableAgents} />
          ))
        )}
      </div>
    </div>
  );
});
