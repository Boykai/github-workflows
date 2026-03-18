/**
 * BoardStatusBanners — Rate limit and error banners for the ProjectsPage board.
 * Extracted from ProjectsPage to keep the page within 250 lines.
 */

import { TriangleAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ApiError } from '@/services/api';
import { formatTimeUntil } from '@/utils/formatTime';
import type { RateLimitInfo, RefreshError } from '@/types';

interface BoardStatusBannersProps {
  showRateLimitBanner: boolean;
  rateLimitRetryAfter: Date | undefined;
  isRateLimitLow: boolean;
  rateLimitInfo: RateLimitInfo | null | undefined;
  refreshError: RefreshError | null | undefined;
  projectsError: Error | null | undefined;
  projectsRateLimitError: boolean;
  boardError: Error | null | undefined;
  boardLoading: boolean;
  boardRateLimitError: boolean;
  selectedProjectId: string | null | undefined;
  onRetryBoard: () => void;
}

export function BoardStatusBanners({
  showRateLimitBanner,
  rateLimitRetryAfter,
  isRateLimitLow,
  rateLimitInfo,
  refreshError,
  projectsError,
  projectsRateLimitError,
  boardError,
  boardLoading,
  boardRateLimitError,
  onRetryBoard,
}: BoardStatusBannersProps) {
  const projectsErrorReason =
    projectsError instanceof ApiError
      ? (projectsError.error.details?.reason as string | undefined)
      : undefined;

  return (
    <>
      {showRateLimitBanner && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground"
          role="alert"
        >
          <span className="text-lg" aria-hidden="true">⏳</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit reached</strong>
            <p>
              {rateLimitRetryAfter
                ? `Resets ${formatTimeUntil(rateLimitRetryAfter)}.`
                : 'GitHub API rate limit reached. Retry after the quota window resets.'}
            </p>
          </div>
        </div>
      )}

      {isRateLimitLow && !showRateLimitBanner && rateLimitInfo && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground"
          role="alert"
        >
          <TriangleAlert aria-hidden="true" className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Rate limit low</strong>
            <p>Only {rateLimitInfo.remaining} API requests remaining.</p>
          </div>
        </div>
      )}

      {refreshError && refreshError.type !== 'rate_limit' && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert aria-hidden="true" className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
          </div>
        </div>
      )}

      {projectsError && !projectsRateLimitError && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert aria-hidden="true" className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
            {typeof projectsErrorReason === 'string' && (
              <p className="text-sm opacity-75">{projectsErrorReason}</p>
            )}
          </div>
        </div>
      )}

      {boardError && !boardLoading && !boardRateLimitError && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert aria-hidden="true" className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            className="ml-auto self-start"
            onClick={onRetryBoard}
          >
            Retry loading board data
          </Button>
        </div>
      )}
    </>
  );
}
