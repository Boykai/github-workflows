/**
 * Hook to fetch pipeline states for all issues in the selected project.
 * Wraps the existing GET /workflow/pipeline-states endpoint (returns in-memory data, zero GitHub API calls).
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { workflowApi } from '@/services/api';
import { STALE_TIME_SHORT } from '@/constants';
import type { PipelineStateInfo } from '@/types';

export function usePipelineStates(projectId?: string | null) {
  const { data } = useQuery({
    queryKey: ['workflow', 'pipeline-states', projectId],
    queryFn: () => workflowApi.getPipelineStates(),
    enabled: !!projectId,
    staleTime: STALE_TIME_SHORT,
    refetchInterval: STALE_TIME_SHORT,
  });

  const statesMap = useMemo(() => {
    const map = new Map<number, PipelineStateInfo>();
    if (!data?.pipeline_states) return map;
    for (const [key, value] of Object.entries(data.pipeline_states)) {
      map.set(Number(key), value);
    }
    return map;
  }, [data]);

  return statesMap;
}
