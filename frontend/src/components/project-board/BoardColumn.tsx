/**
 * Board column component displaying status header and issue cards.
 */

import type { BoardStatusColumn as BoardStatusColumnType, BoardIssueCard as BoardIssueCardType } from '@/types';
import { BoardIssueCard } from './BoardIssueCard';

interface BoardColumnProps {
  column: BoardStatusColumnType;
  onCardClick: (card: BoardIssueCardType) => void;
}

export function BoardColumn({ column, onCardClick }: BoardColumnProps) {
  return (
    <div className="board-column">
      <div className="board-column-header">
        <span className={`status-dot status-dot--${column.color}`} />
        <span className="board-column-name">{column.name}</span>
        <span className="board-column-count">{column.item_count}</span>
        {column.total_estimate !== null && column.total_estimate !== undefined && (
          <span className="board-column-estimate">{column.total_estimate}pt</span>
        )}
      </div>
      {column.description && (
        <div className="board-column-description">{column.description}</div>
      )}
      <div className="board-column-cards">
        {column.items.map((card) => (
          <BoardIssueCard
            key={card.item_id}
            card={card}
            onClick={() => onCardClick(card)}
          />
        ))}
      </div>
    </div>
  );
}
