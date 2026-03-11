/**
 * BlockingIssuePill — Small card/pill showing the oldest active blocking issue.
 *
 * Displays the issue number with a link to the GitHub issue. Provides
 * "Skip" (advance to next in queue) and "Delete" (close on GitHub and skip)
 * actions with a confirmation dialog for the destructive delete operation.
 */

import { useState } from 'react';
import { ExternalLink, SkipForward, Trash2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { boardApi } from '@/services/api';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import type { BlockingQueueEntry } from '@/types';
import { cn } from '@/lib/utils';

interface BlockingIssuePillProps {
  entries: BlockingQueueEntry[];
  projectId: string;
}

/**
 * Find the oldest non-completed blocking issue from the queue entries.
 * Entries are already sorted by created_at ASC from the backend.
 */
function getOldestActiveBlocking(entries: BlockingQueueEntry[]): BlockingQueueEntry | null {
  return entries.find((e) => e.is_blocking && e.queue_status !== 'completed') ?? null;
}

function buildGitHubUrl(repoKey: string, issueNumber: number): string {
  return `https://github.com/${repoKey}/issues/${issueNumber}`;
}

export function BlockingIssuePill({ entries, projectId }: BlockingIssuePillProps) {
  const queryClient = useQueryClient();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const oldest = getOldestActiveBlocking(entries);

  const invalidateQueue = () => {
    void queryClient.invalidateQueries({ queryKey: ['blocking-queue', projectId] });
  };

  const skipMutation = useMutation({
    mutationFn: () => boardApi.skipBlockingIssue(projectId, oldest!.issue_number),
    onSuccess: invalidateQueue,
  });

  const deleteMutation = useMutation({
    mutationFn: () => boardApi.deleteBlockingIssue(projectId, oldest!.issue_number),
    onSuccess: () => {
      setShowDeleteConfirm(false);
      setDeleteError(null);
      invalidateQueue();
    },
    onError: (err: Error) => {
      setDeleteError(err.message || 'Failed to close issue on GitHub');
    },
  });

  if (!oldest) return null;

  const ghUrl = buildGitHubUrl(oldest.repo_key, oldest.issue_number);
  const statusLabel =
    oldest.queue_status === 'in_review'
      ? 'In Review'
      : oldest.queue_status === 'pending'
        ? 'Pending'
        : 'Active';
  const isBusy = skipMutation.isPending || deleteMutation.isPending;

  return (
    <>
      <div className="flex items-center gap-1.5 rounded-full border border-gold/40 bg-gold/8 px-3 py-1.5 text-xs font-medium shadow-sm">
        {/* Status dot */}
        <span
          className={cn(
            'h-2 w-2 shrink-0 rounded-full',
            oldest.queue_status === 'in_review'
              ? 'bg-status-active'
              : oldest.queue_status === 'pending'
                ? 'bg-status-warning'
                : 'bg-status-success'
          )}
          title={statusLabel}
        />

        {/* Issue link — clicking opens the GitHub issue */}
        <a
          href={ghUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors"
          title={`Open issue #${oldest.issue_number} on GitHub`}
        >
          <span className="font-semibold">#{oldest.issue_number}</span>
          <ExternalLink className="h-3 w-3" />
        </a>

        {/* Separator */}
        <span className="mx-0.5 h-3 w-px bg-border/60" />

        {/* Skip button */}
        <button
          type="button"
          onClick={() => skipMutation.mutate()}
          disabled={isBusy}
          className="flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-muted-foreground hover:bg-gold/15 hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Skip to next blocking issue"
        >
          <SkipForward className="h-3 w-3" />
          <span className="sr-only sm:not-sr-only text-[10px] uppercase tracking-wide">Skip</span>
        </button>

        {/* Delete button */}
        <button
          type="button"
          onClick={() => {
            setDeleteError(null);
            setShowDeleteConfirm(true);
          }}
          disabled={isBusy}
          className="flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-muted-foreground hover:bg-destructive/15 hover:text-destructive transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Close issue on GitHub and skip"
        >
          <Trash2 className="h-3 w-3" />
          <span className="sr-only sm:not-sr-only text-[10px] uppercase tracking-wide">
            Delete
          </span>
        </button>
      </div>

      {/* Delete confirmation dialog */}
      <ConfirmationDialog
        isOpen={showDeleteConfirm}
        title="Close Blocking Issue"
        description={`This will close issue #${oldest.issue_number} on GitHub (as "not planned") and advance the blocking queue to the next issue. This action cannot be undone.`}
        variant="danger"
        confirmLabel="Close & Skip"
        cancelLabel="Cancel"
        isLoading={deleteMutation.isPending}
        error={deleteError}
        onConfirm={() => deleteMutation.mutate()}
        onCancel={() => {
          setShowDeleteConfirm(false);
          setDeleteError(null);
        }}
      />
    </>
  );
}
