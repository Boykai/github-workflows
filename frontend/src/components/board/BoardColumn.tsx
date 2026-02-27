/**
 * BoardColumn component - displays a status column with header and scrollable card list.
 */

import type { BoardColumn as BoardColumnType, BoardItem } from '@/types';
import { statusColorToCSS } from './colorUtils';
import { IssueCard } from './IssueCard';

interface BoardColumnProps {
  column: BoardColumnType;
  onCardClick: (item: BoardItem) => void;
}

export function BoardColumn({ column, onCardClick }: BoardColumnProps) {
  const dotColor = statusColorToCSS(column.status.color);

  return (
    <div className="flex flex-col w-[320px] shrink-0 bg-muted/30 rounded-lg border border-border overflow-hidden">
      {/* Column Header */}
      <div className="flex items-center justify-between p-3 border-b border-border bg-muted/50">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: dotColor }}
          />
          <span className="font-semibold text-sm">{column.status.name}</span>
          <span className="flex items-center justify-center px-2 py-0.5 text-xs font-medium bg-background rounded-full text-muted-foreground border border-border">{column.item_count}</span>
        </div>
        {column.estimate_total > 0 && (
          <span className="text-xs font-medium text-muted-foreground" title="Total estimate points">
            {column.estimate_total}pt
          </span>
        )}
      </div>

      {/* Column description */}
      {column.status.description && (
        <div className="px-3 py-2 text-xs text-muted-foreground border-b border-border bg-background/50">{column.status.description}</div>
      )}

      {/* Card list */}
      <div className="flex flex-col gap-3 p-3 overflow-y-auto flex-1">
        {column.items.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-8 italic">No items</div>
        ) : (
          column.items.map((item) => (
            <IssueCard key={item.item_id} item={item} onClick={onCardClick} />
          ))
        )}
      </div>
    </div>
  );
}
