/**
 * CleanUpSummary — post-operation summary displaying results of the cleanup.
 *
 * Shows counts of deleted/closed/preserved/failed items,
 * per-item results with error details, and a dismiss button.
 */

import { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import type { CleanupExecuteResponse } from '@/types';

interface CleanUpSummaryProps {
  result: CleanupExecuteResponse | null;
  error: string | null;
  onDismiss: () => void;
  onViewHistory?: () => void;
}

export function CleanUpSummary({ result, error, onDismiss, onViewHistory }: CleanUpSummaryProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onDismiss();
    },
    [onDismiss]
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
    if (e.target === e.currentTarget) onDismiss();
  };

  // If there was a fatal error with no result
  if (!result && error) {
    return createPortal(
      <div
        className="fixed inset-0 z-[2000] flex items-center justify-center bg-background/80 backdrop-blur-sm"
        role="none"
        onClick={handleBackdropClick}
      >
        <div
          className="relative w-full max-w-md bg-card text-card-foreground rounded-lg border border-border shadow-lg p-6 m-4"
          role="dialog"
          aria-modal="true"
          aria-label="Cleanup Error"
        >
          <h2 className="text-lg font-semibold text-destructive mb-2">Cleanup Failed</h2>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <div className="flex justify-end">
            <button
              onClick={onDismiss}
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      </div>,
      document.body
    );
  }

  if (!result) return null;

  const successfulBranches = result.results.filter(r => r.item_type === 'branch' && r.action === 'deleted');
  const successfulPRs = result.results.filter(r => r.item_type === 'pr' && r.action === 'closed');
  const successfulIssues = result.results.filter(r => r.item_type === 'issue' && r.action === 'closed');
  const failedItems = result.results.filter(r => r.action === 'failed');

  return createPortal(
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-background/80 backdrop-blur-sm"
      role="none"
      onClick={handleBackdropClick}
    >
      <div
        className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto bg-card text-card-foreground rounded-lg border border-border shadow-lg p-6 m-4"
        role="dialog"
        aria-modal="true"
        aria-label="Cleanup Summary"
      >
        <h2 className="text-lg font-semibold mb-4">
          {failedItems.length > 0 ? '⚠️ Cleanup Completed with Errors' : '✅ Cleanup Complete'}
        </h2>

        {/* Summary counts */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="p-3 rounded bg-green-100/80 dark:bg-green-900/30 text-center">
            <div className="text-2xl font-bold text-green-800 dark:text-green-400">{result.branches_deleted}</div>
            <div className="text-xs text-muted-foreground">Branches Deleted</div>
          </div>
          <div className="p-3 rounded bg-green-100/80 dark:bg-green-900/30 text-center">
            <div className="text-2xl font-bold text-green-800 dark:text-green-400">{result.prs_closed}</div>
            <div className="text-xs text-muted-foreground">PRs Closed</div>
          </div>
          <div className="p-3 rounded bg-green-100/80 dark:bg-green-900/30 text-center">
            <div className="text-2xl font-bold text-green-800 dark:text-green-400">{result.issues_closed ?? 0}</div>
            <div className="text-xs text-muted-foreground">Issues Closed</div>
          </div>
        </div>

        {/* Successful deletions */}
        {successfulBranches.length > 0 && (
          <div className="mb-3">
            <h3 className="text-sm font-medium mb-1">Deleted Branches</h3>
            <ul className="space-y-1 text-sm">
              {successfulBranches.map((item) => (
                <li key={item.identifier} className="flex items-center gap-2 px-2 py-1 rounded bg-green-100/80 dark:bg-green-900/30">
                  <span className="text-green-800 dark:text-green-400">✓</span>
                  <span className="font-mono text-xs">{item.identifier}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {successfulPRs.length > 0 && (
          <div className="mb-3">
            <h3 className="text-sm font-medium mb-1">Closed Pull Requests</h3>
            <ul className="space-y-1 text-sm">
              {successfulPRs.map((item) => (
                <li key={item.identifier} className="flex items-center gap-2 px-2 py-1 rounded bg-green-100/80 dark:bg-green-900/30">
                  <span className="text-green-800 dark:text-green-400">✓</span>
                  <span>#{item.identifier}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {successfulIssues.length > 0 && (
          <div className="mb-3">
            <h3 className="text-sm font-medium mb-1">Closed Orphaned Issues</h3>
            <ul className="space-y-1 text-sm">
              {successfulIssues.map((item) => (
                <li key={item.identifier} className="flex items-center gap-2 px-2 py-1 rounded bg-green-100/80 dark:bg-green-900/30">
                  <span className="text-green-800 dark:text-green-400">✓</span>
                  <span>#{item.identifier}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Failed items */}
        {failedItems.length > 0 && (
          <div className="mb-3">
            <h3 className="text-sm font-medium text-destructive mb-1">Failed Operations ({failedItems.length})</h3>
            <ul className="space-y-1 text-sm">
              {failedItems.map((item) => (
                <li key={`${item.item_type}-${item.identifier}`} className="px-2 py-1 rounded bg-destructive/10">
                  <div className="flex items-center gap-2">
                    <span className="text-destructive">✗</span>
                    <span className="font-mono text-xs">
                      {item.item_type === 'pr' ? `#${item.identifier}` : item.identifier}
                    </span>
                  </div>
                  {item.error && (
                    <p className="text-xs text-muted-foreground ml-5 mt-0.5">{item.error}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center mt-4">
          <div>
            {onViewHistory && (
              <button
                onClick={onViewHistory}
                className="text-sm text-primary hover:underline"
              >
                View Audit History
              </button>
            )}
          </div>
          <button
            onClick={onDismiss}
            className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
