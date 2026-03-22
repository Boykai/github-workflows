/**
 * ProjectBoardErrorBanners — Rate limit and error banners for the Projects page.
 * Extracted from ProjectsPage to keep the page file ≤250 lines.
 */

import { TriangleAlert, Lightbulb } from '@/lib/icons';
import { Button } from '@/components/ui/button';
import { formatTimeUntil } from '@/utils/formatTime';
import { ApiError } from '@/services/api';
import { getErrorHint, type ErrorHint } from '@/utils/errorHints';

interface RateLimitInfo {
  remaining: number;
  reset_at: number;
}

interface RefreshError {
  type: string;
  message: string;
  retryAfter?: Date;
  rateLimitInfo?: RateLimitInfo;
}

interface ProjectBoardErrorBannersProps {
  showRateLimitBanner: boolean;
  rateLimitRetryAfter: Date | undefined;
  isRateLimitLow: boolean;
  rateLimitInfo: RateLimitInfo | null | undefined;
  refreshError: RefreshError | null;
  projectsError: Error | null;
  projectsRateLimitError: boolean;
  boardError: Error | null;
  boardLoading: boolean;
  boardRateLimitError: boolean;
  selectedProjectId: string | null;
  onRetryBoard: (projectId: string) => void;
}

/** Shared hint row used by every error/rate-limit banner. */
function ErrorHintRow({ hint }: { hint: ErrorHint }) {
  return (
    <p className="flex items-start gap-1.5 text-sm opacity-75">
      <Lightbulb className="h-3.5 w-3.5 shrink-0 mt-0.5" />
      <span>
        {hint.hint}
        {hint.action && (
          <>
            {' '}
            <a href={hint.action.href} className="underline hover:opacity-80">
              {hint.action.label}
            </a>
          </>
        )}
      </span>
    </p>
  );
}

export function ProjectBoardErrorBanners({
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
  selectedProjectId,
  onRetryBoard,
}: ProjectBoardErrorBannersProps) {
  return (
    <>
      {showRateLimitBanner && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground"
          role="alert"
        >
          <span className="text-lg">⏳</span>
          <div className="flex flex-col gap-1">
            <strong>Rate limit reached</strong>
            <p>
              {rateLimitRetryAfter
                ? `Resets ${formatTimeUntil(rateLimitRetryAfter)}.`
                : 'GitHub API rate limit reached. Retry after the quota window resets.'}
            </p>
            <ErrorHintRow hint={getErrorHint({ status: 429 })} />
          </div>
        </div>
      )}

      {isRateLimitLow && !showRateLimitBanner && rateLimitInfo && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-accent/30 bg-accent/12 p-4 text-accent-foreground"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
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
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Refresh failed</strong>
            <p>{refreshError.message}</p>
            <ErrorHintRow hint={getErrorHint(refreshError)} />
          </div>
        </div>
      )}

      {projectsError && !projectsRateLimitError && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load projects</strong>
            <p>{projectsError.message}</p>
            {(() => {
              if (!(projectsError instanceof ApiError)) return null;
              const reason = projectsError.error.details?.reason;
              return typeof reason === 'string' ? (
                <p className="text-sm opacity-75">{reason}</p>
              ) : null;
            })()}
            <ErrorHintRow hint={getErrorHint(projectsError)} />
          </div>
        </div>
      )}

      {boardError && !boardLoading && !boardRateLimitError && (
        <div
          className="flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive"
          role="alert"
        >
          <TriangleAlert className="h-5 w-5 shrink-0" />
          <div className="flex flex-col gap-1">
            <strong>Failed to load board data</strong>
            <p>{boardError.message}</p>
            <ErrorHintRow hint={getErrorHint(boardError)} />
          </div>
          <Button
            variant="destructive"
            size="sm"
            className="ml-auto self-start"
            onClick={() => selectedProjectId && onRetryBoard(selectedProjectId)}
          >
            Retry loading board data
          </Button>
        </div>
      )}
    </>
  );
}
