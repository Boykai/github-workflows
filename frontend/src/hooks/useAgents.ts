import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  agentsApi,
  type AgentConfig,
  type AgentCreate,
  type AgentCreateResult,
  type AgentUpdate,
  type AgentDeleteResult,
  type AgentChatMessage,
  type AgentChatResponse,
  type ApiError,
} from '@/services/api';
import { STALE_TIME_LONG } from '@/constants';

export const agentKeys = {
  all: ['agents'] as const,
  list: (projectId: string) => [...agentKeys.all, 'list', projectId] as const,
};

export function useAgentsList(projectId: string | null | undefined) {
  return useQuery<AgentConfig[]>({
    queryKey: agentKeys.list(projectId ?? ''),
    queryFn: () => agentsApi.list(projectId!),
    staleTime: STALE_TIME_LONG,
    enabled: !!projectId,
  });
}

export function useCreateAgent(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentCreateResult, ApiError, AgentCreate>({
    mutationFn: (data) => agentsApi.create(projectId!, data),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
    },
  });
}

export function useUpdateAgent(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentCreateResult, ApiError, { agentId: string; data: AgentUpdate }>({
    mutationFn: ({ agentId, data }) => agentsApi.update(projectId!, agentId, data),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
    },
  });
}

export function useDeleteAgent(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation<AgentDeleteResult, ApiError, string>({
    mutationFn: (agentId) => agentsApi.delete(projectId!, agentId),
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
    },
  });
}

export function useAgentChat(projectId: string | null | undefined) {
  return useMutation<AgentChatResponse, ApiError, AgentChatMessage>({
    mutationFn: (data) => agentsApi.chat(projectId!, data),
  });
}
