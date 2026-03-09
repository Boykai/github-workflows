/**
 * useAgentTools — TanStack Query hooks for agent-tool assignment management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentToolsApi, ApiError } from '@/services/api';
import type { ToolChip } from '@/types';

export const agentToolKeys = {
  tools: (agentId: string) => ['agents', agentId, 'tools'] as const,
};

export function useAgentTools(
  projectId: string | null | undefined,
  agentId: string | null | undefined
) {
  const queryClient = useQueryClient();

  const query = useQuery<{ tools: ToolChip[] }>({
    queryKey: agentToolKeys.tools(agentId ?? ''),
    queryFn: () => agentToolsApi.getTools(projectId!, agentId!),
    staleTime: 60_000,
    enabled: !!projectId && !!agentId,
  });

  const updateMutation = useMutation<{ tools: ToolChip[] }, ApiError, string[]>({
    mutationFn: (toolIds) => agentToolsApi.updateTools(projectId!, agentId!, toolIds),
    onSuccess: () => {
      if (agentId) queryClient.invalidateQueries({ queryKey: agentToolKeys.tools(agentId) });
    },
  });

  return {
    tools: query.data?.tools ?? [],
    isLoading: query.isLoading,
    updateTools: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
  };
}
