import { useQuery } from '@tanstack/react-query';
import { toolsApi, ApiError } from '@/services/api';
import type { RepoMcpConfigResponse } from '@/types';

export const repoMcpKeys = {
  all: ['repo-mcp'] as const,
  detail: (projectId: string) => [...repoMcpKeys.all, projectId] as const,
};

export function useRepoMcpConfig(projectId: string | null | undefined) {
  const query = useQuery<RepoMcpConfigResponse, ApiError>({
    queryKey: repoMcpKeys.detail(projectId ?? ''),
    queryFn: () => toolsApi.getRepoConfig(projectId!),
    staleTime: 60_000,
    enabled: !!projectId,
  });

  return {
    repoConfig: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
    refetch: query.refetch,
  };
}