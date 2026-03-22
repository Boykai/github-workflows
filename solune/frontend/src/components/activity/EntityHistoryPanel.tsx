/**
 * EntityHistoryPanel — collapsible "History" section for entity detail views.
 * Shows a mini-timeline of activity events for a specific entity.
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, Clock } from '@/lib/icons';
import { useEntityHistory } from '@/hooks/useEntityHistory';
import { cn } from '@/lib/utils';

interface EntityHistoryPanelProps {
  projectId: string;
  entityType: string;
  entityId: string;
  className?: string;
}

function formatRelativeTime(isoDate: string): string {
  const now = Date.now();
  const then = new Date(isoDate + (isoDate.endsWith('Z') ? '' : 'Z')).getTime();
  const diff = now - then;

  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) {
    const mins = Math.floor(diff / 60_000);
    return `${mins}m ago`;
  }
  if (diff < 86_400_000) {
    const hrs = Math.floor(diff / 3_600_000);
    return `${hrs}h ago`;
  }
  const days = Math.floor(diff / 86_400_000);
  if (days < 30) return `${days}d ago`;
  return new Date(then).toLocaleDateString();
}

export function EntityHistoryPanel({
  projectId,
  entityType,
  entityId,
  className,
}: EntityHistoryPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { allItems: events, isLoading } = useEntityHistory(projectId, entityType, entityId);

  return (
    <div className={cn('border-t border-border/50', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
      >
        {isOpen ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        <Clock className="h-3.5 w-3.5" />
        History
        {events.length > 0 && (
          <span className="ml-auto text-[10px] text-muted-foreground/70">{events.length}</span>
        )}
      </button>

      {isOpen && (
        <div className="px-3 pb-2">
          {isLoading && (
            <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
              <div className="h-3 w-3 animate-spin rounded-full border border-primary/30 border-t-primary" />
              Loading…
            </div>
          )}

          {!isLoading && events.length === 0 && (
            <p className="py-2 text-xs text-muted-foreground/70">No activity recorded</p>
          )}

          {!isLoading && events.length > 0 && (
            <div className="space-y-1">
              {events.slice(0, 10).map((event) => (
                <div key={event.id} className="flex items-start gap-2 py-0.5 text-xs">
                  <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                  <div className="min-w-0 flex-1">
                    <p className="text-foreground/80 truncate">{event.summary}</p>
                    <span className="text-muted-foreground/60">
                      {formatRelativeTime(event.created_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
