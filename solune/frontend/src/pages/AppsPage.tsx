/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { GitBranch, Plus, RefreshCw } from '@/lib/icons';
import {
  useApp,
  useApps,
  useAppsPaginated,
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
import { Skeleton } from '@/components/ui/skeleton';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';
import { useConfirmation } from '@/hooks/useConfirmation';
import { isRateLimitApiError } from '@/utils/rateLimit';
import { appsApi, pipelinesApi } from '@/services/api';
import { useQuery } from '@tanstack/react-query';
import type { AppCreate, RepoType } from '@/types/apps';
import { useBreadcrumb } from '@/hooks/useBreadcrumb';
import { toTitleCase } from '@/lib/breadcrumb-utils';

export function AppsPage() {
  const { appName } = useParams<{ appName?: string }>();
  const navigate = useNavigate();
  const { data: apps, isLoading, error, refetch } = useApps();
  const {
    allItems: paginatedApps,
    hasNextPage: appsHasNextPage,
    isFetchingNextPage: appsIsFetchingNextPage,
    fetchNextPage: appsFetchNextPage,
    isError: appsPaginatedError,
  } = useAppsPaginated();

  // Dynamic breadcrumb label for app detail view
  const { data: appData } = useApp(appName);
  const { setLabel, removeLabel } = useBreadcrumb();
  useEffect(() => {
    if (!appName) return;
    const path = `/apps/${appName}`;
    const breadcrumbLabel = appData?.display_name ?? toTitleCase(appName);
    setLabel(path, breadcrumbLabel);
    return () => removeLabel(path);
  }, [appName, appData?.display_name, setLabel, removeLabel]);

  // Use paginated items when available; fall back to non-paginated for initial load
  const displayApps = paginatedApps.length > 0 ? paginatedApps : (apps ?? []);
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
  const createButtonRef = useRef<HTMLButtonElement>(null);

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
          navigate(`/apps/${createdApp.name}`);
          callbacks.onSuccess(createdApp);
        },
        onError: (err) => {
          callbacks.onError(err);
        },
      });
    },
    [createMutation, closeCreateDialog, navigate]
  );

  const handleStart = useCallback(
    async (name: string) => {
      startMutation.mutate(name);
    },
    [startMutation]
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
        stopMutation.mutate(name);
      }
    },
    [confirm, stopMutation]
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
      );
    },
    [confirm, deleteMutation]
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

        {/* Loading state */}
        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-live="polite">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-700">
                <Skeleton variant="shimmer" className="mb-3 h-5 w-32" />
                <Skeleton variant="shimmer" className="mb-2 h-4 w-48" />
                <Skeleton variant="shimmer" className="h-4 w-24" />
              </div>
            ))}
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
        {!isLoading && !error && displayApps.length === 0 && (
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
        {!isLoading && !error && displayApps.length > 0 && (
          <InfiniteScrollContainer
            hasNextPage={appsHasNextPage ?? false}
            isFetchingNextPage={appsIsFetchingNextPage}
            fetchNextPage={appsFetchNextPage}
            isError={appsPaginatedError}
            onRetry={appsFetchNextPage}
          >
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {displayApps.map((app) => (
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
          </InfiniteScrollContainer>
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
