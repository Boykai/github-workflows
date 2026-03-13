/** Pipeline query orchestration — list, assignment, and stage execution config. */

import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';
import { STALE_TIME_SHORT } from '@/constants';
import type { PipelineConfig, PipelineConfigListResponse } from '@/types';

export const pipelineKeys = {
  all: ['pipelines'] as const,
  list: (projectId: string) => [...pipelineKeys.all, 'list', projectId] as const,
  detail: (projectId: string, pipelineId: string) =>
    [...pipelineKeys.all, 'detail', projectId, pipelineId] as const,
  assignment: (projectId: string) => [...pipelineKeys.all, 'assignment', projectId] as const,
};

export function usePipelineOrchestration(
  projectId: string | null,
  setPipeline: (updater: React.SetStateAction<PipelineConfig | null>) => void,
) {
  const { data: pipelines, isLoading: pipelinesLoading } = useQuery<PipelineConfigListResponse>({
    queryKey: pipelineKeys.list(projectId ?? ''),
    queryFn: () => pipelinesApi.list(projectId!),
    staleTime: STALE_TIME_SHORT,
    enabled: !!projectId,
  });

  const { data: assignment } = useQuery({
    queryKey: pipelineKeys.assignment(projectId ?? ''),
    queryFn: () => pipelinesApi.getAssignment(projectId!),
    enabled: !!projectId,
    staleTime: STALE_TIME_SHORT,
  });

  const setStageExecutionMode = useCallback(
    (stageId: string, mode: 'sequential' | 'parallel') => {
      setPipeline((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          stages: prev.stages.map((s) => {
            if (s.id !== stageId) return s;
            const effectiveMode = mode === 'parallel' && s.agents.length < 2 ? 'sequential' : mode;
            return { ...s, execution_mode: effectiveMode };
          }),
        };
      });
    },
    [setPipeline],
  );

  return {
    pipelines: pipelines ?? null,
    pipelinesLoading,
    assignedPipelineId: assignment?.pipeline_id ?? '',
    setStageExecutionMode,
  };
}
