/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useCallback, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { GitBranch, Plus, RefreshCw } from 'lucide-react';
import { useApps, useStartApp, useStopApp, useDeleteApp, getErrorMessage } from '@/hooks/useApps';
import { AppCard } from '@/components/apps/AppCard';
import { AppDetailView } from '@/components/apps/AppDetailView';
import { CreateAppDialog } from '@/components/apps/CreateAppDialog';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';
import type { RepoType } from '@/types/apps';

export function AppsPage() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading, error, refetch } = useApps();
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createInitialRepoType, setCreateInitialRepoType] = useState<RepoType>('same-repo');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const errorTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

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

  const openCreateDialog = useCallback((initialRepoType: RepoType = 'same-repo') => {
    setCreateInitialRepoType(initialRepoType);
    setShowCreateDialog(true);
  }, []);

  const handleStart = useCallback(async (name: string) => {
    startMutation.mutate(name, {
      onSuccess: () => showSuccess(`App "${name}" started successfully.`),
      onError: (err) => showError(getErrorMessage(err, `Could not start app "${name}".`)),
    });
  }, [startMutation, showSuccess, showError]);

  const handleStop = useCallback(async (name: string) => {
    const confirmed = await confirm({
      title: 'Stop App',
      description: `Stop app "${name}"? The app will no longer be accessible until restarted.`,
      variant: 'warning',
      confirmLabel: 'Stop App',
    });
    if (confirmed) {
      stopMutation.mutate(name, {
        onSuccess: () => showSuccess(`App "${name}" stopped successfully.`),
        onError: (err) => showError(getErrorMessage(err, `Could not stop app "${name}".`)),
      });
    }
  }, [confirm, stopMutation, showSuccess, showError]);

  const handleDelete = useCallback(async (name: string) => {
    const confirmed = await confirm({
      title: 'Delete App',
      description: `Delete app "${name}"? This action cannot be undone.`,
      variant: 'danger',
      confirmLabel: 'Delete App',
    });
    if (confirmed) {
      deleteMutation.mutate(name, {
        onSuccess: () => showSuccess(`App "${name}" deleted successfully.`),
        onError: (err) => showError(getErrorMessage(err, `Could not delete app "${name}".`)),
      });
    }
  }, [confirm, deleteMutation, showSuccess, showError]);

  // Detail view for a specific app
  if (appName) {
    return (
      <ErrorBoundary>
        <div className="mx-auto max-w-5xl px-6 py-8">
          <AppDetailView appName={appName} onBack={() => navigate('/apps')} />
        </div>
      </ErrorBoundary>
    );
  }

  const isRateLimited = error ? isRateLimitApiError(error) : false;

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-5xl px-6 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Apps</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Create, manage, and preview your applications.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              onClick={() => openCreateDialog('new-repo')}
            >
              <GitBranch aria-hidden="true" className="h-4 w-4" /> Create Repository
            </button>
            <button
              ref={createButtonRef}
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              onClick={() => openCreateDialog()}
            >
              <Plus aria-hidden="true" className="h-4 w-4" /> Create App
            </button>
          </div>
        </div>

        {/* Success feedback */}
        {successMessage && (
          <div
            className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300"
            role="status"
          >
            {successMessage}
          </div>
        )}

        {/* Action error feedback */}
        {actionError && (
          <div
            className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
            role="alert"
          >
            {actionError}
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex min-h-[30vh] items-center justify-center" aria-busy="true" aria-live="polite">
            <CelestialLoader size="md" label="Loading apps…" />
          </div>
        )}

        {/* Error state */}
        {!isLoading && error && (
          <div className="flex min-h-[30vh] flex-col items-center justify-center gap-3" aria-live="polite">
            <p className="text-sm text-muted-foreground">
              {isRateLimited
                ? 'You have exceeded the API rate limit. Please wait a moment before trying again.'
                : 'Could not load applications. Please try again.'}
            </p>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              onClick={() => refetch()}
            >
              <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" /> Retry
            </button>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && (!apps || apps.length === 0) && (
          <div className="flex min-h-[30vh] flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-background/50">
            <p className="text-sm text-muted-foreground">No applications yet. Create your first app to get started.</p>
            <button
              type="button"
              className="text-sm font-medium text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
              onClick={() => openCreateDialog()}
            >
              Create your first app →
            </button>
          </div>
        )}

        {/* App grid */}
        {!isLoading && !error && apps && apps.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {apps.map((app) => (
              <AppCard
                key={app.name}
                app={app}
                onSelect={(name) => navigate(`/apps/${name}`)}
                onStart={handleStart}
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
          <CreateAppDialog
            initialRepoType={createInitialRepoType}
            triggerRef={createButtonRef}
            onClose={() => setShowCreateDialog(false)}
            onSuccess={(msg) => showSuccess(msg)}
            onError={(msg) => showError(msg)}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
