/**
 * PipelineRunHistory — collapsible panel showing past pipeline runs
 * with status badges, durations, and timestamps.
 */

import { useState } from 'react';
import { ChevronDown, ChevronRight, Clock, CheckCircle2, XCircle, Ban } from '@/lib/icons';
import { useQuery } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { cn } from '@/lib/utils';

interface PipelineRunHistoryProps {
  pipelineId: string;
  className?: string;
}

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle2; color: string; label: string }> = {
  completed: { icon: CheckCircle2, color: 'text-green-500', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-500', label: 'Failed' },
  cancelled: { icon: Ban, color: 'text-yellow-500', label: 'Cancelled' },
  running: { icon: Clock, color: 'text-blue-500', label: 'Running' },
  pending: { icon: Clock, color: 'text-muted-foreground', label: 'Pending' },
};

function formatDuration(ms: number | undefined | null): string {
  if (!ms) return '—';
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSec = seconds % 60;
  return `${minutes}m ${remainingSec}s`;
}

function getRunDurationMs(run: Record<string, unknown>): number | null {
  const startedAt = typeof run.started_at === 'string' ? run.started_at : null;
  if (!startedAt) return null;

  const startedMs = new Date(startedAt).getTime();
  if (Number.isNaN(startedMs)) return null;

  const completedAt = typeof run.completed_at === 'string' ? run.completed_at : null;
  const completedMs = completedAt ? new Date(completedAt).getTime() : Date.now();
  if (Number.isNaN(completedMs)) return null;

  return Math.max(0, completedMs - startedMs);
}

function formatRelativeTime(isoDate: string): string {
  const now = Date.now();
  const then = new Date(isoDate + (isoDate.endsWith('Z') ? '' : 'Z')).getTime();
  const diff = now - then;

  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  const days = Math.floor(diff / 86_400_000);
  if (days < 30) return `${days}d ago`;
  return new Date(then).toLocaleDateString();
}

export function PipelineRunHistory({ pipelineId, className }: PipelineRunHistoryProps) {
  const [isOpen, setIsOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['pipeline-runs', pipelineId],
    queryFn: () => pipelinesApi.listRuns(pipelineId, { limit: 20 }),
    enabled: !!pipelineId && isOpen,
    staleTime: 30_000,
  });

  const runs = data?.runs ?? [];

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
        Run History
      </button>

      {isOpen && (
        <div className="px-3 pb-3">
          {isLoading && (
            <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
              <div className="h-3 w-3 animate-spin rounded-full border border-primary/30 border-t-primary" />
              Loading…
            </div>
          )}

          {!isLoading && runs.length === 0 && (
            <p className="py-2 text-xs text-muted-foreground/70">No runs recorded yet</p>
          )}

          {!isLoading && runs.length > 0 && (
            <div className="space-y-1.5">
              {runs.map((run) => {
                const status = String(run.status ?? 'pending');
                const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
                const StatusIcon = config.icon;

                return (
                  <div
                    key={String(run.id)}
                    className="flex items-center gap-2 rounded-md border border-border/40 px-2.5 py-1.5 text-xs"
                  >
                    <StatusIcon className={cn('h-3.5 w-3.5 shrink-0', config.color)} />
                    <span className="font-medium text-foreground/80">{config.label}</span>
                    <span className="text-muted-foreground/60">
                      {formatDuration(getRunDurationMs(run))}
                    </span>
                    <span className="ml-auto text-muted-foreground/50">
                      {typeof run.started_at === 'string' ? formatRelativeTime(run.started_at) : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
