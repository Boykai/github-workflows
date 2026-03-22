/**
 * CleanUpButton — triggers the cleanup workflow.
 *
 * Renders a button with a descriptive tooltip, orchestrates the full
 * cleanup flow: preflight → confirmation → execution → summary.
 * Also handles error display, permission errors, and audit history.
 */

import { useCleanup } from '@/hooks/useCleanup';
import { CleanUpConfirmModal } from './CleanUpConfirmModal';
import { CleanUpSummary } from './CleanUpSummary';
import { CleanUpAuditHistory } from './CleanUpAuditHistory';
import { Button } from '@/components/ui/button';
import { Tooltip } from '@/components/ui/tooltip';
import { Trash2, Loader2, Lock, TriangleAlert } from '@/lib/icons';
import type { CleanupConfirmPayload } from '@/types';

interface CleanUpButtonProps {
  owner?: string;
  repo?: string;
  projectId: string;
}

export function CleanUpButton({ owner, repo, projectId }: CleanUpButtonProps) {
  const {
    state,
    preflightData,
    executeResult,
    historyData,
    error,
    permissionError,
    startPreflight,
    confirmExecute,
    cancel,
    dismiss,
    loadHistory,
    showAuditHistory,
    closeAuditHistory,
  } = useCleanup();

  const handleClick = () => {
    if (!owner || !repo) return;
    startPreflight(owner, repo, projectId);
  };

  const handleConfirm = (payload: CleanupConfirmPayload) => {
    if (!owner || !repo) return;
    confirmExecute(owner, repo, projectId, payload);
  };

  const handleViewHistory = async () => {
    if (!owner || !repo) return;
    // Await the history fetch before transitioning to the audit
    // history view so users never see a misleading empty-state flash.
    await loadHistory(owner, repo);
    showAuditHistory();
  };

  return (
    <>
      {/* Clean Up Button */}
      <Tooltip contentKey="board.toolbar.cleanUpButton">
        <Button
          onClick={handleClick}
          disabled={!owner || !repo || state === 'loading' || state === 'executing'}
          variant="outline"
          size="lg"
          className="gap-2"
        >
          {state === 'loading' || state === 'executing' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
          {state === 'loading'
            ? 'Analyzing...'
            : state === 'executing'
              ? 'Cleaning up...'
              : 'Clean Up'}
        </Button>
      </Tooltip>

      {/* Permission error inline display */}
      {permissionError && (
        <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 text-destructive border border-destructive/20 text-sm">
          <Lock className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="flex-1">
            <p>{permissionError}</p>
            {owner && repo && (
              <button
                onClick={() => startPreflight(owner, repo, projectId)}
                className="text-xs underline mt-1"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      )}

      {/* Preflight error inline display */}
      {error && state === 'idle' && (
        <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 text-destructive border border-destructive/20 text-sm">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="flex-1">
            <p>{error}</p>
            {owner && repo && (
              <button
                onClick={() => startPreflight(owner, repo, projectId)}
                className="text-xs underline mt-1"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {state === 'confirming' && preflightData && owner && repo && (
        <CleanUpConfirmModal data={preflightData} owner={owner} repo={repo} onConfirm={handleConfirm} onCancel={cancel} />
      )}

      {/* Summary Modal */}
      {state === 'summary' && (
        <CleanUpSummary
          result={executeResult}
          error={error}
          onDismiss={dismiss}
          onViewHistory={handleViewHistory}
        />
      )}

      {/* Audit History Modal */}
      {state === 'auditHistory' && (
        <CleanUpAuditHistory data={historyData} onClose={closeAuditHistory} />
      )}
    </>
  );
}
