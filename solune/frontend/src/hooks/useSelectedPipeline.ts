/**
 * Shared hook for reading the current project's pipeline assignment.
 *
 * Used by both the chat (for PipelineWarningBanner) and optionally by
 * ProjectsPage for DRY cache-sharing.  Wraps two React Query calls:
 *   1. pipelinesApi.getAssignment(projectId) — gets the assigned pipeline ID
 *   2. pipelinesApi.list(projectId) — resolves the pipeline name from the ID
 */

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';

export interface SelectedPipelineState {
  pipelineId: string;
  pipelineName: string;
  isLoading: boolean;
  hasAssignment: boolean;
}

export function useSelectedPipeline(projectId: string | null): SelectedPipelineState {
  const enabled = !!projectId;

  const { data: assignment, isLoading: assignmentLoading } = useQuery({
    queryKey: ['pipelines', 'assignment', projectId],
    queryFn: () => pipelinesApi.getAssignment(projectId!),
    staleTime: 60_000,
    enabled,
  });

  const { data: pipelineList, isLoading: listLoading } = useQuery({
    queryKey: ['pipelines', projectId],
    queryFn: () => pipelinesApi.list(projectId!),
    staleTime: 60_000,
    enabled,
  });

  const pipelineId = assignment?.pipeline_id ?? '';

  const pipelineName = useMemo(() => {
    if (!pipelineId || !pipelineList?.pipelines) return '';
    const match = pipelineList.pipelines.find((p) => p.id === pipelineId);
    // Assigned pipeline was deleted — surface "Unknown Pipeline"
    if (!match) return 'Unknown Pipeline';
    return match.name;
  }, [pipelineId, pipelineList]);

  return {
    pipelineId,
    pipelineName,
    isLoading: assignmentLoading || listLoading,
    hasAssignment: pipelineId !== '',
  };
}
