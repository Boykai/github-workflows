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
    <div className="board-column">
      {/* Column Header */}
      <div className="board-column-header">
        <div className="board-column-header-left">
          <span
            className="board-column-dot"
            style={{ backgroundColor: dotColor }}
          />
          <span className="board-column-name">{column.status.name}</span>
          <span className="board-column-count">{column.item_count}</span>
        </div>
        {column.estimate_total > 0 && (
          <span className="board-column-estimate" title="Total estimate points">
            {column.estimate_total}pt
          </span>
        )}
      </div>

      {/* Column description */}
      {column.status.description && (
        <div className="board-column-description">{column.status.description}</div>
      )}

      {/* Card list */}
      <div className="board-column-cards">
        {column.items.length === 0 ? (
          <div className="board-column-empty">No items</div>
        ) : (
          column.items.map((item) => (
            <IssueCard key={item.item_id} item={item} onClick={onCardClick} />
          ))
        )}
      </div>
    </div>
  );
}
