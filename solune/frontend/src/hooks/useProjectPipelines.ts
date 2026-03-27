/**
 * useProjectPipelines — Pipeline list, assignment, and mutation for a project.
 *
 * Extracted from ProjectsPage to keep the page ≤ 250 lines (FR-001).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/services/api';

export function useProjectPipelines(projectId: string | null) {
  const queryClient = useQueryClient();

  const {
    data: savedPipelines,
    isLoading: savedPipelinesLoading,
    error: savedPipelinesError,
    refetch: refetchSavedPipelines,
  } = useQuery({
    queryKey: ['pipelines', projectId],
    queryFn: () => pipelinesApi.list(projectId!),
    enabled: !!projectId,
    staleTime: 60_000,
  });

  const { data: pipelineAssignment } = useQuery({
    queryKey: ['pipelines', 'assignment', projectId],
    queryFn: () => pipelinesApi.getAssignment(projectId!),
    enabled: !!projectId,
    staleTime: 60_000,
  });

  const assignPipelineMutation = useMutation({
    mutationFn: (pipelineId: string) => pipelinesApi.setAssignment(projectId!, pipelineId),
    onSuccess: (assignment) => {
      if (!projectId) return;
      queryClient.setQueryData(['pipelines', 'assignment', projectId], assignment);
    },
  });

  return {
    savedPipelines,
    savedPipelinesLoading,
    savedPipelinesError,
    refetchSavedPipelines,
    pipelineAssignment,
    assignPipelineMutation,
  };
}
