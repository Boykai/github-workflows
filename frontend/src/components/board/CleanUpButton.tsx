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

interface CleanUpButtonProps {
  owner: string;
  repo: string;
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
    startPreflight(owner, repo, projectId);
  };

  const handleConfirm = () => {
    confirmExecute(owner, repo, projectId);
  };

  const handleViewHistory = async () => {
    // Await the history fetch before transitioning to the audit
    // history view so users never see a misleading empty-state flash.
    await loadHistory(owner, repo);
    showAuditHistory();
  };

  return (
    <>
      {/* Clean Up Button with tooltip */}
      <div className="relative group">
        <button
          onClick={handleClick}
          disabled={state === 'loading' || state === 'executing'}
          className="inline-flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Remove stale branches and pull requests while preserving 'main' and items linked to open issues on the project board"
        >
          {state === 'loading' && (
            <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
          )}
          {state === 'executing' && (
            <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
          )}
          {state !== 'loading' && state !== 'executing' && (
            <span>🧹</span>
          )}
          {state === 'loading' ? 'Analyzing...' : state === 'executing' ? 'Cleaning up...' : 'Clean Up'}
        </button>
      </div>

      {/* Permission error inline display */}
      {permissionError && (
        <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 text-destructive border border-destructive/20 text-sm">
          <span>🔒</span>
          <div className="flex-1">
            <p>{permissionError}</p>
            <button
              onClick={() => startPreflight(owner, repo, projectId)}
              className="text-xs underline mt-1"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Preflight error inline display */}
      {error && state === 'idle' && (
        <div className="flex items-start gap-2 p-3 rounded-md bg-destructive/10 text-destructive border border-destructive/20 text-sm">
          <span>⚠️</span>
          <div className="flex-1">
            <p>{error}</p>
            <button
              onClick={() => startPreflight(owner, repo, projectId)}
              className="text-xs underline mt-1"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {state === 'confirming' && preflightData && (
        <CleanUpConfirmModal
          data={preflightData}
          onConfirm={handleConfirm}
          onCancel={cancel}
        />
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
        <CleanUpAuditHistory
          data={historyData}
          onClose={closeAuditHistory}
        />
      )}
    </>
  );
}
