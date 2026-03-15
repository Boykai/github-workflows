/**
 * useCleanup hook — manages the full cleanup workflow state machine.
 *
 * States: idle → loading → confirming → executing → summary → idle
 * Also handles: error, permissionError, and auditHistory states.
 */

import { useState, useCallback } from 'react';
import { cleanupApi } from '@/services/api';
import type {
  CleanupPreflightResponse,
  CleanupExecuteResponse,
  CleanupHistoryResponse,
  CleanupConfirmPayload,
} from '@/types';

export type CleanupState =
  | 'idle'
  | 'loading'
  | 'confirming'
  | 'executing'
  | 'summary'
  | 'auditHistory';

interface UseCleanupReturn {
  /** Current workflow state */
  state: CleanupState;
  /** Preflight response data (available in confirming/executing/summary states) */
  preflightData: CleanupPreflightResponse | null;
  /** Execute response data (available in summary state) */
  executeResult: CleanupExecuteResponse | null;
  /** Audit history data */
  historyData: CleanupHistoryResponse | null;
  /** Error message for preflight/execute failures */
  error: string | null;
  /** Permission error message */
  permissionError: string | null;
  /** Start the preflight check */
  startPreflight: (owner: string, repo: string, projectId: string) => Promise<void>;
  /** Confirm and execute the cleanup with the user's final selections */
  confirmExecute: (owner: string, repo: string, projectId: string, payload: CleanupConfirmPayload) => Promise<void>;
  /** Cancel and return to idle */
  cancel: () => void;
  /** Dismiss summary and return to idle */
  dismiss: () => void;
  /** Load audit history */
  loadHistory: (owner: string, repo: string) => Promise<void>;
  /** Show audit history view */
  showAuditHistory: () => void;
  /** Return from audit history to idle */
  closeAuditHistory: () => void;
}

export function useCleanup(): UseCleanupReturn {
  const [state, setState] = useState<CleanupState>('idle');
  const [preflightData, setPreflightData] = useState<CleanupPreflightResponse | null>(null);
  const [executeResult, setExecuteResult] = useState<CleanupExecuteResponse | null>(null);
  const [historyData, setHistoryData] = useState<CleanupHistoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const startPreflight = useCallback(async (owner: string, repo: string, projectId: string) => {
    setState('loading');
    setError(null);
    setPermissionError(null);

    try {
      const data = await cleanupApi.preflight(owner, repo, projectId);

      if (!data.has_permission) {
        setPermissionError(
          data.permission_error ||
            'You need at least push access to this repository to delete branches and close pull requests.'
        );
        setState('idle');
        return;
      }

      setPreflightData(data);
      setState('confirming');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to perform preflight check';
      setError(message);
      setState('idle');
    }
  }, []);

  const confirmExecute = useCallback(
    async (owner: string, repo: string, projectId: string, payload: CleanupConfirmPayload) => {
      setState('executing');
      setError(null);
      setExecuteResult(null);

      try {
        const result = await cleanupApi.execute({
          owner,
          repo,
          project_id: projectId,
          branches_to_delete: payload.branches_to_delete,
          prs_to_close: payload.prs_to_close,
          issues_to_delete: payload.issues_to_delete,
        });

        setExecuteResult(result);
        setState('summary');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Cleanup operation failed';
        setError(message);
        setState('summary');
      }
    },
    []
  );

  const cancel = useCallback(() => {
    setState('idle');
    setPreflightData(null);
    setError(null);
    setPermissionError(null);
  }, []);

  const dismiss = useCallback(() => {
    setState('idle');
    setPreflightData(null);
    setExecuteResult(null);
    setError(null);
  }, []);

  const loadHistory = useCallback(async (owner: string, repo: string) => {
    try {
      const data = await cleanupApi.history(owner, repo);
      setHistoryData(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load history';
      setError(message);
    }
  }, []);

  const showAuditHistory = useCallback(() => {
    setState('auditHistory');
  }, []);

  const closeAuditHistory = useCallback(() => {
    setState('idle');
    setHistoryData(null);
  }, []);

  return {
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
  };
}
