/**
 * AppDetailView — full-page detail view for a single application.
 * Shows app info, embedded preview iframe, and lifecycle controls.
 */

import { ArrowLeft, Play, Square, Trash2 } from 'lucide-react';
import { useApp, useStartApp, useStopApp, useDeleteApp, friendlyErrorMessage } from '@/hooks/useApps';
import { useConfirmation } from '@/hooks/useConfirmation';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { Tooltip } from '@/components/ui/tooltip';
import { isRateLimitApiError } from '@/utils/rateLimit';
import { cn } from '@/lib/utils';
import { AppPreview } from './AppPreview';

interface AppDetailViewProps {
  appName: string;
  onBack: () => void;
}

/** Format a timestamp as relative ("2 hours ago") or absolute for older dates. */
function formatTimestamp(isoString: string): { label: string; iso: string } {
  const date = new Date(isoString);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  let label: string;
  if (diffMinutes < 1) {
    label = 'Just now';
  } else if (diffMinutes < 60) {
    label = `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  } else if (diffHours < 24) {
    label = `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  } else if (diffDays < 7) {
    label = `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  } else {
    label = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date);
  }

  return { label, iso: date.toISOString() };
}

export function AppDetailView({ appName, onBack }: AppDetailViewProps) {
  const { data: app, isLoading, error, refetch } = useApp(appName);
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center" aria-live="polite" aria-busy="true">
        <CelestialLoader size="md" label="Loading app details…" />
      </div>
    );
  }

  if (error || !app) {
    const isRateLimit = isRateLimitApiError(error);
    const message = isRateLimit
      ? 'Rate limit exceeded. Please wait a moment before retrying.'
      : 'Could not load app details. The app may not exist or there was a network error.';

    return (
      <div className="flex flex-col items-center gap-3 p-6 text-center" aria-live="polite">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{message}</p>
        <button
          type="button"
          className={cn(
            'rounded-lg px-4 py-2 text-sm font-medium text-white',
            'bg-emerald-600 hover:bg-emerald-700',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500'
          )}
          onClick={() => refetch()}
        >
          Retry
        </button>
      </div>
    );
  }

  const handleStart = () => startMutation.mutate(appName);

  const handleStop = async () => {
    const confirmed = await confirm({
      title: 'Stop App',
      description: `Stop app "${app.display_name}"? The app will no longer be accessible until restarted.`,
      variant: 'danger',
      confirmLabel: 'Stop',
    });
    if (confirmed) {
      stopMutation.mutate(appName);
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Delete app "${app.display_name}"? This action cannot be undone.`,
      variant: 'danger',
      confirmLabel: 'Delete',
    });
    if (confirmed) {
      deleteMutation.mutate(appName, { onSuccess: onBack });
    }
  };

  const created = formatTimestamp(app.created_at);

  return (
    <div className="space-y-6">
      {/* Back button + Header */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          aria-label="Back to apps list"
          onClick={onBack}
          className={cn(
            'inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50'
          )}
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back
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
            <time dateTime={created.iso}>{created.label}</time>
          </dd>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        {app.status === 'stopped' && (
          <button
            type="button"
            aria-label={`Start app ${app.display_name}`}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500'
            )}
            onClick={handleStart}
            disabled={startMutation.isPending}
          >
            <Play className="h-4 w-4" aria-hidden="true" />
            {startMutation.isPending ? 'Starting…' : 'Start App'}
          </button>
        )}
        {app.status === 'active' && (
          <button
            type="button"
            aria-label={`Stop app ${app.display_name}`}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-lg bg-zinc-600 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500'
            )}
            onClick={handleStop}
            disabled={stopMutation.isPending}
          >
            <Square className="h-4 w-4" aria-hidden="true" />
            {stopMutation.isPending ? 'Stopping…' : 'Stop App'}
          </button>
        )}
        {app.status !== 'active' && (
          <button
            type="button"
            aria-label={`Delete app ${app.display_name}`}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500'
            )}
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            {deleteMutation.isPending ? 'Deleting…' : 'Delete App'}
          </button>
        )}
      </div>

      {/* Mutation error feedback */}
      {(startMutation.error || stopMutation.error || deleteMutation.error) && (
        <div
          className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          role="alert"
        >
          {friendlyErrorMessage(
            startMutation.error ?? stopMutation.error ?? deleteMutation.error,
            'Could not complete the action. Please try again.'
          )}
        </div>
      )}

      {/* Error message from the app itself */}
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
