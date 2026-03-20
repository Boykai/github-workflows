/**
 * useEntityHistory — wrapper around useInfiniteList for entity-scoped activity history.
 */

import { useInfiniteList } from './useInfiniteList';
import { activityApi } from '@/services/api';
import type { ActivityEvent } from '@/types';

export function useEntityHistory(projectId: string, entityType: string, entityId: string) {
  return useInfiniteList<ActivityEvent>({
    queryKey: ['activity', 'entity', projectId, entityType, entityId],
    queryFn: ({ limit, cursor }) =>
      activityApi.entityHistory(projectId, entityType, entityId, { limit, cursor }),
    limit: 50,
    staleTime: 30_000,
    enabled: !!projectId && !!entityType && !!entityId,
  });
}
