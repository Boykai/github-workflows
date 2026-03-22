/**
 * ActivityPage — unified activity timeline with filter chips and infinite scroll.
 */

import { useState, useMemo, useCallback } from 'react';
import {
  GitBranch,
  ListChecks,
  Bot,
  Boxes,
  Wrench,
  Webhook,
  Trash2,
  ArrowRightLeft,
  Clock,
  ChevronDown,
  ChevronRight,
  Activity,
} from '@/lib/icons';
import { useActivityFeed } from '@/hooks/useActivityFeed';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

// ── Event type → category mapping ──

const EVENT_CATEGORIES = [
  { label: 'Pipeline', types: ['pipeline_run', 'pipeline_stage'], icon: GitBranch },
  { label: 'Chore', types: ['chore_trigger', 'chore_crud'], icon: ListChecks },
  { label: 'Agent', types: ['agent_crud', 'agent_execution'], icon: Bot },
  { label: 'App', types: ['app_crud'], icon: Boxes },
  { label: 'Tool', types: ['tool_crud'], icon: Wrench },
  { label: 'Webhook', types: ['webhook'], icon: Webhook },
  { label: 'Cleanup', types: ['cleanup'], icon: Trash2 },
  { label: 'Status', types: ['status_change'], icon: ArrowRightLeft },
] as const;

const EVENT_TYPE_ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  pipeline_run: GitBranch,
  pipeline_stage: GitBranch,
  chore_trigger: ListChecks,
  chore_crud: ListChecks,
  agent_crud: Bot,
  agent_execution: Bot,
  cleanup: Trash2,
  app_crud: Boxes,
  tool_crud: Wrench,
  status_change: ArrowRightLeft,
  webhook: Webhook,
};

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

function DetailView({ detail }: { detail: Record<string, unknown> }) {
  return (
    <div className="mt-2 rounded-lg bg-muted/40 px-3 py-2 text-xs">
      {Object.entries(detail).map(([key, value]) => (
        <div key={key} className="flex gap-2 py-0.5">
          <span className="font-medium text-muted-foreground">{key}:</span>
          <span className="text-foreground">
            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function ActivityPage() {
  const { user } = useAuth();
  const projectId = user?.selected_project_id ?? '';

  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const eventTypes = useMemo(() => {
    if (selectedCategories.length === 0) return undefined;
    return EVENT_CATEGORIES.filter((c) => selectedCategories.includes(c.label)).flatMap(
      (c) => c.types,
    );
  }, [selectedCategories]);

  const {
    allItems: events,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    isLoading,
    isError,
  } = useActivityFeed(projectId, eventTypes);

  const toggleCategory = useCallback((label: string) => {
    setSelectedCategories((prev) =>
      prev.includes(label) ? prev.filter((c) => c !== label) : [...prev, label],
    );
  }, []);

  const clearFilters = useCallback(() => setSelectedCategories([]), []);

  const toggleExpanded = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <Activity className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-display font-semibold tracking-tight">Activity</h1>
      </div>

      {/* Filter chips */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {EVENT_CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const active = selectedCategories.includes(cat.label);
          return (
            <button
              key={cat.label}
              type="button"
              onClick={() => toggleCategory(cat.label)}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                active
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border bg-background text-muted-foreground hover:border-primary/50 hover:text-foreground',
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {cat.label}
            </button>
          );
        })}
        {selectedCategories.length > 0 && (
          <button
            type="button"
            onClick={clearFilters}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
          <span className="ml-3 text-sm text-muted-foreground">Loading activity…</span>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && events.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border/60 py-20">
          <Clock className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-sm font-medium text-muted-foreground">
            {selectedCategories.length > 0
              ? `No ${selectedCategories.join(', ').toLowerCase()} events found`
              : 'No activity recorded yet'}
          </p>
          <p className="mt-1 text-xs text-muted-foreground/70">
            Events will appear here as you use the system.
          </p>
        </div>
      )}

      {/* Event timeline */}
      {!isLoading && events.length > 0 && (
        <InfiniteScrollContainer
          hasNextPage={hasNextPage}
          isFetchingNextPage={isFetchingNextPage}
          fetchNextPage={fetchNextPage}
          isError={isError}
        >
          <div className="space-y-1">
            {events.map((event) => {
              const Icon = EVENT_TYPE_ICON_MAP[event.event_type] ?? Clock;
              const expanded = expandedIds.has(event.id);
              const hasDetail = event.detail && Object.keys(event.detail).length > 0;

              return (
                <div key={event.id} className="group">
                  <button
                    type="button"
                    onClick={() => hasDetail && toggleExpanded(event.id)}
                    className={cn(
                      'flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors',
                      hasDetail
                        ? 'hover:bg-muted/50 cursor-pointer'
                        : 'cursor-default',
                    )}
                  >
                    <Icon className="mt-0.5 h-4 w-4 shrink-0 text-primary/70" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-foreground">{event.summary}</p>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{formatRelativeTime(event.created_at)}</span>
                        <span>·</span>
                        <span>{event.actor}</span>
                      </div>
                    </div>
                    {hasDetail && (
                      expanded ? (
                        <ChevronDown className="mt-1 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="mt-1 h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                      )
                    )}
                  </button>
                  {expanded && event.detail && <DetailView detail={event.detail} />}
                </div>
              );
            })}
          </div>

          {/* End of activity indicator */}
          {!hasNextPage && events.length > 0 && (
            <div className="flex items-center justify-center gap-2 py-6 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-border/50" />
              <span>End of activity log</span>
              <div className="h-px flex-1 bg-border/50" />
            </div>
          )}
        </InfiniteScrollContainer>
      )}
    </div>
  );
}
