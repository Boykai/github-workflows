import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { toolsApi, ApiError } from '@/services/api';
import type { RepoMcpConfigResponse, RepoMcpServerConfig, RepoMcpServerUpdate } from '@/types';

export const repoMcpKeys = {
  all: ['repo-mcp'] as const,
  detail: (projectId: string) => [...repoMcpKeys.all, projectId] as const,
};

export function useRepoMcpConfig(projectId: string | null | undefined) {
  const queryClient = useQueryClient();
  const [updatingServerName, setUpdatingServerName] = useState<string | null>(null);
  const [deletingServerName, setDeletingServerName] = useState<string | null>(null);
  const query = useQuery<RepoMcpConfigResponse, ApiError>({
    queryKey: repoMcpKeys.detail(projectId ?? ''),
    queryFn: () => toolsApi.getRepoConfig(projectId!),
    staleTime: 60_000,
    enabled: !!projectId,
  });

  const updateMutation = useMutation<
    RepoMcpServerConfig,
    ApiError,
    { serverName: string; data: RepoMcpServerUpdate }
  >({
    mutationFn: ({ serverName, data }) => {
      setUpdatingServerName(serverName);
      return toolsApi.updateRepoServer(projectId!, serverName, data);
    },
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: repoMcpKeys.detail(projectId) });
      }
    },
    onSettled: () => {
      setUpdatingServerName(null);
    },
  });

  const deleteMutation = useMutation<RepoMcpServerConfig, ApiError, string>({
    mutationFn: (serverName) => {
      setDeletingServerName(serverName);
      return toolsApi.deleteRepoServer(projectId!, serverName);
    },
    onSuccess: () => {
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: repoMcpKeys.detail(projectId) });
      }
    },
    onSettled: () => {
      setDeletingServerName(null);
    },
  });

  return {
    repoConfig: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    rawError: query.error ?? null,
    refetch: query.refetch,
    updateRepoServer: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updatingServerName,
    updateError: updateMutation.error?.message ?? null,
    resetUpdateError: updateMutation.reset,
    deleteRepoServer: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    deletingServerName,
    deleteError: deleteMutation.error?.message ?? null,
    resetDeleteError: deleteMutation.reset,
  };
}
