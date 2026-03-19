/**
 * BoardDragOverlay — ghost card overlay that follows cursor during drag.
 * Follows the AgentDragOverlay pattern.
 */

import type { BoardItem } from '@/types';
import { PRIORITY_COLORS } from '@/constants';
import { cn } from '@/lib/utils';

interface BoardDragOverlayProps {
  item: BoardItem;
}

export function BoardDragOverlay({ item }: BoardDragOverlayProps) {
  const labels = item.labels ?? [];
  const priorityName = item.priority?.name ?? '';
  const priorityConfig = PRIORITY_COLORS[priorityName] ?? PRIORITY_COLORS.P2;

  return (
    <div
      role="status"
      aria-label={`Dragging card: ${item.title}`}
      className="flex min-w-[240px] max-w-[320px] flex-col gap-1.5 rounded-xl border border-primary/50 bg-card p-3 shadow-lg opacity-80 cursor-grabbing"
    >
      {/* Drag handle (decorative) */}
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground/50" aria-hidden="true">⠿</span>
        <span className="text-sm font-semibold truncate flex-1">{item.title}</span>
      </div>

      {/* Labels (max 3) */}
      {labels.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {labels.slice(0, 3).map((label) => (
            <span
              key={label.id}
              className="rounded-full px-1.5 py-0.5 text-[10px] font-semibold truncate max-w-[100px]"
              style={{
                backgroundColor: `#${label.color || 'd1d5db'}18`,
                color: `#${label.color || 'd1d5db'}`,
              }}
            >
              {label.name}
            </span>
          ))}
          {labels.length > 3 && (
            <span className="text-[10px] text-muted-foreground">+{labels.length - 3}</span>
          )}
        </div>
      )}

      {/* Priority + Assignees */}
      <div className="flex items-center gap-2">
        {item.priority && (
          <span
            className={cn(
              'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase',
              priorityConfig.bg,
              priorityConfig.text
            )}
          >
            {item.priority.name}
          </span>
        )}
        {item.assignees.length > 0 && (
          <span className="text-[10px] text-muted-foreground truncate">
            {item.assignees.map((a) => a.login).join(', ')}
          </span>
        )}
      </div>
    </div>
  );
}
