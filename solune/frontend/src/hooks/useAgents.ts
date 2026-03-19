import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  agentsApi,
  type AgentConfig,
  type AgentCreate,
  type AgentCreateResult,
  type AgentUpdate,
  type AgentDeleteResult,
  type AgentPendingCleanupResult,
  type AgentChatMessage,
  type AgentChatResponse,
  type BulkModelUpdateResult,
  type ApiError,
} from '@/services/api';
import { STALE_TIME_PROJECTS } from '@/constants';

export const agentKeys = {
  all: ['agents'] as const,
  list: (projectId: string) => [...agentKeys.all, 'list', projectId] as const,
  pending: (projectId: string) => [...agentKeys.all, 'pending', projectId] as const,
};

export function useAgentsList(projectId: string | null | undefined) {
  return useQuery<AgentConfig[]>({
    queryKey: agentKeys.list(projectId ?? ''),
    queryFn: () => agentsApi.list(projectId!),
    staleTime: STALE_TIME_PROJECTS,
    enabled: !!projectId,
  });
}

export function usePendingAgentsList(projectId: string | null | undefined) {
  return useQuery<AgentConfig[]>({
    queryKey: agentKeys.pending(projectId ?? ''),
    queryFn: () => agentsApi.pending(projectId!),
    staleTime: STALE_TIME_PROJECTS,
    enabled: !!projectId,
  });
}

export function useCreateAgent(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentCreateResult, ApiError, AgentCreate>({
    mutationFn: (data) => agentsApi.create(projectId!, data),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      toast.success('Agent created');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create agent', { duration: Infinity });
    },
  });
}

export function useUpdateAgent(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentCreateResult, ApiError, { agentId: string; data: AgentUpdate }>({
    mutationFn: ({ agentId, data }) => agentsApi.update(projectId!, agentId, data),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      }
      toast.success('Agent updated');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update agent', { duration: Infinity });
    },
  });
}

export function useDeleteAgent(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentDeleteResult, ApiError, string>({
    mutationFn: (agentId) => agentsApi.delete(projectId!, agentId),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      toast.success('Agent deleted');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete agent', { duration: Infinity });
    },
  });
}

export function useClearPendingAgents(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentPendingCleanupResult, ApiError>({
    mutationFn: () => agentsApi.clearPending(projectId!),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      }
      toast.success('Pending agents cleared');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to clear pending agents', { duration: Infinity });
    },
  });
}

export function useAgentChat(projectId: string | null | undefined) {
  return useMutation<AgentChatResponse, ApiError, AgentChatMessage>({
    mutationFn: (data) => agentsApi.chat(projectId!, data),
  });
}

export function useBulkUpdateModels(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<
    BulkModelUpdateResult,
    ApiError,
    { targetModelId: string; targetModelName: string }
  >({
    mutationFn: ({ targetModelId, targetModelName }) =>
      agentsApi.bulkUpdateModels(projectId!, targetModelId, targetModelName),
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
        queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      }
      toast.success('Models updated');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update models', { duration: Infinity });
    },
  });
}
