/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useApps, useStartApp, useStopApp, useDeleteApp, friendlyErrorMessage } from '@/hooks/useApps';
import { useConfirmation } from '@/hooks/useConfirmation';
import { AppCard } from '@/components/apps/AppCard';
import { AppDetailView } from '@/components/apps/AppDetailView';
import { CreateAppDialog } from '@/components/apps/CreateAppDialog';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { isRateLimitApiError } from '@/utils/rateLimit';
import { cn } from '@/lib/utils';

function AppsPageContent() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading, error, refetch } = useApps();
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const createButtonRef = useRef<HTMLButtonElement>(null);

  const openCreateDialog = () => setShowCreateDialog(true);
  const closeCreateDialog = () => {
    setShowCreateDialog(false);
    requestAnimationFrame(() => createButtonRef.current?.focus());
  };

  // Detail view for a specific app
  if (appName) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-8">
        <AppDetailView appName={appName} onBack={() => navigate('/apps')} />
      </div>
    );
  }

  const handleStop = async (name: string) => {
    const app = apps?.find((a) => a.name === name);
    const confirmed = await confirm({
      title: 'Stop App',
      description: `Stop app "${app?.display_name ?? name}"? The app will no longer be accessible until restarted.`,
      variant: 'danger',
      confirmLabel: 'Stop',
    });
    if (confirmed) {
      stopMutation.mutate(name);
    }
  };

  const handleDelete = async (name: string) => {
    const app = apps?.find((a) => a.name === name);
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Delete app "${app?.display_name ?? name}"? This action cannot be undone.`,
      variant: 'danger',
      confirmLabel: 'Delete',
    });
    if (confirmed) {
      deleteMutation.mutate(name);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Apps</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Create, manage, and preview your applications.
          </p>
        </div>
        <button
          ref={createButtonRef}
          type="button"
          className={cn(
            'inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500'
          )}
          onClick={openCreateDialog}
        >
          <Plus className="h-4 w-4" aria-hidden="true" /> Create App
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex min-h-[30vh] items-center justify-center" aria-live="polite" aria-busy="true">
          <CelestialLoader size="md" label="Loading apps…" />
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="flex min-h-[30vh] flex-col items-center justify-center gap-3" aria-live="polite">
          <p className="text-sm text-destructive">
            {isRateLimitApiError(error)
              ? 'Rate limit exceeded. Please wait a moment before retrying.'
              : 'Could not load apps. Please check your connection and try again.'}
          </p>
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
      )}

      {/* Empty state */}
      {!isLoading && !error && (!apps || apps.length === 0) && (
        <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900/50">
          <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">No applications yet.</p>
          <button
            type="button"
            className="text-sm font-medium text-emerald-600 hover:underline dark:text-emerald-400"
            onClick={openCreateDialog}
          >
            Create your first app →
          </button>
        </div>
      )}

      {/* Mutation error feedback */}
      {(startMutation.error || stopMutation.error || deleteMutation.error) && (
        <div
          className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          role="alert"
        >
          {friendlyErrorMessage(
            startMutation.error ?? stopMutation.error ?? deleteMutation.error,
            'Could not complete the action. Please try again.'
          )}
        </div>
      )}

      {/* App grid */}
      {apps && apps.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {apps.map((app) => (
            <AppCard
              key={app.name}
              app={app}
              onSelect={(name) => navigate(`/apps/${name}`)}
              onStart={(name) => startMutation.mutate(name)}
              onStop={handleStop}
              onDelete={handleDelete}
              isStartPending={startMutation.isPending}
              isStopPending={stopMutation.isPending}
              isDeletePending={deleteMutation.isPending}
            />
          ))}
        </div>
      )}

      {/* Create dialog */}
      {showCreateDialog && (
        <CreateAppDialog
          onClose={closeCreateDialog}
          onCreated={(appName) => {
            closeCreateDialog();
            navigate(`/apps/${appName}`);
          }}
        />
      )}
    </div>
  );
}

export function AppsPage() {
  return (
    <ErrorBoundary>
      <AppsPageContent />
    </ErrorBoundary>
  );
}
