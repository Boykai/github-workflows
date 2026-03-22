/**
 * AppDetailView — full-page detail view for a single application.
 * Shows app info, embedded preview iframe, and lifecycle controls.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ExternalLink, Play, Square, Trash2, RefreshCw } from '@/lib/icons';
import { useApp, useStartApp, useStopApp, useUndoableDeleteApp, getErrorMessage } from '@/hooks/useApps';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';
import { Tooltip } from '@/components/ui/tooltip';
import { EntityHistoryPanel } from '@/components/activity/EntityHistoryPanel';
import { useAuth } from '@/hooks/useAuth';
import { AppPreview } from './AppPreview';

/** Format a date string as relative time ("2 hours ago") or absolute. */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin} minute${diffMin === 1 ? '' : 's'} ago`;
  if (diffHour < 24) return `${diffHour} hour${diffHour === 1 ? '' : 's'} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? '' : 's'} ago`;
  return date.toLocaleDateString();
}

interface AppDetailViewProps {
  appName: string;
  onBack: () => void;
}

export function AppDetailView({ appName, onBack }: AppDetailViewProps) {
  const { user } = useAuth();
  const { data: app, isLoading, error, refetch } = useApp(appName);
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const { deleteApp } = useUndoableDeleteApp();
  const { confirm } = useConfirmation();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    return () => {
      clearTimeout(successTimerRef.current);
      clearTimeout(errorTimerRef.current);
    };
  }, []);

  const showSuccess = useCallback((message: string) => {
    setSuccessMessage(message);
    clearTimeout(successTimerRef.current);
    successTimerRef.current = setTimeout(() => setSuccessMessage(null), 3000);
  }, []);

  const showError = useCallback((message: string) => {
    setActionError(message);
    clearTimeout(errorTimerRef.current);
    errorTimerRef.current = setTimeout(() => setActionError(null), 5000);
  }, []);

  if (isLoading) {
    return (
      <div
        className="flex min-h-[40vh] items-center justify-center"
        aria-busy="true"
        aria-live="polite"
      >
        <CelestialLoader size="md" label="Loading app details…" />
      </div>
    );
  }

  if (error || !app) {
    const isRateLimited = error ? isRateLimitApiError(error) : false;
    return (
      <div
        className="flex min-h-[40vh] flex-col items-center justify-center gap-3 p-6 text-center"
        aria-live="polite"
      >
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {isRateLimited
            ? 'Rate limit exceeded. Please wait a moment before trying again.'
            : 'Could not load app details. The app may not exist or an error occurred.'}
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
            onClick={() => refetch()}
          >
            <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" /> Retry
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
            onClick={onBack}
          >
            <ArrowLeft aria-hidden="true" className="h-3.5 w-3.5" /> Back to Apps
          </button>
        </div>
      </div>
    );
  }

  const handleStart = () => {
    startMutation.mutate(appName, {
      onSuccess: () => showSuccess(`App "${app.display_name}" started successfully.`),
      onError: (err) =>
        showError(getErrorMessage(err, `Could not start app "${app.display_name}".`)),
    });
  };

  const handleStop = async () => {
    const confirmed = await confirm({
      title: 'Stop App',
      description: `Stop app "${app.display_name}"? The app will no longer be accessible until restarted.`,
      variant: 'warning',
      confirmLabel: 'Stop App',
    });
    if (confirmed) {
      stopMutation.mutate(appName, {
        onSuccess: () => showSuccess(`App "${app.display_name}" stopped successfully.`),
        onError: (err) =>
          showError(getErrorMessage(err, `Could not stop app "${app.display_name}".`)),
      });
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Delete app "${app.display_name}"?`,
      variant: 'danger',
      confirmLabel: 'Delete App',
    });
    if (confirmed) {
      deleteApp(appName, app.display_name);
      onBack();
    }
  };

  return (
    <div className="space-y-6">
      {/* Success feedback */}
      {successMessage && (
        <div
          className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300"
          role="status"
        >
          {successMessage}
        </div>
      )}

      {/* Action error feedback */}
      {actionError && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
          role="alert"
        >
          {actionError}
        </div>
      )}

      {/* Back button + Header */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to apps list"
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" /> Back
        </button>
        <div className="min-w-0 flex-1">
          <Tooltip content={app.display_name}>
            <h2 className="truncate text-xl font-bold text-zinc-900 dark:text-zinc-100">
              {app.display_name}
            </h2>
          </Tooltip>
          {app.description && (
            <Tooltip content={app.description}>
              <p className="truncate text-sm text-zinc-500 dark:text-zinc-400">{app.description}</p>
            </Tooltip>
          )}
        </div>
      </div>

      {/* Info Grid */}
      <dl className="grid grid-cols-2 gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900 sm:grid-cols-4">
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Status</dt>
          <dd className="mt-1 text-sm font-semibold capitalize text-zinc-900 dark:text-zinc-100">
            {app.status}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Port</dt>
          <dd className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">{app.port ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Repo Type</dt>
          <dd className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">{app.repo_type}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Created</dt>
          <dd className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">
            <time dateTime={app.created_at}>{formatRelativeTime(app.created_at)}</time>
          </dd>
        </div>
      </dl>

      {/* GitHub Links */}
      {(app.github_repo_url || app.github_project_url || app.parent_issue_url) && (
        <div className="flex flex-wrap gap-3">
          {app.github_repo_url && (
            <a
              href={app.github_repo_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              <ExternalLink aria-hidden="true" className="h-3.5 w-3.5" /> GitHub Repository
            </a>
          )}
          {app.github_project_url && (
            <a
              href={app.github_project_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              <ExternalLink aria-hidden="true" className="h-3.5 w-3.5" /> GitHub Project
            </a>
          )}
          {app.parent_issue_url && (
            <a
              href={app.parent_issue_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
            >
              <ExternalLink aria-hidden="true" className="h-3.5 w-3.5" /> Parent Issue
            </a>
          )}
        </div>
      )}

      {/* Pipeline Info */}
      {app.associated_pipeline_id && (
        <div className="text-sm text-zinc-500 dark:text-zinc-400">
          Pipeline:{' '}
          <span className="font-medium text-zinc-700 dark:text-zinc-300">
            {app.associated_pipeline_id}
          </span>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        {app.status === 'stopped' && (
          <button
            type="button"
            aria-label={`Start app ${app.display_name}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={handleStart}
            disabled={startMutation.isPending}
          >
            <Play aria-hidden="true" className="h-4 w-4" />
            {startMutation.isPending ? 'Starting…' : 'Start App'}
          </button>
        )}
        {app.status === 'active' && (
          <button
            type="button"
            aria-label={`Stop app ${app.display_name}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-600 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={handleStop}
            disabled={stopMutation.isPending}
          >
            <Square aria-hidden="true" className="h-4 w-4" />
            {stopMutation.isPending ? 'Stopping…' : 'Stop App'}
          </button>
        )}
        {app.status !== 'active' && (
          <button
            type="button"
            aria-label={`Delete app ${app.display_name}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={handleDelete}
          >
            <Trash2 aria-hidden="true" className="h-4 w-4" />
            Delete App
          </button>
        )}
      </div>

      {/* Error message */}
      {app.error_message && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300">
          {app.error_message}
        </div>
      )}

      {/* Live Preview */}
      <div>
        <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">Live Preview</h3>
        <AppPreview port={app.port} appName={app.name} isActive={app.status === 'active'} />
      </div>

      <EntityHistoryPanel
        projectId={user?.selected_project_id ?? ''}
        entityType="app"
        entityId={app.name}
      />
    </div>
  );
}
