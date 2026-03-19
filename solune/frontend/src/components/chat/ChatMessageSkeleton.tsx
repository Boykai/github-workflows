/**
 * ChatMessageSkeleton — skeleton placeholder matching MessageBubble dimensions.
 */

import { Skeleton } from '@/components/ui/skeleton';

export function ChatMessageSkeleton() {
  return (
    <div className="flex items-start gap-3 max-w-[80%]">
      <Skeleton className="h-8 w-8 rounded-full shrink-0" />
      <div className="flex-1 space-y-2 border border-border bg-background/62 rounded-2xl p-3">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}
