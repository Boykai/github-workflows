/**
 * IssueCardSkeleton — skeleton placeholder matching IssueCard dimensions.
 */

import { Skeleton } from '@/components/ui/skeleton';

export function IssueCardSkeleton() {
  return (
    <div className="rounded-[1.15rem] border border-border/75 bg-card/90 p-3 space-y-2">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
      <div className="flex gap-1.5">
        <Skeleton className="h-5 w-14 rounded-full" />
        <Skeleton className="h-5 w-14 rounded-full" />
      </div>
      <div className="flex items-center gap-2 pt-1">
        <Skeleton className="h-6 w-6 rounded-full" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  );
}
