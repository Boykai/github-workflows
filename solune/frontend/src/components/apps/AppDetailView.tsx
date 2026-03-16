/**
 * AppDetailView — full-page detail view for a single application.
 * Shows app info, embedded preview iframe, and lifecycle controls.
 */

import { ArrowLeft, Play, Square, Trash2, RefreshCw } from 'lucide-react';
import { useApp, useStartApp, useStopApp, useDeleteApp } from '@/hooks/useApps';
import { AppPreview } from './AppPreview';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';

interface AppDetailViewProps {
  appName: string;
  onBack: () => void;
}

export function AppDetailView({ appName, onBack }: AppDetailViewProps) {
  const { data: app, isLoading, error, refetch } = useApp(appName);
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <CelestialLoader size="md" label="Loading app…" />
      </div>
    );
  }

  if (error || !app) {
    return (
      <div className="flex min-h-[30vh] flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-red-300 bg-red-50 p-6 dark:border-red-800 dark:bg-red-950/20">
        <p className="text-sm text-red-700 dark:text-red-300">
          {isRateLimitApiError(error)
            ? 'Rate limit reached. Please wait a moment before retrying.'
            : 'Could not load app details. Please try again.'}
        </p>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 rounded-lg border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900/30"
          onClick={() => void refetch()}
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Retry
        </button>
      </div>
    );
  }

  const handleStart = () => startMutation.mutate(appName);

  const handleStop = async () => {
    const confirmed = await confirm({
      title: 'Stop App',
      description: `Are you sure you want to stop "${app.display_name}"?`,
      confirmLabel: 'Stop',
      variant: 'warning',
    });
    if (confirmed) {
      stopMutation.mutate(appName);
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Are you sure you want to delete "${app.display_name}"? This action cannot be undone.`,
      confirmLabel: 'Delete',
      variant: 'danger',
    });
    if (confirmed) {
      deleteMutation.mutate(appName, { onSuccess: onBack });
    }
  };

  return (
    <div className="space-y-6">
      {/* Back button + Header */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to apps"
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-1 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back
        </button>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
            {app.display_name}
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{app.description}</p>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900 sm:grid-cols-4">
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Status</dt>
          <dd className="mt-1 text-sm font-semibold capitalize text-zinc-900 dark:text-zinc-100">
            {app.status}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Port</dt>
          <dd className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">
            {app.port ?? '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Repo Type</dt>
          <dd className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">{app.repo_type}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-zinc-500 dark:text-zinc-400">Created</dt>
          <dd className="mt-1 text-sm text-zinc-900 dark:text-zinc-100">
            {new Date(app.created_at).toLocaleDateString()}
          </dd>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        {app.status === 'stopped' && (
          <button
            type="button"
            aria-label={`Start ${app.display_name}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={handleStart}
            disabled={startMutation.isPending}
          >
            <Play className="h-4 w-4" aria-hidden="true" />
            {startMutation.isPending ? 'Starting…' : 'Start'}
          </button>
        )}
        {app.status === 'active' && (
          <button
            type="button"
            aria-label={`Stop ${app.display_name}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-600 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={() => void handleStop()}
            disabled={stopMutation.isPending}
          >
            <Square className="h-4 w-4" aria-hidden="true" />
            {stopMutation.isPending ? 'Stopping…' : 'Stop'}
          </button>
        )}
        {app.status !== 'active' && (
          <button
            type="button"
            aria-label={`Delete ${app.display_name}`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 disabled:opacity-50"
            onClick={() => void handleDelete()}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            {deleteMutation.isPending ? 'Deleting…' : 'Delete'}
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
        <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Live Preview
        </h3>
        <AppPreview port={app.port} appName={app.name} isActive={app.status === 'active'} />
      </div>
    </div>
  );
}
