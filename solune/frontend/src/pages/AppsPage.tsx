/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { GitBranch, Plus, RefreshCw } from 'lucide-react';
import {
  useApps,
  useCreateApp,
  useOwners,
  useStartApp,
  useStopApp,
  useDeleteApp,
  getErrorMessage,
} from '@/hooks/useApps';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { useSelectedPipeline } from '@/hooks/useSelectedPipeline';
import { AppCard } from '@/components/apps/AppCard';
import { AppDetailView } from '@/components/apps/AppDetailView';
import { CreateAppDialog } from '@/components/apps/CreateAppDialog';
import { CelestialLoader } from '@/components/common/CelestialLoader';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';
import { appsApi, pipelinesApi } from '@/services/api';
import { useQuery } from '@tanstack/react-query';
import type { AppCreate, RepoType } from '@/types/apps';

export function AppsPage() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading, error, refetch } = useApps();
  const createMutation = useCreateApp();
  const startMutation = useStartApp();
  const stopMutation = useStopApp();
  const deleteMutation = useDeleteApp();
  const { confirm } = useConfirmation();
  const { data: owners } = useOwners();
  const { user } = useAuth();
  const { selectedProject } = useProjects(user?.selected_project_id);
  const projectId = selectedProject?.project_id ?? null;
  const { pipelineId: defaultPipelineId } = useSelectedPipeline(projectId);
  const { data: pipelineList, isLoading: pipelinesLoading } = useQuery({
    queryKey: ['pipelines', projectId],
    queryFn: () => pipelinesApi.list(projectId!),
    staleTime: 60_000,
    enabled: !!projectId,
  });
  const pipelines = pipelineList?.pipelines ?? [];
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createRepoType, setCreateRepoType] = useState<RepoType | undefined>();
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

  const openCreateDialog = (initialRepoType?: RepoType) => {
    createMutation.reset();
    setCreateRepoType(initialRepoType);
    setShowCreateDialog(true);
  };

  const closeCreateDialog = useCallback(() => {
    createMutation.reset();
    setShowCreateDialog(false);
    createButtonRef.current?.focus();
  }, [createMutation]);

  const handleCreateSubmit = useCallback(
    (
      payload: AppCreate,
      callbacks: {
        onSuccess: (app: {
          name: string;
          repo_type?: string;
          parent_issue_url?: string | null;
          warnings?: string[] | null;
        }) => void;
        onError: (err: unknown) => void;
      }
    ) => {
      createMutation.mutate(payload, {
        onSuccess: (createdApp) => {
          closeCreateDialog();
          const lines: string[] = [];
          if (createdApp.repo_type === 'new-repo') {
            lines.push('✓ Repository created', '✓ Template files committed');
          } else if (createdApp.repo_type === 'external-repo') {
            lines.push('✓ External repository linked');
          } else {
            lines.push('✓ App created');
          }
          if (createdApp.parent_issue_url) {
            lines.push('✓ Pipeline started');
          }
          if (createdApp.warnings?.length) {
            for (const w of createdApp.warnings) {
              lines.push(`⚠ ${w}`);
            }
          }
          showSuccess(lines.join(' | '));
          navigate(`/apps/${createdApp.name}`);
          callbacks.onSuccess(createdApp);
        },
        onError: (err) => {
          callbacks.onError(err);
        },
      });
    },
    [createMutation, closeCreateDialog, showSuccess, navigate]
  );

  const handleStart = useCallback(
    async (name: string) => {
      startMutation.mutate(name, {
        onSuccess: () => showSuccess(`App "${name}" started successfully.`),
        onError: (err) => showError(getErrorMessage(err, `Could not start app "${name}".`)),
      });
    },
    [startMutation, showSuccess, showError]
  );

  const handleStop = useCallback(
    async (name: string) => {
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
    },
    [confirm, stopMutation, showSuccess, showError]
  );

  const handleDelete = useCallback(
    async (name: string) => {
      // Step 1: Fetch asset inventory
      let assetSummary = 'This action cannot be undone.';
      try {
        const assets = await appsApi.assets(name);
        const parts: string[] = [];
        if (assets.github_repo) parts.push(`Repository: ${assets.github_repo}`);
        if (assets.github_project_id) parts.push('GitHub Project');
        if (assets.parent_issue_number) parts.push(`Parent issue #${assets.parent_issue_number}`);
        if (assets.sub_issues.length > 0) parts.push(`${assets.sub_issues.length} sub-issue(s)`);
        if (assets.branches.length > 0) parts.push(`${assets.branches.length} branch(es)`);
        if (parts.length > 0) {
          assetSummary = `The following assets will be permanently deleted:\n• ${parts.join('\n• ')}\n\nThis action cannot be undone.`;
        }
      } catch {
        // If asset fetch fails, proceed with generic confirmation
      }

      // Step 1: Show asset inventory confirmation
      const firstConfirm = await confirm({
        title: 'Delete App & All Assets',
        description: assetSummary,
        variant: 'danger',
        confirmLabel: 'Continue to Final Confirmation',
      });
      if (!firstConfirm) return;

      // Step 2: Type-to-confirm
      const secondConfirm = await confirm({
        title: 'Confirm Permanent Deletion',
        description: `You are about to permanently delete "${name}" and all associated GitHub assets. This cannot be reversed.`,
        variant: 'danger',
        confirmLabel: `Delete "${name}" Forever`,
      });
      if (!secondConfirm) return;

      deleteMutation.mutate(
        { appName: name, force: true },
        {
          onSuccess: (result) => {
            if (result && 'errors' in result && result.errors.length > 0) {
              showSuccess(`App "${name}" deleted with ${result.errors.length} warning(s).`);
            } else {
              showSuccess(`App "${name}" and all assets deleted successfully.`);
            }
          },
          onError: (err) => showError(getErrorMessage(err, `Could not delete app "${name}".`)),
        }
      );
    },
    [confirm, deleteMutation, showSuccess, showError]
  );

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
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Apps</h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Create, manage, and preview your applications.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800"
              onClick={() => openCreateDialog('new-repo')}
            >
              <GitBranch aria-hidden="true" className="h-4 w-4" /> New Repository
            </button>
            <button
              ref={createButtonRef}
              type="button"
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
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
            className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
            role="alert"
          >
            {actionError}
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div
            className="flex min-h-[30vh] items-center justify-center"
            aria-busy="true"
            aria-live="polite"
          >
            <CelestialLoader size="md" label="Loading apps…" />
          </div>
        )}

        {/* Error state */}
        {!isLoading && error && (
          <div
            className="flex min-h-[30vh] flex-col items-center justify-center"
            aria-live="polite"
          >
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
        {showCreateDialog && (
          <CreateAppDialog
            onClose={closeCreateDialog}
            onSubmit={handleCreateSubmit}
            isPending={createMutation.isPending}
            owners={owners}
            getErrorMessage={getErrorMessage}
            initialRepoType={createRepoType}
            pipelines={pipelines}
            isLoadingPipelines={pipelinesLoading}
            defaultPipelineId={defaultPipelineId}
            projectId={projectId}
          />
        )}
      </div>
    </ErrorBoundary>
  );
}
