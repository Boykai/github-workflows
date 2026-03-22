/**
 * CleanUpAuditHistory — displays past cleanup operations with details.
 */

import { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X } from '@/lib/icons';
import type { CleanupHistoryResponse } from '@/types';
import { useScrollLock } from '@/hooks/useScrollLock';
import { cn } from '@/lib/utils';

interface CleanUpAuditHistoryProps {
  data: CleanupHistoryResponse | null;
  onClose: () => void;
}

export function CleanUpAuditHistory({ data, onClose }: CleanUpAuditHistoryProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useScrollLock(true);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-background/80 backdrop-blur-sm"
      role="none"
      onClick={handleBackdropClick}
    >
      <div
        className="celestial-fade-in relative w-full max-w-lg max-h-[85vh] overflow-y-auto bg-card text-card-foreground rounded-lg border border-border shadow-lg p-6 m-4"
        role="dialog"
        aria-modal="true"
        aria-label="Cleanup Audit History"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Cleanup Audit History</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {!data || data.operations.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No cleanup operations found for this repository.
          </p>
        ) : (
          <div className="space-y-3">
            {data.operations.map((op) => (
              <div key={op.id} className="p-3 rounded border border-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{formatDate(op.started_at)}</span>
                  <span
                    className={cn('text-xs px-2 py-0.5 rounded-full', op.status === 'completed'
                        ? 'bg-green-100/80 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        : op.status === 'failed'
                          ? 'bg-destructive/20 text-destructive'
                          : 'bg-accent/10 text-accent-foreground dark:bg-accent/20 dark:text-accent-foreground')}
                  >
                    {op.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                  <span>Branches deleted: {op.branches_deleted}</span>
                  <span>PRs closed: {op.prs_closed}</span>
                  <span>Branches preserved: {op.branches_preserved}</span>
                  <span>PRs preserved: {op.prs_preserved}</span>
                  {op.errors_count > 0 && (
                    <span className="text-destructive col-span-2">Errors: {op.errors_count}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end mt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
