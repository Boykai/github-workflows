/**
 * useBlockingQueue — React Query hook for fetching blocking queue entries.
 *
 * Provides the current blocking queue state for a project, used by the
 * BlockingChainPanel component to display queue status.
 */

import { useQuery } from '@tanstack/react-query';
import { boardApi } from '@/services/api';
import type { BlockingQueueEntry } from '@/types';

export function useBlockingQueue(projectId: string | undefined) {
  return useQuery<BlockingQueueEntry[]>({
    queryKey: ['blocking-queue', projectId],
    queryFn: () => boardApi.getBlockingQueue(projectId!),
    enabled: !!projectId,
    refetchInterval: 30_000, // Refresh every 30s; also invalidated by WebSocket
    staleTime: 10_000,
  });
}
