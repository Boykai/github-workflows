/**
 * CleanUpConfirmModal — displays categorized lists of branches/PRs
 * scheduled for deletion and preservation, with confirm/cancel actions.
 */

import { useEffect, useCallback } from 'react';
import type { CleanupPreflightResponse } from '@/types';

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

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onCancel();
  };

  const hasItemsToDelete = data.branches_to_delete.length > 0 || data.prs_to_close.length > 0 || (data.orphaned_issues ?? []).length > 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
      role="none"
      onClick={handleBackdropClick}
    >
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-card text-card-foreground rounded-lg border border-border shadow-lg p-6 m-4"
        role="dialog"
        aria-modal="true"
        aria-label="Confirm Repository Cleanup"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Confirm Repository Cleanup</h2>
          <button
            onClick={onCancel}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Review the items below before confirming. This operation cannot be undone.
        </p>

        {/* Items to delete */}
        {data.branches_to_delete.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              🗑️ Branches to Delete ({data.branches_to_delete.length})
            </h3>
            <ul className="space-y-1 text-sm">
              {data.branches_to_delete.map((branch) => (
                <li key={branch.name} className="flex items-center gap-2 px-2 py-1 rounded bg-destructive/10">
                  <span className="font-mono text-xs">{branch.name}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.prs_to_close.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              🗑️ Pull Requests to Close ({data.prs_to_close.length})
            </h3>
            <ul className="space-y-1 text-sm">
              {data.prs_to_close.map((pr) => (
                <li key={pr.number} className="flex items-center gap-2 px-2 py-1 rounded bg-destructive/10">
                  <span className="font-medium">#{pr.number}</span>
                  <span className="text-muted-foreground truncate">{pr.title}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {(data.orphaned_issues ?? []).length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-destructive mb-2">
              🗑️ Orphaned Issues to Close ({data.orphaned_issues.length})
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
              🛡️ Branches to Preserve ({data.branches_to_preserve.length})
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
              🛡️ Pull Requests to Preserve ({data.prs_to_preserve.length})
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
          <div className="p-4 rounded bg-muted/50 text-center text-sm text-muted-foreground mb-4">
            No stale branches or pull requests found. Nothing to clean up.
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
            className="px-4 py-2 text-sm font-medium rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
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
    </div>
  );
}
