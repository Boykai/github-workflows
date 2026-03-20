/**
 * useEntityHistory — wrapper around useInfiniteList for entity-scoped activity history.
 */

import { useInfiniteList } from './useInfiniteList';
import { activityApi } from '@/services/api';
import type { ActivityEvent } from '@/types';

export function useEntityHistory(entityType: string, entityId: string) {
  return useInfiniteList<ActivityEvent>({
    queryKey: ['activity', 'entity', entityType, entityId],
    queryFn: ({ limit, cursor }) =>
      activityApi.entityHistory(entityType, entityId, { limit, cursor }),
    limit: 50,
    staleTime: 30_000,
    enabled: !!entityType && !!entityId,
  });
}
