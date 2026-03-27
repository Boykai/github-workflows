/**
 * useSeedPresets — Seeds preset pipelines on mount for a project (one-shot).
 */

import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { pipelineKeys } from '@/hooks/usePipelineConfig';

export function useSeedPresets(projectId: string | null) {
  const queryClient = useQueryClient();
  const seededRef = useRef(false);

  useEffect(() => {
    if (!projectId || seededRef.current) return;
    seededRef.current = true;
    pipelinesApi
      .seedPresets(projectId)
      .then(() => {
        queryClient.invalidateQueries({ queryKey: pipelineKeys.list(projectId) });
      })
      .catch(() => {
        // Preset seeding failure is non-critical; silently continue
      });
  }, [projectId, queryClient]);
}
