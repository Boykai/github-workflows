/**
 * InfiniteScrollContainer — reusable scroll sentinel component.
 *
 * Uses IntersectionObserver to detect when the user has scrolled near the
 * bottom of a list and automatically triggers the next page fetch.
 */

import { useEffect, useRef, type ReactNode } from 'react';

interface InfiniteScrollContainerProps {
  children: ReactNode;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  fetchNextPage: () => void;
  isError?: boolean;
  onRetry?: () => void;
  className?: string;
}

export function InfiniteScrollContainer({
  children,
  hasNextPage,
  isFetchingNextPage,
  fetchNextPage,
  isError = false,
  onRetry,
  className,
}: InfiniteScrollContainerProps) {
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasNextPage || isFetchingNextPage || isError) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting && hasNextPage && !isFetchingNextPage && !isError) {
          fetchNextPage();
        }
      },
      { rootMargin: '200px' },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, isError, fetchNextPage]);

  return (
    <div className={className}>
      {children}

      {/* Sentinel element for IntersectionObserver */}
      {hasNextPage && !isError && (
        <div ref={sentinelRef} aria-hidden="true" className="h-1" />
      )}

      {/* Loading indicator */}
      {isFetchingNextPage && (
        <div className="flex items-center justify-center py-4" aria-live="polite">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary/30 border-t-primary" />
          <span className="ml-2 text-sm text-muted-foreground">Loading more…</span>
        </div>
      )}

      {/* Error state with retry */}
      {isError && !isFetchingNextPage && (
        <div className="flex items-center justify-center gap-2 py-4" aria-live="polite">
          <span className="text-sm text-destructive">Failed to load more items.</span>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="text-sm font-medium text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              Retry
            </button>
          )}
        </div>
      )}
    </div>
  );
}
