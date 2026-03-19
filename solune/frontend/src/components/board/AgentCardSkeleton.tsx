/**
 * AgentCardSkeleton — skeleton placeholder matching agent card dimensions.
 */

import { Skeleton } from '@/components/ui/skeleton';

export function AgentCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-3 flex items-center gap-3">
      <Skeleton className="h-10 w-10 rounded-full shrink-0" />
      <div className="flex-1 space-y-1.5">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  );
}
