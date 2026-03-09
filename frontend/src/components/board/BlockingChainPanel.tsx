/**
 * BlockingChainPanel — Collapsible panel showing the blocking queue state for a project.
 *
 * Displays ordered queue entries with status indicators, current base branch,
 * and next-in-line issue. Collapses by default and expands on click.
 */

import { useState } from 'react';
import { GitBranch, Lock, X } from 'lucide-react';
import type { BlockingQueueEntry } from '@/types';

interface BlockingChainPanelProps {
  entries: BlockingQueueEntry[];
}

const STATUS_LABELS: Record<string, { label: string; dot: string }> = {
  active: { label: 'Active', dot: 'bg-green-500' },
  in_review: { label: 'In Review', dot: 'bg-blue-500' },
  pending: { label: 'Pending', dot: 'bg-gray-400' },
  completed: { label: 'Completed', dot: 'bg-purple-500' },
};

function getBaseBranch(entries: BlockingQueueEntry[]): string {
  const openBlocking = entries.filter(
    (e) => e.is_blocking && (e.queue_status === 'active' || e.queue_status === 'in_review')
  );
  for (const entry of openBlocking) {
    if (entry.parent_branch) return entry.parent_branch;
  }
  return 'main';
}

function getNextInLine(entries: BlockingQueueEntry[]): BlockingQueueEntry | null {
  return entries.find((e) => e.queue_status === 'pending') ?? null;
}

export function BlockingChainPanel({ entries }: BlockingChainPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (entries.length === 0) return null;

  const baseBranch = getBaseBranch(entries);
  const nextInLine = getNextInLine(entries);
  const activeCount = entries.filter((e) => e.queue_status === 'active').length;
  const pendingCount = entries.filter((e) => e.queue_status === 'pending').length;

  return (
    <div className="relative">
      {/* Toggle button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-medium uppercase tracking-[0.16em] transition-colors ${
          isExpanded
            ? 'border-amber-500/50 bg-amber-500/10 text-amber-600 dark:text-amber-400'
            : 'border-border/70 bg-background/50 hover:bg-accent/45'
        }`}
        type="button"
        title="View blocking queue status"
      >
        <Lock className="h-3.5 w-3.5" />
        Queue
        <span className="flex items-center justify-center rounded-full border border-border/70 bg-background/78 px-1.5 py-0 text-[10px] font-medium text-muted-foreground">
          {entries.length}
        </span>
      </button>

      {/* Expanded panel */}
      {isExpanded && (
        <div className="celestial-fade-in absolute right-0 top-full mt-2 z-50 w-80 rounded-lg border border-border bg-card shadow-lg p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Blocking Queue</span>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              type="button"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Summary */}
          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              {activeCount} active
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-400" />
              {pendingCount} pending
            </span>
            <span className="inline-flex items-center gap-1" title="Current base branch for new issues">
              <GitBranch className="h-3.5 w-3.5" /> {baseBranch}
            </span>
          </div>

          {/* Queue entries */}
          <div className="flex flex-col gap-1.5 max-h-60 overflow-y-auto">
            {entries.map((entry, idx) => {
              const statusInfo = STATUS_LABELS[entry.queue_status] ?? STATUS_LABELS.pending;
              const isNext = nextInLine?.issue_number === entry.issue_number;

              return (
                <div
                  key={entry.id}
                  className={`flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs ${
                    isNext
                      ? 'border-amber-500/30 bg-amber-500/5'
                      : 'border-border/50 bg-background/30'
                  }`}
                >
                  <span className="text-muted-foreground w-4 text-center text-[10px]">{idx + 1}</span>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${statusInfo.dot}`} title={statusInfo.label} />
                  <span className="font-medium">#{entry.issue_number}</span>
                  {entry.is_blocking && (
                    <Lock className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                  )}
                  <span className="text-muted-foreground ml-auto text-[10px]">
                    {statusInfo.label}
                  </span>
                  {isNext && (
                    <span className="text-amber-600 dark:text-amber-400 text-[10px] font-medium">
                      Next
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Next in line */}
          {nextInLine && (
            <div className="border-t border-border/50 pt-2 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Next up:</span> Issue #{nextInLine.issue_number}
              {nextInLine.is_blocking ? ' (blocking)' : ' (non-blocking)'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
