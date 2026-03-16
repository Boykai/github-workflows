/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, RefreshCw } from 'lucide-react';
import { useApps, useCreateApp, useStartApp, useStopApp, useDeleteApp, getErrorMessage } from '@/hooks/useApps';
import { AppCard } from '@/components/apps/AppCard';
import { AppDetailView } from '@/components/apps/AppDetailView';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';
import type { AppCreate } from '@/types/apps';

export function AppsPage() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading, error, refetch } = useApps();
  const createMutation = useCreateApp();
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);
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

  const openCreateDialog = () => {
    createMutation.reset();
    setCreateError(null);
    setShowCreateDialog(true);
  };

  const closeCreateDialog = useCallback(() => {
    createMutation.reset();
    setCreateError(null);
    setShowCreateDialog(false);
    createButtonRef.current?.focus();
  }, [createMutation]);

  // Document-level Escape key handler for the create dialog
  useEffect(() => {
    if (!showCreateDialog) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeCreateDialog();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showCreateDialog, closeCreateDialog]);

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

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setCreateError(null);

    const formData = new FormData(e.currentTarget);
    const name = String(formData.get('name') ?? '').trim();
    const displayName = String(formData.get('display_name') ?? '').trim();
    const description = String(formData.get('description') ?? '').trim();
    const branch = String(formData.get('branch') ?? '').trim();

    if (!name || !displayName || !branch) {
      setCreateError('Name, display name, and target branch are required.');
      return;
    }

    const payload: AppCreate = { name, display_name: displayName, description, branch };
    createMutation.mutate(payload, {
      onSuccess: (createdApp) => {
        closeCreateDialog();
        showSuccess(`App "${createdApp.display_name}" created successfully.`);
        navigate(`/apps/${createdApp.name}`);
      },
      onError: (err) => {
        setCreateError(getErrorMessage(err, 'Could not create app. Please try again.'));
      },
    });
  };

  const isRateLimited = error ? isRateLimitApiError(error) : false;

  return (
    <ErrorBoundary>
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
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
            onClick={openCreateDialog}
          >
            <Plus aria-hidden="true" className="h-4 w-4" /> Create App
          </button>
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
            className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
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
          <div className="flex min-h-[30vh] flex-col items-center justify-center" aria-live="polite">
            <p className="mb-3 text-sm text-zinc-500 dark:text-zinc-400">
              {isRateLimited
                ? 'You have exceeded the API rate limit. Please wait a moment before trying again.'
                : 'Could not load applications. Please try again.'}
            </p>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-400 dark:hover:bg-zinc-800"
              onClick={() => refetch()}
            >
              <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" /> Retry
            </button>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && (!apps || apps.length === 0) && (
          <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700 dark:bg-zinc-900/50">
            <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">No applications yet.</p>
            <button
              type="button"
              className="text-sm font-medium text-emerald-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:text-emerald-400"
              onClick={openCreateDialog}
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
        {showCreateDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={closeCreateDialog}
              role="presentation"
              aria-hidden="true"
            />

            {/* Dialog */}
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="create-app-dialog-title"
              className="relative z-10"
            >
              <form
                onSubmit={handleCreate}
                className="w-full max-w-md rounded-xl border border-border/80 bg-card p-6 shadow-xl"
              >
                <h2 id="create-app-dialog-title" className="mb-4 text-lg font-bold text-foreground">
                  Create App
                </h2>
                {createError && (
                  <div
                    className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
                    role="alert"
                  >
                    {createError}
                  </div>
                )}
                <div className="space-y-4">
                  <div>
                    <label htmlFor="app-name" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Name
                    </label>
                    <input
                      id="app-name"
                      name="name"
                      type="text"
                      required
                      pattern="[a-z0-9][a-z0-9-]*[a-z0-9]"
                      minLength={2}
                      maxLength={64}
                      placeholder="my-awesome-app"
                      className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                    <p className="mt-1 text-xs text-zinc-400">
                      Lowercase letters, numbers, and hyphens only.
                    </p>
                  </div>
                  <div>
                    <label htmlFor="app-display-name" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Display Name
                    </label>
                    <input
                      id="app-display-name"
                      name="display_name"
                      type="text"
                      required
                      maxLength={128}
                      placeholder="My Awesome App"
                      className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                  </div>
                  <div>
                    <label htmlFor="app-description" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Description
                    </label>
                    <textarea
                      id="app-description"
                      name="description"
                      rows={2}
                      placeholder="A brief description of your app…"
                      className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                  </div>
                  <div>
                    <label htmlFor="app-branch" className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
                      Target Branch
                    </label>
                    <input
                      id="app-branch"
                      name="branch"
                      type="text"
                      required
                      maxLength={256}
                      placeholder="parent-issue/my-feature"
                      className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
                    />
                    <p className="mt-1 text-xs text-zinc-400">
                      The parent issue branch where the app scaffold will be committed.
                    </p>
                  </div>
                </div>
                <div className="mt-6 flex justify-end gap-3">
                  <button
                    type="button"
                    className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:ring-offset-2 dark:text-zinc-400 dark:hover:bg-zinc-800"
                    onClick={closeCreateDialog}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:opacity-50"
                  >
                    {createMutation.isPending ? 'Creating…' : 'Create App'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
