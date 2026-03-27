/**
 * AppsPage — Solune application management page.
 * Displays a card grid of managed applications with create dialog
 * and navigation to the detail view.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
import { AppDetailView } from '@/components/apps/AppDetailView';
import { AppsListView } from '@/components/apps/AppsListView';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
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
      // Fetch asset inventory for confirmation dialog
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

      const firstConfirm = await confirm({
        title: 'Delete App & All Assets',
        description: assetSummary,
        variant: 'danger',
        confirmLabel: 'Continue to Final Confirmation',
      });
      if (!firstConfirm) return;

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
        <AppsListView
          apps={displayApps}
          isLoading={isLoading}
          error={error}
          isRateLimited={isRateLimited}
          onRetry={() => refetch()}
          onSelectApp={(name) => navigate(`/apps/${name}`)}
          onStart={handleStart}
          onStop={handleStop}
          onDelete={handleDelete}
          isStartPending={startMutation.isPending}
          isStopPending={stopMutation.isPending}
          isDeletePending={deleteMutation.isPending}
          hasNextPage={appsHasNextPage ?? false}
          isFetchingNextPage={appsIsFetchingNextPage}
          fetchNextPage={appsFetchNextPage}
          isPaginatedError={appsPaginatedError}
          showCreateDialog={showCreateDialog}
          createButtonRef={createButtonRef}
          onOpenCreateDialog={openCreateDialog}
          onCloseCreateDialog={closeCreateDialog}
          onCreateSubmit={handleCreateSubmit}
          isCreatePending={createMutation.isPending}
          owners={owners}
          getErrorMessage={getErrorMessage}
          createRepoType={createRepoType}
          pipelines={pipelines}
          isLoadingPipelines={pipelinesLoading}
          defaultPipelineId={defaultPipelineId}
          projectId={projectId}
        />
      </div>
    </ErrorBoundary>
  );
}
