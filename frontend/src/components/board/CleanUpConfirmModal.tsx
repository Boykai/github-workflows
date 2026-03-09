/**
 * CleanUpConfirmModal — displays categorized lists of branches/PRs
 * scheduled for deletion and preservation, with confirm/cancel actions.
 */

import { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { GitBranch, GitPullRequest, Shield, Trash2, X } from 'lucide-react';
import type { CleanupPreflightResponse } from '@/types';
import { useScrollLock } from '@/hooks/useScrollLock';

interface CleanUpConfirmModalProps {
  data: CleanupPreflightResponse;
  onConfirm: () => void;
  onCancel: () => void;
}

export function CleanUpConfirmModal({ data, onConfirm, onCancel }: CleanUpConfirmModalProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    },
    [onCancel]
  );

  useScrollLock(true);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onCancel();
  };

  const hasItemsToDelete = data.branches_to_delete.length > 0 || data.prs_to_close.length > 0 || (data.orphaned_issues ?? []).length > 0;

  return createPortal(
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-background/80 backdrop-blur-sm"
      role="none"
      onClick={handleBackdropClick}
    >
      <div
        className="celestial-fade-in celestial-panel relative m-4 w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-[1.4rem] border border-border p-6 text-card-foreground shadow-lg"
        role="dialog"
        aria-modal="true"
        aria-label="Confirm Repository Cleanup"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Confirm Repository Cleanup</h2>
          <button
            onClick={onCancel}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Review the Solune-generated items below before confirming. Assets created outside the app will be preserved. This operation cannot be undone.
        </p>

        {/* Items to delete */}
        {data.branches_to_delete.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              <span className="inline-flex items-center gap-2"><Trash2 className="h-4 w-4" />Branches to Delete ({data.branches_to_delete.length})</span>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.branches_to_delete.map((branch) => (
                <li key={branch.name} className="flex flex-col gap-0.5 px-2 py-1.5 rounded bg-destructive/10">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-3 w-3 shrink-0 text-muted-foreground" />
                    <span className="font-mono text-xs">{branch.name}</span>
                  </div>
                  {branch.deletion_reason && (
                    <span className="ml-5 text-[11px] text-muted-foreground">{branch.deletion_reason}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.prs_to_close.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              <span className="inline-flex items-center gap-2"><Trash2 className="h-4 w-4" />Pull Requests to Close ({data.prs_to_close.length})</span>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.prs_to_close.map((pr) => (
                <li key={pr.number} className="flex flex-col gap-0.5 px-2 py-1.5 rounded bg-destructive/10">
                  <div className="flex items-center gap-2">
                    <GitPullRequest className="h-3 w-3 shrink-0 text-muted-foreground" />
                    <span className="font-medium">#{pr.number}</span>
                    <span className="text-muted-foreground truncate">{pr.title}</span>
                  </div>
                  {pr.deletion_reason && (
                    <span className="ml-5 text-[11px] text-muted-foreground">{pr.deletion_reason}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {(data.orphaned_issues ?? []).length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              <span className="inline-flex items-center gap-2"><Trash2 className="h-4 w-4" />Orphaned Issues to Close ({data.orphaned_issues.length})</span>
            </h3>
            <p className="text-xs text-muted-foreground mb-2">
              App-created issues no longer attached to the project board.
            </p>
            <ul className="space-y-1 text-sm">
              {data.orphaned_issues.map((issue) => (
                <li key={issue.number} className="flex items-center gap-2 px-2 py-1 rounded bg-destructive/10">
                  <span className="font-medium">#{issue.number}</span>
                  <span className="text-muted-foreground truncate">{issue.title}</span>
                  {issue.labels.length > 0 && (
                    <span className="text-xs text-muted-foreground">
                      [{issue.labels.join(', ')}]
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Items to preserve */}
        {data.branches_to_preserve.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-green-800 dark:text-green-400 mb-2">
              <span className="inline-flex items-center gap-2"><Shield className="h-4 w-4" />Branches to Preserve ({data.branches_to_preserve.length})</span>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.branches_to_preserve.map((branch) => (
                <li key={branch.name} className="flex items-center gap-2 px-2 py-1 rounded bg-green-100/80 dark:bg-green-900/30">
                  <span className="font-mono text-xs">{branch.name}</span>
                  {branch.preservation_reason && (
                    <span className="text-xs text-muted-foreground">— {branch.preservation_reason}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.prs_to_preserve.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-green-800 dark:text-green-400 mb-2">
              <span className="inline-flex items-center gap-2"><Shield className="h-4 w-4" />Pull Requests to Preserve ({data.prs_to_preserve.length})</span>
            </h3>
            <ul className="space-y-1 text-sm">
              {data.prs_to_preserve.map((pr) => (
                <li key={pr.number} className="flex items-center gap-2 px-2 py-1 rounded bg-green-100/80 dark:bg-green-900/30">
                  <span className="font-medium">#{pr.number}</span>
                  <span className="text-muted-foreground truncate">{pr.title}</span>
                  {pr.preservation_reason && (
                    <span className="text-xs text-muted-foreground">— {pr.preservation_reason}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {!hasItemsToDelete && (
          <div className="mb-4 rounded-[1rem] border border-border bg-background/48 p-4 text-center text-sm text-muted-foreground">
            No stale Solune-generated branches, pull requests, or orphaned issues found. Nothing to clean up.
          </div>
        )}

        {/* Summary line */}
        <p className="text-xs text-muted-foreground mb-4">
          {data.open_issues_on_board} open issue{data.open_issues_on_board !== 1 ? 's' : ''} on the project board used for cross-referencing.
        </p>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="rounded-full border border-input bg-background/72 px-4 py-2 text-sm font-medium transition-colors hover:bg-primary/10"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={!hasItemsToDelete}
            className="px-4 py-2 text-sm font-medium rounded-md bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirm Cleanup
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
