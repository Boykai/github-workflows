/**
 * useActivityFeed — wrapper around useInfiniteList for the activity feed.
 * Supports optional event type filtering with 30s stale time.
 */

import { useInfiniteList } from './useInfiniteList';
import { activityApi } from '@/services/api';
import type { ActivityEvent } from '@/types';

export function useActivityFeed(projectId: string, eventTypes?: string[]) {
  const eventTypeParam = eventTypes?.length ? eventTypes.join(',') : undefined;

  return useInfiniteList<ActivityEvent>({
    queryKey: ['activity', projectId, eventTypeParam],
    queryFn: ({ limit, cursor }) =>
      activityApi.feed(projectId, { limit, cursor, event_type: eventTypeParam }),
    limit: 50,
    staleTime: 30_000,
    enabled: !!projectId,
  });
}
