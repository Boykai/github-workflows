import { useQuery, useMutation, useQueryClient, type InfiniteData } from '@tanstack/react-query';
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
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { useUndoableDelete } from '@/hooks/useUndoableDelete';
import type { PaginatedResponse } from '@/types';

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

export function useAgentsListPaginated(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  const result = useInfiniteList<AgentConfig>({
    queryKey: [...agentKeys.list(projectId ?? ''), 'paginated'],
    queryFn: (params) => agentsApi.listPaginated(projectId!, params),
    limit: 25,
    staleTime: STALE_TIME_PROJECTS,
    enabled: !!projectId,
  });

  return {
    ...result,
    invalidate: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
      }
    },
  };
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
  return useMutation<AgentCreateResult, ApiError, AgentCreate, {
    pendingSnapshot: AgentConfig[] | undefined;
    pendingKey: readonly string[];
  } | undefined>({
    mutationFn: (data) => agentsApi.create(projectId!, data),
    onMutate: async (data: AgentCreate) => {
      if (!projectId) return;
      const pendingKey = agentKeys.pending(projectId);
      await queryClient.cancelQueries({ queryKey: pendingKey });
      const pendingSnapshot = queryClient.getQueryData<AgentConfig[]>(pendingKey);

      const now = new Date().toISOString();
      const placeholder = {
        id: `temp-${Date.now()}`,
        name: data.name,
        slug: '',
        description: data.description ?? '',
        icon_name: data.icon_name ?? null,
        system_prompt: data.system_prompt,
        default_model_id: data.default_model_id ?? '',
        default_model_name: data.default_model_name ?? '',
        status: 'pending_pr' as const,
        tools: data.tools ?? [],
        status_column: data.status_column ?? null,
        github_issue_number: null,
        github_pr_number: null,
        branch_name: null,
        source: 'local' as const,
        created_at: now,
        _optimistic: true,
      } satisfies AgentConfig & { _optimistic: boolean };

      queryClient.setQueryData<AgentConfig[]>(pendingKey, [
        placeholder,
        ...(pendingSnapshot ?? []),
      ]);

      return { pendingSnapshot, pendingKey };
    },
    onSuccess: () => {
      toast.success('Agent created');
    },
    onError: (error, _variables, context) => {
      if (context?.pendingKey) {
        if (context.pendingSnapshot !== undefined) {
          queryClient.setQueryData(context.pendingKey, context.pendingSnapshot);
        } else {
          // setQueryData(key, undefined) is a no-op in TanStack Query v5;
          // removeQueries clears the optimistic entry when no cache existed before
          queryClient.removeQueries({ queryKey: context.pendingKey });
        }
      }
      toast.error(error.message || 'Failed to create agent', { duration: Infinity });
    },
    onSettled: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      }
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
  return useMutation<AgentDeleteResult, ApiError, string, {
    snapshot: AgentConfig[] | undefined;
    queryKey: readonly string[];
    paginatedSnapshot: InfiniteData<PaginatedResponse<AgentConfig>> | undefined;
    paginatedQueryKey: string[];
  } | undefined>({
    mutationFn: async (agentId) => {
      const result = await agentsApi.delete(projectId!, agentId);
      if (!result.success) {
        throw new Error(`Failed to delete agent "${agentId}"`);
      }
      return result;
    },
    onMutate: async (agentId: string) => {
      if (!projectId) return;
      const queryKey = agentKeys.list(projectId);
      const paginatedQueryKey = [...agentKeys.list(projectId), 'paginated'];
      await queryClient.cancelQueries({ queryKey });
      await queryClient.cancelQueries({ queryKey: paginatedQueryKey });
      const snapshot = queryClient.getQueryData<AgentConfig[]>(queryKey);
      const paginatedSnapshot = queryClient.getQueryData<InfiniteData<PaginatedResponse<AgentConfig>>>(paginatedQueryKey);

      if (snapshot) {
        queryClient.setQueryData<AgentConfig[]>(queryKey, (old) =>
          old?.filter((agent) => agent.id !== agentId),
        );
      }

      if (paginatedSnapshot?.pages) {
        queryClient.setQueryData<InfiniteData<PaginatedResponse<AgentConfig>>>(paginatedQueryKey, {
          ...paginatedSnapshot,
          pages: paginatedSnapshot.pages.map((page) => ({
            ...page,
            items: page.items.filter((item) => item.id !== agentId),
          })),
        });
      }

      return { snapshot, queryKey, paginatedSnapshot, paginatedQueryKey };
    },
    onSuccess: () => {
      if (projectId) queryClient.invalidateQueries({ queryKey: agentKeys.pending(projectId) });
      toast.success('Agent deleted');
    },
    onError: (error, _variables, context) => {
      if (context?.snapshot && context.queryKey) {
        queryClient.setQueryData(context.queryKey, context.snapshot);
      }
      if (context?.paginatedSnapshot && context.paginatedQueryKey) {
        queryClient.setQueryData(context.paginatedQueryKey, context.paginatedSnapshot);
      }
      toast.error(error.message || 'Failed to delete agent', { duration: Infinity });
    },
    onSettled: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: agentKeys.list(projectId) });
      }
    },
  });
}

export function useUndoableDeleteAgent(projectId: string | null | undefined) {
  const { undoableDelete, pendingIds } = useUndoableDelete({
    queryKeys: projectId
      ? [agentKeys.list(projectId), [...agentKeys.list(projectId), 'paginated']]
      : [],
  });

  return {
    deleteAgent: (agentId: string, agentName: string) =>
      undoableDelete({
        id: agentId,
        entityLabel: `Agent: ${agentName}`,
        onDelete: async () => {
          const result = await agentsApi.delete(projectId!, agentId);
          if (!result.success) {
            throw new Error(`Failed to delete agent "${agentName}"`);
          }
        },
      }),
    pendingIds,
  };
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
