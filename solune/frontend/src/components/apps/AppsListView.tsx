/**
 * AppsListView — Renders the app list view with header, loading/error/empty
 * states, app card grid, and create dialog.
 * Extracted from AppsPage to keep the page file focused on routing and state.
 */

import type { RefObject } from 'react';
import { GitBranch, Plus, RefreshCw } from '@/lib/icons';
import { AppCard } from '@/components/apps/AppCard';
import { CreateAppDialog } from '@/components/apps/CreateAppDialog';
import { Skeleton } from '@/components/ui/skeleton';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';
import type { App, AppCreate, Owner, RepoType } from '@/types/apps';
import type { PipelineConfigSummary } from '@/types';

interface AppsListViewProps {
  apps: App[];
  isLoading: boolean;
  error: Error | null;
  isRateLimited: boolean;
  onRetry: () => void;
  onSelectApp: (name: string) => void;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  onDelete: (name: string) => void;
  isStartPending: boolean;
  isStopPending: boolean;
  isDeletePending: boolean;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
  isPaginatedError: boolean;
  showCreateDialog: boolean;
  createButtonRef: RefObject<HTMLButtonElement | null>;
  onOpenCreateDialog: (initialRepoType?: RepoType) => void;
  onCloseCreateDialog: () => void;
  onCreateSubmit: (
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
  ) => void;
  isCreatePending: boolean;
  owners: Owner[] | undefined;
  getErrorMessage: (err: unknown, fallback: string) => string;
  createRepoType?: RepoType;
  pipelines: PipelineConfigSummary[];
  isLoadingPipelines: boolean;
  defaultPipelineId?: string;
  projectId: string | null;
}

export function AppsListView({
  apps,
  isLoading,
  error,
  isRateLimited,
  onRetry,
  onSelectApp,
  onStart,
  onStop,
  onDelete,
  isStartPending,
  isStopPending,
  isDeletePending,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  isPaginatedError,
  showCreateDialog,
  createButtonRef,
  onOpenCreateDialog,
  onCloseCreateDialog,
  onCreateSubmit,
  isCreatePending,
  owners,
  getErrorMessage,
  createRepoType,
  pipelines,
  isLoadingPipelines,
  defaultPipelineId,
  projectId,
}: AppsListViewProps) {
  return (
    <>
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
            onClick={() => onOpenCreateDialog('new-repo')}
          >
            <GitBranch aria-hidden="true" className="h-4 w-4" /> New Repository
          </button>
          <button
            ref={createButtonRef}
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2"
            onClick={() => onOpenCreateDialog()}
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
            onClick={onRetry}
          >
            <RefreshCw aria-hidden="true" className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && apps.length === 0 && (
        <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700 dark:bg-zinc-900/50">
          <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">No applications yet.</p>
          <button
            type="button"
            className="text-sm font-medium text-emerald-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:text-emerald-400"
            onClick={() => onOpenCreateDialog()}
          >
            Create your first app →
          </button>
        </div>
      )}

      {/* App grid */}
      {!isLoading && !error && apps.length > 0 && (
        <InfiniteScrollContainer
          hasNextPage={hasNextPage}
          isFetchingNextPage={isFetchingNextPage}
          fetchNextPage={fetchNextPage}
          isError={isPaginatedError}
          onRetry={fetchNextPage}
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {apps.map((app) => (
              <AppCard
                key={app.name}
                app={app}
                onSelect={onSelectApp}
                onStart={onStart}
                onStop={onStop}
                onDelete={onDelete}
                isStartPending={isStartPending}
                isStopPending={isStopPending}
                isDeletePending={isDeletePending}
              />
            ))}
          </div>
        </InfiniteScrollContainer>
      )}

      {/* Create dialog */}
      {showCreateDialog && (
        <CreateAppDialog
          onClose={onCloseCreateDialog}
          onSubmit={onCreateSubmit}
          isPending={isCreatePending}
          owners={owners}
          getErrorMessage={getErrorMessage}
          initialRepoType={createRepoType}
          pipelines={pipelines}
          isLoadingPipelines={isLoadingPipelines}
          defaultPipelineId={defaultPipelineId}
          projectId={projectId}
        />
      )}
    </>
  );
}
