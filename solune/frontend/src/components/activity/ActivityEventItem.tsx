/**
 * ActivityEventItem — Single event row in the activity timeline.
 * Renders the event icon, summary, timestamp, actor, expand/collapse
 * chevron, and optional detail view.
 */

import { ChevronDown, ChevronRight, Clock } from '@/lib/icons';
import { cn } from '@/lib/utils';
import { formatRelativeTime } from '@/utils/formatTime';

// ── Detail view for expanded events ──

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

// ── Event type → icon mapping ──

import {
  GitBranch,
  ListChecks,
  Bot,
  Boxes,
  Wrench,
  Webhook,
  Trash2,
  ArrowRightLeft,
} from '@/lib/icons';

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

// ── Types ──

interface ActivityEvent {
  id: string;
  event_type: string;
  summary: string;
  created_at: string;
  actor: string;
  detail?: Record<string, unknown> | null;
}

interface ActivityEventItemProps {
  event: ActivityEvent;
  expanded: boolean;
  onToggleExpand: (id: string) => void;
}

// ── Component ──

export function ActivityEventItem({ event, expanded, onToggleExpand }: ActivityEventItemProps) {
  const Icon = EVENT_TYPE_ICON_MAP[event.event_type] ?? Clock;
  const hasDetail = event.detail != null && Object.keys(event.detail).length > 0;

  return (
    <div className="group">
      <button
        type="button"
        onClick={() => hasDetail && onToggleExpand(event.id)}
        aria-expanded={hasDetail ? expanded : undefined}
        className={cn(
          'flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors',
          hasDetail ? 'hover:bg-muted/50 cursor-pointer' : 'cursor-default',
        )}
      >
        <Icon aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-primary/70" />
        <div className="min-w-0 flex-1">
          <p className="text-sm text-foreground">{event.summary}</p>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatRelativeTime(event.created_at)}</span>
            <span>·</span>
            <span>{event.actor}</span>
          </div>
        </div>
        {hasDetail &&
          (expanded ? (
            <ChevronDown aria-hidden="true" className="mt-1 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight
              aria-hidden="true"
              className="mt-1 h-3.5 w-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
            />
          ))}
      </button>
      {expanded && event.detail && <DetailView detail={event.detail} />}
    </div>
  );
}
