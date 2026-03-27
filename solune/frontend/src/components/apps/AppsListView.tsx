/**
 * AppsListView — Loading, error, empty, and grid states for the apps list.
 *
 * Extracted from AppsPage to keep the page ≤ 250 lines (FR-001).
 */

import { Skeleton } from '@/components/ui/skeleton';
import { InfiniteScrollContainer } from '@/components/common/InfiniteScrollContainer';
import { AppCard } from '@/components/apps/AppCard';
import { RefreshCw } from '@/lib/icons';
import { isRateLimitApiError } from '@/utils/rateLimit';
import type { App } from '@/types/apps';

interface AppsListViewProps {
  displayApps: App[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
  appsHasNextPage: boolean | undefined;
  appsIsFetchingNextPage: boolean;
  appsFetchNextPage: () => void;
  appsPaginatedError: boolean;
  onSelect: (name: string) => void;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  onDelete: (name: string) => void;
  isStartPending: boolean;
  isStopPending: boolean;
  isDeletePending: boolean;
  onCreateApp: () => void;
}

export function AppsListView({
  displayApps,
  isLoading,
  error,
  refetch,
  appsHasNextPage,
  appsIsFetchingNextPage,
  appsFetchNextPage,
  appsPaginatedError,
  onSelect,
  onStart,
  onStop,
  onDelete,
  isStartPending,
  isStopPending,
  isDeletePending,
  onCreateApp,
}: AppsListViewProps) {
  const isRateLimited = error ? isRateLimitApiError(error) : false;

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true" aria-live="polite">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-700">
            <Skeleton variant="shimmer" className="mb-3 h-5 w-32" />
            <Skeleton variant="shimmer" className="mb-2 h-4 w-48" />
            <Skeleton variant="shimmer" className="h-4 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
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
    );
  }

  if (displayApps.length === 0) {
    return (
      <div className="flex min-h-[30vh] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 dark:border-zinc-700 dark:bg-zinc-900/50">
        <p className="mb-2 text-sm text-zinc-500 dark:text-zinc-400">No applications yet.</p>
        <button
          type="button"
          className="text-sm font-medium text-emerald-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 dark:text-emerald-400"
          onClick={onCreateApp}
        >
          Create your first app →
        </button>
      </div>
    );
  }

  return (
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
            onSelect={onSelect}
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
  );
}
